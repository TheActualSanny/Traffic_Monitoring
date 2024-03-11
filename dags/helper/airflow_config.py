DEFAULT_ARGS = {
    'owner': 'barbare',
    'depends_on_past': True
}

TABLE_SCHEMA = [
    {"name": "TARGET_MAC_ADDRESS", "type": "STRING", "mode": "REQUIRED"},
    {"name": "TIMESTAMP", "type": "TIMESTAMP", "mode": "REQUIRED"},
    {"name": "PROTOCOL", "type": "STRING", "mode": "REQUIRED"},
    {"name": "SOURCE_IP", "type": "STRING", "mode": "REQUIRED"},
    {"name": "DESTINATION_IP", "type": "STRING", "mode": "REQUIRED"},
    {"name": "PACKET_LENGTH", "type": "INTEGER", "mode": "REQUIRED"}
]

TIME_PARTITIONING = {
    "type": "DAY",
    "field": "TIMESTAMP"
}
