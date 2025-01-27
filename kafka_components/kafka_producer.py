from kafka import KafkaProducer
import json
from utils.config import KAFKA_BROKER, KAFKA_TOPIC

class KafkaMessageProducer:
    def __init__(self, broker: str, topic: str):
        self.broker = broker
        self.topic = topic
        self.producer = self.create_kafka_producer()

    def create_kafka_producer(self):
        return KafkaProducer(
            bootstrap_servers=self.broker,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')  
        )

    def send_message(self, message: dict):
        self.producer.send(self.topic, message)
        print(f"Sent: {message}")

    def produce_sample_messages(self):
        for i in range(5):
            message = {
                "id": i,
                "content": f"Message number {i}",
                "timestamp": "2025-01-14 20:25:00"
            }
            self.send_message(message)

    def close(self):
        self.producer.close()


kafka_producer = KafkaMessageProducer(KAFKA_BROKER, KAFKA_TOPIC)
kafka_producer.produce_sample_messages()
kafka_producer.close()
