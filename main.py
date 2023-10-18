# External imports
from flask_ngrok import run_with_ngrok
from flask import Flask, request, session
from apscheduler.schedulers.background import BackgroundScheduler
import firebase_admin
from firebase_admin import db, credentials, firestore
from time import sleep
from dotenv import load_dotenv


# Internal imports
from api_firestore.__init__ import register_firebaseMS
from api_whatsapp.__init__ import register_whatsappMS
from api_dialogflow.__init__ import register_dialogflowMS
from api_openai.__init__ import register_openaiMS

app = Flask(__name__)
app.config['DEBUG'] = True
# run_with_ngrok(app)
load_dotenv()



if __name__ == '__main__':
    app = register_firebaseMS(app)
    app = register_dialogflowMS(app)
    app = register_whatsappMS(app)
    app = register_openaiMS(app)

    # app.run()  # adjust host and port as needed
    app.run(host='0.0.0.0', port=5000)