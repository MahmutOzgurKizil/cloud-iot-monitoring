import time
import kafka_client as kc

if __name__ == "__main__":
    for i in range(10):
        try:
            kc.consume_score_updates()
            break
        except Exception as e:
            print(f"Kafka not ready, retrying in 5s... ({i+1}/10) Error: {e}")
            time.sleep(5)