# External imports
import atexit
import datetime
import firebase_admin
import json
import nlp_model
import os
import requests
import time
from firebase_admin import credentials, db, firestore
from flask import Flask, jsonify, request, session
from flask_ngrok import run_with_ngrok
from flask_session import Session
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant
from twilio.rest import Client
from twilio.twiml.messaging_response import Message, MessagingResponse
from time import sleep
from dotenv import load_dotenv

# Internal imports
import Constants
import helperFunctions
from firestore_api import create_app

# ======= SETUP =======

load_dotenv()
root_ref = db_reference
whatsappMS = Blueprint('whatsappMS', __name__)

# ======= END SETUP =======

# ======= ROUTES =======

# Test Route
def refresh_twilio_auth_token():
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

@whatsappMS.route("/getReply", methods=['POST'])
def get_message_reply():
    incoming_message = request.form['Body']  # Extract the incoming message content
    sender_phone_number = request.form['From'] # Extract the phone number
    data = {
        "message": incoming_message,
        "userId": sender_phone_number
    }
    url = os.getenv("HOST_URL") + "/runModel"
    response_data = requests.post(url, json=data)
    response = setup_ocbc_api_request(response_data)
    # Default success response
    print(response.text)
    send_message(response.text, phone_number, client)
    return incoming_message  # Return the response as the HTTP response

@whatsappMS.route("/unableToFindReply", methods=['POST'])
def reply_with_none():
    data = request.json
    phone_number = data.get('phoneNumber')  # Extract phone number from the JSON data
    send_message('We are unable to find a reply for this.', phone_number, client)
    return 'We are unable to find a reply for this.'


# ======= END ROUTES =======

# ======= MAIN - OCBC API ROUTES =======


# OCBC_URL = "https://api.ocbc.com:8243/transactional"
def setup_ocbc_api_request(response_data):
    '''Sets up the OCBC API request'''
    endpoint = response_data.get('endpoint')
    data = response_data.get('data')

    if endpoint == "/accountSummary":
        #TODO Change to user's account number
        url = Constants.OCBC_URL + "/account/1.0/summary*?accountNo="+Constants.ACCOUNT_NO+"&accountType=" +Constants.ACCOUNT_TYPE
        payload = {}
        response = send_ocbc_api(url, "GET", payload)
        
        return response
    
    elif endpoint == "/checkBalance":
        account_number = data.get('accountNumber')
        phone_number = data.get('phoneNumber')
        url = Constants.OCBC_URL + "/accountbalance/1.0/balance*?accountNo=" + account_number
        payload = {}    
        response = send_ocbc_api(url, "GET", payload)
        
        return response
    
    elif endpoint == "/balanceEnquiry":
        url = Constants.OCBC_URL + "/corp/balance/1.0/enquiry"
        payload = {
        "AccountNo": Constants.ACCOUNT_NO,
        "AccountType": Constants.ACCOUNT_TYPE,
        "AccountCurrency": "SGD",
        "AccountBIC": "OCBCSGSGXXX",
        "TimeDepositNo": "129"
        }
        response = send_ocbc_api(url, "POST", payload)

        return response

    elif endpoint == "/last6MonthsStatement":
        #TODO change to user's account number
        url = Constants.OCBC_URL + "/account/1.0/recentAccountActivity*?accountNo="+Constants.ACCOUNT_NO+"&accountType=" +Constants.ACCOUNT_TYPE
        payload = {}
        response = send_ocbc_api(url, "GET", payload)

        return response 
    
    elif endpoint == "/paynowEnquiry":
        url = Constants.OCBC_URL + "/paynowenquiry/1.0/payNowEnquiry"
        proxyType = data.get('proxyType')
        proxyValue = data.get('proxyValue')
        payload = {
        "ProxyType": proxyType,
        "ProxyValue": proxyValue
        }
        response = send_ocbc_api(url, "POST", payload)

        resBody = json.loads(response.text)
        if resBody["Success"] == True:
            return True 
        else:
            return False 

    elif endpoint == "/paynow":
        #Setup for Enquiry
        amount = data.get('transferAmount')
        phoneNumber = data.get('phoneNumber')
        accountNumber = data.get('bankAccountNumber')
        nric = data.get('nric') 
        proxyData = getProxy(phoneNumber, nric)
        setupData = {
            "endpoint": "/paynowEnquiry",
            "data": proxyData,
            "message": ""
        }
        #Validated
        if setup_ocbc_api_request(setupData) :
            url = Constants.OCBC_URL + "/paynow/1.0/sendPayNowMoney"
            payload = {
            "Amount": amount,
            "ProxyType": proxyData["proxyType"],
            "ProxyValue": proxyData["proxyValue"],
            "FromAccountNo": accountNumber
            }
            response = send_ocbc_api(url, "POST", payload)

            approvalMessage = format_paynow_response(response)
        #Not Valid
        else:
            approvalMessage = f"Your PayNow request of ${amount} to {proxyValue} is not approved. Please ensure you have entered a valid phone number or NRIC."
        return {"text": approvalMessage}

    elif endpoint == "/unableToFindReply":
        #Default no reply
        phone_number = data.get('phoneNumber')
        helperFunctions.send_message('We are unable to find a reply for this.', phone_number, client)
        return 'We are unable to find a reply for this.'
    
    else:
        #Default no endpoint response
        message = response_data.get('message')
        return {"text": message}

def send_ocbc_api(url, method, payload, headers=Constants.HEADERS):
    '''Sends a request to the OCBC API'''
    data = json.dumps(payload)
    response = requests.request(method, url, headers=headers, data=data)
    return response


# ======= HELPER FUNCTIONS =======

def getProxy(phoneNumber, nric):
    '''Returns the proxy type and value for PayNow'''
    if phoneNumber != "0":
        proxyType = "MSISDN"
        proxyValue = phoneNumber
    else:
        proxyType = "NRIC"
        proxyValue = nric


    return {
        "proxyType": proxyType,
        "proxyValue": proxyValue
    }

def format_paynow_response(response, amount, proxyValue):
    '''Returns the approval message for PayNow'''
    response_data = json.loads(response.text)
    if response_data["Success"]:
        transaction_time = response_data["Results"]["TransactionTime"]
        transaction_date = response_data["Results"]["TransactionDate"]
        available_balance = response_data["Results"]["AvailableBalance"]
        approval_message = (
            f"Your PayNow request of ${amount} to {proxyValue} is successful.\n"
            f"Transaction Time: {transaction_time}\n"
            f"Transaction Date: {transaction_date}\n"
            f"Available Balance: {available_balance}"
        )
    else:
        error_msg = response_data["Results"]["ErrorMsg"]
        approval_message = (
            f"Your PayNow request of ${amount} to {proxyValue} is not approved.\n"
            f"{error_msg}"
        )
    
    return approval_message

def generate_reply(message):
    #TODO: check if still needed
    '''Returns the endpoint based on user's message'''
    #dictionary for routes (key: message, value: endpoint)
    routes = {
        "Check my balance": "/checkBalance",
    }
    
    return routes.get(message, "/unableToFindReply")


def send_message(messageBody, recepientNumber, client):
    '''Sends a message to the user'''
    message = client.messages.create(
    from_='whatsapp:+14155238886',
    body=messageBody,
    to=recepientNumber
    )
    print(message.sid)
    return