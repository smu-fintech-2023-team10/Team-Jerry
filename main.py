from flask import Flask, request, session
from flask_session import Session  # Import the Session extension
import requests
import Constants
import json
from twilio.rest import Client
from twilio.twiml.messaging_response import Message, MessagingResponse
from flask_ngrok import run_with_ngrok

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Set session timeout to 1 hour (in seconds)
run_with_ngrok(app)
Session(app)  # Initialize the Session extension

account_sid = Constants.TWILIO_ACCOUNT_SID
auth_token = Constants.TWILIO_AUTH_TOKEN
client = Client(account_sid, auth_token)


@app.route("/getReply", methods=['POST'])
def get_message_reply():
    incoming_message = request.form['Body']  # Extract the incoming message content

    response = MessagingResponse()
    message = response.message()  # Create a new message within the response
    message.body("You said: {incoming_message}. This is your custom response.")  # Set the message content

    print(str(response))  # Print the TwiML response (including the message)

    return str(response)  # Return the response as the HTTP response


@app.route("/")
def get_account_details():
    session['account_no'] = "201770161001"
    session['account_type'] = "D"
    session_str = json.dumps(dict(session))
    message = client.messages.create(
    from_='whatsapp:+14155238886',
    body='Hello! Welcome to OCBC Whatsapp Banking. What would you like to do today?',
    to='whatsapp:+6597988922'
    )
    print(message.sid)
    return session_str

# OCBC APIs
@app.route("/accountSummary")
def account_summary():
    url = "https://api.ocbc.com:8243/transactional/account/1.0/summary*?accountNo="+session["account_no"]+"&accountType=" +session["account_type"]
    payload={}
    headers = {
    'Authorization': 'Bearer 901b6881-359b-358e-adee-ef6b2bc1a3cd',
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)
    return response.text


@app.route("/checkBalance")
def get_account_balance():
    accountNo = session["account_no"]
    url = "https://api.ocbc.com:8243/transactional/accountbalance/1.0/balance*?accountNo=" + accountNo
    payload={}
    headers = {
    'Authorization': 'Bearer ' + Constants.ACCESS_TOKEN
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    print(response.text)
    return response.text

@app.route("/balanceEnquiry")
def balance_enquiry():

    url = "https://api.ocbc.com:8243/transactional/corp/balance/1.0/enquiry"

    payload = json.dumps({
    "AccountNo": session["account_no"],
    "AccountType": session["account_type"],
    "AccountCurrency": "SGD",
    "AccountBIC": "OCBCSGSGXXX",
    "TimeDepositNo": "129"
    })
    headers = {
    'Authorization': 'Bearer ' + Constants.ACCESS_TOKEN,
    'Content-Type': 'application/json',
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
    "FromAccountNo": session["account_no"]
    })
    headers = {
    'Authorization': 'Bearer ' + Constants.ACCESS_TOKEN,
    'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
    return response.text

@app.route("/paynowEnquiry")
def paynow_enquiry():
    url = "https://api.ocbc.com:8243/transactional/paynowenquiry/1.0/payNowEnquiry"

    payload = json.dumps({
    "ProxyType": "MSISDN", #OR NRIC
    "ProxyValue": "+6597988922" #OR S9801118H
    })    
    headers = {
    'Authorization': 'Bearer 901b6881-359b-358e-adee-ef6b2bc1a3cd',
    'Content-Type': 'application/json',
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    print(response.text)
    return response.text


@app.route("/last6MonthsStatement")
def last_6month_statement():
    url = "https://api.ocbc.com:8243/transactional/account/1.0/recentAccountActivity*?accountNo="+session["account_no"]+"&accountType=" +session["account_type"]

    payload={}
    headers = {
    'Authorization': 'Bearer ' + Constants.ACCESS_TOKEN
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)
    return response.text


if __name__ == '__main__':
    app.run()






