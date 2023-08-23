from flask import Flask
import firebase_admin
from firebase_admin import db, credentials
import json
import os
from dotenv import load_dotenv


load_dotenv()
json_key_string = os.getenv("FIRESTORE_API_KEY")
json_key_dict = json.loads(json_key_string)

cred = credentials.Certificate(json_key_dict)
firebase_admin.initialize_app(cred, {"databaseURL": "https://smu-fyp-3a677-default-rtdb.asia-southeast1.firebasedatabase.app"})

def create_app():
    app = Flask(__name__)

    return app