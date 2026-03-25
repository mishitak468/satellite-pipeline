Real-Time Satellite Telemetry Pipeline
An end-to-end data engineering pipeline that simulates satellite telemetry, processes it in real-time, and stores it for analytical use.

Tech Stack
Language: Python 3.9

Streaming: Apache Kafka (Confluent)

Processing: Apache Spark 4.0.0 (Structured Streaming)

Storage: PostgreSQL (Relational) and Parquet (Analytical Data Lake)

Orchestration: Docker and Docker Compose

System Architecture
Producer: Simulates satellite data (altitude, velocity, temperature) and streams to Kafka.

Kafka: High-throughput message broker for streaming data ingestion.

Spark: Consumes streams, performs schema validation, and flags anomalies (e.g., high battery temperature).

Sinks: Multi-sink architecture writing to a PostgreSQL database for real-time alerts and a Parquet lake for historical analysis.

Technical Challenges and Solutions
Spark 4.0 Migration: Managed the transition to Scala 2.13 and Spark 4.0, resolving library incompatibilities by pinning specific JAR connectors.

macOS Docker Networking: Resolved common localhost-to-container networking hurdles by implementing advanced Kafka Listener configurations.

Environment Stability: Implemented custom foreachBatch logic to handle JDBC driver registration and local file system pathing in a preview Spark environment.

How to Run
Start infrastructure: docker-compose -f infra/docker-compose.yml up -d

Start Producer: python src/producer.py

Start Processor: python src/spark_stream.py

Testing and Validation
To verify the anomaly detection logic:

Modify src/producer.py to set battery_temp range to random.uniform(41, 60).

Run the pipeline for 10 seconds.

Query the PostgreSQL database to confirm the is_anomaly flag is set to 1 for those records.
