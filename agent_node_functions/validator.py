# File: agent_node_functions/validator.py
import os
import sys
import io
import time
import shutil
import traceback
import findspark
from pyspark.sql import SparkSession

# os.environ["JAVA_HOME"] = "/Library/Java/JavaVirtualMachines/amazon-corretto-17.jdk/Contents/Home"
findspark.init()

def validate_and_explain(state: dict) -> dict:
    updated_variants = []
    ROOT_DIR = os.path.abspath(os.getcwd())
    script_name = state["current_script_name"]

    for item in state["variants"]:
        strategy = item["strategy_name"]
        code_string = item["code"]
        explain_plan = ""
        error_msg = ""
        execution_time_sec = 0.0
        
        safe_strategy_name = strategy.lower().replace(" ", "_").replace("&", "and")
        variant_output_path = os.path.join(ROOT_DIR, "output_data", script_name, safe_strategy_name)
        
        if os.path.exists(variant_output_path):
            shutil.rmtree(variant_output_path)
        os.makedirs(variant_output_path, exist_ok=True)
        
        # 1. EXPLICIT INTERCEPTION WORKAROUND:
        # Comment out the LLM's internal definition of OUTPUT_PATH so it does not overwrite our sandbox path.
        intercepted_code = code_string.replace("OUTPUT_PATH =", "# OUTPUT_PATH =")
        
        # 2. Prepend the sandbox header path definition safely at the top
        header_overrides = (
            f"import os\n"
            f"ROOT_DIR = r'{ROOT_DIR}'\n"
            f"OUTPUT_PATH = r'{variant_output_path}'\n"
        )
        
        modified_code = header_overrides + intercepted_code

        print(f'\n⚙️ VALIDATOR: Testing Variant "{strategy}" for script "{script_name}"...')

        spark = SparkSession.builder \
            .appName(f"Benchmarking_{script_name}_{safe_strategy_name}") \
            .master("local[*]") \
            .config("spark.driver.host", "localhost") \
            .getOrCreate()
            
        local_vars = {"spark": spark}
        
        try:
            start_time = time.perf_counter()
            exec(modified_code, {}, local_vars)
            
            if "final_df" in local_vars:
                local_vars["final_df"].storageLevel
                local_vars["final_df"].count() 
                
            end_time = time.perf_counter()
            execution_time_sec = round(end_time - start_time, 4)
            
            if "final_df" in local_vars:
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                local_vars["final_df"].explain(extended=True)
                explain_plan = sys.stdout.getvalue()
                sys.stdout = old_stdout
            else:
                error_msg = "Execution warning: The variable 'final_df' was not found in code context."
                
        except Exception as e:
            print(f"\n❌ VALIDATOR FAILURE: Variant '{strategy}' for script '{script_name}' crashed.")
            print("="*60)
            traceback.print_exc()
            print("="*60)
            error_msg = str(e)
        finally:
            spark.stop()
            
        updated_variants.append({
            "strategy_name": strategy,
            "code": code_string,
            "explain_plan": explain_plan,
            "execution_error": error_msg,
            "execution_time_sec": execution_time_sec
        })
        
    return {"variants": updated_variants}
