import os
from dotenv import load_dotenv
load_dotenv()

HOST_URL = "http://localhost:5000"
ACCOUNT_NO = "201770161001"
ACCOUNT_TYPE = "D"
HEADERS =  {
    'Authorization': 'Bearer ' + os.environ.get("ACCESS_TOKEN"),
    'Content-Type': 'application/json'
    }

OCBC_URL = "https://api.ocbc.com:8243/transactional"
MESSAGES=[{"role": "system", "content": "You are an OCBC support assistant. Only answer questions related to OCBC. If the question is 'Stop' or 'End' , return 'False' without any other texts or punctuations. Word limit is 1600 characters."}]
OPENAIENGAGED = False
USER_SESSION = {}