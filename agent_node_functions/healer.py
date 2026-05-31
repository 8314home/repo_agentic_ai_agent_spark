import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
    temperature=0
)

prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an expert PySpark debugging engineer.\n"
        "Your previous generated code failed validation with a runtime error.\n"
        "Analyze the provided original input code, your broken code generation, and the exact Spark runtime execution error track to fix the bug.\n\n"
        "CRITICAL CONSTRAINTS:\n"
        "1. Fix the syntax error or schema/column layout mismatch specified in the error track.\n"
        "2. Maintain your core optimization strategies (e.g., broadcast join, coalesce, configurations) without reverting back to unoptimized syntax.\n"
        "3. Preserve external variable definitions like ROOT_DIR, TXN_PATH, USER_PATH, and OUTPUT_PATH. Do NOT hardcode paths.\n"
        "4. Assign the terminal target DataFrame to a variable named exactly 'final_df'.\n"
        "5. Return ONLY raw, valid, executable naked Python code syntax. Do not wrap code blocks in markdown fences (```python)."
    )),
    ("user", (
        "Verified File Schemas on Disk:\n{schema_context}\n\n"
        "Original Unoptimized Target Script:\n{orig_code}\n\n"
        "Your Broken Code Generation:\n{broken_code}\n\n"
        "Spark Runtime Execution Error Track:\n{error_trace}\n\n"
        "Generate corrected executable Python code now:"
    ))
])


def self_heal_variants(state: dict) -> dict:
    """
    Self-Correction Node.
    Iterates through variants, picks up failed entries, and uses the 
    validation error log stack trace to generate fixed PySpark code blocks.
    """
    updated_variants = []
    
    for v in state["variants"]:
        # SUCCESSFUL VARIANT, keep it untouched
        if not v.get("execution_error"):
            updated_variants.append(v)
            continue
        
        ## FOR FAILED VARIATNT

        print(f"🩹 HEALER: Attempting to fix code for strategy '{v['strategy_name']}'...")
        
        chain = prompt | llm
        response = chain.invoke({
            "schema_context": state["discovered_schemas_context"],
            "orig_code": state["original_code"],
            "broken_code": v["code"],
            "error_trace": v["execution_error"]
        })
        
        corrected_code = response.content.strip().replace("```python", "").replace("```", "").strip()
        
        # Increment retry count and clear out previous error tracking messages
        updated_variants.append({
            "strategy_name": v["strategy_name"],
            "code": corrected_code,
            "explain_plan": "",
            "execution_error": "",
            "execution_time_sec": 0.0,
            "retry_count": v.get("retry_count", 0) + 1
        })
        
    return {"variants": updated_variants}
