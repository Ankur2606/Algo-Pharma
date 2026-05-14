# ⬡ AlgoPharma: High-Fidelity Pharmacovigilance Intelligence

AlgoPharma is a state-of-the-art, agentic AI platform engineered for proactive, large-scale detection of Adverse Drug Events (ADEs). Unlike traditional keyword-matching systems, AlgoPharma deploys a highly decoupled, asynchronously scalable architecture that leverages dynamic LLM query routing, multi-stage PII neutralization, and strict clinical logic gates to extract verified pharmacovigilance signals from unstructured social media and regional forums.

## 🚀 Architectural Novelties & Technical Moats

Our system is defined by zero-to-one engineering breakthroughs that establish a deep technical moat for automated pharmacovigilance:

### 1. Agentic Forum Onboarding & MCP Dynamic Query Routing
- **Autonomous Crawler Generation**: Instead of manual scraping scripts, AlgoPharma utilizes **Nvidia Nemotron-3** via Firecrawl to autonomously analyze unknown forum structures and generate tailored CSS/JSON crawling configurations on the fly.
- **MCP-Driven Slot Filling**: The ingestion layer acts as a Model Context Protocol (MCP) router powered by **Groq (Llama 3.3 70B)**. It handles conversational state management across chat turns, performing low-latency slot-filling (identifying target drugs, symptoms, and data sources) to dynamically parameterize and dispatch Python crawling tasks without hardcoded logic.

### 2. Zero-Leakage 3-Layer PII Guard
Data security is embedded at the earliest stage. Before any unstructured text reaches an external LLM or translation API, it passes through a rigorous three-layer redaction funnel:
- **Layer 1: Indian-Specific Regex**: Instantly strips Aadhaar, PAN, UPI, phone numbers, and standard identifiers.
- **Layer 2: Localized Clinical NER**: Runs entirely locally using `OpenMed-PII-SuperClinical-Small-44M` (with an 82M variant for regional languages) to accurately scrub patient names, hospital locations, and personal health metadata.
- **Layer 3: Verification Check**: Ensures absolute anonymity, enabling HIPAA/GDPR-compliant processing of sensitive patient narratives without third-party exposure.

### 3. Cross-Lingual Clinical Translation
To capture adverse events across diverse demographics, AlgoPharma natively processes vernacular content.
- **Sarvam AI Integration**: Automatically intercepts regional Indian languages (Hindi, Tamil, Telugu, etc.) and translates them to context-accurate English using specialized Indic models. This ensures downstream NER and clinical gating operate on uniform, high-quality semantic representations.

### 4. 4-Gate Explainable Adverse Event (AE) Detection
We reject the "black-box" approach to signal detection. Our `ae_detector` enforces strict, explainable clinical logic gates:
1. **Drug Presence**: Verifies pharmaceutical entities via `OpenMed-NER-PharmaDetect-ModernClinical-149M`.
2. **Symptom/Disease Presence**: Confirms clinical manifestations via `OpenMed-NER-DiseaseDetect-SuperClinical-184M`.
3. **Sentiment Polarity**: Utilizes `cardiffnlp/twitter-roberta-base-sentiment` to confirm negative or distressing patient experiences.
4. **Negation Detection**: Applies `medspaCy` clinical rules to prevent false positives (e.g., explicitly dismissing "no nausea" as an AE).
*Crucially, any gate failure is explicitly logged with its reason, ensuring 100% auditability for regulatory compliance.*

### 5. Multi-Turn Thread Scoring
An isolated post is a data point; a corroborated thread is a signal.
- **Corroboration Matrix**: The `thread_scorer` mechanism evaluates the main post against all subsequent replies. It mathematically weighs corroborating symptoms against contradicting sentiment, synthesizing a final Confidence Score (0.0 to 1.0) and assigning a definitive RAG status (Red/Amber/Green) for the entire discussion thread.

### 6. Relational Risk Mapping & Asynchronous Scalability
- **Decoupled Architecture**: **FastAPI** handles high-throughput API requests while **Celery** workers (backed by Upstash Redis) asynchronously execute the heavy, multi-model NLP funnel. This prevents UI blocking and guarantees horizontal scalability.
- **Relational Risk Intelligence**: The frontend dashboard dynamically maps drug-symptom co-occurrence clusters. Medicines exhibiting high symptomatic density are instantly flagged with a "Relational Risk" metric, automatically surfacing emerging safety signals for priority review.

---

## 🏗️ Architecture & Data Flow

<img width="2048" height="2048" alt="image (3)" src="https://github.com/user-attachments/assets/98f75875-f0a2-45ba-afac-622ad124e966" />
<br>

*The interaction flow moves from the React/Vanilla JS Dashboard, through the FastAPI orchestration layer, into the Celery worker queue where the 7-stage NLP pipeline (PII Guard → Translation → NER → Sentiment → Negation → AE Gating → Thread Scoring) executes.*

---

## 🚀 Quick Setup & Execution

### 1. Environment Configuration
Create a `.env` file based on `.env.example`. You must provide:
- `GROQ_API_KEY`: For Llama 3.3 MCP routing.
- `NVIDIA_API_KEY`: For agentic forum structure analysis.
- `FIRECRAWL_API_KEY`: For the crawling engine.
- `SARVAM_API_KEY`: For regional translation.
- `REDIS_URL`: An Upstash Redis connection string (`rediss://...`).

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
*Access the UI at http://localhost:8000 or http://localhost:5173 for the React dev server*

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
- **LLM Orchestration**: Groq API + Nvidia Nemotron + Native Python Local Tool Calling
- **NLP Models**: HuggingFace Transformers, spaCy, medspaCy, NLTK/VADER, Sarvam AI, OpenMed
- **Frontend**: React (TSX) & Vanilla HTML/JS, Chart.js
- **Package Manager**: `uv`
