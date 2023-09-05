# External imports
from flask_ngrok import run_with_ngrok
from flask import Flask, request, session
from flask_session import Session  # Import the Session extension
from apscheduler.schedulers.background import BackgroundScheduler
import firebase_admin
from firebase_admin import db, credentials, firestore
from time import sleep
from dotenv import load_dotenv


# Internal imports
from firestore_api.__init__ import register_firebaseMS
from whatsapp_api.__init__ import register_whatsappMS
from whatsapp_api.api import refresh_twilio_auth_token



app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Set session timeout to 1 hour (in seconds)
run_with_ngrok(app)
Session(app)  # Initialize the Session extension
load_dotenv()



if __name__ == '__main__':
    app = register_firebaseMS(app)
    app = register_whatsappMS(app)

    app.run()  # adjust host and port as needed
