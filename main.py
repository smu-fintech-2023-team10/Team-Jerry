# External imports
import requests
import time
from twilio.rest import Client
from twilio.twiml.messaging_response import Message, MessagingResponse
from flask_ngrok import run_with_ngrok
from datetime import datetime, timedelta
from flask import Flask, request, session
from flask_session import Session  # Import the Session extension
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import firebase_admin
from firebase_admin import db, credentials, firestore
from time import sleep
import os
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant

cred = credentials.Certificate("firestore_api/key.json")
firebase_admin.initialize_app(cred, {"databaseURL": "https://team-jerry-default-rtdb.asia-southeast1.firebasedatabase.app/"})

# Internal imports
import Constants
import json
import nlp_model
import helperFunctions
from firestore_api import create_app
from firestore_api.api import get_token_refresh_time

app = create_app()

app.config['DEBUG'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Set session timeout to 1 hour (in seconds)
run_with_ngrok(app)
Session(app)  # Initialize the Session extension

account_sid = Constants.TWILIO_ACCOUNT_SID
auth_token = Constants.TWILIO_AUTH_TOKEN
api_key = Constants.TWILIO_API_KEY
api_secret = Constants.API_SECRET
client = Client(account_sid, auth_token)

@app.route("/test", methods=['GET'])
def refresh_twilio_auth_token():
    # Shut down the scheduler when exiting the app
    print("startanr")
    account_sid = Constants.TWILIO_ACCOUNT_SID
    root_ref = db.reference()
    # Get a reference to the specific user node using the provided user_id
    last_refresh_time = root_ref.child('auth_token').child('time').get()
    token = root_ref.child('auth_token').child('token').get()
    print(token)
    print(last_refresh_time)
    client = Client(account_sid, token)
    auth_token = client.tokens.create()
    print(type(auth_token))
    # auth_token_ref = root_ref.child('auth_token')
    # current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    # auth_token_ref.update({
    #     'token': auth_token,  # or another appropriate attribute if `sid` isn't what you're looking for
    #     'time': current_time
    # })
    return {"lastRefreshDateTime:":last_refresh_time, "oldAuthToken":token}


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
        helperFunctions.send_message('Hello! Welcome to OCBC Whatsapp Banking. What would you like to do today?', sender_phone_number)
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
    helperFunctions.send_message('We are unable to find a reply for this.', phone_number)
    return 'We are unable to find a reply for this.'


# OCBC APIs
@app.route("/accountSummary", methods=['POST'])
def account_summary():
    url = "https://api.ocbc.com:8243/transactional/account/1.0/summary*?accountNo="+Constants.ACCOUNT_NO+"&accountType=" +Constants.ACCOUNT_TYPE
    payload={}
    headers = {
    'Authorization': 'Bearer ' + Constants.ACCESS_TOKEN,
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
    'Authorization': 'Bearer ' + Constants.ACCESS_TOKEN
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    print(response.text)
    helperFunctions.send_message(response.text, phone_number)
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
    'Authorization': 'Bearer ' + Constants.ACCESS_TOKEN,
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
    'Authorization': 'Bearer ' + Constants.ACCESS_TOKEN,
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
    'Authorization': 'Bearer ' + Constants.ACCESS_TOKEN,
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
    'Authorization': 'Bearer ' + Constants.ACCESS_TOKEN
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)
    return response.text

def is_time_more_than_x_hours(input_time_str_with_hour,hours):
    # Convert the input time string with hour to a datetime object
    input_time = datetime.strptime(input_time_str_with_hour, '%Y-%m-%d %H:%M:%S')

    # Get the current time
    current_time = datetime.now()

    # Calculate the time difference between input time and current time
    time_difference = input_time - current_time

    # Define a timedelta for 20 hours
    twenty_hours = timedelta(hours=hours)

    # Compare the time difference with twenty_hours
    if time_difference > twenty_hours:
        return True
    else:
        return False



if __name__ == '__main__':
    # Set up the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_twilio_auth_token, 'interval', hours=20)
    scheduler.start()
    refresh_twilio_auth_token()
    app.run()  # adjust host and port as needed


# revalidate token