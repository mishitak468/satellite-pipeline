from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp, when
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# Spark Setup with Kafka, Postgres, and Delta Lake connectors
# Updated Spark Setup for Spark 4.0.x (Scala 2.13) compatibility
spark = SparkSession.builder \
    .appName("SatellitePipeline") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.0-preview2,org.postgresql:postgresql:42.5.0,io.delta:delta-spark_2.13:3.3.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

schema = StructType([
    StructField("satellite_id", StringType()),
    StructField("timestamp", DoubleType()),
    StructField("altitude", DoubleType()),
    StructField("velocity", DoubleType()),
    StructField("battery_temp", DoubleType())
])

# Read from Kafka
df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "satellite_telemetry").load()

# Transform & DQ Logic
clean_df = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")).select("data.*") \
    .withColumn("ingestion_time", current_timestamp()) \
    .withColumn("is_anomaly", when(col("battery_temp") > 40, 1).otherwise(0))

# Multi-Stage Sink


def process_batch(batch_df, batch_id):
    # 1. Write to PostgreSQL (Working!)
    batch_df.write.format("jdbc") \
        .option("url", "jdbc:postgresql://localhost:5432/telemetry_db") \
        .option("driver", "org.postgresql.Driver") \
        .option("dbtable", "telemetry") \
        .option("user", "user") \
        .option("password", "password") \
        .mode("append") \
        .save()

    # 2. Write to Data Lake using Parquet (Stable for Spark 4.0)
    batch_df.write.mode("append").parquet(
        "/Users/mishitakaja/satellite-pipeline/data_lake/telemetry")

    print(f"Batch {batch_id} processed successfully to Postgres and Parquet.")


query = clean_df.writeStream.foreachBatch(process_batch) \
    .option("checkpointLocation", "./checkpoints").start()

query.awaitTermination()
