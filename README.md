🤖 AutoParser AI
An autonomous AI agent that automatically writes, tests, and self-corrects Python code to parse bank statement PDFs. This project leverages generative AI to turn unstructured PDF data into clean, structured output with minimal human intervention.

✨ Key Features
🤖 Autonomous Operation: A full generate -> test -> self-correct loop that runs without manual input.

🧠 Dual AI Backends: Utilizes both Gemini for deep reasoning and Groq for high-speed generation.

✅ Contract-Based Testing: Ensures every auto-generated parser meets a strict quality and output contract using pytest.

🔧 Dynamic Code Generation: Creates new, custom Python parser files on the fly for any given bank.

🚀 CLI-Driven: Simple and easy to run directly from your terminal.

⚙️ How It Works
The agent follows a simple yet powerful iterative loop. When you run it, it identifies the target bank and initiates a cycle to create a working parser.

The Generate-and-Test Loop:

Analyze & Generate: The agent prompts an AI model with the specific requirements for the bank's PDF, asking it to generate a Python parser script.

Save & Clean: It saves the generated code to a file within custom_parsers/, cleaning up any non-code text from the AI's response.

Test Rigorously: The agent immediately runs a pytest test against the new script. This test acts as a "contract," ensuring the parser has the right functions and produces valid, structured data.

Evaluate & Repeat:

If the test passes, the agent's job is done. The valid parser is saved and ready to use.

If the test fails, the agent analyzes the failure, provides debug output, and returns to step 1 to generate a new, improved version. This loop continues until the parser passes or 3 attempts have been made.

graph TD
    subgraph "AutoParser AI Workflow"
        A(Start) --> B{"Set Target Bank (e.g., ICICI)"};
        B --> C[Step 1: Generate Python Code];
        subgraph "AI Generation & Testing Loop (Max 3 Attempts)"
            direction LR
            C --> D["Step 2: Save Parser to `custom_parsers/`"];
            D --> E["Step 3: Run `pytest` Validation"];
            E --> F{Tests Pass?};
        end
        F -- Yes --> G([Success: Parser is Valid ✅]);
        F -- No --> H{Attempts Left?};
        H -- Yes --> I["Step 4: Analyze Failure & Self-Correct"];
        I --> C;
        H -- No --> J([Failure: Max Retries Reached 🚨]);
    end

    style A fill:#D5E8D4,stroke:#82B366,stroke-width:2px
    style G fill:#D5E8D4,stroke:#82B366,stroke-width:2px
    style J fill:#F8CECC,stroke:#B85450,stroke-width:2px
    style C fill:#DAE8FC,stroke:#6C8EBF,stroke-width:2px
    style E fill:#DAE8FC,stroke:#6C8EBF,stroke-width:2px
    style I fill:#FFE6CC,stroke:#D79B00,stroke-width:2px

In essence, the agent's core logic follows this cycle:

Plan: Analyze the PDF structure to decide on a parsing strategy.

Code: Generate a new custom_parsers/<bank>_parser.py file.

Test: Compare the parser's output with the ground-truth CSV file.

Fix: If the test fails, refine the approach and retry the loop.

🚀 Getting Started: 5-Step Setup
Follow these steps to get the agent running in under a minute.

1. Clone the Repository
Get a local copy of the project.

git clone [https://github.com/](https://github.com/)<your-username>/<your-repo-name>.git
cd <your-repo-name>

2. Create and Activate a Virtual Environment
It's best practice to keep project dependencies isolated.

# For Windows
python -m venv venv
.\venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

3. Install Dependencies
Install all the required Python packages from the requirements.txt file.

pip install -r requirements.txt

4. Configure Your API Keys
The agent needs API keys to communicate with the AI backends.

# Copy the example file
cp .env.example .env

Now, open the .env file with a text editor and paste in your secret keys for GEMINI_API_KEY and GROQ_API_KEY.

5. Run the Agent
Execute the agent from the command line, using the --target flag to specify which bank to parse.

python agent.py --target icici

The agent will now begin its autonomous loop. You can replace icici with any other bank name that has a corresponding sample folder in /data.

🧪 Testing
While the agent runs tests automatically, you can also run them manually on any existing parser.

pytest

A successful run will show that all tests passed for the available parsers.

📂 Project Structure
.
├── agent.py                 # The main autonomous agent script
├── custom_parsers/          # Directory for all auto-generated parsers
├── data/
│   └── icici/
│       ├── icici_sample.csv   # The ground truth data for validation
│       └── icici_sample.pdf   # The sample PDF to be parsed
├── tests/
│   └── test_parser_contract.py # The pytest contract all parsers must pass
├── .env.example             # Template for API keys
├── requirements.txt         # Project dependencies
└── README.md
