from flask import Flask
import firebase_admin
from firebase_admin import db, credentials, firestore

# cred = credentials.Certificate("firestore_api/key.json")
# firebase_admin.initialize_app(cred, {"databaseURL": "https://team-jerry-default-rtdb.asia-southeast1.firebasedatabase.app/"})
# from api import *
from .api import userAPI

def create_app():
    app = Flask(__name__)

    app.register_blueprint(userAPI)
    # print(api.get_auth_token_from_firebase())
    
    return app


create_app()