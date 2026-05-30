# File: agent_node_functions/optimizer.py
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
    temperature=0
)

def generate_variants(state: dict) -> dict:
    """
    Generalized Optimizer Node.
    Dynamically analyzes the schema and columns present inside the input code string
    and generates exactly 2 platform-agnostic optimization variants.
    """
    
    # 1. Platform-Agnostic Core Rules Engine Template
    common_rules_template = (
        "CRITICAL ARCHITECTURAL CONSTRAINTS:\n"
        "1. STRICT SCHEMA ALIGNMENT: Review the verified data metrics from disk provided below. "
        "You MUST map the explicit StructType schema fields to match the exact column names discovered for each data file on disk. "
        "Do NOT mix columns between separate tables, swap positions, or inject fields that do not exist in the source data file.\n"

        "2. DATA LINEAGE FILTER PUSHDOWN: Place your .filter() or .where() operations directly onto the source DataFrame "
        "that naturally owns that column according to the verified disk schemas. Push filters down to run BEFORE any heavy join "
        "or shuffle operations. Do not filter dataframes that lack the target column.\n"

        "3. NO NEW SPARKSESSION: Do NOT append any 'SparkSession.builder' blocks or initialize new sessions. "
        "Assume an active session variable named exactly 'spark' is pre-initialized in the runtime environment scope.\n"

        "4. MANDATORY FUNCTION IMPORTS: You MUST explicitly include 'import pyspark.sql.functions as F' "
        "at the very top of your code output if your transformations utilize any function calls prefixed with 'F.' "
        "(such as F.col(), F.broadcast(), or F.approx_count_distinct()). Failure to include this import will break execution.\n"

        "5. TARGET TERMINAL VALUE: Assign the final computed processing target DataFrame to a variable named exactly 'final_df' right before the write block.\n"

        "6. PATH INTEGRITY: Preserve variable references like ROOT_DIR, TXN_PATH, USER_PATH, and OUTPUT_PATH exactly as written in the source script. "
        "Do NOT hardcode raw string paths inside your file readers or .write.csv() actions. Use the defined variables.\n"

        "7. NAKED PYTHON SYNTAX: Return ONLY raw, valid, executable Python code. Do not wrap outputs inside markdown characters (like ```python) or add annotations.\n\n"
        "VERIFIED FILE COLUMNS FROM DISK CONTEXT:\n"

        "8. NO NUMPARTITIONS IN WRITE: Never include a 'numPartitions' parameter inside the .write.csv(...) or .write.format('csv').save(...) method blocks. "
        "The PySpark CSV writer does not support a partitioning count argument. To control partition numbers before file execution, you MUST always use "
        "DataFrame transformations like '.coalesce(1)' directly on the target variable right before writing. "
        "Example of WRONG syntax: final_df.write.csv(OUTPUT_PATH, numPartitions=4) "
        "Example of CORRECT syntax: final_df.coalesce(1).write.mode('overwrite').csv(OUTPUT_PATH, header=True)"

        "9. ACCURATE NUMERIC TYPES: When defining structural schemas via StructType, inspect the original code values carefully. "
        "If a numerical column contains decimal points or floating-point properties (like 'amount', 'price','orders','views' or fractional metrics), "
        "you MUST define its StructField directly as DoubleType() or FloatType(), never as IntegerType(). "
        "This ensures that PySpark reads the decimal values cleanly from disk into memory without dropping them to null."

        "{schema_context}" # <- Placeholder dynamically filled by the Discoverer node data
    )
    
    # 2. Inject state["discovered_schemas_context"] into the rules template
    current_schema_context = state.get("discovered_schemas_context", "No schema context available.")
    formatted_common_rules = common_rules_template.format(schema_context=current_schema_context)
    
    # VARIANT 1: Baseline Structural Optimization
    prompt1 = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert PySpark performance tuning engineer.\n\n"
            f"{formatted_common_rules}\n\n"
            "OPTIMIZATION STRATEGY: Baseline Structural Optimization\n"
            "Apply these optimizations to the original code structure:\n"
            "- Swap out inferSchema with custom StructType schemas derived directly from the code columns.\n"
            "- Push down filter transformations to run as early as possible on their correct, matching parent DataFrames.MUST verify if column against in dataframe schema before applying filter.\n"
            "- Apply explicit 'F.broadcast()' hints on the smaller lookup DataFrame if an inner/left join operation is present.\n"
            "- Inject '.coalesce(1)' right before file write operations to reduce output partitions cleanly without full shuffles."
        )),
        ("user", "Bottlenecks Analysis:\n{bottlenecks}\n\nOriginal Code:\n{code}\n\nGenerate Variant 1 code now.")
    ])
    
    # VARIANT 2: Advanced Engine Tuning
    prompt2 = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert PySpark performance tuning engineer.\n\n"
            f"{formatted_common_rules}\n\n"
            "OPTIMIZATION STRATEGY: Advanced Engine Tuning\n"
            "Apply these optimizations to the original code structure:\n"
            "- Incorporate all logical improvements from Variant 1 (StructType, predicate pushdowns, broadcast joins, coalesce).\n"
            "- Add explicit runtime configuration parameter calls at the very top of the script using the active session object 'spark.conf.set()'. "
            "Set 'spark.sql.shuffle.partitions' and 'spark.sql.files.maxPartitionBytes' to reasonable values matching a local testing workspace environment.\n"
            "- Identify heavy row-by-row expressions or Python UDFs and replace them with vectorized native PySpark expressions (like F.when().otherwise()) or Window frameworks.\n"
            "- Optimize aggregations: if countDistinct() is used, swap it with approx_count_distinct() to minimize shuffle footprints."
        )),
        ("user", "Bottlenecks Analysis:\n{bottlenecks}\n\nOriginal Code:\n{code}\n\nGenerate Variant 2 code now.")
    ])
    
    # Generate Variant 1
    chain1 = prompt1 | llm
    response1 = chain1.invoke({
        "schema_context": state["discovered_schemas_context"],
        "bottlenecks": state["bottlenecks"],
        "code": state["original_code"]
        })
    variant1_code = response1.content.strip()
    variant1_code = variant1_code.replace("```python", "").replace("```", "").strip()
    
    # Generate Variant 2
    chain2 = prompt2 | llm
    response2 = chain2.invoke({
        "schema_context": state["discovered_schemas_context"],
        "bottlenecks": state["bottlenecks"], 
        "code": state["original_code"]
        })
    variant2_code = response2.content.strip()
    variant2_code = variant2_code.replace("```python", "").replace("```", "").strip()
    
    variant_list = [
        {
            "strategy_name": "Baseline Structural Optimization",
            "code": variant1_code,
            "explain_plan": "",
            "execution_error": "",
            "execution_time_sec": 0.0
        },
        {
            "strategy_name": "Advanced Engine Tuning",
            "code": variant2_code,
            "explain_plan": "",
            "execution_error": "",
            "execution_time_sec": 0.0
        }
    ]
    
    print(f"\n✅ OPTIMIZER: Successfully generated {len(variant_list)} optimized code variants.")
    print(f"\n\n variant1_code : {"-"*60} \n {variant1_code}")
    print(f"\n\n variant2_code : {"-"*60} \n {variant2_code}")

    return {"variants": variant_list}
