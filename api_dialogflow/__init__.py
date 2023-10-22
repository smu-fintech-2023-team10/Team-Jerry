from flask import Flask
import firebase_admin
from firebase_admin import db, credentials, firestore
from .api import dialogflowMS

def create_app():
    app = Flask(__name__)
    app.register_blueprint(dialogflowMS)
    return app


def register_dialogflowMS(app):
    app.register_blueprint(dialogflowMS)
    return app


# For Testing
if __name__ == '__main__':
    create_app()


