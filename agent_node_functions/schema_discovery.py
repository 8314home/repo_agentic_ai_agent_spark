# File: agent_node_functions/discoverer.py
import os
import findspark
from pyspark.sql import SparkSession

def discover_schemas(state: dict) -> dict:
    """
    Programmatically logs the precise columns present in local CSV datasets.
    Provides bulletproof context directly to the optimizer.
    """
    ROOT_DIR = os.path.abspath(os.getcwd())
    data_folder = os.path.join(ROOT_DIR, "data")
    
    # Fallback default if data folder doesn't exist
    if not os.path.exists(data_folder):
        return {"discovered_schemas_context": "No local datasets discovered."}
        
    spark = SparkSession.builder \
        .appName("Schema_Discovery") \
        .master("local[1]") \
        .getOrCreate()
        
    schema_reporting = "GROUND TRUTH LOCAL FILE COLUMNS:\n"
    
    try:
        for file in os.listdir(data_folder):
            if file.endswith(".csv"):
                file_path = os.path.join(data_folder, file)
                # Read just the header row to capture accurate column names quickly
                temp_df = spark.read.option("header", "true").csv(file_path).limit(1)
                columns_list = temp_df.columns
                schema_reporting += f"- File '{file}' contains columns: {columns_list}\n"
    except Exception as e:
        schema_reporting += f"Discovery warning: {str(e)}"
    finally:
        spark.stop()
        
    print(f"\n🔍 DISCOVERERED schema :\n{schema_reporting}")
    return {"discovered_schemas_context": schema_reporting}

if __name__ == '__main__':
    print(f'Schema discover')