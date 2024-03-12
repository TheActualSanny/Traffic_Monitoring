from airflow.providers.google.cloud.transfers.gcs_to_local import GCSHook
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from google.cloud.storage import Bucket

from datetime import datetime
import time
import re

from helper.retrieve_variables import get_variables


def create_backup_bucket() -> None:
    """ Function creates a backup bucket, with a lifecycle of 2 weeks
    if it doesn't already exist. """

    variables = get_variables()
    backup_bucket = variables['BACKUP_ID']

    gcs_hook = GCSHook(gcp_conn_id=variables['CONN_ID'])
    conn = gcs_hook.get_conn()
    project_buckets = conn.list_buckets()

    # if bucket exists mark task as successful
    for bucket in project_buckets:
        if bucket.name == backup_bucket:
            return

    # create a bucket if it doesn't already exist
    gcs_hook.create_bucket(bucket_name=backup_bucket,
                           location='US')

    # add lifecycle to the bucket
    bucket = Bucket(conn, backup_bucket)
    bucket.add_lifecycle_delete_rule(age=14)
    bucket.patch()

    # making sure that table will be created for the next tasks successful run
    time.sleep(5)


def get_max_date(ti) -> None:
    """ Function retrieves max_date from TIMESTAMP column of bigquery table
    and passes it to the next task. This task failing indicates that the BigQuery table was empty,
    meaning no files needed to be moved to the backup bucket. """

    variables = get_variables()

    bigquery_hook = BigQueryHook(variables['CONN_ID'], use_legacy_sql=False)

    # query to get max date from bigquery table
    sql_query = (f"SELECT CAST(MAX(TIMESTAMP) AS STRING) AS max_date "
                 f"FROM `{variables['PROJECT_ID']}.{variables['DATASET_ID']}.{variables['TABLE_ID']}`")

    # turn max_date into a datetime object
    max_date = bigquery_hook.get_first(sql_query)[0]
    max_date = max_date.split('+')[0]  # remove timezone
    max_date = datetime.strptime(max_date, "%Y-%m-%d %H:%M:%S.%f")

    ti.xcom_push(key='MAX_DATE', value=max_date)


def remove_duplicate_data(ti) -> None:
    """ Function compares file creation dates to max_date from BigQuery table to find files
    that were already transformed and uploaded to Bigquery and moves these files to the backup bucket.
    Files with invalid filenames are moved to a new folder called 'invalid' in the backup bucket.  """

    variables = get_variables()
    max_date = ti.xcom_pull(key='MAX_DATE', task_ids='retrieve_max_date')

    gcs_hook = GCSHook(gcp_conn_id=variables['CONN_ID'])

    # get filenames from bucket
    blobs = gcs_hook.list(bucket_name=variables['BUCKET_NAME'])
    datetime_pattern = r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d+'

    for blob in blobs:
        destination_filename = blob

        # check if filename is valid
        file_datetime_match = re.search(datetime_pattern, blob)
        if file_datetime_match:
            file_datetime = datetime.strptime(file_datetime_match.group(), "%Y-%m-%d %H:%M:%S.%f")
        else:
            file_datetime = max_date
            destination_filename = "invalid/" + destination_filename

        # move transformed files to a backup bucket
        if blob.endswith(".pcap") and file_datetime <= max_date:
                gcs_hook.copy(source_bucket=variables['BUCKET_NAME'],
                              source_object=blob,
                              destination_bucket=variables['BACKUP_ID'],
                              destination_object=destination_filename)

                gcs_hook.delete(bucket_name=variables['BUCKET_NAME'],
                                object_name=blob)
