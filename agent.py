# agent.py
import argparse
import subprocess
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import importlib
import pdfplumber
from groq import Groq

# ======================
# Setup
# ======================
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("⚠️ Missing GROQ_API_KEY in .env")
    sys.exit(1)

groq_client = Groq(api_key=GROQ_API_KEY)

# ======================
# LLM Call
# ======================
def call_llm(prompt: str) -> str:
    resp = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content

# ======================
# Core Loop
# ======================
def generate_parser_code(bank: str, csv_header: str) -> str:
    prompt = f"""
Write Python code for a bank statement parser.

Requirements:
- Define: def parse(pdf_path: str) -> pandas.DataFrame
- Use pdfplumber to read the PDF
- Return a DataFrame with columns: {csv_header}
- Fill missing values with ""
- No explanations, only valid Python code
"""
    return call_llm(prompt)

def write_parser_file(bank: str, code: str):
    parser_dir = Path("custom_parsers")
    parser_dir.mkdir(exist_ok=True)
    file_path = parser_dir / f"{bank}_parser.py"

    clean_code = code
    if "```" in clean_code:
        parts = clean_code.split("```")
        clean_code = parts[1].replace("python", "")
    file_path.write_text(clean_code.strip(), encoding="utf-8")
    print(f"✅ Wrote parser to {file_path}")
    return file_path

def run_pytest(bank: str) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_parser_contract.py"],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
    return result.returncode == 0

# ======================
# Main Agent
# ======================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="Bank name (e.g. icici)")
    args = parser.parse_args()

    bank = args.target.lower()
    pdf_path = Path(f"data/{bank}/{bank}_sample.pdf")
    csv_path = Path(f"data/{bank}/{bank}_sample.csv")

    assert pdf_path.exists(), f"Missing {pdf_path}"
    assert csv_path.exists(), f"Missing {csv_path}"

    csv_header = ",".join(pd.read_csv(csv_path, nrows=0).columns)

    for attempt in range(1, 4):
        print(f"\n🌀 Attempt {attempt}/3...")
        code = generate_parser_code(bank, csv_header)
        write_parser_file(bank, code)

        if run_pytest(bank):
            # Preview top 5 rows
            expected_df = pd.read_csv(csv_path)
            sys.path.insert(0, str(Path("custom_parsers").resolve()))
            parser_module = importlib.import_module(f"{bank}_parser")
            parsed_df = parser_module.parse(str(pdf_path))

            print("\n📊 Expected (CSV) top 5:")
            print(expected_df.head())
            print("\n🤖 Parsed (PDF) top 5:")
            print(parsed_df.head())

            print("✅ Tests passed!")
            return

        print("❌ Tests failed, retrying...")

    print("🚨 Failed after 3 attempts.")

if __name__ == "__main__":
    main()
