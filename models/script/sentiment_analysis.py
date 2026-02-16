#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, from_json, struct, to_json
from pyspark.sql.types import StructType, StructField, StringType, FloatType, ArrayType
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

print("=" * 70)
print("SPARK STREAMING + BERT ASPECT ANALYSIS")
print("=" * 70)

print("\n[1/6] Waiting for Kafka to be ready...")
time.sleep(15)

LABEL_ORDER = [
    "direction", "cinematography", "unique_concept",
    "story", "emotions", "characters", "production_design"
]

# ===== CARICAMENTO MODELLO =====
print("\n[2/6] Loading BERT model and tokenizer...")
MODEL_PATH = "/models"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"   Device: {device}")

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, use_fast=False)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    model.to(device)
    model.eval()
    print("   ✓ Model loaded successfully!")
    
    with open(f"{MODEL_PATH}/meta.json", "r") as f:
        meta = json.load(f)
        max_length = meta.get("max_length", 128)
        print(f"   Max sequence length: {max_length}")
        print(f"   Model: {meta.get('model_name', 'N/A')}")
        
except Exception as e:
    print(f"   ✗ Error loading model: {e}")
    raise

# ===== UDF PER PREDIZIONE =====
def predict_aspects(review_text):
    if not review_text or len(review_text.strip()) == 0:
        return [0.0] * 7
    
    try:
        inputs = tokenizer(
            review_text,
            return_tensors="pt",
            truncation=True,
            max_length=max_length,
            padding=True
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            predictions = outputs.logits.detach().cpu().numpy().reshape(-1).tolist()
        
        return predictions
    
    except Exception as e:
        print(f"   ⚠ Prediction error: {e}")
        return [0.0] * 7

predict_udf = udf(predict_aspects, ArrayType(FloatType()))

# ===== SPARK SESSION =====
print("\n[3/6] Creating Spark session...")
spark = SparkSession.builder \
    .appName("ReviewAspectAnalysis") \
    .master("local[2]") \
    .config("spark.sql.shuffle.partitions", "2") \
    .config("spark.driver.memory", "1500m") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
print("   ✓ Spark session created")

# ===== SCHEMA KAFKA MESSAGE =====
kafka_schema = StructType([
    StructField("review_id", StringType(), True),        # PRIMARY KEY
    StructField("imdb_id", StringType(), True),          # ID IMDb
    StructField("review_title", StringType(), True),
    StructField("review_text", StringType(), True),
    StructField("review_rating", StringType(), True),
    StructField("review_author", StringType(), True),
    StructField("review_date", StringType(), True),
    StructField("imdb_reviews_url", StringType(), True), # Opzionale
    StructField("@timestamp", StringType(), True),       # Da Fluent
    StructField("source", StringType(), True),           # Da Fluent
])

# ===== KAFKA STREAMING =====
print("\n[4/6] Connecting to Kafka...")
try:
    df = spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "reviewFilm") \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .option("maxOffsetsPerTrigger", "10") \
        .load()
    
    print("   ✓ Connected to Kafka topic 'reviewFilm'")
    
except Exception as e:
    print(f"   ✗ Kafka connection error: {e}")
    raise

# ===== PROCESSAMENTO STREAM =====
print("\n[5/6] Setting up stream processing...")

reviews_df = df.selectExpr("CAST(value AS STRING) as json_string") \
    .select(from_json(col("json_string"), kafka_schema).alias("data")) \
    .select("data.*")

# Applica modello BERT
predictions_df = reviews_df.withColumn("predictions", predict_udf(col("review_text")))

# Esplodi predizioni
for i, label in enumerate(LABEL_ORDER):
    predictions_df = predictions_df.withColumn(label, col("predictions")[i])

# Output finale
output_df = predictions_df.select(
    "review_id",
    "imdb_id",
    "review_title",
    "review_author",
    "review_rating",
    "review_date",
    col("direction").alias("pred_direction"),
    col("cinematography").alias("pred_cinematography"),
    col("unique_concept").alias("pred_unique_concept"),
    col("story").alias("pred_story"),
    col("emotions").alias("pred_emotions"),
    col("characters").alias("pred_characters"),
    col("production_design").alias("pred_production_design")
)

# ===== OUTPUT SU KAFKA =====
print("\n[6/6] Starting streaming query...")
print("=" * 70)
print("Input:  Kafka topic 'reviewFilm'")
print("Output: Kafka topic 'revisedReview'")
print("=" * 70)

# Converti in JSON per Kafka
output_json = output_df.select(
    to_json(struct([output_df[c] for c in output_df.columns])).alias("value")
)

query = output_json.writeStream \
    .outputMode("append") \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("topic", "revisedReview") \
    .option("checkpointLocation", "/tmp/checkpoint_revisedReview") \
    .trigger(processingTime='5 seconds') \
    .start()

print("✓ Streaming started!")

try:
    query.awaitTermination()
except KeyboardInterrupt:
    print("\n\nStopping stream...")
    query.stop()
    spark.stop()
    print("Done!")