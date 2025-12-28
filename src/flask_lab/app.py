# SPDX-License-Identifier: MIT
# Copyright (c) 2025 flask-lab contributors

import os
import tomllib
from pathlib import Path
import boto3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
import gunicorn.app.base
from flask_lab.models import Base
from flask_lab.todo_view import TodoView


def load_config():
    config_path = Path(os.getenv('CONFIG_PATH', 'config.toml'))
    if not config_path.exists():
        return None

    with open(config_path, 'rb') as f:
        return tomllib.load(f)


def get_rds_iam_token(db_host, db_port, db_user, region):
    rds_client = boto3.client('rds', region_name=region)
    token = rds_client.generate_db_auth_token(
        DBHostname=db_host,
        Port=db_port,
        DBUsername=db_user,
        Region=region
    )
    return token


def get_database_uri(config):
    if not config:
        return 'sqlite:////tmp/todo.db'

    db_type = config.get('database', {}).get('type', 'sqlite')

    if db_type == 'sqlite':
        sqlite_config = config.get('database', {}).get('sqlite', {})
        return sqlite_config.get('uri', 'sqlite:////tmp/todo.db')

    if db_type == 'rds':
        rds_config = config.get('database', {}).get('rds', {})
        db_host = rds_config.get('host')
        db_port = rds_config.get('port', 5432)
        db_name = rds_config.get('name')
        db_user = rds_config.get('user')
        use_iam_auth = rds_config.get('use_iam_auth', True)
        region = rds_config.get('region', 'us-east-1')

        # Use hostname_override for connection URI if set, otherwise use host
        connection_host = rds_config.get('hostname_override', db_host)

        if use_iam_auth:
            token = get_rds_iam_token(db_host, db_port, db_user, region)
            return f"postgresql://{db_user}:{token}@{connection_host}:{db_port}/{db_name}"
        else:
            return f"postgresql://{db_user}@{connection_host}:{db_port}/{db_name}"

    return 'sqlite:////tmp/todo.db'


def setup_iam_token_refresh(engine, config):
    rds_config = config.get('database', {}).get('rds', {})
    db_host = rds_config.get('host')
    db_port = rds_config.get('port', 5432)
    db_user = rds_config.get('user')
    region = rds_config.get('region', 'us-east-1')

    @event.listens_for(engine, "do_connect")
    def receive_do_connect(dialect, conn_rec, cargs, cparams):
        token = get_rds_iam_token(db_host, db_port, db_user, region)
        cparams['password'] = token


def create_app():
    config = load_config()

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri(config)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db_type = config.get('database', {}).get('type', 'sqlite') if config else 'sqlite'
    use_iam_auth = False
    if db_type == 'rds' and config:
        use_iam_auth = config.get('database', {}).get('rds', {}).get('use_iam_auth', True)

    if use_iam_auth:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,
            'pool_recycle': 900,
        }

    db = SQLAlchemy(model_class=Base)
    db.init_app(app)

    with app.app_context():
        if use_iam_auth:
            setup_iam_token_refresh(db.engine, config)
        db.create_all()

    @app.route("/")
    def hello():
        return {"message": "Hello from Flask!"}

    # Initialize TodoView with db dependency
    todo_view = TodoView(db)

    # Register todo routes
    app.add_url_rule('/todos', view_func=todo_view.list_todos, methods=['GET'])
    app.add_url_rule('/todos/<int:todo_id>', view_func=todo_view.get_todo, methods=['GET'])
    app.add_url_rule('/todos', view_func=todo_view.create_todo, methods=['POST'])
    app.add_url_rule('/todos/<int:todo_id>', view_func=todo_view.update_todo, methods=['PUT'])
    app.add_url_rule('/todos/<int:todo_id>', view_func=todo_view.delete_todo, methods=['DELETE'])

    return app


class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

    def load(self):
        return self.application


def main():
    app = create_app()
    options = {
        'bind': '0.0.0.0:8080',
        'workers': 4,
        'accesslog': '-',
        'errorlog': '-',
    }
    StandaloneApplication(app, options).run()


if __name__ == '__main__':
    main()
