# SPDX-License-Identifier: MIT
# Copyright (c) 2025 flask-lab contributors

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    return {"message": "Hello from Flask!"}


def create_app():
    return app
