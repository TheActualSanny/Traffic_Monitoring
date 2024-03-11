from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime

from dag_functions.transform_functions import download_pcap, transform_and_upload
from helper.airflow_config import DEFAULT_ARGS


with DAG(
        dag_id='bucket_to_bigquery',
        start_date=datetime(2024, 3, 1),
        default_args=DEFAULT_ARGS,
        schedule=None,
        # render_template_as_native_obj=True,
        tags=["etl"]
) as dag:
    downlaod_pcap_files = PythonOperator(
        task_id='download_pcap_files',
        python_callable=download_pcap,
        provide_context=True
    )

    transform_and_upload = PythonOperator(
        task_id="transform_and_upload_files",
        python_callable=transform_and_upload,
        provide_context=True
    )

    downlaod_pcap_files >> transform_and_upload
