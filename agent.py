import os
import pypdf
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
import importlib.util
from groq import Groq

# --- 1. Configuration & Setup ---
load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found. Please set it in your .env file.")
client = Groq(api_key=api_key)

# --- 2. Utility Functions ---
def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extracts all text content from a given PDF file."""
    print(f"--- Reading PDF from: {pdf_path} ---")
    reader = pypdf.PdfReader(pdf_path)
    return "".join(page.extract_text() or "" for page in reader.pages)

def get_csv_schema(csv_path: Path) -> str:
    """Reads a CSV and returns a string with its schema and a few rows."""
    print(f"--- Reading CSV schema from: {csv_path} ---")
    df = pd.read_csv(csv_path)
    from io import StringIO
    buffer = StringIO()
    df.info(buf=buffer)
    schema_info = buffer.getvalue()
    head = df.head(3).to_string()
    return f"The CSV has the following columns and types:\n{schema_info}\n\nHere are the first 3 rows:\n{head}"

# --- 3. LLM Agent Roles ---
def call_generator_agent(prompt: str) -> str:
    """The 'Generator' agent: Writes Python code."""
    print("--- Prompting Generator Agent (LLaMA 3.1 70b) ---")
    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert Python developer. Your task is to write a complete, self-contained Python script. Respond with only the raw Python code, starting with `import`."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=3000
    )
    return response.choices[0].message.content

def call_evaluator_agent(broken_code: str, error_message: str) -> str:
    """The 'Evaluator' agent: Analyzes failed code and provides feedback."""
    print("--- Prompting Evaluator Agent (LLaMA 3.1 8b) ---")
    prompt = f"""
    You are a senior code reviewer. A Python script has failed its tests. Your task is to provide a concise, high-level analysis of the failure and suggest a fix. Do NOT write the code yourself.

    **FAILED CODE:**
    ```python
    {broken_code}
    ```

    **ERROR / DIAGNOSTICS:**
    {error_message}

    Provide a short analysis and a clear suggestion for the fix.
    """
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a helpful and analytical code reviewer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=1000
    )
    return response.choices[0].message.content

# --- 4. Main Execution Loop ---
if __name__ == "__main__":
    script_dir = Path(__file__).parent
    pdf_file_path = script_dir / "data" / "icici" / "icici sample.pdf"
    csv_file_path = script_dir / "data" / "icici" / "result.csv"

    extracted_text = extract_text_from_pdf(pdf_file_path)
    csv_schema = get_csv_schema(csv_file_path)

    MAX_ATTEMPTS = 4
    generated_code = ""
    evaluation_feedback = ""

    for attempt in range(MAX_ATTEMPTS):
        print(f"\n--- Attempt {attempt + 1} of {MAX_ATTEMPTS} ---")

        # Step 1: Generate Code
        if attempt == 0:
            prompt = f"""
            Write a Python script with a function `def parse(pdf_path: str) -> pd.DataFrame:`.
            It must use the 'balance change' logic to determine debits and credits.

            **THE GOLDEN RULE:**
            1.  Establish a `previous_balance`.
            2.  For each transaction, compare its `current_balance` to `previous_balance`.
            3.  If balance decreases, it's a **DEBIT**. Credit Amt must be `np.nan`.
            4.  If balance increases, it's a **CREDIT**. Debit Amt must be `np.nan`.

            The script needs to import `pypdf` and `numpy as np`.

            **Target Schema:**
            {csv_schema}
            """
        else:
            prompt = f"""
            The previous parser failed. A code reviewer has provided the following feedback. Rewrite the entire script from scratch, implementing the suggested fix.

            **Code Review Feedback:**
            {evaluation_feedback}

            **Previously Broken Code:**
            ```python
            {generated_code}
            ```
            Provide the corrected, complete Python script.
            """
        
        generated_code = call_generator_agent(prompt)
        generated_code = generated_code.replace("```python", "").replace("```", "").strip()
        print("\n--- AI Generated Code ---\n" + generated_code)

        # Step 2: Test Code
        parser_dir = script_dir / "custom_parsers"
        parser_dir.mkdir(exist_ok=True)
        parser_file_path = parser_dir / "icici_parser.py"
        with open(parser_file_path, "w", encoding="utf-8") as f:
            f.write(generated_code)
        print(f"\n--- Code saved to {parser_file_path} ---")

        try:
            spec = importlib.util.spec_from_file_location("icici_parser", parser_file_path)
            icici_parser = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(icici_parser)

            generated_df = icici_parser.parse(str(pdf_file_path))
            expected_df = pd.read_csv(csv_file_path)

            generated_df.columns = expected_df.columns
            generated_df = generated_df.astype(str).reset_index(drop=True)
            expected_df = expected_df.astype(str).reset_index(drop=True)

            if generated_df.equals(expected_df):
                print("\n✅✅✅ Test Passed! The generated parser works correctly. ✅✅✅")
                break
            else:
                diff_message = "Test Failed: DataFrames do not match.\n"
                diff_message += "=== Expected Head ===\n" + expected_df.head(3).to_string() + "\n"
                diff_message += "=== Generated Head ===\n" + generated_df.head(3).to_string()
                error_message = diff_message
                print(f"\n❌ {error_message} ❌")
                # Step 3: Evaluate the failure
                evaluation_feedback = call_evaluator_agent(generated_code, error_message)

        except Exception as e:
            error_message = f"An exception occurred during testing: {e}"
            print(f"\n❌ {error_message} ❌")
            # Step 3: Evaluate the failure
            evaluation_feedback = call_evaluator_agent(generated_code, error_message)

        if attempt == MAX_ATTEMPTS - 1:
            print("\n--- Max attempts reached. Agent could not fix the code. ---")

