from kafka import KafkaProducer
import json
import time
import random

# Added api_version to avoid the auto-check and retries for stability
producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    request_timeout_ms=10000,
    reconnect_backoff_ms=500
)

print("Connection successful! Starting telemetry stream...")
while True:
    data = {
        "satellite_id": f"SAT-{random.randint(1, 5)}",
        "timestamp": time.time(),
        "altitude": random.uniform(300, 400),
        "velocity": random.uniform(7.5, 7.9),
        "battery_temp": 150
        # random.uniform(-10, 45)
    }
    producer.send('satellite_telemetry', data)
    print(f"Sent to Kafka: {data}")
    time.sleep(1)
