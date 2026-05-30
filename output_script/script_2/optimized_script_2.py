import os 
import pyspark.sql.functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

# Set Spark configuration parameters
spark.conf.set("spark.sql.shuffle.partitions", "4")
spark.conf.set("spark.sql.files.maxPartitionBytes", "134217728")  # 128 MB

ROOT_DIR = os.path.abspath(os.getcwd())

TXN_PATH = os.path.join(ROOT_DIR, "data", "transactions.csv")
OUTPUT_PATH = os.path.join(ROOT_DIR, "output_data_segments")

# Define schema explicitly
txn_schema = StructType([
    StructField("transaction_id", StringType(), True),
    StructField("user_id", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("country", StringType(), True),
    StructField("category", StringType(), True)
])

# Read the transactions data with the defined schema
txn_df = spark.read.csv(TXN_PATH, header=True, schema=txn_schema)

# Filter early for the "Electronics" category
filtered_txn_df = txn_df.filter(F.col("category") == "Electronics")

# Use vectorized operations to calculate customer tier
segmented_df = filtered_txn_df.withColumn(
    "customer_tier",
    F.when(F.col("amount").isNull(), "Unknown")
     .when(F.col("amount") > 500, "High-Value")
     .when(F.col("amount") > 100, "Mid-Value")
     .otherwise("Low-Value")
)

# Count high-value transactions
high_value_count = segmented_df.filter(F.col("customer_tier") == "High-Value").count()
print(f"Total High-Value Transactions logged: {high_value_count}")

# Assign final DataFrame for writing
final_df = segmented_df

# Write the final DataFrame to CSV
final_df.coalesce(1).write.mode("overwrite").csv(OUTPUT_PATH, header=True)