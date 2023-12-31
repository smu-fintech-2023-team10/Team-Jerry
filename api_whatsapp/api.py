# External imports
import atexit
from datetime import datetime, timedelta
import firebase_admin
import json
import os
import hashlib
import requests
import time
import logging
from firebase_admin import credentials, db, firestore
from flask import Flask, request, Blueprint
from flask_session import Session
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import ChatGrant
from twilio.rest import Client
from twilio.twiml.messaging_response import Message, MessagingResponse
from apscheduler.schedulers.background import BackgroundScheduler
from time import sleep
from dotenv import load_dotenv
from .components.qrDecoder import decode_paynow_qr
from .components.parseQrImageToString import parseQrToString

# Internal imports
import Constants
from api_firestore import create_app, db_reference
from api_dialogflow.api import get_session_id

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
    print("Starting... Refreshing Twilio Token... DO NOT CANCEL YET")
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = token
    client = Client(account_sid, auth_token)
    auth_token_promotion = client.accounts.v1.auth_token_promotion().update()
    new_primary_auth_token = auth_token_promotion.auth_token
    secondary_auth_token = client.accounts.v1.secondary_auth_token().create()
    new_secondary_auth_token = secondary_auth_token.secondary_auth_token
    client = Client(account_sid, new_primary_auth_token)
    auth_token_ref = root_ref.child('auth_token')
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    auth_token_ref.update({
        'secondary_token': new_secondary_auth_token,
        'token': new_primary_auth_token,
        'time': current_time
    })
    print("Token Updated... Now can cancel if you want")
    return client

@whatsappMS.route("/getReply", methods=['POST'])
def get_message_reply():
    # incoming_message = request.form['Body']  # Extract the incoming message content
    sender_phone_number = request.form.get('From')
    incoming_message = request.form.get('Body')
    media_url = request.form.get('MediaUrl0')
    ## GEN SESS according to user ID TODO Dyanmic timeout session
    # userId = '84820352' #tmp
    session_id = get_session_id(sender_phone_number)
    logging.info("Session ID: {}".format(session_id))
    if media_url != None:
        qrStringObj = parseQrToString(media_url)
        if(qrStringObj['success'] == True):
            qrString = qrStringObj['qrString']
            decoded = decode_paynow_qr(qrString) #QR object with payment info
            # {
            # 'Payload Format Indicator': '01', 
            # 'Point of Initiation Method': '11', 
            # 'Merchant Account Information': {'Reverse Domain Name': 'SG.PAYNOW', 'Proxy Type': 'MSIDN', 'Proxy Value': '+6597988922', 'Editable': '1'}, 
            # 'Merchant Category Code': '0000', 
            # 'Transaction Currency': '702', 
            # 'Country Code': 'SG', 
            # 'Merchant Name': 'NA',
            # 'Merchant City': 'SINGAPORE', 
            # 'CRC': '7F54'
            # }
            data = {
            "message": "ProxyType:" + decoded['Merchant Account Information']['Proxy Type'] + ', ProxyValue: ' + decoded['Merchant Account Information']['Proxy Value'],
            "userId": sender_phone_number,
            "sessionId": session_id
            }
            #print(decoded) #{'Reverse Domain Name': 'SG.PAYNOW', 'Proxy Type': 'MSIDN', 'Proxy Value': '+6597988922', 'Editable': '1'}
            url = os.getenv("HOST_URL") + "/runModel"
            response_data = requests.post(url, json=data)
            print(response_data)
            response = setup_ocbc_api_request(response_data)
            log = {'userID': sender_phone_number,
                'userMsg': incoming_message,
                'intent': json.loads(response_data.text)['intent'],
                'response':response}
            
            dataStore = constructDataStore(sender_phone_number, data['message'], response_data, response)
            send_message(response, sender_phone_number, client,dataStore)
            return "Success"
        else:
            data = {
            "message": "Not QR Code",
            "userId": sender_phone_number,
            "sessionId": session_id
            }
            url = os.getenv("HOST_URL") + "/runModel"
            response_data = requests.post(url, json=data)
            
            response = setup_ocbc_api_request(response_data)
            ##send to FB ##CONTINUE FROM HERE
            log = {'userID': sender_phone_number,
                'userMsg': incoming_message,
                'intent': json.loads(response_data.text)['intent'],
                'response':response}
            dataStore = constructDataStore(sender_phone_number,incoming_message, response_data, response)
            send_message(response, sender_phone_number, client,dataStore)
            return "Success"
    else:
        data = {
            "message": incoming_message,
            "userId": sender_phone_number,
            "sessionId": session_id
        }
        #If openAPI is not engaged for this user, call dialogflow
        if Constants.USER_SESSION[sender_phone_number][2] == False:
            print(Constants.USER_SESSION[sender_phone_number][2])
            url = os.getenv("HOST_URL") + "/runModel"
            response_data = requests.post(url, json=data)
            res = json.loads(response_data.text)
            if res["endpoint"] == "/callChatGPT":
                Constants.USER_SESSION[sender_phone_number][2] = True
            response = setup_ocbc_api_request(response_data)
            dataStore = constructDataStore(sender_phone_number, incoming_message, response_data, response)
        #If openAPI is engaged for this user, call chatGPT
        else:
            client.messages.create(
                from_='whatsapp:+14155238886',
                body="Generating reply, please wait a moment...",
                to=sender_phone_number
                )
            print(Constants.USER_SESSION[sender_phone_number][2])
            url = os.getenv("HOST_URL") + "/callChatGPT"
            response = requests.post(url, json=data)
            response = response.text
            dataStore = constructDataStore(sender_phone_number, incoming_message, "GPT", response)
        send_message(response, sender_phone_number, client,dataStore)
        return "Success"

# ======= END ROUTES =======

# ======= MAIN - OCBC API ROUTES =======

# {
#     "data": {}
#     "message": ""
#     "endpoint": ""
# }

def setup_ocbc_api_request(res):
    '''Sets up the OCBC API request'''

    def accountSummary():
        #TODO Change to user's account number
        url = Constants.OCBC_URL + "/account/1.0/summary*?accountNo="+Constants.ACCOUNT_NO+"&accountType=" +Constants.ACCOUNT_TYPE
        payload = {}
        response = send_ocbc_api(url, "GET", payload)
        
        return response
    
    def checkBalance():
        payloadData = json.loads(data)
        account_number = payloadData.get('accountNumber')
        phone_number = payloadData.get('phoneNumber')
        url = Constants.OCBC_URL + "/accountbalance/1.0/balance*?accountNo=" + account_number
        payload = {}    
        response = send_ocbc_api(url, "GET", payload)
        CurrencyCode= response['Results']['CurrencyCode']
        AvailableBalance= response['Results']['AvailableBalance']
        BalanceAsOfDate= response['Results']['BalanceAsOfDate']
        resString = f'{CurrencyCode} ${AvailableBalance}, as of : {BalanceAsOfDate}'
        # helperFunctions.send_message(response.text, phone_number, client)
        return {"balance": resString}
    
    def balanceEnquiry():
        url = Constants.OCBC_URL + "/corp/balance/1.0/enquiry"
        # TODO: Change to user's account number
        payload = {
        "AccountNo": Constants.ACCOUNT_NO,
        "AccountType": Constants.ACCOUNT_TYPE,
        "AccountCurrency": "SGD",
        "AccountBIC": "OCBCSGSGXXX",
        "TimeDepositNo": "129"
        }
        response = send_ocbc_api(url, "POST", payload)
        return response

    def last6MonthsActivity():
        #TODO change to user's account number
        url = Constants.OCBC_URL + "/account/1.0/recentAccountActivity*?accountNo="+Constants.ACCOUNT_NO+"&accountType=" +Constants.ACCOUNT_TYPE
        payload = {}
        response = send_ocbc_api(url, "GET", payload)

        return response 
    
    def paynowEnquiry():
        url = Constants.OCBC_URL + "/paynowenquiry/1.0/payNowEnquiry"
        proxyData = json.loads(data)
        proxyType = proxyData.get('ProxyType')
        proxyValue = proxyData.get('ProxyValue')
        payload = {
        "ProxyType": proxyType,
        "ProxyValue": proxyValue
        }
        response = send_ocbc_api(url, "POST", payload)
        if response["Success"] == True:
            return {"isValid": "valid"}
        else:
            return {"isValid": "invalid"}

    def paynow():
        #Setup for Enquiry
        payloadData = json.loads(data)
        print(payloadData)
        type = payloadData.get('type')
        amount = payloadData.get('transferAmount')
        #NOTE: HARDCODED VALUE FOR NOW
        accountNumber = payloadData.get('bankAccountNumber')
        formatType = "NORMALPAYNOW"
        if type == "Scan":
            proxyData = {
                "ProxyType" : payloadData.get('ProxyType'),
                "ProxyValue" : payloadData.get('ProxyValue')
            }

            url = Constants.OCBC_URL + "/paynow/1.0/sendPayNowMoney"
            payload = {
                "Amount": amount,
                "ProxyType": proxyData["ProxyType"],
                "ProxyValue": proxyData["ProxyValue"],
                "FromAccountNo": accountNumber
            }

            if proxyData["ProxyType"] == "UEN":
                formatType = "CORPORATEPAYNOW"
                url = Constants.OCBC_URL + '/corporate/paynowpayment/1.0/corporatePayment'
                payload = {
                    "TransactionDescription": "Whatsapp Banking Transfer",
                    "Amount": amount,
                    "ProxyType": proxyData["ProxyType"],
                    "ProxyValue": proxyData["ProxyValue"],
                    "FromAccountNo": accountNumber,
                    "PurposeCode": "OTHR",
                    "TransactionReferenceNo": "OrgXYZ1212123"
                }

        elif type == "Transfer":
            phoneNumber = payloadData.get('phoneNumber')
            nric = payloadData.get('nric') 
            proxyData = getProxy(phoneNumber, nric) 

            url = Constants.OCBC_URL + "/paynow/1.0/sendPayNowMoney"
            payload = {
            "Amount": amount,
            "ProxyType": proxyData["ProxyType"],
            "ProxyValue": proxyData["ProxyValue"],
            "FromAccountNo": accountNumber
            }

        response = send_ocbc_api(url, "POST", payload)
        if response["Success"]:
            approvalMessage = format_paynow_response(response, amount, proxyData["ProxyValue"],formatType)
        else:
            approvalMessage = f"Your PayNow request of ${amount} to {proxyData['ProxyValue']} is not approved. Please ensure you have entered a valid phone number/NRIC/UEN."
        
        return {"approvalMessage": approvalMessage}
    def unableToFindReply():
        #Default no reply
        phone_number = data.get('phoneNumber')
        send_message('We are unable to find a reply for this.', phone_number, client)
        return 'We are unable to find a reply for this.'
    
    def default_response():
        #Default no endpoint response
        message = response_data.get('message')
        return {"text": message}
    
    if isinstance(res, requests.Response):
        response_data = json.loads(res.text)
    else:
        response_data = res
    endpoint = response_data.get('endpoint')
    data = response_data.get('data')
    message = response_data.get('message')

    switch = {
        "/accountSummary": accountSummary,
        "/checkBalance": checkBalance,
        "/balanceEnquiry": balanceEnquiry,
        "/last6MonthsActivity": last6MonthsActivity,
        "/paynowEnquiry": paynowEnquiry,
        "/paynow": paynow,
        "/unableToFindReply": unableToFindReply,
    }

    func = switch.get(endpoint, default_response)
    finalRes = func()
    print("########THIS#######")
    print(finalRes)
    print(message)
    return format_message(message, finalRes)
    


def send_ocbc_api(url, method, payload, headers=Constants.HEADERS):
    '''Sends a request to the OCBC API'''
    data = json.dumps(payload)
    response = requests.request(method, url, headers=headers, data=data)
    return json.loads(response.text)
    


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
        "ProxyType": proxyType,
        "ProxyValue": proxyValue
    }

def format_paynow_response(response, amount, proxyValue,type):
    '''Returns the approval message for PayNow'''
    if type == "NORMALPAYNOW":
        response_data = response
        if response_data["Success"]:
            transaction_time = response_data["Results"]["TransactionTime"]
            transaction_date = response_data["Results"]["TransactionDate"]
            available_balance = response_data["Results"]["AvailableBalance"]
            avail_bal_formatted = format(available_balance, ".2f")
            amount_formatted = format(float(amount), ".2f")
            approval_message = (
                f"Your PayNow request of ${amount_formatted} to {proxyValue} is successful.\n"
                f"Transaction Time: {transaction_time}\n"
                f"Transaction Date: {transaction_date}\n"
                f"Available Balance: ${avail_bal_formatted}"
            )
        else:
            error_msg = response_data["Results"]["ErrorMsg"]
            approval_message = (
                f"Your PayNow request of ${amount} to {proxyValue} is not approved.\n"
                f"{error_msg}"
            )
        
    #formatType = "CORPORATEPAYNOW"
    else:
        response_data = response
        if response_data["Success"]:
            ocbc_refno = response_data["Results"]["ocbcreferenceNo"]
            transaction_refno = response_data["Results"]["TransactionReferenceNo"]
            transaction_description = response_data["Results"]["TransactionDescription"]
            amount_formatted = format(float(amount), ".2f")
            approval_message = (
                f"Your PayNow request of ${amount_formatted} to {proxyValue} is successful.\n"
                f"OCBC Reference Number: {ocbc_refno}\n"
                f"Transaction Reference: {transaction_refno}\n"
                f"Transaction Description: {transaction_description}\n"
            )
    return approval_message

# ---- Helper functions #
def generate_shortened_hash(input_string):
    md5_hash = hashlib.md5(input_string.encode())
    shortened_hash = md5_hash.hexdigest()[:7]
    return shortened_hash

def create_session_key(userId):
    current_timestamp = str(int(time.time()))
    shortened_hash = generate_shortened_hash(userId+current_timestamp)
    return shortened_hash

def get_session_id(userId):
    if userId in Constants.USER_SESSION:
        session_id = Constants.USER_SESSION[userId][0]
        create_time = Constants.USER_SESSION[userId][1]

        if int(time.time()) - create_time >= 30*60: ## check if more then 30 min else create new one
            session_id = create_session_key(userId)
            user_sessionData = [session_id,int(time.time()),False, [
                {"role": "system", "content": "You are an OCBC support assistant. Only answer questions related to OCBC. If you are not sure about the question, reply 'I am unable to find the answer for this. If you need help, contact the OCBC hotline at 1800 363 3333.' If the question is 'Stop' or 'End' , return 'False' without any other texts or punctuations. Word limit is 1000 characters."},
            ]]
            Constants.USER_SESSION[userId] = user_sessionData
        else: ## update time
            Constants.USER_SESSION[userId][1] = int(time.time())
    else: # new user
        session_id = create_session_key(userId)
        user_sessionData = [session_id,int(time.time()), False, [
                {"role": "system", "content": "You are an OCBC support assistant. Only answer questions related to OCBC. If you are not sure about the question, reply 'I am unable to find the answer for this. If you need help, contact the OCBC hotline at 1800 363 3333.' If the question is 'Stop' or 'End' , return 'False' without any other texts or punctuations. Word limit is 1000 characters."},
            ]]
        Constants.USER_SESSION[userId] = user_sessionData
    print("USER SESSION: ", Constants.USER_SESSION)
    return session_id

def format_message(message, response):
    '''Returns the formatted message by replacing variables inside message with variables gotten from endpoints'''
    if '{' not in message:
        return message 
    else:
        for key in response:
            token = "{"+key+"}"
            message = message.replace(token,response[key])
        return message


def generate_reply(message):
    #TODO: check if still needed
    '''Returns the endpoint based on user's message'''
    #dictionary for routes (key: message, value: endpoint)
    routes = {
        "Check my balance": "/checkBalance",
    }
    
    return routes.get(message, "/unableToFindReply")


def send_message(messageBody, recepientNumber, client, dataStore):
    '''Sends a message to the user'''

    #Logging
    storeUnstructedChatData(recepientNumber, dataStore)

    message = client.messages.create(
    from_='whatsapp:+14155238886',
    body=messageBody,
    to=recepientNumber
    )

    return message

def constructDataStore(sender_phone_number, message, response_data, response):
    if response_data == "GPT":
        dataStore = {'userID': sender_phone_number,
               'userMsg': message,
               'intent': "GPT",
               'response':response,
            }
        return dataStore
    dataStore = {'userID': sender_phone_number,
               'userMsg': message,
               'intent': json.loads(response_data.text)['intent'],
               'response':response,
            }
    dataStore['sessionId'] = get_session_id(sender_phone_number)

    return dataStore

def storeUnstructedChatData(userId,dataStore):
    # Specify the key/id you want to use
    timeNow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry_id = userId+"_"+timeNow

    chat_data_ref = root_ref.child('chatData')
    dataStore['timestamp'] = timeNow
    
    # Set data with the custom key
    res = chat_data_ref.child(entry_id).set(dataStore)
    return res

def constructDataStore(sender_phone_number, message, response_data, response):
    dataStore = {'userID': sender_phone_number,
               'userMsg': message,
               'intent': json.loads(response_data.text)['intent'],
               'response':response,
            }
    dataStore['sessionId'] = get_session_id(sender_phone_number)

    return dataStore

def storeUnstructedChatData(userId,dataStore):
    # Specify the key/id you want to use
    timeNow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry_id = userId+"_"+timeNow

    chat_data_ref = root_ref.child('chatData')
    dataStore['timestamp'] = timeNow
    
    # Set data with the custom key
    res = chat_data_ref.child(entry_id).set(dataStore)
    return res

client = refresh_twilio_auth_token()
# Set up the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(refresh_twilio_auth_token, 'interval', hours=20)
scheduler.start()