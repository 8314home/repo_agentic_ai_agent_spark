# AGI Agent Spark - Usage Guide

## Setup Complete! ✅

Your PySpark optimization agent is now properly configured and ready to use.

## How to Run the Application

### Option 1: Direct Python Path (Recommended for one-off runs)
```bash
/Users/shubmukh/Desktop/cdk_projects/agi_agent_spark/venv_ai_agent_spark/bin/python /Users/shubmukh/Desktop/cdk_projects/agi_agent_spark/main.py
```

### Option 2: Activate Virtual Environment (Recommended for interactive work)
```bash
# Navigate to your project directory
cd /Users/shubmukh/Desktop/cdk_projects/agi_agent_spark

# Activate the virtual environment
source venv_ai_agent_spark/bin/activate

# Now you can run python directly
python main.py

# When done, deactivate the environment
deactivate
```

### Option 3: Create an Alias (For convenience)
Add this to your `~/.zshrc` file:
```bash
alias spark-optimize='cd /Users/shubmukh/Desktop/cdk_projects/agi_agent_spark && source venv_ai_agent_spark/bin/activate && python main.py'
```

Then reload your shell:
```bash
source ~/.zshrc
```

Now you can run from anywhere:
```bash
spark-optimize
```

## How to Use

1. **Place your unoptimized PySpark script** in the `input_script/` folder
   - Only `.py` files are processed
   - The script will automatically pick up the first Python file it finds

2. **Run the application** using any of the methods above

3. **Check the results** in the `output_script/` folder:
   - `optimized_code.py` - Your optimized PySpark code
   - `README.md` - Performance analysis and optimization documentation

## Environment Variables

The application uses a `.env` file for configuration:
- `OPENAI_API_KEY` - Your OpenAI API key (already configured)
- `OPENAI_BASE_URL` - Custom OpenAI endpoint (already configured)

**⚠️ IMPORTANT**: Never commit the `.env` file to git! It's already in `.gitignore`.

## Troubleshooting

### "python: command not found"
- You're not using the virtual environment's Python
- Use the full path or activate the virtual environment first

### "Missing credentials" error
- Check that `.env` file exists in the project root
- Verify `OPENAI_API_KEY` is set correctly in `.env`

### "No module named 'dotenv'" or similar
- Make sure you're using the virtual environment's Python
- All dependencies are installed in `venv_ai_agent_spark/`

## Project Structure

```
agi_agent_spark/
├── .env                          # Environment variables (DO NOT COMMIT)
├── main.py                       # Main application entry point
├── input_script/                 # Place your PySpark scripts here
├── output_script/                # Optimized code appears here
├── agent_node_functions/         # Agent modules
│   ├── analyzer.py              # Code analysis
│   ├── optimizer.py             # Code optimization
│   ├── evaluator.py             # Code evaluation
│   └── validator.py             # Spark validation
└── venv_ai_agent_spark/         # Virtual environment
```

## Next Steps

1. Place a PySpark script in `input_script/`
2. Run the application
3. Review the optimized output in `output_script/`

Happy optimizing! 🚀
