# AlgoPharma
### Because side effects shouldn't be a social experiment.

> A real-time, MCP-native agentic platform for pharmacovigilance signal detection from social media and patient forums built for PvPI reporting gap.

---

## Reddit API Compliance Statement

AlgoPharma uses the Reddit Data API in strict accordance with Reddit's [Data API Terms](https://redditinc.com/policies/data-api-terms), [Developer Terms](https://redditinc.com/policies/developer-terms), and [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy).

**Compliance commitments in effect:**

Reddit content is used solely for non-commercial academic pharmacovigilance research. No Reddit content is used to train, fine-tune, or update any machine learning or AI model — BioBERT, RoBERTa, and medspaCy are pre-trained public models on which AlgoPharma runs read-only inference. Reddit post embeddings are never stored in pgvector or any persistent store; only derived drug-symptom signal scores (which contain no Reddit text or identifiers) are retained. All API access is authenticated via OAuth2 under a registered, approved app and is rate-limited well within the free tier. Reddit content is never redistributed, sold, cached beyond immediate processing, or displayed alongside advertisements. When Reddit removes or modifies any post or User Content, AlgoPharma deletes the corresponding derived signal record from its database immediately upon detection or upon Reddit's written request, in accordance with Developer Terms Section 3.3. Reddit API credentials are stored exclusively in environment variables, never committed to source control, and are never shared with third parties. AlgoPharma does not process Reddit data for law enforcement, surveillance, or any purpose outside the stated pharmacovigilance research use case.

**Attribution:** Every signal record retains the original post's permalink and subreddit attribution, clearly indicating the source is Reddit, in compliance with Developer Terms Section 5.4. Usernames are stored only within the locked signal record for attribution traceability and are not used for profiling, analysis, or any secondary purpose.

---

## The Problem

India's PvPI (Pharmacovigilance Programme of India), coordinated by IPC under CDSCO, depends almost entirely on spontaneous Individual Case Safety Reports (ICSRs) submitted by healthcare professionals. The system is structurally sound but statistically hollow.

Only 6 to 10 percent of adverse drug reactions are actually reported in Indian healthcare settings. India contributes just 2 percent of total ICSRs to WHO VigiBase despite being one of the world's largest pharmaceutical markets. Over 55 percent of Indian health professionals remain unaware of PvPI's existence. Patients are writing detailed real-time symptom descriptions on Reddit, X, 1mg, and Practo — and nobody in any regulatory body is reading this at scale.

When Dolo 650 paracetamol was being overused during COVID-19, online communities were posting about nausea, liver discomfort, and overuse patterns weeks before a single formal ICSR reached IPC Ghaziabad. That signal existed. It just had no pipeline. AlgoPharma is that pipeline.

---

## What It Does

AlgoPharma is a two-part, MCP-native agentic platform:

**Part 1 — Data Acquisition Engine**
A configurable engine built on the `BaseEngine` abstraction. A drug safety officer defines drug names, MedDRA-aligned symptom keywords, source targets, and crawl frequency entirely through a Next.js 15 dashboard with zero code required.

**Part 2 — Clinical NLP Pipeline**
Every ingested post passes through a five-stage inference pipeline. Posts are processed in memory and are not stored raw. Only the derived drug-symptom signal output — containing no original Reddit text — is persisted.

1. BioBERT NER — inference only on post text in memory; identifies drug and symptom entity mentions
2. RoBERTa sentiment scoring — inference only; interprets colloquial patient language
3. medspaCy negation parsing — filters false positives such as "I did not feel nausea"
4. Rule-based AE classification — flags posts with co-located drug, symptom, and sentiment signals
5. Thread-level corroboration scoring — aggregates signal strength across multiple posts for the same drug-symptom pair

Output: a structured adverse event signal record containing drug name, symptom term (MedDRA-coded), confidence score, post permalink, subreddit, and date. No raw Reddit text is stored in any output record.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js 15 Dashboard                      │
│         (Drug config · Source management · Signal review)    │
└──────────────────────────┬──────────────────────────────────┘
                           │ MCP Tool Interface
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   PRAW (Reddit)    twitterapi.io        Firecrawl MCP
  OAuth2 · read-only
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    BaseEngine Layer                          │
│              (Standardized data acquisition)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │  Post text processed in memory only
                           │  Raw Reddit content is NEVER stored
┌──────────────────────────▼──────────────────────────────────┐
│           Presidio PII Redaction (in memory)                 │
│        PAN · UPI · GSTIN · Aadhaar patterns removed         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│           5-Stage NLP Inference Pipeline (in memory)         │
│                                                              │
│  BioBERT NER → RoBERTa Sentiment → medspaCy Negation        │
│       → AE Classification → Thread Corroboration            │
│                                                              │
│  Pre-trained public models · Inference only · No fine-tuning │
│  Reddit content never used to update any model weights       │
│  Post embeddings are never stored or persisted               │
└──────────────────────────┬──────────────────────────────────┘
                           │  Derived signal record only (no Reddit text)
┌──────────────────────────▼──────────────────────────────────┐
│              Signal Record (PostgreSQL)                      │
│                                                              │
│  drug_name · symptom_meddra · confidence_score              │
│  post_permalink · subreddit · date                          │
│                                                              │
│  No raw Reddit text · No user profiles                       │
│  Permalink retained for Reddit attribution (Dev Terms 5.4)   │
│  Deleted on Reddit content removal (Dev Terms 3.3)          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│            PvPI-Format ICSR Export                           │
│     Reviewed by drug safety officer before submission        │
└─────────────────────────────────────────────────────────────┘
```

---

## Seven Decoupled Layers

| Layer | Responsibility | Stack |
|-------|---------------|-------|
| 1. Config & Auth | JWT RBAC, Redis blacklisting, append-only audit logs for CDSCO compliance | FastAPI + PostgreSQL |
| 2. Data Acquisition | Read-only extraction via BaseEngine, OAuth2 authenticated | PRAW, twitterapi.io, Firecrawl MCP |
| 3. PII Redaction | In-memory Indian PII pattern removal before any processing | Microsoft Presidio |
| 4. Biomedical NER | Drug-disease entity detection via inference on in-memory text | BioBERT BC5CDR (pre-trained, public) |
| 5. Sentiment Scoring | Colloquial patient language interpretation via inference | Twitter-roBERTa-base-sentiment (pre-trained, public) |
| 6. AE Classification | Negation-aware rule engine | medspaCy |
| 7. Signal Confidence | Weighted composite score; only this output is persisted — no Reddit text | PostgreSQL + custom formula |

---

## Signal Confidence Formula

```
Signal Confidence = (AE Detection × 0.60) + (Thread Corroboration × 0.25) + (Source Health × 0.15)

Source Health = f(
  crawler_success_rate_7d,          ← operational metric only, no Reddit content
  volume_consistency (CV),          ← aggregate count metric, no user data
  bot_ratio_estimate,               ← derived from aggregate post-volume patterns,
                                       NOT from individual account metadata
  content_relevance                 ← cosine similarity computed in memory against
                                       a static ADR reference corpus; no Reddit
                                       embeddings are stored in pgvector
)
```

Signal records stored in the database contain only: drug name, MedDRA symptom term, confidence score, post permalink, subreddit name, and date. No Reddit text, no usernames, no embeddings.

---

## Hero Feature: Agentic Source Onboarding

Every competing system — OpenVigil, VigiAccess, Veeva Vault Safety — requires an engineer to integrate a new data source. AlgoPharma does not.

A drug safety officer pastes any patient forum URL. A `claude-sonnet-4-20250514` agent invokes the Firecrawl MCP server to fetch the page as clean markdown, analyzes thread structure, generates a Python `ForumEngine` subclass with correct selectors and pagination logic, validates it against three live thread URLs, and surfaces three sample extracted posts for human review before activation. The entire flow completes in under two minutes.

**Why this matters for India:** Regional patient communities — Tamil Nadu cancer support groups, Marathi diabetes communities, Hindi-language aggregators like Sehat.com — currently produce zero structured input into PvPI. These communities become monitorable in under two minutes with no engineering involvement.

---

## Data Sources

| Source | Method | Access Type |
|--------|--------|------------|
| Reddit | PRAW, OAuth2, approved API registration | Read-only, public posts, in-memory processing |
| X / Twitter | twitterapi.io filtered stream | Read-only, public posts |
| Patient Forums | Firecrawl MCP + Claude agent | Read-only, public pages |
| 1mg / Practo | Firecrawl MCP | Read-only, public pages |

---

## Compliance

**Reddit Developer Terms & Data API Terms**
Access is read-only under an approved non-commercial registration. Raw Reddit content is processed in memory only and never stored. No Reddit content is used to train or fine-tune any model. Post embeddings are never persisted. Signal records retain only the permalink and subreddit for attribution, as required by Developer Terms Section 5.4. If Reddit removes any content, the corresponding derived signal record is deleted, as required by Developer Terms Section 3.3. API credentials are stored in environment variables only. The app does not process Reddit data for surveillance or law enforcement purposes.

**DPDP Act 2023 (India)**
Presidio-based PII redaction runs in memory before any NLP step, covering PAN, UPI, GSTIN, and Aadhaar patterns. The Firecrawl self-hosting option under AGPL-3.0 eliminates all external data egress for organisations with strict data residency requirements.

**MedDRA & PvPI**
Symptom keywords are mapped to MedDRA Preferred Terms. Structured output is compatible with IPC ICSR submission format and exportable to WHO VigiBase format.

---

## Tech Stack

```
Frontend        Next.js 15, TypeScript, Tailwind CSS
Backend         FastAPI (Python), PostgreSQL, Redis
ML/NLP          BioBERT BC5CDR · Twitter-roBERTa · medspaCy
                All pre-trained public models · Inference only · No fine-tuning
                Reddit content never used to update model weights
Vector DB       pgvector for static ADR reference corpus only
                No Reddit post embeddings stored
MCP Servers     Firecrawl · PRAW · twitterapi.io
AI Agent        Anthropic claude-sonnet-4-20250514
Auth            JWT + RBAC + Redis token blacklisting
Privacy         Microsoft Presidio (custom Indian PII recognizers)
```

---

## Content Deletion Policy

In accordance with Reddit Developer Terms Section 3.3 and Data API Terms Section 6, AlgoPharma implements the following deletion behaviour. When Reddit removes, modifies, or withholds any post, AlgoPharma deletes the corresponding derived signal record from its database as soon as the change is detected via the API. When a user requests deletion of their content through Reddit, AlgoPharma deletes the linked signal record within 48 hours of being notified. Upon termination of API access, all derived signal records linked to Reddit content are permanently deleted.

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ with pgvector extension
- Redis 7+
- Approved Reddit Data API access — register at [reddit.com/wiki/api](https://www.reddit.com/wiki/api)

### Installation

```bash
git clone https://github.com/yourusername/algopharma.git
cd algopharma

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in credentials — never commit .env to source control
alembic upgrade head
uvicorn main:app --reload

# Frontend (new terminal)
cd ../frontend
npm install
npm run dev
```

### Environment Variables

```env
# Reddit Data API — approved non-commercial access required
# Never commit these values to source control
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=AlgoPharma/1.0 by /u/yourusername

# AI & MCP
ANTHROPIC_API_KEY=your_anthropic_key
FIRECRAWL_API_KEY=your_firecrawl_key

# Social
TWITTER_API_KEY=your_twitterapi_io_key

# Infrastructure
DATABASE_URL=postgresql://user:pass@localhost:5432/algopharma
REDIS_URL=redis://localhost:6379
SECRET_KEY=your_jwt_secret
```

---

## References

- Dong F et al. (2024). BERT-based language model for accurate drug adverse event extraction from social media. *Frontiers in Public Health* 12:1392180.
- Biseda B and Mo K (2020). Enhancing Drug Safety Surveillance with Drug Reviews and Social Media. *arXiv:2004.08731*.
- Singh P et al. (2023). Development of Pharmacovigilance System in India. *Current Drug Safety* 18(4):448–464.
- Lee J et al. (2020). BioBERT: a pre-trained biomedical language representation model. *Bioinformatics* 36(4):1234–1240.
- Evans SJW et al. (2001). Proportional reporting ratios for signal generation from spontaneous ADR reports. *Pharmacoepidemiology and Drug Safety* 10(6):483–486.
- Golder S et al. (2023). The role of social media for identifying adverse drug data in post-market surveillance. *JMIR Research Protocols* 12:e47068.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*AlgoPharma is a non-commercial pharmacovigilance research tool. It does not provide medical advice. All signals require review and validation by a qualified drug safety professional before submission to any regulatory body. Reddit data is accessed under approved non-commercial API terms, processed in memory only, and is never used for model training or persistent storage of raw content.*
