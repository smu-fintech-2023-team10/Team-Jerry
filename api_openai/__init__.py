from flask import Flask
from .api import openaiMS

def create_app():
    app = Flask(__name__)
    app.register_blueprint(openaiMS)
    return app


def register_openaiMS(app):
    app.register_blueprint(openaiMS)
    return app


# For Testing
if __name__ == '__main__':
    create_app()


