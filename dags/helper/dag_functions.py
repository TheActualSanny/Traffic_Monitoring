from airflow.models.variable import Variable
from airflow.providers.google.cloud.transfers.gcs_to_local import GCSHook
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook

from datetime import datetime
from scapy.all import rdpcap
from scapy.layers.l2 import Ether
from scapy.layers.inet import UDP, TCP, IP
import tempfile
import os

from helper.table_config import TABLE_SCHEMA, TIME_PARTITIONING


def get_variables():
    variables = Variable.get("GCP_CONFIG", deserialize_json=True)
    variables['OBJECT_NAME'] = "172.24.24.110/file3.pcap"
    variables['TABLE_SCHEMA'] = TABLE_SCHEMA
    variables['TIME_PARTITIONING'] = TIME_PARTITIONING

    return variables


def create_bigquery_table():
    variables = get_variables()
    hook = BigQueryHook(variables['CONN_ID'])

    hook.create_empty_table(project_id=variables["PROJECT_ID"],
                            dataset_id=variables["DATASET_ID"],
                            table_id=variables["TABLE_ID"],
                            schema_fields=variables["TABLE_SCHEMA"],
                            time_partitioning=variables["TIME_PARTITIONING"]
                            )


def download_pcap(ti):
    variables = get_variables()
    gcs_hook = GCSHook(gcp_conn_id=variables['CONN_ID'])

    file_contents = gcs_hook.download(bucket_name=variables['BUCKET_NAME'], object_name=variables['OBJECT_NAME'])

    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(file_contents)
    temp_file.close()
    ti.xcom_push(key='TEMP_FILENAME', value=temp_file.name)


def transform_and_upload(ti):
    variables = get_variables()
    bigquery_hook = BigQueryHook(gcp_conn_id=variables['CONN_ID'])

    filename = ti.xcom_pull(key='TEMP_FILENAME', task_ids='extract_files')
    packets = rdpcap(filename)

    data = []

    for packet in packets:
        source_mac = packet[Ether].src.lower()
        timestamp = datetime.fromtimestamp(packet.time).strftime('%Y-%m-%d %H:%M:%S')
        source_ip = packet[IP].src
        destination_ip = packet[IP].dst

        if packet.haslayer(UDP):
            protocol = "UDP"
            packet_length = packet[UDP].len
        elif packet.haslayer(TCP):
            protocol = "TCP"
            packet_length = len(packet[TCP].payload)

        data.append({
            'TARGET_MAC_ADDRESS': source_mac,
            'TIMESTAMP': timestamp,
            'PROTOCOL': protocol,
            'SOURCE_IP': source_ip,
            'DESTINATION_IP': destination_ip,
            'PACKET_LENGTH': packet_length,
        })

    os.unlink(filename)

    bigquery_hook.insert_all(
        project_id=variables['PROJECT_ID'],
        dataset_id=variables['DATASET_ID'],
        table_id=variables['TABLE_ID'],
        rows=data
    )
