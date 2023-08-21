from flask import Flask, request, session
from flask_session import Session  # Import the Session extension
import requests
import Constants
import json
from twilio.rest import Client
from twilio.twiml.messaging_response import Message, MessagingResponse
from flask_ngrok import run_with_ngrok
import nlp_model
import helperFunctions
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Set session timeout to 1 hour (in seconds)
run_with_ngrok(app)
Session(app)  # Initialize the Session extension

account_sid = Constants.TWILIO_ACCOUNT_SID
auth_token = Constants.TWILIO_AUTH_TOKEN
client = Client(account_sid, auth_token)

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
    'Authorization': 'Bearer 901b6881-359b-358e-adee-ef6b2bc1a3cd',
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


if __name__ == '__main__':
    app.run()
