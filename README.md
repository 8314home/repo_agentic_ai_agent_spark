# 🚀 Automated PySpark Code Optimization Agent (LangGraph & LangChain SDK)

An enterprise-grade, platform-agnostic AI agent built with **LangGraph** and **LangChain** that automatically parses, profiles, benchmarks, optimizes, and documents PySpark code pipelines.

By executing code variants inside an isolated local Apache Spark (JVM) session, the agent captures real-time execution plans (Spark Catalyst Extended Plans) and runtime metrics to deliver verified high-performance code alongside an engineering scorecard.

---

## 📌 1. Agent Objective & Business Context

In distributed computing, sub-optimal PySpark code (e.g., unnecessary network shuffles, missing broadcast hints, improper data types, or row-by-row Python UDF processing) leads to massive infrastructure cost overheads and delayed data pipelines.

This agent **automates the code review and tuning cycle** by:

- **Discovering Ground Truth Data Shapes**: Reading actual file structures from storage to eliminate LLM guesswork.
- **Diagnosing Performance Bottlenecks**: Identifying anti-patterns using plain text architectural constraints.
- **Generating Code Hypotheses Parallelly**: Compiling Baseline Structural versus Advanced Engine-Tuning alternatives.
- **Programmatically Verifying Code Performance**: Executing alternatives inside an isolated runtime container to track execution durations and plan efficiency.
- **Self-Healing Code Errors**: Automatically detecting and correcting syntax errors or runtime failures in generated code variants (up to 2 retry attempts per variant).
- **Selecting Verified Winners**: Acting as a benchmark judge to select and output the highest performing code along with a professional architectural profile report.

---

## 📐 2. Agent Architecture & Execution Flow

The agent is designed as a **stateful, decoupled directed graph** managed by LangGraph:

```
[Start] ➔ [Discover Schemas] ➔ [Analyze Code] ➔ [Generate Variants] ➔ [Validate & Benchmark] 
   ➔ [Conditional Router] 
      ├─ All Pass → [Evaluate & Select] ➔ [Compile README] ➔ [End]
      ├─ Errors Detected → [Self-Heal Variants] ➔ [Re-validate] (max 2 retries)
      └─ Max Retries Exhausted → [Compile README with Diagnostics] ➔ [End]
```

### 🔁 Step-by-Step Execution Sequence

1. **discover_schemas** (State Entry): Automatically scans the local `data/` folder and reads the headers of all CSV files via Spark to extract exact column listings.

2. **analyze_code**: Evaluates the input script text against plain-text engineering benchmarks to isolate bottleneck metrics (without generating code snippets).

3. **generate_variants**: Uses separate sequential LLM chains to translate findings into exactly two competitive optimization configurations (Baseline vs Advanced Engine). It dynamically binds the schemas discovered by step 1 to prevent column lineage drops.

4. **validate_and_explain**: Overrides output target locations, spins up an isolated Spark thread, runs the code strings using Python `exec()`, forces execution via `.count()`, captures exact millisecond execution times, and extracts the physical `explain(extended=True)` text.

5. **Conditional Router (should_continue_or_heal)**: Evaluates validation results and intelligently routes the workflow:
   - If all variants execute successfully → proceeds to evaluator
   - If errors detected and retries remaining → routes to self-healing node
   - If maximum retry attempts exhausted → gracefully exits with diagnostic documentation

6. **self_heal_variants**: An AI-powered debugging node that analyzes runtime error stack traces, identifies syntax errors or schema mismatches, and generates corrected code while preserving optimization strategies. Limited to 2 retry attempts per variant to prevent infinite loops.

7. **evaluate_and_clean**: An LLM Judge weighs the execution metrics and plan overheads of both approaches to select the absolute high-performance winner. Now includes enhanced metadata output with winning variant name and measured execution runtime embedded as structured comments in the final code.

8. **compile_readme** (State Exit): Formulates an enterprise-ready markdown report compiling the diagnostic analysis and optimization metrics.

---

## 📁 3. Project Directory & Core Modular Files

### 📂 Directory Layout

```
agi_agent_spark/
├── agent_node_functions/   # Decentralized Graph Node Handlers
│   ├── __init__.py         # Package initialization marker
│   ├── schema_discovery.py # Programmatic schema inspector 
│   ├── analyzer.py         # Static code diagnostic scanner
│   ├── optimizer.py        # Algorithmic PySpark variant generator
│   ├── validator.py        # Code compilation & metric tracking engine
│   ├── healer.py           # Self-healing code error correction node
│   └── evaluator.py        # LLM performance judge node with enhanced metadata output
├── data/                   # Drop source CSV datasets here
├── input_script/           # Put your unoptimized *.py target scripts here
├── output_script/          # Agent generates optimized code and documentation here
├── output_data/            # Sandboxed tracking directories for variant run parts
├── .env                    # Workspace secret environment configurations
├── requirements.txt        # Production dependency configuration log
├── Dockerfile              # Multilayered Linux OpenJDK runtime build recipe
└── main.py                 # LangGraph state orchestrator and batch pipeline entry point
```

### 🛠️ Component Blueprint Breakdown

- **main.py**: Declares the global `AgentState` schema, wires node-to-node routing sequences, loads local environment parameters, and loops batch directories to process multiple inputs back-to-back without manual interventions.

- **schema_discovery.py**: Intercepts structural metadata on your physical disk, formatting explicit, verifiable mapping strings to guide code generators.

- **analyzer.py**: Employs an LLM to scan for logical bugs (e.g., `inferSchema=True`, out-of-order transformations, expensive `countDistinct()`) and categorizes them textually.

- **optimizer.py**: Houses strict system instruction rules (e.g., mapping decimals as `DoubleType()`, forbidding `numPartitions` inside file writers) to generate safe PySpark code.

- **validator.py**: Dynamically intercepts the script's `OUTPUT_PATH` assignment variable to partition variant targets. It handles try-except-traceback layers to prevent silent execution crashes.

- **healer.py**: An intelligent self-healing node that automatically debugs and corrects failed code variants. It analyzes the original code, broken generated code, and runtime error traces to produce fixed versions while maintaining optimization strategies. Implements a maximum retry limit of 2 attempts per variant to ensure graceful failure handling.

- **evaluator.py**: Collates real runtime statistics down to the millisecond to choose the definitive optimized script. Now generates enhanced output with structured comment headers containing the winning variant strategy name and measured execution runtime in seconds for improved traceability.

---

## 🚀 4. Installation & Local Development Setup

### 1. Prerequisites

Ensure your Mac has **Java JDK 11 or 17** installed (e.g., Amazon Corretto 17). Check your version by running:

```bash
java -version
```

### 2. Configure Virtual Environment & Install Dependencies

Navigate to your project root folder inside the terminal, initialize an isolated virtual environment shell, and install the pinned dependencies:

```bash
# Move to workspace
cd /Users/shubmukh/Desktop/cdk_projects/agi_agent_spark

# Create and activate environment
python3 -m venv venv_ai_agent_spark
source venv_ai_agent_spark/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Setup Secrets

Configure a `.env` file in your root folder:

```env
OPENAI_API_KEY=your_actual_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 4. Execute the Application Local Pipeline

Place your target unoptimized python files inside `input_script/` and run the orchestration script:

```bash
python3 main.py
```

---

## 🐳 5. Production Deployment via Docker

Using Docker guarantees a containerized setup with pre-configured Linux paths and OpenJDK 17, eliminating environmental discrepancies.

### 1. Build the Docker Image

Execute the build sequence from the root workspace directory:

```bash
docker build -t pyspark-optimizer-agent .
```

### 2. Execute the Isolated Agent Container

Run the container by passing your credential file and mounting your local workspace directories. This allows the containerized agent to safely save newly compiled assets right back onto your host Mac filesystem:

```bash
docker run --env-file .env \
  -v $(pwd)/input_script:/app/input_script \
  -v $(pwd)/output_script:/app/output_script \
  -v $(pwd)/output_data:/app/output_data \
  -v $(pwd)/data:/app/data \
  pyspark-optimizer-agent
```

---

## 📈 Final Output Verification

Once the container run logs complete successfully, inspect your workspace folders on your Mac. You will see that the agent generated high-performance code and scorecards for each script processed:

- **`output_script/<script_name>/optimized_<script_name>.py`**: The clean, tuned PySpark script.
- **`output_script/<script_name>/README.md`**: The performance scorecard profiling runtime execution durations and the exact Spark Catalyst plans tested.

---

## 🎯 Key Features

- ✅ **Automated Schema Discovery**: Reads actual CSV file structures to understand data shapes
- ✅ **Dual Variant Generation**: Creates 2 distinct optimization strategies (Baseline + Advanced)
- ✅ **Real Execution Benchmarking**: Runs code variants in isolated Spark sessions
- ✅ **Performance Metrics Tracking**: Captures execution times and Spark execution plans
- ✅ **AI-Powered Code Review**: Uses LLM to identify bottlenecks and generate optimizations
- ✅ **Self-Healing Error Correction**: Automatically detects and fixes syntax errors or runtime failures (max 2 retries)
- ✅ **Conditional Intelligent Routing**: Smart workflow orchestration based on validation results
- ✅ **Automatic Winner Selection**: LLM judge selects the best performing variant
- ✅ **Enhanced Metadata Output**: Winning code includes strategy name and execution runtime as structured comments
- ✅ **Professional Documentation**: Generates detailed performance reports with comprehensive error diagnostics

---

## 📦 Technology Stack

- **LangGraph**: Stateful workflow orchestration
- **LangChain**: LLM integration and prompt management
- **OpenAI GPT-4**: Code analysis and generation
- **PySpark 4.1.2**: Distributed data processing
- **Python 3.11+**: Core runtime
- **Docker**: Containerized deployment

---

## 📄 License

This project is intended for enterprise use. Please review licensing terms before deployment.

---

## 🤝 Contributing

Contributions are welcome! Please ensure your code follows PEP 8 standards and includes appropriate tests.

---

## 📧 Contact & Support

For issues, questions, or feature requests, please open an issue in the repository.
