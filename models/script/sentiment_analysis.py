#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StructField, StringType
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

MODEL_PATH = "/models"

# ===== CARICAMENTO MODELLO =====
print("\n[2/6] Loading BERT model and tokenizer...")
device = torch.device("cpu")
print(f"   Device: {device}")

try:
    global_tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, use_fast=False)
    global_model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    global_model.eval()
    
    with open(f"{MODEL_PATH}/meta.json", "r") as f:
        meta = json.load(f)
        max_length = meta.get("max_length", 128) 
    
    print("   ✓ Model loaded successfully!")
    print(f"   Max sequence length: {max_length}")
        
except Exception as e:
    print(f"   ✗ Error loading model: {e}")
    raise

# ===== SPARK SESSION =====
print("\n[3/6] Creating Spark session...")
spark = SparkSession.builder \
    .appName("ReviewAspectAnalysis") \
    .master("local[1]") \
    .config("spark.sql.shuffle.partitions", "1") \
    .config("spark.driver.memory", "512m") \
    .config("spark.memory.fraction", "0.6") \
    .config("spark.python.worker.faulthandler.enabled", "true") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
print("   ✓ Spark session created")

# ===== SCHEMA KAFKA =====
kafka_schema = StructType([
    StructField("review_id", StringType(), True),
    StructField("imdb_id", StringType(), True),
    StructField("film_title", StringType(), True),
    StructField("review_title", StringType(), True),
    StructField("review_text", StringType(), True),
    StructField("review_rating", StringType(), True),
    StructField("review_author", StringType(), True),
    StructField("review_date", StringType(), True),
    StructField("imdb_reviews_url", StringType(), True),
    StructField("@timestamp", StringType(), True),
    StructField("source", StringType(), True),
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

# ===== PROCESSING =====
print("\n[5/6] Setting up stream processing...")

reviews_df = df.selectExpr("CAST(value AS STRING) as json_string") \
    .select(from_json(col("json_string"), kafka_schema).alias("data")) \
    .select("data.*")

# ===== FOREACHBATCH =====
def process_batch(batch_df, batch_id):
    """Processa batch con BERT."""
    try:
        if batch_df.isEmpty():
            return
        
        count = batch_df.count()
        print(f"\n[Batch {batch_id}] Processing {count} reviews...")
        
        # Raccogli righe
        rows = batch_df.collect()
        results = []
        
        for idx, row in enumerate(rows, 1):
            text = row.review_text
            
            if not text or len(str(text).strip()) == 0:
                predictions = [0.0] * 7
            else:
                try:
                    inputs = global_tokenizer(
                        str(text),
                        return_tensors="pt",
                        truncation=True,
                        max_length=max_length,
                        padding=True
                    )
                    
                    with torch.no_grad():
                        outputs = global_model(**inputs)
                        predictions = outputs.logits.detach().cpu().numpy().reshape(-1).tolist()
                    
                    print(f"  [{idx}/{count}] ✓ Predicted")
                        
                except Exception as e:
                    print(f"  [{idx}/{count}] ✗ Error: {e}")
                    predictions = [0.0] * 7
            
            # Crea risultato
            result = {
                "review_id": row.review_id,
                "imdb_id": row.imdb_id,
                "film_title": row.film_title if row.film_title else "",
                "review_title": row.review_title if row.review_title else "",
                "review_author": row.review_author if row.review_author else "",
                "review_rating": row.review_rating if row.review_rating else "",
                "review_date": row.review_date if row.review_date else "",
                "pred_direction": float(predictions[0]),
                "pred_cinematography": float(predictions[1]),
                "pred_unique_concept": float(predictions[2]),
                "pred_story": float(predictions[3]),
                "pred_emotions": float(predictions[4]),
                "pred_characters": float(predictions[5]),
                "pred_production_design": float(predictions[6])
            }
            results.append(result)
        
        # Invia a Kafka
        output_rows = [Row(value=json.dumps(r)) for r in results]
        
        if output_rows:
            output_df = spark.createDataFrame(output_rows)
            output_df.write \
                .format("kafka") \
                .option("kafka.bootstrap.servers", "kafka:9092") \
                .option("topic", "revisedReview") \
                .save()
            
            print(f"[Batch {batch_id}] ✓ Sent {len(results)} reviews to Kafka")
    
    except Exception as e:
        print(f"[Batch {batch_id}] ✗ Batch error: {e}")
        import traceback
        traceback.print_exc()

# ===== START STREAMING =====
print("\n[6/6] Starting streaming query...")
print("=" * 70)
print("Input:  Kafka topic 'reviewFilm'")
print("Output: Kafka topic 'revisedReview'")
print("=" * 70)

query = reviews_df.writeStream \
    .foreachBatch(process_batch) \
    .trigger(processingTime='10 seconds') \
    .option("checkpointLocation", "/tmp/spark-checkpoints/reviewFilm") \
    .start()

print("✓ Streaming started!")

try:
    query.awaitTermination()
except KeyboardInterrupt:
    print("\n\nStopping stream...")
    query.stop()
    spark.stop()
    print("Done!")