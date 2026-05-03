# AlgoPharma
### Because side effects shouldn't be a social experiment.

> A real-time, MCP-native agentic platform for pharmacovigilance signal detection from social media and patient forums — built for India's PvPI reporting gap.

---

## The Problem

India's PvPI (Pharmacovigilance Programme of India), coordinated by IPC under CDSCO, depends almost entirely on spontaneous Individual Case Safety Reports (ICSRs) submitted by healthcare professionals. The system is structurally sound but statistically hollow.

- Only **6–10%** of ADRs are actually reported in Indian healthcare settings
- India contributes just **2%** of total ICSRs to WHO VigiBase despite being one of the world's largest pharmaceutical markets
- Over **55%** of Indian health professionals remain unaware of PvPI's existence
- Patients are writing detailed real-time symptom descriptions on Reddit, X, 1mg, Practo — **nobody in any regulatory body is reading this at scale**

When Dolo 650 paracetamol was being overused during COVID-19, online communities were posting about nausea, liver discomfort, and overuse patterns **weeks before** a single formal ICSR reached IPC Ghaziabad. That signal existed. It just had no pipeline.

**AlgoPharma is that pipeline.**

---

## What It Does

AlgoPharma is a two-part, MCP-native agentic platform:

**Part 1 — Data Acquisition Engine**
A configurable engine built on the `BaseEngine` abstraction. A drug safety officer defines drug names, MedDRA-aligned symptom keywords, source targets, and crawl frequency entirely through a Next.js 15 dashboard — zero code required.

**Part 2 — Clinical NLP Pipeline**
Every ingested post passes through a five-stage pipeline:
1. BioBERT NER (drug-disease entity extraction)
2. RoBERTa sentiment scoring
3. medspaCy negation parsing
4. Rule-based AE classification
5. Thread-level corroboration scoring

Output: structured, auditable adverse event signal records in PvPI-compatible format.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js 15 Dashboard                      │
│         (Drug config · Source management · Alerts)          │
└──────────────────────────┬──────────────────────────────────┘
                           │ MCP Tool Interface
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   PRAW (Reddit)    twitterapi.io        Firecrawl MCP
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    BaseEngine Layer                          │
│              (Standardized data acquisition)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 Presidio PII/PHI Redaction                   │
│     (PAN · UPI · GSTIN · Aadhaar · Custom Indian patterns)  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  5-Stage NLP Pipeline                        │
│                                                              │
│  BioBERT NER → RoBERTa Sentiment → medspaCy Negation        │
│       → AE Classification → Thread Corroboration            │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              Signal Confidence Scoring                       │
│   AE Detection (60%) + Thread Corroboration (25%)           │
│                + Source Health (15%)                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│            PvPI-Format ICSR Export                           │
│        (One-click submission to IPC Ghaziabad)               │
└─────────────────────────────────────────────────────────────┘
```

---

## Seven Decoupled Layers

| Layer | Responsibility | Stack |
|-------|---------------|-------|
| 1. Config & Auth | JWT RBAC, Redis blacklisting, audit logs | FastAPI + PostgreSQL |
| 2. Data Acquisition | Standardized extraction via BaseEngine | PRAW, twitterapi.io, Firecrawl MCP |
| 3. PII/PHI Redaction | Indian identifier patterns | Microsoft Presidio |
| 4. Biomedical NER | Drug-disease entity co-location | BioBERT (BC5CDR fine-tuned) |
| 5. Sentiment Scoring | Colloquial patient language | Twitter-roBERTa-base-sentiment |
| 6. AE Classification | Negation-aware rule engine | medspaCy |
| 7. Signal Confidence | Weighted composite score | pgvector + custom formula |

---

## Signal Confidence Formula

```
Signal Confidence = (AE Detection × 0.60) + (Thread Corroboration × 0.25) + (Source Health × 0.15)

Source Health = f(
  crawler_success_rate_7d,
  volume_consistency (CV),
  bot_ratio_estimate (karma + account age heuristics),
  content_relevance (cosine similarity vs. ADR reference corpus in pgvector)
)
```

---

## Hero Feature: Agentic Source Onboarding

Every competing system — OpenVigil, VigiAccess, Veeva Vault Safety — requires an **engineer** to integrate a new data source.

**AlgoPharma does not.**

A drug safety officer pastes any forum URL. A `claude-sonnet-4-20250514` agent:
1. Invokes Firecrawl MCP to fetch the fully-rendered page as clean markdown
2. Analyzes thread structure and pagination patterns
3. Generates a complete Python `ForumEngine` subclass with correct CSS selectors
4. Validates against 3 live thread URLs from the same forum
5. Surfaces 3 sample extracted posts for human review before activation

**Total time: under 2 minutes. No engineer required.**

When a forum updates its layout and extraction breaks — paste the URL again.

### Why This Matters for India

Regional patient communities currently produce **zero** structured input into PvPI:
- Tamil Nadu cancer support communities
- Marathi diabetes groups on Facebook
- Hindi-language health aggregators like Sehat.com

Firecrawl renders any JavaScript stack natively. Claude analyzes forum structure regardless of regional language. These communities become monitorable in 2 minutes.

---

## Data Sources

| Source | Method | Coverage |
|--------|--------|----------|
| Reddit | PRAW (OAuth2) | r/india, r/pharmacy, r/medicine, global health subs |
| X / Twitter | twitterapi.io filtered stream | Real-time keyword stream |
| Patient Forums | Firecrawl MCP + Claude agent | Any JS-rendered forum, any language |
| 1mg / Practo | Firecrawl MCP | Indian health communities |

---

## Compliance

- **DPDP Act 2023** — Presidio-based PII redaction at pipeline entry point
- **Data residency** — Firecrawl self-hosting option under AGPL-3.0 eliminates external data egress
- **MedDRA coding** — Symptom keywords mapped to MedDRA Preferred Terms
- **PvPI export schema** — Structured output compatible with IPC ICSR submission format
- **WHO VigiBase** — Signal records exportable to Uppsala Monitoring Centre format

---

## Tech Stack

```
Frontend        Next.js 15, TypeScript, Tailwind CSS
Backend         FastAPI (Python), PostgreSQL, Redis
ML/NLP          BioBERT (BC5CDR), Twitter-roBERTa, medspaCy, HuggingFace
Vector DB       pgvector (ADR reference corpus)
MCP Servers     Firecrawl, PRAW, twitterapi.io
AI Agent        Anthropic claude-sonnet-4-20250514
Auth            JWT + RBAC + Redis token blacklisting
Privacy         Microsoft Presidio (custom Indian recognizers)
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ with pgvector extension
- Redis 7+

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/algopharma.git
cd algopharma

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Fill in: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, ANTHROPIC_API_KEY,
#          TWITTER_API_KEY, FIRECRAWL_API_KEY, DATABASE_URL, REDIS_URL

# Run database migrations
alembic upgrade head

# Start backend
uvicorn main:app --reload

# Frontend setup (new terminal)
cd ../frontend
npm install
npm run dev
```

### Environment Variables

```env
# Reddit Data API
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

*AlgoPharma is a pharmacovigilance research tool. It does not provide medical advice. All signals require validation by a qualified drug safety professional before submission to regulatory bodies.*
