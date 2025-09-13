# **🤖 AutoParser AI**

An autonomous AI agent that automatically writes, tests, and self-corrects Python code to parse bank statement PDFs. This project leverages generative AI to turn unstructured PDF data into clean, structured output with minimal human intervention.

## **✨ Key Features**

* **🤖 Autonomous Operation**: A full generate → test → self-correct loop that runs without manual input.  
* **🧠 Dual AI Backends**: Utilizes both **Gemini** for deep reasoning and **Groq** for high-speed generation.  
* **✅ Contract-Based Testing**: Ensures every auto-generated parser meets a strict quality and output contract using pytest.  
* **🔧 Dynamic Code Generation**: Creates new, custom Python parser files on the fly for any given bank.  
* **🚀 CLI-Driven**: Simple and easy to run directly from your terminal.

## **⚙️ How It Works**

The agent follows a simple yet powerful iterative loop. When you run it, it identifies the target bank and initiates a cycle to create a working parser.

### **The Generate-and-Test Loop**

```
[Start] 
   |
   v
[Generate Parser Code]
   |
   v
[Run Pytest Contract]
   |
   v
[Tests Pass?] ----No----> [Self-Correct] 
   |                          |
   |                          v
   +--------------------------+
   |
  Yes
   |
   v
[Finish: Parser Saved ✅]


```

In essence, the agent's core logic follows this cycle:

* **Plan**: Analyze the PDF structure to decide on a parsing strategy.  
* **Code**: Generate a new `custom_parsers/<bank>_parser.py` file.  
* **Test**: Compare the parser's output with the ground-truth CSV file.  
* **Fix**: If the test fails, refine the approach and retry the loop.

## **🚀 Getting Started: 5-Step Setup**

Follow these steps to get the agent running in under a minute.

### **1. Clone the Repository**

```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### **2. Create and Activate a Virtual Environment**

It's best practice to keep project dependencies isolated.

**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **4. Configure Your API Keys**

The agent needs API keys to communicate with the AI backends.

```bash
cp .env.example .env
```

Then, open the `.env` file and paste in your secret keys for `GEMINI_API_KEY` and `GROQ_API_KEY`.

### **5. Run the Agent**

```bash
python agent.py --target icici
```

The agent will now begin its autonomous loop. Replace `icici` with any other bank name that has a corresponding sample folder in `/data`.

## **🧪 Testing**

While the agent runs tests automatically, you can also run them manually on any existing parser:

```bash
pytest
```

A successful run will show that all tests passed for the available parsers.

## **📂 Project Structure**

```
.
├── agent.py                     # The main autonomous agent script
├── custom_parsers/              # Directory for all auto-generated parsers
├── data/
│   └── icici/
│       ├── icici_sample.csv     # Ground truth data for validation
│       └── icici_sample.pdf     # Sample PDF to be parsed
├── tests/
│   └── test_parser_contract.py  # Pytest contract all parsers must pass
├── .env.example                 # Template for API keys
├── requirements.txt             # Project dependencies
└── README.md
```

