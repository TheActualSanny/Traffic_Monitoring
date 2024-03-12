from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime

from dag_functions.backup_functions import create_backup_bucket, get_max_date, remove_duplicate_data


default_args = {
    'owner': 'airflow',
    'depends_on_past': True
}


with DAG(
        dag_id='backup_files',
        start_date=datetime(2024, 3, 1),
        default_args=default_args,
        schedule=None
) as dag:
    create_backup = PythonOperator(
        task_id='create_backup',
        python_callable=create_backup_bucket,
        provide_context=True
    )

    retrieve_max_date = PythonOperator(
        task_id='retrieve_max_date',
        python_callable=get_max_date,
        provide_context=True
    )

    remove_duplicates = PythonOperator(
        task_id='remove_duplicates',
        python_callable=remove_duplicate_data,
        provide_context=True
    )

    create_backup >> retrieve_max_date >> remove_duplicates
