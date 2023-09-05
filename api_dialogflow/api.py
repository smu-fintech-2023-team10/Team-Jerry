from flask import Flask, request, Blueprint
import hashlib
import time 
import requests 
import os
from dotenv import load_dotenv
import logging

import google.auth
from google.oauth2 import service_account
import google.auth.transport.requests

load_dotenv()
logging.basicConfig(level=logging.INFO)

dialogflowMS = Blueprint('dialogflowMS', __name__)

# ---- Helper functions #
#TODO: Fix hashing algo + session stored in Firebase
def generate_shortened_hash(input_string):
    md5_hash = hashlib.md5(input_string.encode())
    shortened_hash = md5_hash.hexdigest()[:7]
    return shortened_hash

def get_session_id():
    #generate a random session id based on md5 hash of current time concat 7 
    current_timestamp = str(int(time.time()))
    shortened_hash = generate_shortened_hash(current_timestamp)

    print(shortened_hash)
    return shortened_hash

def get_access_token():
    SERVICE_ACCOUNT_FILE = 'api_dialogflow/gcloud.json'

    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    request = google.auth.transport.requests.Request()
    credentials.refresh(request)

    logging.info("Access token: {}".format(credentials.token))

    return credentials.token

# ---- Routes #
@dialogflowMS.route("/run_sample", methods=["POST"])
def send_user_input():
    data = request.json  # Get the JSON data from the request body
    text = data.get('message')  
    print("Function ran")
    project_id = os.getenv("DIALOGFLOW_PROJECT_ID")
    location_id = os.getenv("DIALOGFLOW_LOCATION_ID")
    agent_id = os.getenv("DIALOGFLOW_AGENT_ID")

    #TODO: session store in Flask 
    session_id = get_session_id()
    logging.info("Session ID: {}".format(session_id))
    agent = f'projects/{project_id}/locations/{location_id}/agents/{agent_id}/sessions/{session_id}'

    language_code = "en-US"

    logging.info("Agent: {}".format(agent))

    response = detect_intent_texts(agent, text, language_code)
    return response

def detect_intent_texts(agent, text, language_code):
    json_message = {
        "queryInput": {
            "text": {
                "text": text
            },
            "languageCode": language_code
        },
        "queryParams": {
            "timeZone": "Asia/Singapore"
        }
    }

    access_token = get_access_token()
    
    headers = {
        "Authorization": "Bearer {}".format(access_token),
        "x-goog-user-project": os.getenv("DIALOGFLOW_PROJECT_ID"),
        "Content-Type": "application/json"
    }

    url = f"https://asia-southeast1-dialogflow.googleapis.com/v3/{agent}:detectIntent"
    
    logging.info("URL: %s", url)
    logging.info("Headers: %s", headers)
    logging.info("JSON Message: %s", json_message)

    response = requests.post(url, headers=headers, json=json_message)

    if response.status_code == 200:
        logging.info("Response: %s", response.json())
    else:
        logging.error("Error %s: %s", response.status_code, response.text)

    return response.json()  # return the response in case it's needed in future


