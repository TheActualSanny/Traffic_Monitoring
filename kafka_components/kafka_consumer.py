from kafka import KafkaConsumer
import json

def create_kafka_consumer(kafka_broker, kafka_topic, group_id='test_group'):
    consumer = KafkaConsumer(
        kafka_topic,
        bootstrap_servers=kafka_broker,
        group_id=group_id,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )
    return consumer
