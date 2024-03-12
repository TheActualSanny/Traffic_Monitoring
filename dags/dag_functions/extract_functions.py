from airflow.providers.google.cloud.transfers.gcs_to_local import GCSHook
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from airflow.api.common.trigger_dag import trigger_dag

from datetime import datetime
import time

from helper.retrieve_variables import get_variables


def create_dataset_and_table() -> None:
    """ Function creates a BigQuery dataset and table with
    time-based partitioning if they don't already exist. """

    variables = get_variables()
    hook = BigQueryHook(variables['CONN_ID'])

    hook.create_empty_dataset(project_id=variables['PROJECT_ID'],
                              dataset_id=variables['DATASET_ID'],
                              location="US",
                              exists_ok=True)

    hook.create_empty_table(project_id=variables['PROJECT_ID'],
                            dataset_id=variables['DATASET_ID'],
                            table_id=variables['TABLE_ID'],
                            schema_fields=variables['TABLE_SCHEMA'],
                            time_partitioning=variables['TIME_PARTITIONING'],
                            exists_ok=True)

    # making sure that table will be created for the next tasks
    time.sleep(5)


def trigger_transform_dag(blob_conf: dict) -> None:
    """ Function triggers the transformation dag with filename configuration and run_id.
    Current datetime is used as the run_id to ensure unique dag run-id's for each filename.

    Args:
        blob_conf - dictionary containing the filename the DAG should be run with. """

    run_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    trigger_dag(dag_id="bucket_to_bigquery", conf=blob_conf, run_id=run_id)


def extract_pcap_files() -> None:
    """ Function extracts valid pcap filenames from Google Cloud Storage Bucket and
    triggers the next task for each valid filename, passing filename. """

    variables = get_variables()
    gcs_hook = GCSHook(gcp_conn_id=variables['CONN_ID'])

    blobs = gcs_hook.list(bucket_name=variables['BUCKET_NAME'])

    for blob in blobs:
        if blob.endswith(".pcap"):
            trigger_transform_dag({'new_filename': blob})

            # making sure dag_id's will be unique for the next dag run
            time.sleep(2)
