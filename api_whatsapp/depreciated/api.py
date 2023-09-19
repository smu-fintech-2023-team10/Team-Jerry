# External imports
import requests
import time
from twilio.rest import Client
from twilio.twiml.messaging_response import Message, MessagingResponse
from flask_ngrok import run_with_ngrok
from datetime import datetime, timedelta
from flask import Flask, request, Blueprint
from apscheduler.schedulers.background import BackgroundScheduler
from time import sleep
import os
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant
from dotenv import load_dotenv


# Internal imports
import Constants
import json
import nlp_model
import helperFunctions
from api_firestore import create_app, db_reference
from api_firestore.api import get_token_refresh_time
# Load the environment variables from .env file

whatsappMS = Blueprint('whatsappMS', __name__)
load_dotenv()
root_ref = db_reference

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



@whatsappMS.route("/sendMessageTest", methods=['POST'])
def sendMessageTest():

    return "True"

@whatsappMS.route("/getReply", methods=['POST'])
def get_message_reply():
    incoming_message = request.form['Body']  # Extract the incoming message content
    sender_phone_number = request.form['From'] # Extract the phone number
    print(incoming_message)
    print(sender_phone_number)
    data = {
        "message": incoming_message,
        "userId": sender_phone_number
    }
    url = os.getenv("HOST_URL") + "/runModel"
    res = requests.post(url, json=data)
    helperFunctions.send_message("\n".join(json.loads(res.text)), sender_phone_number, client)
    print(str(res))
    return incoming_message  # Return the response as the HTTP response
    
@whatsappMS.route("/unableToFindReply", methods=['POST'])
def reply_with_none():
    data = request.json
    phone_number = data.get('phoneNumber')  # Extract phone number from the JSON data
    helperFunctions.send_message('We are unable to find a reply for this.', phone_number, client)
    return 'We are unable to find a reply for this.'


# OCBC APIs
@whatsappMS.route("/accountSummary", methods=['POST'])
def account_summary():
    url = "https://api.ocbc.com:8243/transactional/account/1.0/summary*?accountNo="+Constants.ACCOUNT_NO+"&accountType=" +Constants.ACCOUNT_TYPE
    payload={}
    headers = {
    'Authorization': 'Bearer ' + os.environ.get("ACCESS_TOKEN"),
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)
    return response.text


@whatsappMS.route("/checkBalance" , methods=['POST'])
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
    resBody = json.loads(response.text)
    print(resBody)
    CurrencyCode= resBody['Results']['CurrencyCode']
    AvailableBalance= resBody['Results']['AvailableBalance']
    BalanceAsOfDate= resBody['Results']['BalanceAsOfDate']
    resString = f'{CurrencyCode} {AvailableBalance}, as of : {BalanceAsOfDate}'
    # helperFunctions.send_message(response.text, phone_number, client)
    return {"balance": resString}

@whatsappMS.route("/balanceEnquiry", methods=['POST'])
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

@whatsappMS.route("/paynow", methods=['POST'])
def transfer_money():
    try:
        data = request.json
        amount = data.get("transferAmount")
        phoneNumber = data.get("phoneNumber")
        accountNum =  data.get("bankAccountNumber")
        nric = data.get("nric")
        if phoneNumber != "0":
            ProxyType = "MSISDN"
        else:
            ProxyType = "NRIC"

        if ProxyType == "MSISDN":
            proxyValue = phoneNumber
        else:
            proxyValue =  nric
        payNowEnquiryData  = json.dumps({
            "ProxyType": ProxyType,
            "ProxyValue": proxyValue
        })
        payNowEnquiryHeaders = {
                    'Content-Type': 'application/json',  # Example header
                    # Add more headers as needed
                }
        payNowEnquiryResponse = requests.request("POST", os.getenv("HOST_URL")+"/paynowEnquiry" , headers=payNowEnquiryHeaders, data=payNowEnquiryData)
        payNowEnquiryResponseBody = json.loads(payNowEnquiryResponse.text)
        if payNowEnquiryResponseBody["isValid"] == "valid":
            url = "https://api.ocbc.com:8243/transactional/paynow/1.0/sendPayNowMoney"
            #{"phoneNumber": "$session.params.phone_number", "bankAccountNumber": "$session.params.bank_acc_number",,"nric": "$session.params.nric","transferAmount": "$intent.params.transfer_amount"}
            payload = json.dumps({
            "Amount": amount,
            "ProxyType": ProxyType,
            "ProxyValue": proxyValue,
            "FromAccountNo": accountNum
            })
            headers = {
            'Authorization': 'Bearer ' + os.environ.get("ACCESS_TOKEN"),
            'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            resBody = json.loads(response.text)
            print(resBody)
            if resBody["Success"] == True:
                transationTime = resBody["Results"]["TransactionTime"]
                transationDate = resBody["Results"]["TransactionDate"]
                availableBalance = resBody["Results"]["AvailableBalance"]
                approvalMessage = f"Your PayNow request of ${amount} to {proxyValue} is successful.\nTransaction Time: {transationTime} \nTransaction Date: {transationDate}\nAvailable Balance: {availableBalance}"
                return {"approvalMessage": approvalMessage}
            else:
                errorMsg = resBody["Results"]["ErrorMsg"]
                approvalMessage = f"Your PayNow request of ${amount} to {proxyValue} is not approved.\n{errorMsg}"
                return {"approvalMessage": approvalMessage}
        else:
            approvalMessage = f"Your PayNow request of ${amount} to {proxyValue} is not approved. Please ensure you have entered a valid phone number or NRIC."
            return {"approvalMessage": approvalMessage}
    except Exception as e:
        return e

@whatsappMS.route("/paynowEnquiry", methods=['POST'])
def paynow_enquiry():
    data = request.json
    proxyType = data.get("ProxyType")
    proxyValue = data.get("ProxyValue")
    url = "https://api.ocbc.com:8243/transactional/paynowenquiry/1.0/payNowEnquiry"

    payload = json.dumps({
    "ProxyType": proxyType, #OR NRIC
    "ProxyValue": proxyValue #OR S9801118H
    })    
    headers = {
    'Authorization': 'Bearer ' + os.environ.get("ACCESS_TOKEN"),
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    resBody = json.loads(response.text)
    print(resBody["Success"])
    if resBody["Success"] == True:
        return {"isValid": "valid"}
    else:
        return {"isValid": "invalid"}


@whatsappMS.route("/last6MonthsStatement", methods=['POST'])
def last_6month_statement():
    url = "https://api.ocbc.com:8243/transactional/account/1.0/recentAccountActivity*?accountNo="+Constants.ACCOUNT_NO+"&accountType=" +Constants.ACCOUNT_TYPE

    payload={}
    headers = {
    'Authorization': 'Bearer ' + os.environ.get("ACCESS_TOKEN")
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)
    return response.text


# if __name__ == '__main__':
client = refresh_twilio_auth_token()
# Set up the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_twilio_auth_token, 'interval', hours=20)
scheduler.start()
    # whatsappMS.run()  # adjust host and port as needed
