from firestore_api import create_app
from flask import Flask, request, session, jsonify
import firebase_admin
from firebase_admin import credentials, db
from flask_session import Session  # Import the Session extension
import uuid
import requests
import Constants
import json
from twilio.rest import Client
from twilio.twiml.messaging_response import Message, MessagingResponse
from flask_ngrok import run_with_ngrok
import nlp_model
import helperFunctions

app = create_app()

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

#Firestore RealtimeDB APIs
@app.route('/addUser', methods=['POST'])
def createUser():
    try:
        id = uuid.uuid4()
        # Get a reference to the root of the Realtime Database
        root_ref = db.reference()

        # Create a new child node with the generated UUID as the key
        user_ref = root_ref.child('user').child(id.hex)
        user_ref.set(request.json)

        return jsonify({"success": True}), 200
    except Exception as e:
        return f"An Error occurred: {e}"

@app.route('/readUser/<user_id>', methods=['GET'])
def readUser(user_id):
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

@app.route('/updateUser/<user_id>', methods=['PUT'])
def updateUser(user_id):
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

@app.route('/deleteUser/<user_id>', methods=['DELETE'])
def deleteUser(user_id):
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
    app.run()
