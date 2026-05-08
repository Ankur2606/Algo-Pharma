# ⬡ AlgoPharma: AI-Powered Pharmacovigilance Pipeline

AlgoPharma is an end-to-end agentic workflow and NLP pipeline designed to proactively detect adverse drug events (ADEs) and pharmacovigilance signals from unstructured social media and forum data (Reddit, Twitter, etc.).

## 🌟 Key Features

- **Agentic Chat Interface**: A Groq-powered (Llama 3.3 70B) local tool-calling agent that translates natural language requests (e.g., *"Find side effects of paracetamol on Reddit"*) into parameterized crawling jobs.
- **Decoupled Ingestion Pipeline**: Asynchronous processing using FastAPI, Upstash Redis, and Celery to ensure the UI remains non-blocking while heavy NLP tasks run in the background.
- **7-Stage NLP Analysis**: An extensive pipeline covering PII redaction (Nemotron/Regex), Drug/Symptom Named Entity Recognition (NER), Sentiment Analysis, Negation Detection, and PRR/ROR signal statistical scoring.
- **Premium Glassmorphic Dashboard**: A fully responsive, dark-themed UI built with vanilla JS and Chart.js that dynamically polls backend endpoints to render live metrics, AE probabilities, and signal distributions.

---

## 🏗️ Architecture & Data Flow

The platform is designed around a decoupled, event-driven architecture to handle high-latency web scraping and heavy machine learning inference without blocking the user interface.

### 1. The Interaction Layer (FastAPI + JS)
- The user logs into the static dashboard (`index.html`) served directly by FastAPI.
- They submit a natural language query via the chat UI.
- FastAPI's `/api/chat` endpoint spawns `llm_module.py` as an isolated subprocess.

### 2. The Agentic Layer (Groq Tool Calling)
- `llm_module.py` acts as the orchestrator.
- It uses the **Groq API** (`llama-3.3-70b-versatile`) to perform slot-filling and intent recognition.
- Groq selects the appropriate local python tool (e.g., `reddit_crawler` or `twitter_crawler`) from the tool registry (`mcp_tools.py`).
- The crawler executes, storing raw JSON posts in the SQLite database (`algopharma.db`), and immediately pushes a task to the **Upstash Redis** broker.

### 3. The Asynchronous Worker Layer (Celery)
- A separate Celery worker (`celery_app.py`) listens to a dedicated Upstash Redis queue (`algopharma_ankur_queue` for team isolation).
- It consumes `process_unprocessed` tasks, loading the heavy HuggingFace/spaCy models into memory just once upon startup.

### 4. The 7-Stage NLP Pipeline
Once the Celery worker picks up raw posts, they are pushed through a rigorous NLP funnel:

1. **Language Detection**: Determines the text language.
2. **PII Guard**: Redacts sensitive data using `OpenMed/privacy-filter-nemotron` (55 clinical entities) and Indian-specific regex (Aadhaar, PAN, UPI).
3. **Drug NER**: Identifies pharmaceutical terms using `OpenMed-NER-PharmaDetect-BigMed-278M` and maps them to MedDRA standards.
4. **Symptom/Disease NER**: Identifies adverse symptoms using `OpenMed-NER-DiseaseDetect-BioMed-335M`.
5. **Sentiment & Negation Scoring**: Uses `cardiffnlp/twitter-roberta-base-sentiment` alongside `medspaCy` clinical negation rules to prevent false positives (e.g., "no nausea" is NOT an adverse event).
6. **AE Rule Engine**: If `(Drug + Symptom + Negative Sentiment + Not Negated)` → Flags the post as an Adverse Event (AE) with a calculated confidence score.
7. **Signal Detection**: Calculates **Proportional Reporting Ratio (PRR)**, **Reporting Odds Ratio (ROR)**, and **Chi-Square (χ²)** statistics across the dataset. If thresholds are met (e.g., PRR ≥ 2, χ² ≥ 4), a high-confidence Pharmacovigilance Signal is generated.

### 5. The Presentation Layer (Polling UI)
- The dashboard polls the `/api/results/{project_id}` endpoint every 4 seconds.
- It renders live updates using Chart.js:
  - **AE Probability Gauge**: Percentage of processed posts flagged as adverse events.
  - **Sentiment Split**: Doughnut chart of positive/neutral/negative posts.
  - **Platform Breakdown**: Bar chart of data sources.
  - **Signal Strength Matrix**: Distribution of PRR and ROR scores per drug/symptom pair.

---

## 🚀 Quick Setup & Execution

For detailed commands, see `setup.txt` and `setup.md`. Here is the high-level summary:

### 1. Environment Configuration
Create a `.env` file based on `.env.example`. You must provide:
- `GROQ_API_KEY`: For the agentic crawler selection.
- `REDIS_URL`: An Upstash Redis connection string (`rediss://...`).
- `SECRET_KEY`: A secure random string for JWT auth.

### 2. Installation
We use `uv` for blazing-fast dependency management:
```bash
uv sync
uv run python -m spacy download en_core_web_sm
```

### 3. Running the Stack (3 Terminals)
You must run the web server and the background worker concurrently:

**Terminal 1: FastAPI Backend & UI**
```bash
uv run uvicorn main:app --reload --port 8000
```
*Access the UI at http://localhost:8000*

**Terminal 2: Celery Background Worker**
```bash
uv run celery -A celery_app worker --loglevel=info --pool=solo
```
*Note: `--pool=solo` is required on Windows systems.*

---

## 🛠️ Tech Stack Overview

- **Backend Framework**: FastAPI (Python 3.12)
- **Database (ORM)**: SQLAlchemy 2.0 with SQLite (Production ready for Postgres/Supabase)
- **Task Queue & Broker**: Celery + Upstash Redis (Cloud)
- **LLM Orchestration**: Groq API + Native Python Local Tool Calling
- **NLP Models**: HuggingFace Transformers, spaCy, medspaCy, NLTK/VADER
- **Frontend**: Vanilla HTML/CSS/JS (Zero-build), Chart.js
- **Package Manager**: `uv`

---

## 🔒 Security & Isolation Notes
- **JWT Authentication**: All API endpoints and the dashboard are secured via OAuth2 with Password Flow (JWT Bearer tokens).
- **Queue Isolation**: The Celery worker uses `task_default_queue="algopharma_ankur_queue"` to prevent cross-contamination if multiple developers share the same Upstash Redis database.
- **Process Isolation**: The Groq agent (`llm_module.py`) is spawned as an entirely separate subprocess via `api/chat.py` to prevent stdout/stderr log pollution from leaking into the clean FastAPI console.
