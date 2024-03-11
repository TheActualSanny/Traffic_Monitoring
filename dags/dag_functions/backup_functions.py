from airflow.providers.google.cloud.transfers.gcs_to_local import GCSHook
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from google.cloud.storage import Bucket

from datetime import datetime
import time
import re

from helper.retrieve_variables import get_variables


def create_backup_bucket():
    variables = get_variables()
    backup_bucket = variables['BACKUP_ID']

    gcs_hook = GCSHook(gcp_conn_id=variables['CONN_ID'])
    conn = gcs_hook.get_conn()
    project_buckets = conn.list_buckets()

    # check if bucket already exists
    for bucket in project_buckets:
        if bucket.name == backup_bucket:
            print(f"{backup_bucket} bucket already exists ")
            return

    # create a bucket if it doesn't already exist
    gcs_hook.create_bucket(bucket_name=backup_bucket,
                           location='US')

    # add lifecycle to the bucket
    bucket = Bucket(conn, backup_bucket)
    bucket.add_lifecycle_delete_rule(age=14)
    bucket.patch()

    print(f"created a backup bucket called {backup_bucket}")
    time.sleep(5)


def get_max_date(ti):
    # if this task fails, that means there was no data in bigquery, meaning nothing needed to be moved to backup
    variables = get_variables()

    bigquery_hook = BigQueryHook(variables['CONN_ID'], use_legacy_sql=False)

    # get max date from bigquery table
    sql_query = (f"SELECT CAST(MAX(TIMESTAMP) AS STRING) AS max_date "
                 f"FROM `{variables['PROJECT_ID']}.{variables['DATASET_ID']}.{variables['TABLE_ID']}`")

    max_date = bigquery_hook.get_first(sql_query)[0]
    max_date = max_date.split('+')[0]  # remove timezone
    max_date = datetime.strptime(max_date, "%Y-%m-%d %H:%M:%S.%f")

    ti.xcom_push(key='MAX_DATE', value=max_date)


def remove_duplicate_data(ti):
    variables = get_variables()
    max_date = ti.xcom_pull(key='MAX_DATE', task_ids='retrieve_max_date')

    gcs_hook = GCSHook(gcp_conn_id=variables['CONN_ID'])

    # get filenames from bucket
    blobs = gcs_hook.list(bucket_name=variables['BUCKET_NAME'])
    datetime_pattern = r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d+'

    for blob in blobs:
        destination_filename = blob

        file_datetime_match = re.search(datetime_pattern, blob)
        if file_datetime_match:
            file_datetime = datetime.strptime(file_datetime_match.group(), "%Y-%m-%d %H:%M:%S.%f")
        else:
            file_datetime = max_date
            destination_filename = "invalid/" + destination_filename

        # if file was already uploaded to bigquery move it to a backup bucket
        if blob.endswith(".pcap") and file_datetime <= max_date:
                gcs_hook.copy(source_bucket=variables['BUCKET_NAME'],
                              source_object=blob,
                              destination_bucket=variables['BACKUP_ID'],
                              destination_object=destination_filename)

                gcs_hook.delete(bucket_name=variables['BUCKET_NAME'],
                                object_name=blob)
