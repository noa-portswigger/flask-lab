# SPDX-License-Identifier: MIT
# Copyright (c) 2025 flask-lab contributors

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import gunicorn.app.base
from flask_lab.models import Base
from flask_lab.todo_view import TodoView


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/todo.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db = SQLAlchemy(model_class=Base)
    db.init_app(app)

    with app.app_context():
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
