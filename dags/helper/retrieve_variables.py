from airflow.models.variable import Variable

from helper.table_config import TABLE_SCHEMA, TIME_PARTITIONING


def get_variables() -> dict:
    """
    Function retrieves necessary variables from Airflow UI.

    * Variables are predefined in Airflow's variable section, formatted in json.
    * Additional variables such as table schema and time partitioning schema are defined in the
      BigQuery table configuration file.

    Returns:
        variables - dictionary containing all the variables for easy access.
    """

    variables = Variable.get("GCP_CONFIG", deserialize_json=True)
    variables['TABLE_SCHEMA'] = TABLE_SCHEMA
    variables['TIME_PARTITIONING'] = TIME_PARTITIONING

    return variables
