from airflow.models.variable import Variable
from airflow.providers.google.cloud.transfers.gcs_to_local import GCSHook
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from airflow.api.common.trigger_dag import trigger_dag

from datetime import datetime
import time

from helper.airflow_config import TABLE_SCHEMA, TIME_PARTITIONING


def get_variables():
    variables = Variable.get("GCP_CONFIG", deserialize_json=True)
    variables['TABLE_SCHEMA'] = TABLE_SCHEMA
    variables['TIME_PARTITIONING'] = TIME_PARTITIONING

    return variables


def create_dataset_and_table():
    variables = get_variables()
    hook = BigQueryHook(variables['CONN_ID'])

    hook.create_empty_dataset(project_id=variables["PROJECT_ID"],
                              dataset_id=variables["DATASET_ID"],
                              location='US',
                              exists_ok=True)

    hook.create_empty_table(project_id=variables["PROJECT_ID"],
                            dataset_id=variables["DATASET_ID"],
                            table_id=variables["TABLE_ID"],
                            schema_fields=variables["TABLE_SCHEMA"],
                            time_partitioning=variables["TIME_PARTITIONING"],
                            exists_ok=True)


def trigger_transform_dag(blob_conf):
    trigger_dag(dag_id="bucket_to_bigquery", conf=blob_conf, run_id=datetime.now().strftime("%Y%m%d%H%M%S%f"))


def extract_pcap_files():
    variables = get_variables()
    gcs_hook = GCSHook(gcp_conn_id=variables['CONN_ID'])

    blobs = gcs_hook.list(bucket_name=variables['BUCKET_NAME'])

    for blob in blobs:
        if blob.endswith(".pcap"):
            trigger_transform_dag({"new_filename": blob})
            time.sleep(5)
