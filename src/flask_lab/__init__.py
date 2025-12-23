# SPDX-License-Identifier: MIT
# Copyright (c) 2025 flask-lab contributors

from flask import Flask
import gunicorn.app.base


app = Flask(__name__)


@app.route("/")
def hello():
    return {"message": "Hello from Flask!"}


def create_app():
    return app


class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


def main():
    options = {
        'bind': '0.0.0.0:8080',
        'workers': 4,
    }
    StandaloneApplication(app, options).run()


if __name__ == '__main__':
    main()
