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
        "Check Balance" as bank_function,
        FORMAT_TIMESTAMP('%d/%m/%y', timestamp) as date,

        FROM `smu-fyp-396613.smufyp.raw_data` 
        WHERE TIMESTAMP_TRUNC(snap_time, DAY) = TIMESTAMP("2023-09-29")
        ),

        account as (select session_id,
        user_message as account_number FROM `smu-fyp-396613.smufyp.raw_data` 
        WHERE TIMESTAMP_TRUNC(snap_time, DAY) = TIMESTAMP("2023-09-29")
        AND intent = 'Check Balance - Account Number'
        ),

        days_7_check as (select session_id, 
        user_message as see_past_transactions_7 FROM `smu-fyp-396613.smufyp.raw_data` 
        WHERE TIMESTAMP_TRUNC(snap_time, DAY) = TIMESTAMP("2023-09-29")
        AND intent = 'Check Balance - Transactions - Yes + 7 days'
        ),

        days_30_check as (select session_id, 
        user_message as see_past_transactions_30 FROM `smu-fyp-396613.smufyp.raw_data` 
        WHERE TIMESTAMP_TRUNC(snap_time, DAY) = TIMESTAMP("2023-09-29")
        AND intent = 'Check Balance - Transactions - Yes + 30 Days'
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
        a.account_number,
        COALESCE(dc_seven.see_past_transactions_7, dc_thirty.see_past_transactions_30) AS see_past_transactions,
        r.session_rating
        FROM
        base b
        JOIN
        account a
        ON
        b.session_id = a.session_id
        LEFT JOIN
        days_7_check dc_seven
        ON
        b.session_id = dc_seven.session_id
        LEFT JOIN
        days_30_check dc_thirty
        ON
        b.session_id = dc_thirty.session_id
        LEFT JOIN
        rating r
        ON
        b.session_id = r.session_id;
    """

    dataset_id = 'smufyp'  
    table_id = 'check_balance_sessions' 
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
