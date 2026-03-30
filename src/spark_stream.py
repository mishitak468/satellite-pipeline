import os
import requests
import psycopg2
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# config
KAFKA_SERVER = os.getenv("KAFKA_SERVER", "localhost:9092")
INFERENCE_URL = os.getenv("INFERENCE_URL", "http://localhost:8000/predict")
DB_HOST = os.getenv("DB_HOST", "localhost")
DATA_LAKE_PATH = os.getenv("DATA_LAKE_PATH", "data_lake/telemetry")

# Spark setup
spark = SparkSession.builder \
    .appName("SatellitePipeline") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.0-preview2") \
    .getOrCreate()

schema = StructType([
    StructField("satellite_id", StringType()),
    StructField("timestamp", DoubleType()),
    StructField("altitude", DoubleType()),
    StructField("velocity", DoubleType()),
    StructField("battery_temp", DoubleType())
])

# Kafka
df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_SERVER) \
    .option("subscribe", "satellite_telemetry").load()

clean_df = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")).select("data.*") \
    .withColumn("ingestion_time", current_timestamp())

# inference logic


def get_ml_prediction(row):
    try:
        payload = {
            "altitude": float(row.altitude),
            "velocity": float(row.velocity),
            "battery_temp": float(row.battery_temp)
        }
        # Using the dynamic INFERENCE_URL
        response = requests.post(INFERENCE_URL, json=payload, timeout=1.0)
        return response.json().get("is_anomaly", 0)
    except Exception:
        return 0


def process_batch(batch_df, batch_id):
    if batch_df.isEmpty():
        return

    print(f"--- Processing Batch {batch_id} ---")
    pandas_df = batch_df.toPandas()

    # Request predictions from the Inference Microservice
    pandas_df['is_anomaly'] = pandas_df.apply(get_ml_prediction, axis=1)

    # Database Ingestion
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database="postgres",
            user="postgres",
            password="password"
        )
        conn.autocommit = True
        cur = conn.cursor()

        for _, row in pandas_df.iterrows():
            cur.execute(
                """INSERT INTO telemetry 
                   (satellite_id, timestamp, altitude, velocity, battery_temp, ingestion_time, is_anomaly) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (row.satellite_id, row.timestamp, row.altitude, row.velocity,
                 row.battery_temp, row.ingestion_time, int(row.is_anomaly))
            )
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Postgres Error: {e}")

    # Data Lake Storage (Parquet)
    try:
        if not os.path.exists(DATA_LAKE_PATH):
            os.makedirs(DATA_LAKE_PATH)

        file_path = os.path.join(DATA_LAKE_PATH, f"batch_{batch_id}.parquet")
        pandas_df.to_parquet(file_path)
        print(f"Batch {batch_id} saved to Data Lake.")
    except Exception as e:
        print(f"Data Lake Error: {e}")


query = clean_df.writeStream \
    .foreachBatch(process_batch) \
    .option("checkpointLocation", "./checkpoints") \
    .start()

query.awaitTermination()
