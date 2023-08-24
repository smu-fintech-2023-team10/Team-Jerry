# External imports
import requests
import time
from twilio.rest import Client
from twilio.twiml.messaging_response import Message, MessagingResponse
from flask_ngrok import run_with_ngrok
from datetime import datetime, timedelta
from flask import Flask, request, session, jsonify
from flask_session import Session  # Import the Session extension
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import firebase_admin
from firebase_admin import db, credentials, firestore
from time import sleep
import os
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant
from dotenv import load_dotenv

# Internal imports
import Constants
import json
from twilio.rest import Client
from twilio.twiml.messaging_response import Message, MessagingResponse
from flask_ngrok import run_with_ngrok
import nlp_model
import helperFunctions
from firestore_api import create_app

# Load the environment variables from .env file

app = create_app()

app.config['DEBUG'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Set session timeout to 1 hour (in seconds)
run_with_ngrok(app)
Session(app)  # Initialize the Session extension
load_dotenv()

@app.route("/test", methods=['GET'])
def refresh_twilio_auth_token():
    root_ref = db.reference()
    # Get a reference to the specific user node using the provided user_id
    token = root_ref.child('auth_token').child('token').get()
    # Shut down the scheduler when exiting the app
    print("start")
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = token
    client = Client(account_sid, auth_token)
    auth_token_promotion = client.accounts.v1.auth_token_promotion().update()
    new_primary_auth_token = auth_token_promotion.auth_token
    client = Client(account_sid, new_primary_auth_token)
    print(client)
    secondary_auth_token = client.accounts.v1.secondary_auth_token().create()
    new_secondary_auth_token = secondary_auth_token.secondary_auth_token

   
    auth_token_ref = root_ref.child('auth_token')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    auth_token_ref.update({
        'secondary_token': new_secondary_auth_token,
        'token': new_primary_auth_token,
        'time': current_time
    })
    print("Token Updated")
    return client


@app.route("/")
def get_account_details():
    # session['account_no'] = "201770161001"
    # session['account_type'] = "D"
    session_str = json.dumps(dict(session))
    
    return session_str

@app.route("/getReply", methods=['POST'])
def get_message_reply():
    incoming_message = request.form['Body']  # Extract the incoming message content
    sender_phone_number = request.form['From'] # Extract the phone number
    print(incoming_message)
    print(sender_phone_number)
    if incoming_message == "join signal-press":
        helperFunctions.send_message('Hello! Welcome to OCBC Whatsapp Banking. What would you like to do today?', sender_phone_number, client)
    else:
        endpoint = nlp_model.generate_reply(incoming_message) #The relevant endpoints will be generated from the model to reply in whatsapp
        url = Constants.HOST_URL + endpoint
        data = {
            "accountNumber": Constants.ACCOUNT_NO,
            "phoneNumber": sender_phone_number
        }
        res = requests.post(url, json=data)
        print(str(res))
    return incoming_message  # Return the response as the HTTP response
    
@app.route("/unableToFindReply", methods=['POST'])
def reply_with_none():
    data = request.json
    phone_number = data.get('phoneNumber')  # Extract phone number from the JSON data
    helperFunctions.send_message('We are unable to find a reply for this.', phone_number, client)
    return 'We are unable to find a reply for this.'


# OCBC APIs
@app.route("/accountSummary", methods=['POST'])
def account_summary():
    url = "https://api.ocbc.com:8243/transactional/account/1.0/summary*?accountNo="+Constants.ACCOUNT_NO+"&accountType=" +Constants.ACCOUNT_TYPE
    payload={}
    headers = {
    'Authorization': 'Bearer ' + os.environ.get("ACCESS_TOKEN"),
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)
    return response.text


@app.route("/checkBalance" , methods=['POST'])
def get_account_balance():
    data = request.json  # Get the JSON data from the request body
    account_number = data.get('accountNumber')  # Extract account number from the JSON data
    phone_number = data.get('phoneNumber')  # Extract phone number from the JSON data
    url = "https://api.ocbc.com:8243/transactional/accountbalance/1.0/balance*?accountNo=" + account_number
    payload={}
    headers = {
    'Authorization': 'Bearer ' + os.environ.get("ACCESS_TOKEN")
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    print(response.text)
    helperFunctions.send_message(response.text, phone_number, client)
    return response.text

@app.route("/balanceEnquiry", methods=['POST'])
def balance_enquiry():

    url = "https://api.ocbc.com:8243/transactional/corp/balance/1.0/enquiry"

    payload = json.dumps({
    "AccountNo": Constants.ACCOUNT_NO,
    "AccountType": Constants.ACCOUNT_TYPE,
    "AccountCurrency": "SGD",
    "AccountBIC": "OCBCSGSGXXX",
    "TimeDepositNo": "129"
    })
    headers = {
    'Authorization': 'Bearer ' + os.environ.get("ACCESS_TOKEN"),
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
    return response.text

@app.route("/paynow")
def transfer_money():
    url = "https://api.ocbc.com:8243/transactional/paynow/1.0/sendPayNowMoney"

    payload = json.dumps({
    "Amount": 100,
    "ProxyType": "MSISDN",
    "ProxyValue": "+6594XXX567",
    "FromAccountNo": Constants.ACCOUNT_NO
    })
    headers = {
    'Authorization': 'Bearer ' + os.environ.get("ACCESS_TOKEN"),
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
    return response.text

@app.route("/paynowEnquiry", methods=['POST'])
def paynow_enquiry():
    url = "https://api.ocbc.com:8243/transactional/paynowenquiry/1.0/payNowEnquiry"

    payload = json.dumps({
    "ProxyType": "MSISDN", #OR NRIC
    "ProxyValue": "+6597988922" #OR S9801118H
    })    
    headers = {
    'Authorization': 'Bearer ' + os.environ.get("ACCESS_TOKEN"),
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
    return response.text


@app.route("/last6MonthsStatement", methods=['POST'])
def last_6month_statement():
    url = "https://api.ocbc.com:8243/transactional/account/1.0/recentAccountActivity*?accountNo="+Constants.ACCOUNT_NO+"&accountType=" +Constants.ACCOUNT_TYPE

    payload={}
    headers = {
    'Authorization': 'Bearer ' + os.environ.get("ACCESS_TOKEN")
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)
    return response.text

#Firestore RealtimeDB APIs
def get_auth_token_from_firebase():
    try:
        # Get a reference to the root of the Realtime Database
        root_ref = db.reference()

        # Get a reference to the specific user node using the provided user_id
        auth_token = root_ref.child('auth_token')

        # Retrieve the user data
        auth_token_data = auth_token.get()

        return auth_token_data
    except Exception as e:
        return f"An Error occurred: {e}"


@app.route('/add', methods=['POST'])
def create():
    try:
        data = request.json  # Get the JSON data from the request body

        id_value = data.get('id')  # Get the id_value from the JSON data, ID value is phone number as it is unique

        # Get a reference to the root of the Realtime Database
        root_ref = db.reference()

        # Create a new child node with the provided id_value as the key
        user_ref = root_ref.child('user').child(id_value)
        user_ref.set(data)  # Use the parsed JSON data

        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error occurred: {e}"
    
@app.route('/lastTokenRefreshTime', methods=['GET'])
def get_token_refresh_time():
        # Get a reference to the root of the Realtime Database
        root_ref = db.reference()

        # Get a reference to the specific user node using the provided user_id
        last_refresh_time = root_ref.child('auth_token').child('time').get()
        token = root_ref.child('auth_token').child('token').get()
        print(token)
        print(last_refresh_time)
        return {"lastRefreshDateTime:":last_refresh_time, "oldAuthToken":token}


@app.route('/read/<user_id>', methods=['GET'])
def read(user_id):
    try:
        # Get a reference to the root of the Realtime Database
        root_ref = db.reference()

        # Get a reference to the specific user node using the provided user_id
        user_ref = root_ref.child('user').child(user_id)

        # Retrieve the user data
        user_data = user_ref.get()

        if user_data:
            return jsonify(user_data), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return f"An Error occurred: {e}"

@app.route('/update/<user_id>', methods=['PUT'])
def update(user_id):
    try:
        # Get a reference to the root of the Realtime Database
        root_ref = db.reference()

        # Get a reference to the specific user node using the provided user_id
        user_ref = root_ref.child('user').child(user_id)

        # Update the user data with the new data from the request
        user_ref.update(request.json)

        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error occurred: {e}"

@app.route('/delete/<user_id>', methods=['DELETE'])
def delete(user_id):
    try:
        # Get a reference to the root of the Realtime Database
        root_ref = db.reference()

        # Get a reference to the specific user node using the provided user_id
        user_ref = root_ref.child('user').child(user_id)

        # Delete the user node
        user_ref.delete()

        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error occurred: {e}"


if __name__ == '__main__':
    client = refresh_twilio_auth_token()
    # Set up the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_twilio_auth_token, 'interval', hours=20)
    scheduler.start()
    app.run()  # adjust host and port as needed


# revalidate token
