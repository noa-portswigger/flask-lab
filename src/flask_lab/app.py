# SPDX-License-Identifier: MIT
# Copyright (c) 2025 flask-lab contributors

import logging
import os

import gunicorn.app.base
from flask import Flask

from flask_lab import db
from flask_lab.config import load_config
from flask_lab.todo_view import TodoView

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)

    config_path = os.getenv('CONFIG_PATH', 'config.toml')
    config = load_config(config_path)

    database = db.init_db(app, config)

    @app.route("/")
    def hello():
        return {"message": "Hello from Flask"}

    # Initialize TodoView with db dependency
    todo_view = TodoView(database)

    # Register todo routes
    app.add_url_rule('/todos', view_func=todo_view.list_todos, methods=['GET'])
    app.add_url_rule('/todos/<int:todo_id>', view_func=todo_view.get_todo, methods=['GET'])
    app.add_url_rule('/todos', view_func=todo_view.create_todo, methods=['POST'])
    app.add_url_rule('/todos/<int:todo_id>', view_func=todo_view.update_todo, methods=['PUT'])
    app.add_url_rule('/todos/<int:todo_id>', view_func=todo_view.delete_todo, methods=['DELETE'])

    return app


class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app: Flask, options: dict[str, str | int]) -> None:
        self.options = options
        self.application = app
        super().__init__()

    def load_config(self) -> None:
        for key, value in self.options.items():
            # gunicorn guarantees cfg exists after super().__init__(), but type checker can't infer this
            self.cfg.set(key, value)  # type: ignore[union-attr]

    def load(self) -> Flask:
        return self.application

def setup_logging() -> None:
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %z'
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


def main() -> None:
    setup_logging()
    logger.info("Starting application")
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
