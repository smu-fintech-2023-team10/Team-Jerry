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