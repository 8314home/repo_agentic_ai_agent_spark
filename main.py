# File: main.py
import os
from typing import TypedDict, List
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# Load environment variables from .env file
load_dotenv()

# Import your decentralized node functions
from agent_node_functions.analyzer import analyze_code
from agent_node_functions.schema_discovery import discover_schemas
from agent_node_functions.optimizer import generate_variants
from agent_node_functions.validator import validate_and_explain
from agent_node_functions.evaluator import evaluate_and_clean


INPUT_DIR = "input_script"
OUTPUT_DIR = "output_script"

llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
    temperature=0
)

class VariantSchema(TypedDict):
    strategy_name: str
    code: str
    explain_plan: str
    execution_error: str
    execution_time_sec: float

class AgentState(TypedDict):
    current_script_name: str 
    discovered_schemas_context: str
    original_code: str
    bottlenecks: str
    variants: List[VariantSchema]
    best_code: str
    readme_content: str

def compile_readme(state: AgentState):
    testing_history = "| Optimization Strategy | Execution Time (s) | Status | Diagnostic Notes |\n"
    testing_history += "| --- | --- | --- | --- |\n"
    
    plan_details = ""
    for idx, v in enumerate(state["variants"]):
        if v.get("execution_error"):
            status = "❌ Failed"
            notes = v["execution_error"].replace("\n", " ").replace("|", "-")
        else:
            status = "✅ Success"
            notes = "Executed smoothly."
            
        testing_history += f"| {v['strategy_name']} | {v.get('execution_time_sec', 0.0)}s | {status} | {notes} |\n"
        
        plan_details += f"### Strategy {idx+1}: {v['strategy_name']}\n"
        if v.get("execution_error"):
            plan_details += f"**Execution Error Log:**\n```text\n{v['execution_error']}\n```\n\n"
        else:
            plan_details += f"**Spark Catalyst Plan Details:**\n```text\n{v.get('explain_plan', 'No plan captured')[:1500]}\n```\n\n"

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "Generate a professional, production-ready system architecture file named README.md.\n"
            "CRITICAL: Do NOT include the final winning raw python code block string inside this file.\n\n"
            "Incorporate these data metrics:\n"
            "- Initial Bottlenecks Identified: {bottlenecks}\n"
            "- Benchmark Comparison Table:\n{history}\n"
            "- Individual Query Plan Execution Details:\n{plans}\n\n"
            "Layout blocks:\n"
            "1. Executive Optimization Profile\n"
            "2. Experimental Benchmark Scorecard\n"
            "3. Comprehensive Breakdown of Strategies and Errors/Plans\n"
            "4. Technical Rationale supporting the selected high-performance choice."
        )),
        ("user", "Compile the markdown profile documentation now.")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "bottlenecks": state["bottlenecks"], 
        "history": testing_history,
        "plans": plan_details
    })
    return {"readme_content": response.content}

# Construct graph state machine
workflow = StateGraph(AgentState)
workflow.add_node("discover_schemas", discover_schemas)
workflow.add_node("analyze_code", analyze_code)
workflow.add_node("generate_variants", generate_variants)
workflow.add_node("validate_and_explain", validate_and_explain)
workflow.add_node("evaluate_and_clean", evaluate_and_clean)
workflow.add_node("compile_readme", compile_readme)

workflow.set_entry_point("discover_schemas")
workflow.add_edge("discover_schemas", "analyze_code") 
workflow.add_edge("analyze_code", "generate_variants")
workflow.add_edge("generate_variants", "validate_and_explain")
workflow.add_edge("validate_and_explain", "evaluate_and_clean")
workflow.add_edge("evaluate_and_clean", "compile_readme")
workflow.add_edge("compile_readme", END)
app = workflow.compile()

def run_sdk_agent():
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".py")]
    if not files:
        print(f"❌ Error: Place your target unoptimized files into the '{INPUT_DIR}/' folder first.")
        return
        
    print(f"📚 Found {len(files)} script(s) to optimize: {files}\n")

    for script_file in files:
        target_script = os.path.join(INPUT_DIR, script_file)
        script_base_name = os.path.splitext(script_file)[0]
        
        print(f"📖 Reading unoptimized script: {target_script}")
        with open(target_script, "r") as f:
            source_code = f.read()

        print(f"🚀 Running modular optimization engine for '{script_file}'...")
        result = app.invoke({
            "current_script_name": script_base_name,
            "original_code": source_code
        })
        
        # Write optimized script to OUTPUT_SCRIPT path

        unique_output_dir = os.path.join(OUTPUT_DIR, script_base_name)
        os.makedirs(unique_output_dir, exist_ok=True)
        
        out_code_path = os.path.join(unique_output_dir, f"optimized_{script_file}")
        out_readme_path = os.path.join(unique_output_dir, "README.md")
        
        with open(out_code_path, "w") as f:
            f.write(result["best_code"])
        with open(out_readme_path, "w") as f:
            f.write(result["readme_content"])
            
        print(f"✅ Clean optimized code saved: {out_code_path}")
        print(f"✅ Performance documentation saved: {out_readme_path}")
        print("-" * 50)

    print("\n🎉 All scripts processed successfully!")

if __name__ == "__main__":
    run_sdk_agent()
