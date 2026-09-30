# Apex Global | Enterprise Customer Experience (CX) AI Suite

A production-grade, AI-powered Customer Experience and Service Management platform built for enterprise equipment manufacturers interacting with **Retail Customers**, **Authorized Dealers**, **Regional Distributors**, and **Commercial Business Partners**.

---

## 🏛️ System Architecture

```text
                                   +--------------------------------------------------+
                                   |             Omni-Channel Customer Touchpoints    |
                                   |       (Customers, Dealers, Distributors, Partners)|
                                   +--------------------------------------------------+
                                                             |
                                                             v
                                        +---------------------------------------+
                                        |  Streamlit Enterprise UI & Navigation |
                                        +---------------------------------------+
                                                             |
                     +---------------------------------------+--------------------------------------+
                     |                                       |                                      |
                     v                                       v                                      v
       +----------------------------+          +---------------------------+          +---------------------------+
       |   Customer Chat Console    |          |    Management Analytics   |          |  Knowledge Base & RAG Hub |
       | - Context & Profile Sync   |          | - 12+ Real-Time KPIs      |          | - PDF, DOCX, TXT, CSV,XLSX|
       | - Progressive Info Form    |          | - Multi-Dimension Filters |          | - Keyword & Chunk Indexer |
       | - Quick Actions & CSAT     |          | - Grounded AI Insights    |          | - Verified Policy Search  |
       +----------------------------+          +---------------------------+          +---------------------------+
                     |                                       |                                      |
                     +---------------------------------------+--------------------------------------+
                                                             |
                                                             v
                                        +---------------------------------------+
                                        |    CX AI Engine & Orchestrator        |
                                        |   (modules/chatbot.py)                |
                                        +---------------------------------------+
                                                             |
         +-----------------------------------+---------------+-----------------------------------+
         |                                   |                                                   |
         v                                   v                                                   v
+------------------+               +-------------------+                               +--------------------+
| Intent Engine    |               | Sentiment & Urg   |                               | Escalation Engine  |
| - 20 Categories  |               | - Score (-100,+100|                               | - Critical Safety  |
| - OpenAI + Rules |               | - 9 Core Emotions |                               | - SLA >48h / Delays|
+------------------+               | - LOW to CRITICAL |                               | - Legal Threats    |
                                   +-------------------+                               +--------------------+
                                             |                                                   |
                                             +-------------------------+-------------------------+
                                                                       |
                                                                       v
                                                    +------------------------------------+
                                                    |      SQLite Persistence Layer      |
                                                    |  (Complaints, SRs, CSAT, Analytics)|
                                                    +------------------------------------+
```

---

## 📁 Repository Directory Structure

```text
customer_experience_bot/
│
├── app.py                      # Main Streamlit enterprise web application
├── requirements.txt            # Python dependencies (OpenAI, Streamlit, Pandas, Plotly, etc.)
├── .env.example                # Template for environment configuration & API keys
├── .gitignore                  # Git exclusions for venv, secrets, and SQLite files
├── README.md                   # This comprehensive engineering manual
│
├── data/
│   ├── customer_data.csv       # Preloaded master dealer, distributor, and customer directory
│   └── cx_database.sqlite      # SQLite database (auto-generated & seeded on startup)
│
├── modules/
│   ├── __init__.py             # Module package marker
│   ├── chatbot.py              # Main CX conversation engine & OpenAI/hybrid coordinator
│   ├── sentiment.py            # Real-time sentiment (-100 to +100), emotion & urgency analyzer
│   ├── intent.py               # Intent classifier covering all 20 business categories
│   ├── escalation.py           # Intelligent rule-based management escalation engine
│   ├── knowledge_base.py       # RAG retrieval engine & document parser (PDF, DOCX, TXT, CSV, XLSX)
│   ├── analytics.py            # Executive KPIs, dimensional aggregations & AI management insights
│   ├── database.py             # SQLite schema creation, data seeding, and query CRUD layer
│   ├── prompts.py              # Strict system instructions & anti-hallucination guardrails
│   └── voice_ready.py          # Audio transcription, diarization & call quality audit models
│
├── assets/
│   └── logo.png                # Corporate brand logo asset
│
└── uploads/
    └── .gitkeep                # Staging directory for uploaded company documents
```

---

## 🚀 Quick Start Guide: VS Code on Windows

Follow these exact steps in your VS Code terminal to run the application locally:

### 1. Open Terminal in VS Code
Open the repository folder in VS Code, then open a **PowerShell** or **Command Prompt** terminal (`Ctrl + ~` or **Terminal > New Terminal**).

### 2. Create the Python Virtual Environment
```bash
python -m venv venv
```

### 3. Activate the Virtual Environment
**On Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```
*(If PowerShell displays an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

**On Windows Command Prompt (CMD):**
```cmd
venv\Scripts\activate.bat
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Your OpenAI API Key
Create a `.env` file in the `customer_experience_bot` directory:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` in VS Code and paste your OpenAI API key:
   ```ini
   OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_OPENAI_API_KEY_HERE
   OPENAI_MODEL=gpt-4o-mini
   COMPANY_NAME=Apex Global Technologies & Systems
   DATABASE_PATH=data/cx_database.sqlite
   ```
> **Note on Offline / Fallback Mode:**
> If you run the app without an OpenAI API key, the built-in deterministic fallback engine automatically handles intent detection, sentiment scoring, escalation evaluation, and ticket generation without crashing!

### 6. Launch the Streamlit Application
```bash
streamlit run app.py
```
Streamlit will automatically open your default browser to `http://localhost:8501`.

---

## ⚡ Core Functional Capabilities

### 1. Intent Detection (20 Business Categories)
Every incoming message is categorized into one of 20 predefined enterprise intents:
1. `Product Information`
2. `Product Complaint`
3. `Product Defect`
4. `Technical Support`
5. `Installation Issue`
6. `Warranty Query`
7. `Service Request`
8. `Spare Parts`
9. `Delivery Issue`
10. `Order Status`
11. `Dealer Complaint`
12. `Distributor Complaint`
13. `Pricing Query`
14. `Payment Query`
15. `Replacement Request`
16. `Refund Request`
17. `Feedback`
18. `Suggestion`
19. `General Query`
20. `Emergency / High Priority`

### 2. Real-Time Sentiment & Emotion Analysis
- **Sentiment Scale**: `Very Positive`, `Positive`, `Neutral`, `Negative`, `Very Negative`
- **Sentiment Score**: Continuous score from `-100` to `+100`
- **Emotions**: `Frustrated`, `Angry`, `Disappointed`, `Confused`, `Satisfied`, `Happy`, `Neutral`, `Anxious`, `Urgent`
- **Urgency Rating**: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

### 3. Automated Management Escalation Engine
Escalations are automatically triggered when:
- Urgency is `CRITICAL` (smoke, fire, electrical hazard, sparks, risk to life/property)
- Repeated unresolved complaints are detected for the same customer or equipment
- Customer mentions legal action, consumer court, or police
- Customer explicitly demands a manager or supervisor
- Unresolved service delay exceeds the 48-hour SLA threshold with Negative sentiment
- Dealer or distributor reports major commercial loss or contract cancellation

### 4. Ticket Generation & ID Standardization
- **Complaints**: Formatted as `CX-YYYYMMDD-XXXX` (e.g. `CX-20260930-0001`) with full lifecycle statuses (`Open`, `Assigned`, `In Progress`, `Waiting for Customer`, `Resolved`, `Closed`, `Escalated`).
- **Service Requests**: Formatted as `SR-YYYYMMDD-XXXX` (e.g. `SR-20260930-0001`).

### 5. Verified RAG Knowledge Base (Anti-Hallucination)
- Ingests **PDF**, **DOCX**, **TXT**, **CSV**, and **XLSX** files.
- Built-in technical manuals for Inverters, Heat Pumps, EV Chargers, Industrial Pumps, and Commercial Dealer policies.
- Anti-Hallucination Guardrail: If verified technical data is not present in documentation, the AI strictly states:
  > *"I don't have enough verified information to answer that accurately. I can raise this as a service request or connect you with the appropriate team."*

### 6. Executive Management Analytics & Grounded AI Insights
- **12+ Real-Time KPIs**: Total Conversations, Complaints, Escalations, CSAT Score %, Avg Sentiment Score, Repeat Complaint %, SLA Breach %.
- **Multi-Dimension Filters**: By Status, Urgency, Product Line, Dealer, and Region.
- **Data-Grounded AI Insights**: Generates strategic observations strictly from computed SQL aggregates (no fabricated claims).

### 7. Forward-Compatible Voice / Call Analysis Pipeline
- Modular architecture with `VoiceCallAnalyzer` ready for `MP3`, `WAV`, and `M4A` audio.
- Speaker diarization (Customer vs. Agent), speech sentiment shifts, call quality scoring, and action item extraction.

---

## 🧪 Running Automated Unit Tests

Run the test verification suite to test all components locally:
```bash
python test_verification.py
```
This tests database initialization, intent classification, sentiment scoring, escalation triggers, RAG retrieval, and chatbot response generation.

---

## 📄 License & Confidentiality
Confidential and Proprietary. Designed for Apex Global Technologies & Systems and authorized enterprise partners.
