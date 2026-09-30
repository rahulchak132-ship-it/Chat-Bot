# Enterprise Customer Experience (CX) AI Suite

A production-grade, AI-powered Customer Experience and Service Management platform for enterprise equipment manufacturers interacting with **Retail Customers**, **Authorized Dealers**, **Regional Distributors**, and **Commercial Business Partners**.

The complete standalone Streamlit application is located in the [`customer_experience_bot/`](./customer_experience_bot/) directory.

---

## ⚡ Quick Start: Windows VS Code Commands

Open your terminal in VS Code and run:

```bash
cd customer_experience_bot
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

> **API Key Setup:**
> Copy `customer_experience_bot/.env.example` to `customer_experience_bot/.env` and insert your OpenAI API key in `OPENAI_API_KEY=your_key_here`.
> The system also includes an intelligent offline fallback engine that runs immediately even without an API key!

For the exhaustive architecture guide, database schema, intent taxonomy, and escalation rules, refer to [customer_experience_bot/README.md](./customer_experience_bot/README.md).
