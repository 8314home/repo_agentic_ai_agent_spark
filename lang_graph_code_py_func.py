import os
import sys
import io
import findspark
from typing import TypedDict, List

# Initialize paths for PySpark
findspark.init()

from pyspark.sql import SparkSession
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# 1. Setup API Credentials
os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY"

# 2. Define Graph State
class AgentState(TypedDict):
    original_code: str
    bottlenecks: str
    variants: str
    best_code: str
    spark_explain_plan: str
    readme_content: str

# Initialize LLM
#llm = ChatOpenAI(model="gpt-4o", temperature=0)
llm = ChatOpenAI(model_name = "gpt-4o-mini", 
                 api_key = "voc-2033465586156170068dbe3820ba1c1.93790491",
                 base_url = "https://openai.vocareum.com/v1", 
                 temperature=0)

# 3. Define Graph Nodes

def analyze_code(state: AgentState):
    """Node 1: Scans the PySpark code for performance issues."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert PySpark tuning engineer. Identify performance bottlenecks (e.g., shuffles, broad joins missing, row-by-row processing, bad caching). List them clearly."),
        ("user", "Analyze this PySpark code:\n\n{code}")
    ])
    chain = prompt | llm
    response = chain.invoke({"code": state["original_code"]})
    return {"bottlenecks": response.content}

def generate_variants(state: AgentState):
    """Node 2: Builds optimized versions based on findings."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert PySpark developer. Based on these bottlenecks:\n{bottlenecks}\n\n"
            "Generate the single most optimized version of the code.\n"
            "CRITICAL RULES:\n"
            "1. You must assign the final resulting DataFrame to a variable named exactly 'final_df'.\n"
            "2. Do not include action commands like '.show()' or '.collect()' in the final code.\n"
            "3. Return ONLY valid executable Python code block enclosed in ```python markdown blocks."
        )),
        ("user", "Original Code:\n{code}")
    ])
    chain = prompt | llm
    response = chain.invoke({"bottlenecks": state["bottlenecks"], "code": state["original_code"]})
    return {"variants": response.content}

def evaluate_and_select(state: AgentState):
    """Node 3: Cleans and extracts the code out of markdown blocks for execution."""
    raw_variants = state["variants"]
    # Extract code between ```python and ```
    if "```python" in raw_variants:
        clean_code = raw_variants.split("```python")[1].split("```")[0].strip()
    elif "```" in raw_variants:
        clean_code = raw_variants.split("```")[1].split("```")[0].strip()
    else:
        clean_code = raw_variants.strip()
        
    return {"best_code": clean_code}

def validate_and_explain(state: AgentState):
    """Node 4: Programmatically compiles, executes code, and captures Spark explain plans."""
    # Build isolated local session
    spark = SparkSession.builder \
        .appName("LangGraphValidator") \
        .master("local[*]") \
        .config("spark.driver.host", "localhost") \
        .getOrCreate()
        
    code_to_test = state["best_code"]
    local_vars = {"spark": spark}
    
    try:
        # Run code string in safe local memory scope
        exec(code_to_test, {}, local_vars)
        
        if "final_df" not in local_vars:
            return {"spark_explain_plan": "Execution Warning: Code ran, but did not define 'final_df'."}
            
        final_df = local_vars["final_df"]
        
        # Intercept print stream to catch physical graph logs
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        final_df.explain(extended=True)
        
        explain_output = sys.stdout.getvalue()
        sys.stdout = old_stdout  # Restore standard output pipeline
        return {"spark_explain_plan": explain_output}
        
    except Exception as e:
        return {"spark_explain_plan": f"Execution Engine Error: {str(e)}"}
    finally:
        spark.stop()

def compile_readme(state: AgentState):
    """Node 5: Merges plan metadata and architectural reasonings into a clear markdown doc."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "Create a professional, standalone documentation file named README.md.\n"
            "Use these components to formulate it:\n"
            "- Identified Bottlenecks: {bottlenecks}\n"
            "- Spark Catalyst Explain Plan Output: {explain_plan}\n\n"
            "Structure requirements:\n"
            "1. Executive Summary\n"
            "2. Optimizations applied (Explain Spark details like BroadcastHashJoin, Predicate Pushdown, etc.)\n"
            "3. Rationale verifying why this is the highest performance structure."
        )),
        ("user", "Generate the README.md content.")
    ])
    chain = prompt | llm
    response = chain.invoke({
        "bottlenecks": state["bottlenecks"],
        "explain_plan": state["spark_explain_plan"]
    })
    return {"readme_content": response.content}

# 4. Construct LangGraph Workflow
workflow = StateGraph(AgentState)

workflow.add_node("analyze_code", analyze_code)
workflow.add_node("generate_variants", generate_variants)
workflow.add_node("evaluate_and_select", evaluate_and_select)
workflow.add_node("validate_and_explain", validate_and_explain)
workflow.add_node("compile_readme", compile_readme)

workflow.set_entry_point("analyze_code")
workflow.add_edge("analyze_code", "generate_variants")
workflow.add_edge("generate_variants", "evaluate_and_select")
workflow.add_edge("evaluate_and_select", "validate_and_explain")
workflow.add_edge("validate_and_explain", "compile_readme")
workflow.add_edge("compile_readme", END)

app = workflow.compile()

# 5. Run the Workflow with Sample Inefficient PySpark Code
if __name__ == "__main__":
    unoptimized_sample = """
import pyspark.sql.functions as F

# Creating mockup internal lists so the code physically compiles and runs locally
df1 = spark.createDataFrame([(i, f"user_{i}", "IN" if i%2==0 else "US") for i in range(1000)], ["user_id", "name", "country"])
df2 = spark.createDataFrame([(i, f"meta_{i}") for i in range(10)], ["user_id", "metadata"])

# Bottleneck: Inefficient non-broadcast join on tiny dataset, filtering AFTER joining
joined = df1.join(df2, on="user_id", how="inner")
filtered = joined.filter(F.col("country") == "IN")

# Bottleneck: High cost distinct aggregate function
final_df = filtered.groupBy("country").agg(F.countDistinct("user_id"))
"""

    print("🚀 Initiating optimization graph routine...")
    result = app.invoke({"original_code": unoptimized_sample})
    
    print("\n================== 🛠️ OPTIMIZED CODE ==================")
    print(result["best_code"])
    
    print("\n================== 📝 GENERATED README.MD ==================")
    print(result["readme_content"])
