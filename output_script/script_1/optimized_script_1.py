import os 
import pyspark.sql.functions as F

spark.conf.set("spark.sql.shuffle.partitions", "4")
spark.conf.set("spark.sql.files.maxPartitionBytes", "134217728")  # 128 MB

ROOT_DIR = os.path.abspath(os.getcwd())
TXN_PATH = os.path.join(ROOT_DIR, "data", "transactions.csv")
USER_PATH = os.path.join(ROOT_DIR, "data", "small_users.csv")
OUTPUT_PATH = os.path.join(ROOT_DIR, "output_data")

# Load data with explicit schema
txn_df = spark.read.csv(TXN_PATH, header=True, schema="transaction_id STRING, user_id STRING, amount DOUBLE, country STRING, category STRING")
user_df = spark.read.csv(USER_PATH, header=True, schema="user_id STRING, user_name STRING, join_date STRING, account_type STRING")

# Apply filter before join
filtered_txn_df = txn_df.filter(F.col("country") == "IN")

# Use broadcast join for user_df
joined_df = filtered_txn_df.join(F.broadcast(user_df), on="user_id", how="inner")

# Optimize aggregation with approx_count_distinct
final_df = joined_df.groupBy("account_type").agg(F.approx_count_distinct("transaction_id"))

final_df.coalesce(1).write.mode("overwrite").csv(OUTPUT_PATH, header=True)