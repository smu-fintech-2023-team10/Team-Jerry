import os
import json
import datetime
from google.cloud import bigquery
import firebase_admin
from firebase_admin import credentials, db
from google.oauth2 import service_account



def firebase_to_bigquery(event, context):
    current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    service_account_file = '../gcloudadmin.json'
    print(f"Service account file exists: {os.path.exists(service_account_file)}")

    #Credentials
    firebase_cred = credentials.Certificate('../gcloudadmin.json')
    firebase_admin.initialize_app(firebase_cred, {
        'databaseURL': 'https://smu-fyp-396613-default-rtdb.asia-southeast1.firebasedatabase.app'
    })

    db_ref = db.reference('/') 
    data = db_ref.get()


    bigquery_cred = service_account.Credentials.from_service_account_file(
        '../gcloudadmin.json',
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    bigquery_client = bigquery.Client(credentials=bigquery_cred)
    dataset_id = 'smufyp'  
    table_id = 'raw_data' 
    dataset_ref = bigquery_client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)
    table = bigquery_client.get_table(table_ref)

    chatData = data['chatData']

    rows_to_insert = []

    for key, value in chatData.items():
        row = {
            'intent': value.get('intent', ''),
            'response': value.get('response', ''),
            'session_id': value.get('sessionId', ''),
            'timestamp': value.get('timestamp', ''),
            'user_id': value.get('userID', ''),
            'user_message': value.get('userMsg', ''),
            'snap_time' : current_timestamp
        }
        rows_to_insert.append(row)

    if rows_to_insert:
        errors = bigquery_client.insert_rows(table, rows_to_insert)

        if errors:
            print(f'Error inserting data into BigQuery: {errors}')
        else:
            print('Data streamed to BigQuery successfully')