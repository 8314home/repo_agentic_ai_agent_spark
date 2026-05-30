# File: input_script/script_1.py
import os 
import pyspark.sql.functions as F
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("Faulty_Production_Job") \
    .master("local[*]") \
    .getOrCreate()

ROOT_DIR = os.path.abspath(os.getcwd())
TXN_PATH = os.path.join(ROOT_DIR, "data", "transactions.csv")
USER_PATH = os.path.join(ROOT_DIR, "data", "small_users.csv")
OUTPUT_PATH = os.path.join(ROOT_DIR, "output_data")

# Load data
txn_df = spark.read.csv(TXN_PATH, header=True, inferSchema=True)
user_df = spark.read.csv(USER_PATH, header=True, inferSchema=True)

# Processing logic (Faulty/Unoptimized order)
joined_df = txn_df.join(user_df, on="user_id", how="inner")
filtered_df = joined_df.filter(F.col("country") == "IN")
final_df = filtered_df.groupBy("account_type").agg(F.countDistinct("transaction_id"))

final_df.write.mode("overwrite").csv(OUTPUT_PATH, header=True)
