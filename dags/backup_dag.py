from airflow import DAG
from airflow.operators.python import PythonOperator

from datetime import datetime

from dag_functions.backup_functions import create_backup_bucket, remove_duplicate_data
from helper.airflow_config import DEFAULT_ARGS


with DAG(
        dag_id='backup_files',
        start_date=datetime(2024, 3, 1),
        default_args=DEFAULT_ARGS,
        schedule=None,
        # render_template_as_native_obj=True,
        tags=["backup"]
) as dag:
    create_backup = PythonOperator(
        task_id='create_backup',
        python_callable=create_backup_bucket,
        provide_context=True
    )

    remove_duplicates = PythonOperator(
        task_id='remove_duplicates',
        python_callable=remove_duplicate_data,
        provide_context=True
    )

    create_backup >> remove_duplicates
