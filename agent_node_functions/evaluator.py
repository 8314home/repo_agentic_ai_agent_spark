from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os 

# Use environment variables for OpenAI configuration
llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
    temperature=0
)

# prompt = ChatPromptTemplate.from_messages([
#     ("system", (
#         "You are a Principal Spark Tuning Engineer acting as an automated benchmarking judge.\n"
#         "Review the provided performance metrics (specifically the Measured Execution Runtime) and the physical Catalyst execution graphs for all variants.\n"
#         "Select the single best performing variant. Prioritize options that successfully compiled with the lowest execution runtimes, fewer network shuffles, and efficient query plan operations.\n"
#         "CRITICAL: Return ONLY the exact raw Python code of the winning variant. Do not wrap it in markdown block quotes (such as ```python)."
#     )),
#     ("user", "Here is the performance scorecard data for the variants:\n\n{summary}")
# ])

prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a Principal Spark Tuning Engineer acting as an automated benchmarking judge.\n"
            "Review the provided performance metrics (specifically the Measured Execution Runtime) and the physical Catalyst execution graphs for all variants.\n"
            "Select the single best performing variant based on the lowest execution runtimes, fewer network shuffles, and efficient query plan operations.\n\n"
            "CRITICAL RESPONSE FORMAT RULES:\n"
            "You MUST output a Python comment block header at the very top of your response containing the exact winning Variant Strategy Name and its Measured Execution Runtime, followed by the exact raw Python code of that variant.\n"
            "Do NOT wrap any part of your output in markdown code fence blocks (such as ```python).\n\n"
            "Your output block structure MUST look exactly like this:\n"
            "# =========================================================================\n"
            "# 🏆 SELECTED OPTIMIZATION VARIANT: [Insert Winning Strategy Name Here]\n"
            "# ⏱️ MEASURED EXECUTION RUNTIME: [Insert Runtime from scorecard Here] seconds\n"
            "# =========================================================================\n\n"
            "[Insert the raw executable Python code of the winning variant here]"
        )),
        ("user", "Here is the performance scorecard data for the variants:\n\n{summary}")
    ])

def evaluate_and_clean(state: dict) -> dict:
    # 1. Build a performance profile scorecard for the LLM Judge by iterating through the list
    variants_summary = ""
    for idx, v in enumerate(state["variants"]):
        variants_summary += f"=== Variant {idx+1}: {v['strategy_name']} ===\n"

        runtime = v.get("execution_time_sec", 0.0)
        variants_summary += f"- Measured Execution Runtime: {runtime} seconds\n"
        
        if v['execution_error']:
            variants_summary += f"- Execution Error: {v['execution_error']}\n"
        else:
            variants_summary += f"- Spark Catalyst Plan Snippet:\n{v['explain_plan'][:1000]}\n"
        variants_summary += f"- Source Code:\n{v['code']}\n\n"
    
    chain = prompt | llm
    winning_code = (chain.invoke({"summary": variants_summary})).content
    
    clean_code = winning_code.replace("```python", "").replace("```", "").strip()
    return {"best_code": clean_code}


