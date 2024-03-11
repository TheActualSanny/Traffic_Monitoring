from airflow.models.variable import Variable

from helper.table_config import TABLE_SCHEMA, TIME_PARTITIONING


def get_variables():
    variables = Variable.get("GCP_CONFIG", deserialize_json=True)
    variables['TABLE_SCHEMA'] = TABLE_SCHEMA
    variables['TIME_PARTITIONING'] = TIME_PARTITIONING

    return variables
