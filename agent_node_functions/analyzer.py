# File: agent_node_functions/analyzer.py
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
    temperature=0
)

def analyze_code(state: dict) -> dict:
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert PySpark performance tuning engineer. Your sole task is to scan the code and identify architectural performance bugs.\n\n"
            "CRITICAL OUTPUT FORMAT CONSTRAINT:\n"
            "- You must describe bottlenecks using ONLY plain text bullet points.\n"
            "- Do NOT include any Python code snippets, block code examples, or mock code rewrites in your response.\n"
            "- Provide your diagnostic observations organized into exactly two distinct operational strategic levels:\n\n"
            "Level 1: Baseline Structural Issues\n"
            "Identify plain structural flaws: missing explicit schemas (inferSchema usage), misplaced filter conditions (predicates running after joins), missing broadcast hints on small data frames, or uncoalesced file writes.\n\n"
            "Level 2: Advanced Processing & Session Issues\n"
            "Identify engine-level configuration flaws: lack of explicit shuffle partition sizing, sub-optimal file block distributions, row-by-row patterns (like non-vectorized Python UDF loops), or exact distinct aggregations that could use approximation shortcuts."
        )),
        ("user", "Analyze this PySpark code and identify bottlenecks without providing code examples:\n\n{code}")
    ])
    chain = prompt | llm

    chain_content = (chain.invoke({"code": state["original_code"]})).content
    print(f'\n🔍 ANALYZER: Generated text-only bottleneck report:\n{chain_content}\n')
    return {"bottlenecks": chain_content}

if __name__ == '__main__':
    print(f'analyze_code')
