from flask import Flask
import firebase_admin
from firebase_admin import db, credentials

cred = credentials.Certificate("firestore_api/key.json")
firebase_admin.initialize_app(cred, {"databaseURL": "https://team-jerry-default-rtdb.asia-southeast1.firebasedatabase.app/"})

def create_app():
    app = Flask(__name__)

    from .api import userAPI

    app.register_blueprint(userAPI, url_prefix='/user')

    return app