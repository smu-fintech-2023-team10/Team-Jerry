# External imports
from flask import Flask, request, Blueprint
import requests 
import openai
import re
import json
import logging
import os
from dotenv import load_dotenv


# Internal imports
import Constants

# ======= SETUP =======
logging.basicConfig(level=logging.INFO)
load_dotenv()
openaiMS = Blueprint('openaiMS', __name__)
# ======= END SETUP =======

# ======= ROUTES =======
@openaiMS.route("/callChatGPT", methods=['POST'])
def callChatGPT():
    data = request.json  # Get the JSON data from the request body
    question = data.get('message')
    # Define your API key here or make sure it's defined elsewhere in your script
    openai.api_key = os.getenv("OPENAI_APIKEY")
    prompt = Constants.MESSAGES
    try:
        Constants.MESSAGES.append({"role": "user", "content": question})
        # Make an API call to generate text using the chat model
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages = Constants.MESSAGES,
            temperature=0.4  # Include the temperature parameter here
        )
        # Extract the generated text from the response
        generated_text = response.choices[0].message['content'].strip()
        if re.sub(r'^A\d+:\s*', '', generated_text).lower() == 'false':
            Constants.MESSAGES=[
                {"role": "system", "content": "You are an OCBC support assistant. Only answer questions related to OCBC. If you are not sure about the question, reply 'I am unable to find the answer for this. If you need help, contact the OCBC hotline at 1800 363 3333.' If the question is 'Stop' or 'End' , return 'False' without any other texts or punctuations. Word limit is 1600 characters."},
            ]
            Constants.OPENAIENGAGED = False
            print(Constants.OPENAIENGAGED)
            return "Thank you for using our FAQ, this conversation has ended. Type 'end' again to continue"
        Constants.MESSAGES.append({'role':'assistant', 'content':generated_text})
        return generated_text + '\n\nEnter "Stop" or "End" to end this conversation.'
    except Exception as e:
        print(f"An error occurred: {e}")
        return "An error occurred." + '\n\nEnter "Stop" or "End" to end this conversation.'