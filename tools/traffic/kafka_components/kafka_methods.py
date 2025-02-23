import json
from kafka import KafkaConsumer, KafkaProducer

def create_consumer(kafka_broker: str, kafka_topic: str, group_id = 'packet_consumers') -> KafkaConsumer:
    '''
        Instantiates a KafkaConsumer and returns it so that we can store it in an attribute
        of a Server object.
    '''
    consumer = KafkaConsumer(
        kafka_topic,
        bootstrap_servers = kafka_broker,
        group_id = group_id,
        value_deserializer = lambda x: json.loads(x.decode('utf-8'))
    )
    return consumer

def create_producer(kafka_broker: str, kafka_topic: str) -> KafkaProducer:
    '''
        Instantiates and returns an KafkaProducer object tjat we also use in 
        a Server instance to send messages to a topic.
    '''
    producer = KafkaProducer(
        bootstrap_servers = kafka_broker,
        value_serializer = lambda x: json.dumps(x).encode('utf-8')
    )
    return producer
