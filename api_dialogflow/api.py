from flask import Flask, request, Blueprint
import time 
import requests 
import os
from dotenv import load_dotenv
import logging
import json
import google.auth
from google.oauth2 import service_account
import google.auth.transport.requests
load_dotenv()
logging.basicConfig(level=logging.INFO)

#Internal imports
import Constants
dialogflowMS = Blueprint('dialogflowMS', __name__)

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
# @dialogflowMS.route("/run_sample", methods=["POST"])
# def send_user_input():
#     data = request.json  # Get the JSON data from the request body
#     text = data.get('message')
#     # userId = data.get('userId')

#     ## GEN SESS according to user ID TODO Dyanmic timeout session
#     userId = '84820351' #tmp
#     if userId not in userSession:
#         userSession[userId] = get_session_id(userId)
#     session_id = userSession[userId]
        
#     print("Function ran")
#     project_id = os.getenv("DIALOGFLOW_PROJECT_ID")
#     location_id = os.getenv("DIALOGFLOW_LOCATION_ID")
#     agent_id = os.getenv("DIALOGFLOW_AGENT_ID")

#     logging.info("Session ID: {}".format(session_id))
#     agent = f'projects/{project_id}/locations/{location_id}/agents/{agent_id}/sessions/{session_id}'

#     language_code = "en-US"

#     logging.info("Agent: {}".format(agent))

#     response = detect_intent_texts(agent, text, language_code)
#     ## To store each message in 
#     return response


# ---- Routes #
@dialogflowMS.route("/runModel", methods=["POST"])
def send_message_dialogflow():
    data = request.json  # Get the JSON data from the request body
    text = data.get('message')
    userId = data.get('userId')
    session_id = data.get('sessionId')
    project_id = os.getenv("DIALOGFLOW_PROJECT_ID")
    location_id = os.getenv("DIALOGFLOW_LOCATION_ID")
    agent_id = os.getenv("DIALOGFLOW_AGENT_ID")

    agent = f'projects/{project_id}/locations/{location_id}/agents/{agent_id}/sessions/{session_id}'

    language_code = "en-US"

    logging.info("Agent: {}".format(agent))

    response = detect_intent_texts(agent, text, language_code)

    dialogflowMessageRaw = response['queryResult']['responseMessages']
    intent_id = "unidentified"
    try:
        intent_id = response['queryResult']['intent']['displayName']
    except:
        None

    response_data = processRawDFMessage(dialogflowMessageRaw,intent_id, userId)

    return response_data

def processRawDFMessage(raw_message,intent_id,userId):
    print("RAW MESSAGE:",raw_message)
    response_data = {
        "message": "",
        "response_data": "",
        "data": "",
        "intent":intent_id,
    }
    idx = 0
    for message_data in raw_message:
        print("MESSAGE DATA:", message_data)
        try:
            message = message_data['text']['text'][0]
            process_message = message.split('-')
            if idx > 0:
                response_data["message"] += "\n\n"
            if process_message[0] != '' and process_message[0][0] == '/':
                endpoint = process_message[0]
                message_var = process_message[1]
                request_input = process_message[2]
                
                response_data["endpoint"] = endpoint
                response_data["data"] = request_input
                response_data["message"] += message_var
            else:
                response_data["message"] += process_message[1]
            idx+=1
        except Exception as e:
            print("Session Ended")
            response_data["message"] += "\nYou have been logged out. Thank you!\nEnter 'start'/'hi' to start the chatbot"
            del Constants.USER_SESSION[userId]  # User end session, remove session for user
    return response_data



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

