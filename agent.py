import os
import pypdf
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
import re
import argparse
import subprocess
import sys
from dataclasses import dataclass, field
from typing import List
import importlib.util

# --- 1. Configuration & Setup ---

# Load environment variables from a .env file
load_dotenv()

# Simple color logging for better readability in the console
class Color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

def log(message, color=Color.END):
    print(color + message + Color.END)

@dataclass
class AgentContext:
    """A central dataclass to hold the agent's state and history."""
    target: str
    pdf_path: Path
    csv_path: Path
    max_attempts: int = 3
    attempt: int = 1
    plan: str = ""
    generated_code: str = ""
    test_output: str = ""
    feedback: str = "This is the first attempt. No feedback yet."
    history: List[str] = field(default_factory=list)

# --- 2. Core Components (LLM and Tools) ---

class LLMClient:
    """Handles all interactions with different LLM providers."""
    def __init__(self, provider: str = "groq"):
        self.provider = provider
        self.client = self._initialize_client()
        self.system_prompt = """You are a world-class Python developer specializing in data parsing. Your task is to write a complete, standalone Python script to parse PDF bank statements.

RULES:
1.  **CODE ONLY**: Your entire response must be a single, executable block of Python code. Do not include any explanations, markdown, or introductory text.
2.  **FUNCTION SIGNATURE**: The script MUST contain a function with the exact signature: `def parse(pdf_path: str) -> pd.DataFrame`.
3.  **USE THE ARGUMENT**: The `parse` function **MUST** use the `pdf_path` variable it receives. Do not hardcode file paths.
4.  **ALLOWED LIBRARIES**: You may only use `pypdf`, `pandas`, `numpy`, and `re`.
5.  **EXACT SCHEMA**: The returned DataFrame must have the exact column names and order as specified in the prompt.
"""

    def _initialize_client(self):
        """Initializes the appropriate LLM client based on the provider."""
        if self.provider == "groq":
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY not found in .env file.")
            try:
                from groq import Groq
                return Groq(api_key=api_key)
            except ImportError:
                raise ImportError("Please install 'groq' (`pip install groq`) to use this provider.")
        # Add other providers like 'gemini' here
        # elif self.provider == "gemini":
        #     ...
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate(self, prompt: str) -> str:
        """Generates content using the configured LLM."""
        log(f"Generating content with {self.provider}...", Color.CYAN)
        try:
            if self.provider == "groq":
                response = self.client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    max_tokens=4096
                )
                return self._extract_python_code(response.choices[0].message.content)
            # Add other provider logic here
            return ""
        except Exception as e:
            log(f"Error during LLM call: {e}", Color.RED)
            return ""

    def _extract_python_code(self, response: str) -> str:
        """Extracts the Python code block from the LLM's response."""
        match = re.search(r"```python\s*(.*?)\s*```", response, re.DOTALL)
        return match.group(1).strip() if match else response.strip()

class Planner:
    """Tool for analyzing the input files and creating a plan."""
    def run(self, context: AgentContext) -> AgentContext:
        log("Analyzing inputs and forming a plan...")
        try:
            pdf_text = self._extract_text_from_pdf(context.pdf_path)
            csv_info = self._get_csv_info(context.csv_path)
            context.plan = f"""
PDF Analysis:
- The PDF contains {len(pdf_text)} characters.
- Sample Text (first 1000 chars): {pdf_text[:1000]}

Target CSV Structure:
{csv_info}
"""
            context.history.append("Step 1: Planning complete.")
            log("Analysis complete.", Color.GREEN)
        except Exception as e:
            error_message = f"Failed to analyze files: {e}"
            log(error_message, Color.RED)
            context.history.append(f"Step 1: Planning failed. Error: {e}")
            raise
        return context

    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        reader = pypdf.PdfReader(pdf_path)
        return "".join(page.extract_text() or "" for page in reader.pages)

    def _get_csv_info(self, csv_path: Path) -> str:
        df = pd.read_csv(csv_path)
        return f"- Columns: {list(df.columns)}\n- Head:\n{df.head(3).to_string()}"

class CodeGenerator:
    """Tool for generating the parser code based on the plan and feedback."""
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def run(self, context: AgentContext) -> AgentContext:
        log("Generating parser code...")
        prompt = f"""
This is attempt {context.attempt} of {context.max_attempts}.

**Previous Feedback for Correction:**
{context.feedback}

**Execution Plan:**
{context.plan}

Based on the plan and the feedback above, please generate the complete Python script. Focus on fixing the logic error.
"""
        context.generated_code = self.llm.generate(prompt)
        if context.generated_code:
            context.history.append("Step 2: Code generation complete.")
            log("Code generation successful.", Color.GREEN)
        else:
            context.history.append("Step 2: Code generation failed (LLM returned empty).")
            log("Code generation failed.", Color.RED)
        return context

class TestRunner:
    """Tool for running tests on the generated code in an isolated environment."""
    def run(self, context: AgentContext) -> tuple[bool, str]:
        # MODIFICATION: Check if pytest is installed before running.
        if not self._is_pytest_installed():
            error_msg = "Pytest is not installed. Please run 'pip install pytest' to enable testing."
            log(error_msg, Color.RED)
            return False, error_msg
            
        parser_dir = Path("custom_parsers")
        parser_dir.mkdir(exist_ok=True)
        parser_file = parser_dir / f"{context.target}_parser.py"
        parser_file.write_text(context.generated_code, encoding="utf-8")

        test_file = Path("temp_test_parser.py")
        test_file.write_text(self._create_test_content(context, parser_file), encoding="utf-8")

        log(f"Running tests on '{parser_file.name}'...", Color.YELLOW)
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v"],
                capture_output=True, text=True, timeout=60
            )
            output = result.stdout + result.stderr
            success = result.returncode == 0
            log(f"Tests {'passed' if success else 'failed'}.", Color.GREEN if success else Color.RED)
            return success, output
        except subprocess.TimeoutExpired:
            return False, "Test execution timed out after 60 seconds."
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def _is_pytest_installed(self) -> bool:
        """Checks if pytest is available in the current environment."""
        return importlib.util.find_spec("pytest") is not None

    def _create_test_content(self, context: AgentContext, parser_file: Path) -> str:
        module_name = parser_file.stem
        # MODIFICATION: More granular and informative pytest script.
        return f"""
import pytest
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd() / "custom_parsers"))
from {module_name} import parse

@pytest.fixture
def data_frames():
    pdf_path = r"{context.pdf_path.resolve()}"
    csv_path = r"{context.csv_path.resolve()}"
    
    expected_df = pd.read_csv(csv_path).astype(str)
    generated_df = parse(pdf_path)
    
    assert generated_df is not None, "Parser returned None."
    assert not generated_df.empty, "Parser returned an empty DataFrame."
    
    return generated_df.astype(str), expected_df

def test_columns_match(data_frames):
    generated_df, expected_df = data_frames
    assert list(generated_df.columns) == list(expected_df.columns), "Column names or order do not match."

def test_shape_matches(data_frames):
    generated_df, expected_df = data_frames
    assert generated_df.shape == expected_df.shape, f"DataFrame shape mismatch. Got {{generated_df.shape}}, expected {{expected_df.shape}}."

def test_data_matches(data_frames):
    generated_df, expected_df = data_frames
    pd.testing.assert_frame_equal(generated_df, expected_df)
"""

class FeedbackAnalyzer:
    """Tool for analyzing test failures and generating actionable feedback."""
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def run(self, context: AgentContext) -> AgentContext:
        log("Analyzing test failure to generate feedback...")
        # MODIFICATION: More specific prompt to guide the LLM.
        prompt = f"""You are a debugging expert. Analyze the failed pytest output. Your goal is to provide a concise, actionable suggestion to fix the Python code's LOGIC.
Do NOT suggest installing packages or changing the environment. Focus only on the code.

FAILED CODE:
```python
{context.generated_code}
```

PYTEST OUTPUT:
```
{context.test_output}
```

Based on the error (e.g., AssertionError, ValueError), provide a short, clear suggestion for the next attempt.
"""
        context.feedback = self.llm.generate(prompt)
        log("Feedback generated.", Color.GREEN)
        context.history.append("Step 4: Feedback analysis complete.")
        return context

# --- 3. The Main Agent Orchestrator ---

class Agent:
    """The orchestrator that runs the agent loop."""
    def __init__(self, context: AgentContext, llm_client: LLMClient):
        self.context = context
        # Initialize all the tools the agent can use
        self.planner = Planner()
        self.code_generator = CodeGenerator(llm_client)
        self.test_runner = TestRunner()
        self.feedback_analyzer = FeedbackAnalyzer(llm_client)

    def run(self):
        log(f"Starting agent for target: {self.context.target}", Color.HEADER)
        self.context = self.planner.run(self.context)

        while self.context.attempt <= self.context.max_attempts:
            log(f"\n--- Attempt {self.context.attempt}/{self.context.max_attempts} ---", Color.HEADER)

            self.context = self.code_generator.run(self.context)
            if not self.context.generated_code:
                self.context.attempt += 1
                continue

            success, output = self.test_runner.run(self.context)
            self.context.test_output = output
            self.context.history.append(f"Attempt {self.context.attempt}: Tests {'passed' if success else 'failed'}.")

            if success:
                log("\nMISSION SUCCESSFUL! ✅", Color.GREEN)
                log(f"Parser saved to 'custom_parsers/{self.context.target}_parser.py'")
                return

            self.context = self.feedback_analyzer.run(self.context)
            
            # MODIFICATION: Sanity check guardrail for LLM feedback.
            if "install" in self.context.feedback.lower() or "pip" in self.context.feedback.lower():
                log("LLM generated unhelpful environment feedback. Overriding.", Color.YELLOW)
                self.context.feedback = "The previous attempt failed with a data mismatch or code error. Please re-examine the parsing logic, especially the regular expressions and how data is extracted and cleaned. Do not suggest installing packages."

            log(f"\nFeedback for next attempt: {self.context.feedback}", Color.YELLOW)
            self.context.attempt += 1

        log(f"\nMISSION FAILED! ❌ After {self.context.max_attempts} attempts.", Color.RED)

# --- 4. Entry Point ---

def main():
    parser = argparse.ArgumentParser(description="An AI agent that automatically generates PDF parsers.")
    parser.add_argument("--target", type=str, required=True, help="Target bank name (e.g., 'icici').")
    parser.add_argument("--provider", type=str, default="groq", choices=["groq"], help="The LLM provider to use.")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    context = AgentContext(
        target=args.target,
        pdf_path=script_dir / "data" / args.target / f"{args.target} sample.pdf",
        csv_path=script_dir / "data" / args.target / "result.csv"
    )

    if not context.pdf_path.exists() or not context.csv_path.exists():
        log(f"Error: Missing required files for target '{args.target}'.", Color.RED)
        log(f"Checked for PDF at: {context.pdf_path}")
        log(f"Checked for CSV at: {context.csv_path}")
        sys.exit(1)

    llm_client = LLMClient(provider=args.provider)
    agent = Agent(context, llm_client)
    agent.run()

if __name__ == "__main__":
    main()

