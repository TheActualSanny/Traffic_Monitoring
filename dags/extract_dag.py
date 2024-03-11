from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.trigger_rule import TriggerRule

from datetime import datetime

from dag_functions.extract_functions import create_dataset_and_table, extract_pcap_files


default_args = {
    'owner': 'airflow',
    'depends_on_past': True
}


with DAG(
        dag_id='extract_files',
        start_date=datetime(2024, 3, 1),
        default_args=default_args,
        schedule_interval='*/10 * * * *',
        catchup=False,
        # schedule=None
) as dag:
    create_table = PythonOperator(
        task_id='create_table',
        python_callable=create_dataset_and_table,
        provide_context=True
    )

    extract_pcap = PythonOperator(
        task_id='extract_pcap',
        python_callable=extract_pcap_files,
        provide_context=True
    )

    backup_pcap_files = TriggerDagRunOperator(
        task_id='backup_pcap_files',
        trigger_dag_id='backup_files',
        trigger_rule=TriggerRule.ALL_SUCCESS
    )

    create_table >> extract_pcap >> backup_pcap_files
