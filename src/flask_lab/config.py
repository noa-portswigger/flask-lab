# SPDX-License-Identifier: MIT
# Copyright (c) 2025 flask-lab contributors

import logging
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SqliteConfig:
    uri: str = 'sqlite:////tmp/todo.db'


@dataclass
class RdsConfig:
    host: str
    port: int
    name: str
    user: str
    region: str
    hostname_override: str | None = None


@dataclass
class DatabaseConfig:
    type: str
    sqlite: SqliteConfig | None = None
    rds: RdsConfig | None = None


@dataclass
class Config:
    database: DatabaseConfig = field(default_factory=lambda: DatabaseConfig(type='sqlite'))


def load_config(config_path: str) -> Config:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    logger.info(f"Loading config from: {config_path}")
    with open(path, 'rb') as f:
        data = tomllib.load(f)

    # Parse database config
    db_data = data.get('database', {})

    # Validate database type
    db_type = db_data.get('type')
    if db_type not in ('sqlite', 'rds'):
        raise ValueError(
            f"Invalid database type: '{db_type}'. Must be either 'sqlite' or 'rds'"
        )

    # Parse sqlite config if type is sqlite
    if db_type == 'sqlite':
        sqlite_data = db_data.get('sqlite', {})
        sqlite_config = SqliteConfig(
            uri=sqlite_data.get('uri', 'sqlite:////tmp/todo.db')
        )
        rds_config = None
    else:
        # Parse rds config - require fields when the type is 'rds'
        rds_data = db_data.get('rds', {})
        required_fields = ['host', 'port', 'name', 'user', 'region']
        missing_fields = [f for f in required_fields if f not in rds_data]
        if missing_fields:
            raise ValueError(
                f"Missing required RDS configuration fields: {', '.join(missing_fields)}"
            )

        rds_config = RdsConfig(
            host=rds_data['host'],
            port=rds_data['port'],
            name=rds_data['name'],
            user=rds_data['user'],
            region=rds_data['region'],
            hostname_override=rds_data.get('hostname_override')
        )
        sqlite_config = None

    database_config = DatabaseConfig(
        type=db_type,
        sqlite=sqlite_config,
        rds=rds_config
    )

    return Config(database=database_config)
