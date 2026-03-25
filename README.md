# Satellite Telemetry Pipeline
 
A real-time data engineering pipeline that ingests, processes, and monitors streaming satellite telemetry using Apache Kafka, PySpark Structured Streaming, PostgreSQL, and Grafana all containerized with Docker Compose.
 
---
 
## Overview
 
This project simulates a ground station telemetry ingestion system. A producer continuously streams telemetry readings (altitude, velocity, battery temperature) from multiple satellites into a Kafka topic. A PySpark Structured Streaming job picks up those events, applies data quality checks, flags anomalies, and writes processed data to both a PostgreSQL database and a local Parquet data lake. Grafana connects to Postgres for live dashboard visualization.
 
The pipeline is designed around the same patterns used in production data infrastructure, which is event-driven ingestion, micro-batch processing, multi-sink output, and checkpointed fault recovery.
 
---
 
## Architecture
 
```
Telemetry Producer (Python)
        │
        ▼
   Apache Kafka (Topic: satellite_telemetry)
        │
        ▼
PySpark Structured Streaming
   ├── Anomaly Detection (battery_temp > 40°C)
   ├── Schema Validation & Ingestion Timestamps
   └── foreachBatch Sink
          ├── PostgreSQL (telemetry_db)  ←── Grafana Dashboard
          └── Parquet Data Lake
```
 
---
 
## Stack
 
| Layer | Technology |
|---|---|
| Message Broker | Apache Kafka + Zookeeper (Confluent 7.5) |
| Stream Processing | PySpark 4.0 Structured Streaming |
| Storage | PostgreSQL 15, Parquet (Delta Lake-compatible) |
| Orchestration | Docker Compose |
| Visualization | Grafana |
| Language | Python 3 |
 
---
 
## Features
 
- **Real-time ingestion** — Kafka producer emits one telemetry event per second across 5 simulated satellites
- **Stream processing** — PySpark reads from Kafka, parses JSON payloads, attaches ingestion timestamps, and classifies anomalies inline
- **Anomaly flagging** — any reading with `battery_temp > 40°C` is automatically tagged with `is_anomaly = 1` at processing time
- **Dual-sink output** — each micro-batch writes to both PostgreSQL (for live querying) and a Parquet data lake (for historical analysis)
- **Checkpointing** — Spark checkpoints ensure exactly-once processing semantics and recovery from failure
- **Live dashboards** — Grafana connects directly to Postgres for real-time telemetry visualization
 
---
 
## Getting Started
 
### Prerequisites
 
- Docker & Docker Compose
- Python 3.8+
- Java 11+ (required for PySpark)
 
### 1. Start the infrastructure
 
```bash
docker-compose up -d
```
 
This starts Zookeeper, Kafka, PostgreSQL, and Grafana. Wait ~15 seconds for Kafka to be fully ready.
 
### 2. Install Python dependencies
 
```bash
pip install -r requirements.txt
```
 
### 3. Create the Postgres table
 
Connect to the database and run:
 
```sql
CREATE TABLE telemetry (
    satellite_id    VARCHAR(20),
    timestamp       DOUBLE PRECISION,
    altitude        DOUBLE PRECISION,
    velocity        DOUBLE PRECISION,
    battery_temp    DOUBLE PRECISION,
    ingestion_time  TIMESTAMP,
    is_anomaly      INTEGER
);
```
 
### 4. Start the Spark processing job
 
```bash
python consumer.py
```
 
### 5. Start the telemetry producer
 
In a separate terminal:
 
```bash
python producer.py
```
 
You should see telemetry events being sent to Kafka and processed by Spark in real time.
 
### 6. View dashboards
 
Open [http://localhost:3000](http://localhost:3000) in your browser (default Grafana credentials: `admin / admin`) and connect a data source to PostgreSQL at `localhost:5432`.
 
---
 
## Project Structure
 
```
satellite-pipeline/
├── producer.py          # Kafka producer — simulates satellite telemetry stream
├── consumer.py          # PySpark Structured Streaming job — processes & sinks data
├── docker-compose.yml   # Infrastructure: Kafka, Zookeeper, Postgres, Grafana
├── requirements.txt     # Python dependencies
├── data_lake/           # Parquet output (gitignored)
└── checkpoints/         # Spark checkpoint directory (gitignored)
```
 
---
 
## Telemetry Schema
 
| Field | Type | Description |
|---|---|---|
| `satellite_id` | string | Satellite identifier (SAT-1 through SAT-5) |
| `timestamp` | float | Unix epoch of the reading |
| `altitude` | float | Orbital altitude in km (300–400 km range) |
| `velocity` | float | Orbital velocity in km/s (7.5–7.9 km/s range) |
| `battery_temp` | float | Battery temperature in °C (-10 to 45°C range) |
| `ingestion_time` | timestamp | Time the record was processed by Spark |
| `is_anomaly` | int | 1 if battery_temp exceeds 40°C threshold, else 0 |
 
---
 
## Notes
 
- Built and tested against PySpark 4.0 (preview) with Scala 2.13 — required explicit connector version alignment for Kafka and Delta Lake packages
- Kafka is configured with `ENABLE_KRAFT: "no"` to use classic ZooKeeper coordination for broader compatibility
- The Spark job uses `foreachBatch` rather than native Kafka sinks to support writing to multiple heterogeneous targets in a single batch pass
 
---
 
## Potential Extensions
 
- Add a dead-letter queue for malformed Kafka messages
- Swap Parquet sink for Delta Lake with schema enforcement and time travel
- Deploy on AWS (MSK + EMR Serverless + RDS)
- Add Prometheus metrics scraping from the Spark driver
- Containerize the producer and consumer services into the Compose stack
