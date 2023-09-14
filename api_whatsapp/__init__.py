from flask import Flask
import firebase_admin
from firebase_admin import db, credentials, firestore
from .api import whatsappMS
def create_app():
    app = Flask(__name__)
    app.register_blueprint(whatsappMS)
    return app


def register_whatsappMS(app):
    app.register_blueprint(whatsappMS)
    return app


# For Testing
if __name__ == '__main__':
    create_app()