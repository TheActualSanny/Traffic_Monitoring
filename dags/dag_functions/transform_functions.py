from airflow.providers.google.cloud.transfers.gcs_to_local import GCSHook
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook

from scapy.all import rdpcap
from scapy.layers.l2 import Ether
from scapy.layers.inet import UDP, TCP, IP
import tempfile
import os
import re

from helper.retrieve_variables import get_variables


def download_pcap(ti, **kwargs) -> None:
    """ Function retrieves a filename from dag_run configuration, connects to cloud storage
    using an Airflow storage hook, downloads file contents, and stores it in a temporary file. """

    variables = get_variables()
    conf_from_trigger = kwargs['dag_run'].conf
    object_name = conf_from_trigger['new_filename']

    gcs_hook = GCSHook(gcp_conn_id=variables['CONN_ID'])

    file_contents = gcs_hook.download(bucket_name=variables['BUCKET_NAME'], object_name=object_name)

    # create a temporary file, using pcap contents
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(file_contents)
    temp_file.close()

    ti.xcom_push(key='TEMP_FILENAME', value=temp_file.name)
    ti.xcom_push(key="FILENAME", value=object_name)


def transform_and_upload(ti) -> None:
    """ Function reads the passed temporary file, transforms and uploads it to a BigQuery table.
    If file datetime is invalid task will fail, this file will later on be moved to 'invalid' folder
    in the backup bucket. """

    variables = get_variables()
    bigquery_hook = BigQueryHook(gcp_conn_id=variables['CONN_ID'])

    filename = ti.xcom_pull(key='TEMP_FILENAME', task_ids='download_pcap_files')
    file_path = ti.xcom_pull(key='FILENAME', task_ids='download_pcap_files')

    try:
        packets = rdpcap(filename)
        data = []
    finally:
        # making sure temporary file gets deleted
        os.unlink(filename)

    datetime_pattern = r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d+'
    datetime_match = re.search(datetime_pattern, file_path).group()

    # iterate though packets transforming them one by one
    for packet in packets:
        source_mac = packet[Ether].src.lower()
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
            'TIMESTAMP': datetime_match,
            'PROTOCOL': protocol,
            'SOURCE_IP': source_ip,
            'DESTINATION_IP': destination_ip,
            'PACKET_LENGTH': packet_length,
        })

    # insert all the transformed data to the BigQuery table
    bigquery_hook.insert_all(
        project_id=variables['PROJECT_ID'],
        dataset_id=variables['DATASET_ID'],
        table_id=variables['TABLE_ID'],
        rows=data
    )
