# SPDX-License-Identifier: MIT
# Copyright (c) 2025 flask-lab contributors

from flask import jsonify, request
from sqlalchemy import select

from flask_lab.models import Todo


class TodoView:
    def __init__(self, db):
        self.db = db

    def list_todos(self):
        todos = self.db.session.execute(select(Todo)).scalars().all()
        return jsonify([todo.to_dict() for todo in todos])

    def get_todo(self, todo_id):
        todo = self.db.get_or_404(Todo, todo_id)
        return jsonify(todo.to_dict())

    def create_todo(self):
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({'error': 'Title is required'}), 400

        todo = Todo(
            title=data['title'],
            completed=data.get('completed', False)
        )
        self.db.session.add(todo)
        self.db.session.commit()
        return jsonify(todo.to_dict()), 201

    def update_todo(self, todo_id):
        todo = self.db.get_or_404(Todo, todo_id)
        data = request.get_json()

        if 'title' in data:
            todo.title = data['title']
        if 'completed' in data:
            todo.completed = data['completed']

        self.db.session.commit()
        return jsonify(todo.to_dict())

    def delete_todo(self, todo_id):
        todo = self.db.get_or_404(Todo, todo_id)
        self.db.session.delete(todo)
        self.db.session.commit()
        return '', 204
