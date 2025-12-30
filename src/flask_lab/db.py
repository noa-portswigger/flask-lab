# SPDX-License-Identifier: MIT
# Copyright (c) 2025 flask-lab contributors

import logging

import boto3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

from flask_lab.config import Config, RdsConfig
from flask_lab.models import Base

logger = logging.getLogger(__name__)


def get_rds_iam_token(rds_config: RdsConfig) -> str:
    logger.info(f"Generating IAM token for user={rds_config.user} at {rds_config.host}:{rds_config.port} in region={rds_config.region}")
    rds_client = boto3.client('rds', region_name=rds_config.region)
    token = rds_client.generate_db_auth_token(
        DBHostname=rds_config.host,
        Port=rds_config.port,
        DBUsername=rds_config.user,
        Region=rds_config.region
    )
    logger.debug(f"IAM token generated successfully for {rds_config.user}@{rds_config.host}")
    return token


def build_uri(config: Config) -> str:
    rds = config.database.rds
    assert rds is not None, "rds config must be set when type is 'rds'"
    # Use hostname_override for connection URI if set, otherwise use host
    connection_host = rds.hostname_override or rds.host

    # No password in URI - it will be set by setup_iam_token_refresh callback
    return f"postgresql://{rds.user}@{connection_host}:{rds.port}/{rds.name}"


def setup_iam_token_refresh(engine, config: Config):
    rds = config.database.rds
    assert rds is not None, "rds config must be set when type is 'rds'"

    @event.listens_for(engine, "do_connect")
    def receive_do_connect(dialect, conn_rec, cargs, cparams):
        token = get_rds_iam_token(rds)
        cparams['password'] = token


def _init_sqlalchemy(
    app: Flask,
    db_uri: str,
) -> SQLAlchemy:
    """Common SQLAlchemy initialization logic"""
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    engine_options = {
        'pool_pre_ping': True,
        'pool_recycle': 900,
    }
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options

    db = SQLAlchemy(model_class=Base)
    db.init_app(app)
    return db


def init_sqlite(app: Flask, config: Config) -> SQLAlchemy:
    assert config.database.sqlite is not None, "sqlite config must be set when type is 'sqlite'"
    return _init_sqlalchemy(app, config.database.sqlite.uri)


def init_rds(app: Flask, config: Config) -> SQLAlchemy:
    db_uri = build_uri(config)
    db = _init_sqlalchemy(app, db_uri)
    with app.app_context():
        setup_iam_token_refresh(db.engine, config)
    return db


def init_db(app: Flask, config: Config) -> SQLAlchemy:
    """Initialize a database based on a configuration type"""
    match config.database.type:
        case 'sqlite':
            db = init_sqlite(app, config)
        case 'rds':
            db = init_rds(app, config)
        case _:
            raise ValueError(f"Unsupported database type: '{config.database.type}'. Must be 'sqlite' or 'rds'")

    with app.app_context():
        db.create_all()
    return db
