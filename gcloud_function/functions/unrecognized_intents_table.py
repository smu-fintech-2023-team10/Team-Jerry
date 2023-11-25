from google.cloud import bigquery
from google.oauth2 import service_account

def create_table_from_query():
    bigquery_cred = service_account.Credentials.from_service_account_file(
        '../gcloudadmin.json',
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    bq_client = bigquery.Client(credentials=bigquery_cred)

    query = """
    SELECT user_message as message FROM `smu-fyp-396613.smufyp.raw_data` WHERE TIMESTAMP_TRUNC(snap_time, DAY) = TIMESTAMP("2023-09-29")
    AND intent = 'unidentified'
    """

    dataset_id = 'smufyp'  
    table_id = 'unrecognized_messages' 
    dataset_ref = bq_client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)
    table = bq_client.get_table(table_ref)


    job_config = bigquery.QueryJobConfig(
        destination=table_ref,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )

    query_job = bq_client.query(query, job_config=job_config)

    query_job.result()

    print('Table created successfully!')

if __name__ == '__main__':
    create_table_from_query()
