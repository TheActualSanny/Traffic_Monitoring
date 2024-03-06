from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime

from helper.dag_functions import create_bigquery_table, download_pcap, transform_and_upload


default_args = {
    'owner': 'barbare',
    'depends_on_past': False
}

with DAG(
        dag_id='bucket_to_bigquery',
        start_date=datetime(2024, 3, 6),
        default_args=default_args,
        schedule=None,
        render_template_as_native_obj=True,
        tags=["etl"]
) as dag:
    create_table = PythonOperator(
        task_id='create_table',
        python_callable=create_bigquery_table,
        provide_context=True
    )

    extract_files = PythonOperator(
        task_id='extract_files',
        python_callable=download_pcap,
        provide_context=True
    )

    transform_and_upload = PythonOperator(
        task_id="transform_and_upload_files",
        python_callable=transform_and_upload,
        provide_context=True
    )

    create_table >> extract_files >> transform_and_upload
