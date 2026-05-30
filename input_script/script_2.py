

# File: input_script/script_2.py
import os 
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.sql.types import StringType


# Objective: 
# Segment real-time transaction .
# purchasing power into distinct valuation tiers (High, Mid, Low value clusters) .
# specifically targeting the retail "Clothing" division to dynamically route custom marketing rewards.

# 1. Spark Session Initialization
spark = SparkSession.builder \
    .appName("Faulty_Customer_Segmentation_Job") \
    .master("local[*]") \
    .getOrCreate()

ROOT_DIR = os.path.abspath(os.getcwd())

TXN_PATH = os.path.join(ROOT_DIR, "data", "transactions.csv")
OUTPUT_PATH = os.path.join(ROOT_DIR, "output_data_segments")

txn_df = spark.read.csv(TXN_PATH, header=True, inferSchema=True)

def calculate_tier(amount):
    if amount is None:
        return "Unknown"
    elif amount > 500:
        return "High-Value"
    elif amount > 100:
        return "Mid-Value"
    else:
        return "Low-Value"

tier_udf = F.udf(calculate_tier, StringType())
segmented_df = txn_df.withColumn("customer_tier", tier_udf(F.col("amount")))

high_value_count = segmented_df.filter(F.col("customer_tier") == "High-Value").count()
print(f"Total High-Value Transactions logged: {high_value_count}")

final_df = segmented_df.filter(F.col("category") == "Electronics")

final_df.repartition(1).write.mode("overwrite").csv(OUTPUT_PATH, header=True)
