from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from datetime import datetime

from helper.extract_functions import create_bigquery_table, extract_pcap_files


default_args = {
    'owner': 'barbare',
    'depends_on_past': False
}

with DAG(
        dag_id='extract_files',
        start_date=datetime(2024, 3, 1),
        default_args=default_args,
        # schedule=None,
        schedule_interval='*/10 * * * *',
        catchup=False,
        render_template_as_native_obj=True,
        tags=["extract_pcaps"],
) as dag:
    create_table = PythonOperator(
        task_id='create_table',
        python_callable=create_bigquery_table,
        provide_context=True
    )

    extract_pcap = PythonOperator(
        task_id='extract_pcap',
        python_callable=extract_pcap_files,
        provide_context=True
    )

    create_table >> extract_pcap
