import os
import db
from redis_client import rc
from kafka import KafkaProducer, KafkaConsumer
import json

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')

_producer = None

def get_score_producer():
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    return _producer

def get_score_consumer():
    return KafkaConsumer(
        'score_updates',
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='score_worker'
    )

def send_score_update(player_id, score):
    producer = get_score_producer()
    producer.send('score_updates', {'player_id': player_id, 'score': score})
    producer.flush()

def consume_score_updates():
    consumer = get_score_consumer()
    for message in consumer:
        data = message.value
        db.upsert_player_score(data['player_id'], data['score'])
        rc.delete("leaderboard")