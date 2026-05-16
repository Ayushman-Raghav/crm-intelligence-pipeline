# 🤖 Local Multi-Agent CRM Intelligence Pipeline

> A fully local, containerised, multi-agent AI system that transforms raw CRM data into actionable customer health intelligence — zero cloud dependency, one command to run.

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)
![Ollama](https://img.shields.io/badge/Ollama-llama3.1:8b-black?style=flat-square)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-orange?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📌 Overview

This project implements a **three-agent AI pipeline** that ingests Salesforce-style CRM exports, analyses customer behaviour, scores churn risk, and generates tailored proactive emails — all running locally on your machine inside Docker containers.

No OpenAI. No cloud. No per-token costs. Just local intelligence at scale.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    INGESTION LAYER                       │
│   Salesforce-style CSVs (Accounts, Tickets,             │
│   Opportunities, Usage, Emails, Contacts)               │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│               ORCHESTRATION LAYER                        │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ Agent 1     │  │ Agent 2     │  │ Agent 3         │  │
│  │ Data        │─▶│ Customer    │─▶│ Account         │  │
│  │ Analyst     │  │ Success Mgr │  │ Executive       │  │
│  │ (Pandas)    │  │ (LLM+Chroma)│  │ (Email+JSON)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
┌─────────▼──────────┐    ┌─────────────▼──────────────┐
│   MEMORY LAYER     │    │       OUTPUT LAYER          │
│   ChromaDB         │    │   FastAPI + Dashboard       │
│   (localhost:8001) │    │   (localhost:8080)          │
│   50-account docs  │    │   JSON reports per account  │
└────────────────────┘    └────────────────────────────┘
```

---

## 🤖 The Three-Agent Team

| Agent | Role | Technology | Responsibility |
|---|---|---|---|
| **Agent 1 — Data Analyst (DA)** | Pure analytics | Python + Pandas | Scans CRM data; calculates ticket volume spikes, login drops, upcoming renewals |
| **Agent 2 — Customer Success Manager (CSM)** | AI reasoning | Ollama `llama3.1:8b` + ChromaDB | Takes DA findings, queries vector store for account history, scores churn risk (Red/Amber/Green) |
| **Agent 3 — Account Executive (AE)** | Output generation | LLM + JSON | Generates structured health report and tailored proactive email draft per account |

---

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| LLM Runtime | [Ollama](https://ollama.com/) — `llama3.1:8b` (local, no API key) |
| Vector Store | [ChromaDB](https://www.trychroma.com/) |
| API Framework | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| Data Processing | Python 3.11 + Pandas |
| Containerisation | Docker + Docker Compose |
| Frontend Dashboard | HTML / CSS / JavaScript |
| Data Schemas | Pydantic |

---

## 📁 Project Structure

```
crm-intelligence-pipeline/
├── docker-compose.yml          # Full stack orchestration
├── Dockerfile                  # App container definition
├── main.py                     # Pipeline entrypoint
├── generate_data.py            # Synthetic data generator
├── seed_chroma.py              # ChromaDB seeder
├── requirements.txt
│
├── data/
│   └── sample/                 # Synthetic CRM CSVs (50 accounts)
│       ├── accounts.csv
│       ├── contacts.csv
│       ├── opportunities.csv
│       ├── tickets.csv
│       ├── usage.csv
│       └── emails.csv
│
└── src/
    ├── schemas/                # Pydantic data contracts
    │   ├── account.py
    │   ├── risk.py
    │   └── output.py
    ├── ingestion/
    │   └── loader.py           # Data ingestion layer
    ├── memory/
    │   └── chroma_store.py     # ChromaDB wrapper
    ├── agents/
    │   ├── da_agent.py         # Data Analyst agent (Pandas)
    │   ├── csm_agent.py        # CSM agent (LLM + vector store)
    │   └── ae_agent.py         # AE agent (email + JSON output)
    └── orchestration/          # Agent coordination layer
```

---

## ⚡ Prerequisites

Before running, ensure the following are installed and available:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (running)
- [Ollama](https://ollama.com/) installed and running locally
- `llama3.1:8b` model pulled into Ollama

```bash
# Pull the model (one-time setup)
ollama pull llama3.1:8b
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Ayushman-Raghav/crm-intelligence-pipeline.git
cd crm-intelligence-pipeline
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your local settings if needed
```

### 3. Start the full stack

```bash
docker compose up -d
```

This single command will:
- Start ChromaDB on `localhost:8001`
- Wait for ChromaDB to be healthy
- Seed ChromaDB with 50-account context documents
- Start the FastAPI app on `localhost:8080`
- Run the full pipeline across all accounts

### 4. Open the Dashboard

```
http://localhost:8080
```

### 5. View raw output

Structured JSON reports are saved to `data/output/full_report.json`.

---

## 📊 Dashboard Features

| Feature | Description |
|---|---|
| **Health Score Cards** | At-a-glance Red / Amber / Green totals |
| **Donut Chart** | Visual breakdown of account health distribution |
| **Filterable Table** | Sort and filter all 50 accounts by risk level |
| **Expandable Rows** | Click any account to view churn reasons |
| **Email Copy** | One-click copy of the AI-drafted outreach email |

---

## 🌐 API Endpoints

The FastAPI backend exposes 5 endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/summary` | Overall pipeline run summary |
| `GET` | `/api/accounts` | All accounts with health scores |
| `GET` | `/api/accounts/{id}` | Single account full report |
| `GET` | `/api/red` | All Red (high-risk) accounts |
| `GET` | `/api/amber` | All Amber (medium-risk) accounts |

---

## 📈 Sample Output

```json
{
  "account_id": "ACC-0042",
  "account_name": "Meridian Technologies",
  "health_score": "Red",
  "churn_reasons": [
    "Support ticket volume increased 340% in last 30 days",
    "Login frequency dropped 60% month-over-month",
    "Contract renewal due in 28 days — no renewal signal"
  ],
  "email_draft": "Hi Sarah, I wanted to reach out personally..."
}
```

---

## 🗺️ Roadmap

- [x] 3-agent local pipeline (DA → CSM → AE)
- [x] ChromaDB vector store with per-account context
- [x] Health scoring with rule-based guardrail (Red / Amber / Green)
- [x] FastAPI backend with 5 endpoints
- [x] Interactive dashboard with donut chart and email copy
- [x] Full Docker Compose containerisation
- [ ] Connect live Salesforce data via API (swap `loader.py` only)
- [ ] Upgrade CSM Agent LLM to Claude (Anthropic API) for improved accuracy
- [ ] Automated nightly pipeline runs via cron
- [ ] Email send integration (SendGrid / SMTP)
- [ ] Multi-tenant support

---

## 🔒 Environment Variables

The `.env` file is excluded from version control. Use `.env.example` as a template:

```env
OLLAMA_HOST=http://host.docker.internal:11434
CHROMA_HOST=chromadb
CHROMA_PORT=8001
APP_PORT=8080
```

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

[MIT](LICENSE)

---

## 👤 Author

**Ayushman Raghav**
GitHub: [@Ayushman-Raghav](https://github.com/Ayushman-Raghav)

---

*Built with 🤖 Ollama + ChromaDB + FastAPI + Docker — 100% local, 0% cloud.*
