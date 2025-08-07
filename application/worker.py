import time
import kafka_client as kc

if __name__ == "__main__":
    while True:
        try:
            kc.consume_score_updates()
            break
        except Exception as e:
            print(f"Kafka not ready, retrying in 5s... Error: {e}")
            time.sleep(5)