from flask import Flask
import firebase_admin
from firebase_admin import db, credentials, firestore
from .api import firebaseMS


# Check if Firebase app is already initialized
if not firebase_admin._apps:
    # Initialize Firebase Admin SDK
    cred = credentials.Certificate("api_firestore/key.json")
    firebase_admin.initialize_app(cred, {"databaseURL": "https://team-jerry-default-rtdb.asia-southeast1.firebasedatabase.app/"})

# Get a reference to the Firebase Realtime Database
db_reference = db.reference()



def create_app():
    app = Flask(__name__)
    app.register_blueprint(firebaseMS)
    # print(api.get_auth_token_from_firebase())
    return app


def register_firebaseMS(app):
    app.register_blueprint(firebaseMS)
    return app

# for testing
if __name__ == '__main__':
    create_app()