# 🤖 AI-Powered Bank Reconciliation App (Multi-Agent)

This project is an AI-powered reconciliation assistant that automates the process of matching and analyzing bank transactions using OpenAI's GPT models. Built with **Streamlit** and a **modular multi-agent architecture**, the app processes Excel inputs (`EDW` and `Journal` sheets), detects unmatched transactions, recommends resolutions, and generates a final reconciled Excel report.

---

## 🧠 Features

- 📥 Upload Excel files containing EDW & Journal sheets
- 📘 Optional SOP PDF upload to guide GPT agents using policy memory
- 🔍 AI-driven transaction matching using OpenAI (GPT-4o)
- 🚨 Detection of unmatched/discrepant transactions
- ✅ Automated suggestions for resolving discrepancies
- 📊 Final report in Excel format with full reconciliation & audit trail
- 🧩 Modular multi-agent structure for flexibility and scalability

---

## 🧩 Architecture

```
Streamlit UI
 └── AgentOrchestrator
      ├── RawDataCollectorAgent
      ├── TransactionAnalyzerAgent (GPT)
      ├── DiscrepancyResolutionAgent (GPT)
      └── ReportGeneratorAgent
```

---

## 📂 Project Structure

```
bank_recon_ai_app/
├── app.py                         # Streamlit app UI
├── agents/
│   ├── base.py                   # BaseAgent class
│   ├── raw_data_collector.py    # Agent 1
│   ├── transaction_analyzer.py  # Agent 2 (GPT)
│   ├── discrepancy_resolution.py# Agent 3 (GPT)
│   ├── report_generator.py      # Agent 4
│   └── orchestrator.py          # Master agent
├── utils/
│   └── pdf_parser.py            # Extracts text from SOP PDF
├── requirements.txt
└── .streamlit/
    └── secrets.toml             # OpenAI API key
```

---

## 📦 Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/bank-recon-ai.git
   cd bank-recon-ai
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up secrets**
   Create `.streamlit/secrets.toml` and add your OpenAI API key:

   ```toml
   [openai]
   api_key = "sk-your-openai-key"
   ```

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

---

## 🛠 Agent Descriptions

### 1. `RawDataCollectorAgent`
- Loads `EDW` and `Journal` sheets from Excel
- Converts them to Pandas DataFrames

### 2. `TransactionAnalyzerAgent` *(GPT-powered)*
- Sends both sheets to GPT for matching
- Uses rules (Account No, Date, Tran Code, Amount) for reconciliation
- Outputs a CSV-formatted reconciliation table

### 3. `DiscrepancyResolutionAgent` *(GPT-powered)*
- Filters unmatched rows
- Sends them to GPT to get suggested resolutions
- Returns explanation table

### 4. `ReportGeneratorAgent`
- Compiles final Excel with:
  - Reconciliation sheet
  - EDW sheet
  - Journal sheet
  - Suggestions sheet (if applicable)

---

## 🧠 SOP PDF as Contextual Memory

You can upload a PDF file containing SOPs, reconciliation rules, or company-specific policy. The extracted text is injected into the GPT prompt to guide the agents in line with real business logic.

---

## 📘 Sample Input File

The Excel file should have two sheets:
- `EDW`: Contains source transactions
- `Journal`: Contains booked GL entries

Ensure the column names match expected formats (Account Number, Amount, Tran Code, etc.).

---

## 💬 Prompt Example (LLM Agent)

```
You are a reconciliation assistant. Use the SOP below to guide your logic.

### SOP:
<insert extracted SOP text>

Match Journal entries with EDW transactions based on:
- Account Number, Tran Code, and Journal Date = Process Date
- Sum of EDW Amounts = Journal Debit Amount

Output final reconciled entries as CSV.
```

---

## 📘 File Requirements

1. Excel file with two sheets:
   - 'EDW' sheet
   - 'Journal' sheet

2. Optional: PDF file containing SOPs

---

## 📘 Setup & Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - Create a `.env` file
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

---

## 📘 Running Locally

```bash
streamlit run app.py
```

---

## 📘 Deployment

This app is configured for deployment on Streamlit Cloud:
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Add OPENAI_API_KEY to Streamlit Cloud secrets

---

## 📘 Security Note

- Do not upload sensitive or real customer data
- Keep your API keys secure
- Use environment variables for secrets