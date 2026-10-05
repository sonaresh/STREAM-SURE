"""Optional Kafka adapter. Core STREAM-SURE does not require this module.
Install requirements-kafka.txt and point KAFKA_BOOTSTRAP_SERVERS at your Kafka/MSK endpoint.
This adapter intentionally contains no embedded credentials.
"""
import json, os

def producer_config():
    return {"bootstrap.servers": os.environ.get("KAFKA_BOOTSTRAP_SERVERS","localhost:9092"), "enable.idempotence": True, "acks":"all"}

def publish(topic, payload):
    try:
        from confluent_kafka import Producer
    except ImportError as e:
        raise RuntimeError("Install requirements-kafka.txt for Kafka support") from e
    p=Producer(producer_config()); p.produce(topic,json.dumps(payload).encode()); p.flush(10)
