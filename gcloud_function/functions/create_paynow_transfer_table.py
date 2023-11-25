from google.cloud import bigquery
from google.oauth2 import service_account

def create_table_from_query():
    bigquery_cred = service_account.Credentials.from_service_account_file(
        '../gcloudadmin.json',
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    bq_client = bigquery.Client(credentials=bigquery_cred)

    query = """
    with base as (SELECT session_id,
        "Paynow Transfer" as bank_function,
        FORMAT_TIMESTAMP('%d/%m/%y', timestamp) as date
        FROM `smu-fyp-396613.smufyp.raw_data` 
        WHERE TIMESTAMP_TRUNC(snap_time, DAY) = TIMESTAMP("2023-09-29")
        ),

        account as (select session_id,
        user_id as account_number FROM `smu-fyp-396613.smufyp.raw_data` 
        WHERE TIMESTAMP_TRUNC(snap_time, DAY) = TIMESTAMP("2023-09-29")
        AND intent = 'Transfer Money'
        ),

        recipient_number as (select session_id, 
        user_message as number FROM `smu-fyp-396613.smufyp.raw_data` 
        WHERE TIMESTAMP_TRUNC(snap_time, DAY) = TIMESTAMP("2023-09-29")
        AND intent = 'Transfer Money - Recipient Phone Number'
        ),

        recipient_nric as (select session_id, 
        user_message as nric FROM `smu-fyp-396613.smufyp.raw_data` 
        WHERE TIMESTAMP_TRUNC(snap_time, DAY) = TIMESTAMP("2023-09-29")
        AND intent = 'Transfer Money - Recipient NRIC'
        ),

        transfer_amount as (select session_id, 
        user_message as amount FROM `smu-fyp-396613.smufyp.raw_data` 
        WHERE TIMESTAMP_TRUNC(snap_time, DAY) = TIMESTAMP("2023-09-29")
        AND intent = 'Transfer Money - Transfer Amount'
        ),

        rating as (SELECT session_id, 
            AVG(CAST(user_message AS INT64)) AS session_rating
        FROM `smu-fyp-396613.smufyp.raw_data`
        WHERE TIMESTAMP_TRUNC(snap_time, DAY) = TIMESTAMP("2023-09-29")
        AND intent = 'End Session - Rating'
        AND user_message IN ("1", "2", "3", "4", "5")
        GROUP BY session_id
        ) 

        SELECT DISTINCT
        b.*,
        SUBSTRING(a.account_number, 10) as account_number,
        COALESCE(rn.number, rnric.nric) AS recipient_number,
        amt.amount,
        r.session_rating
        FROM
        base b
        JOIN
        account a
        ON
        b.session_id = a.session_id
        LEFT JOIN
        recipient_number rn
        ON
        b.session_id = rn.session_id
        LEFT JOIN
        recipient_nric rnric
        ON
        b.session_id = rnric.session_id
        LEFT JOIN
        transfer_amount amt
        ON
        b.session_id = amt.session_id
        LEFT JOIN
        rating r
        ON
        b.session_id = r.session_id;
    """

    dataset_id = 'smufyp'  
    table_id = 'paynow_transfer_sessions' 
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
