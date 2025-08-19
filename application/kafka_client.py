import os
import time
import db
from redis_client import rc
from kafka import KafkaProducer, KafkaConsumer
import json
from datetime import datetime

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')

_producer = None

def get_device_data_producer():
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
        )
    return _producer

def get_device_data_consumer():
    return KafkaConsumer(
        'device_data_updates',
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='device_data_worker'
    )

def send_device_data_update(device_id, metric_type, value, timestamp):
    producer = get_device_data_producer()
    message = {
        'device_id': device_id,
        'metric_type': metric_type,
        'value': value,
        'timestamp': timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp
    }
    producer.send('device_data_updates', message)

def consume_device_data_updates():
    consumer = get_device_data_consumer()
    for message in consumer:
        try:
            data = message.value
            
            # Parse timestamp back to datetime object
            timestamp_str = data['timestamp']
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = timestamp_str
            
            # Store in database
            db.insert_device_data(
                data['device_id'],
                data['metric_type'],
                data['value'],
                timestamp
            )
            
            # Clear relevant caches
            device_id = data['device_id']
            rc.delete("all_devices")
            
        except Exception as e:
            # Keep error output concise
            print(f"Error processing message: {e}")

def run_worker():
    while True:
        try:
            consume_device_data_updates()
            break
        except Exception as e:
            # Minimal retry notice
            print(f"Kafka not ready, retrying in 5s: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_worker()