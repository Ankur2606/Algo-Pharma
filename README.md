# AlgoPharma
### Because side effects shouldn't be a social experiment.

> A real-time, MCP-native agentic platform for pharmacovigilance signal detection from social media and patient forums — built for India's PvPI reporting gap.

---

## Reddit API Compliance Statement

AlgoPharma uses the Reddit Data API strictly in accordance with Reddit's [Data API Terms](https://redditinc.com/policies/data-api-terms), [Developer Terms](https://redditinc.com/policies/developer-terms), and [Responsible Builder Policy](https://support.reddithelp.com/hc/en-us/articles/42728983564564-Responsible-Builder-Policy).

**Key compliance commitments:**

Reddit data is used for non-commercial academic pharmacovigilance research only. No Reddit content is used as input for training, fine-tuning, or updating any machine learning or AI model. BioBERT, RoBERTa, and medspaCy are pre-trained models on which AlgoPharma runs inference only — Reddit posts are never used to update model weights. All analysis is performed at the drug-symptom signal level, not the user level. No user profiles are built, no per-user health characteristics are inferred or stored, and author identifiers are discarded immediately after ingestion. All API access is authenticated via OAuth2, rate-limited to well within the 100 requests/minute free tier, and performed under a registered app with explicit API access approval from Reddit. No Reddit content is redistributed, sold, licensed, or displayed alongside advertisements.

---

## The Problem

India's PvPI (Pharmacovigilance Programme of India), coordinated by IPC under CDSCO, depends almost entirely on spontaneous Individual Case Safety Reports (ICSRs) submitted by healthcare professionals. The system is structurally sound but statistically hollow.

Only 6 to 10 percent of ADRs are actually reported in Indian healthcare settings. India contributes just 2 percent of total ICSRs to WHO VigiBase despite being one of the world's largest pharmaceutical markets. Over 55 percent of Indian health professionals remain unaware of PvPI's existence. Patients are writing detailed real-time symptom descriptions on Reddit, X, 1mg, and Practo — and nobody in any regulatory body is reading this at scale.

When Dolo 650 paracetamol was being overused during COVID-19, online communities were posting about nausea, liver discomfort, and overuse patterns weeks before a single formal ICSR reached IPC Ghaziabad. That signal existed. It just had no pipeline. AlgoPharma is that pipeline.

---

## What It Does

AlgoPharma is a two-part, MCP-native agentic platform:

**Part 1 — Data Acquisition Engine**
A configurable engine built on the `BaseEngine` abstraction. A drug safety officer defines drug names, MedDRA-aligned symptom keywords, source targets, and crawl frequency entirely through a Next.js 15 dashboard with zero code required.

**Part 2 — Clinical NLP Pipeline**
Every ingested post passes through a five-stage inference pipeline. Author identifiers are stripped at ingestion before any NLP step runs.

1. BioBERT NER — inference only, identifies drug and symptom entity mentions in post text
2. RoBERTa sentiment scoring — inference only, interprets colloquial patient language
3. medspaCy negation parsing — filters false positives such as "I did not feel nausea"
4. Rule-based AE classification — flags posts with co-located drug, symptom, and sentiment signals
5. Thread-level corroboration scoring — aggregates signal strength across multiple posts about the same drug-symptom pair

Output: structured, auditable adverse event signal records at the drug-symptom level, in PvPI-compatible format. No user-level records are produced at any stage.

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
│          Author Identifier Strip + Presidio Redaction        │
│   Username discarded · PAN · UPI · GSTIN · Aadhaar removed  │
│         No user-level data passes this boundary              │
└──────────────────────────┬──────────────────────────────────┘
                           │ Anonymised post text only
┌──────────────────────────▼──────────────────────────────────┐
│           5-Stage NLP Inference Pipeline                     │
│                                                              │
│  BioBERT NER → RoBERTa Sentiment → medspaCy Negation        │
│       → AE Classification → Thread Corroboration            │
│                                                              │
│     Pre-trained models · Inference only · No fine-tuning     │
│          Reddit data never updates model weights             │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│         Drug-Symptom Signal Confidence Scoring               │
│   AE Detection (60%) + Thread Corroboration (25%)           │
│                + Source Health (15%)                         │
│            Aggregated at drug-symptom level only             │
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
| 1. Config & Auth | JWT RBAC, Redis blacklisting, append-only audit logs for CDSCO compliance | FastAPI + PostgreSQL |
| 2. Data Acquisition | Standardized read-only extraction via BaseEngine | PRAW, twitterapi.io, Firecrawl MCP |
| 3. Anonymisation | Author identifier discard + Indian PII pattern redaction | Microsoft Presidio |
| 4. Biomedical NER | Drug-disease entity co-location via inference | BioBERT (BC5CDR, pre-trained) |
| 5. Sentiment Scoring | Colloquial patient language interpretation via inference | Twitter-roBERTa-base-sentiment (pre-trained) |
| 6. AE Classification | Negation-aware rule engine | medspaCy |
| 7. Signal Confidence | Weighted composite score at drug-symptom level | pgvector + custom formula |

---

## Signal Confidence Formula

```
Signal Confidence = (AE Detection × 0.60) + (Thread Corroboration × 0.25) + (Source Health × 0.15)

Source Health = f(
  crawler_success_rate_7d,
  volume_consistency (coefficient of variation),
  bot_ratio_estimate (account age and karma heuristics — aggregate quality weight only,
                      no individual user is profiled or stored),
  content_relevance (cosine similarity vs. ADR reference corpus in pgvector)
)
```

Note: bot ratio heuristics are applied solely as an aggregate source reliability weight. No individual user account is profiled, tracked, or stored at any point in the pipeline.

---

## Hero Feature: Agentic Source Onboarding

Every competing system — OpenVigil, VigiAccess, Veeva Vault Safety — requires an engineer to integrate a new data source. AlgoPharma does not.

A drug safety officer pastes any forum URL. A `claude-sonnet-4-20250514` agent then invokes the Firecrawl MCP server to fetch the fully-rendered page as clean markdown, analyzes the thread structure, generates a complete Python `ForumEngine` subclass with correct CSS selectors and pagination logic, validates it against three live thread URLs from the same forum, and surfaces three sample extracted posts for human review before activation. The entire flow completes in under two minutes.

When a forum updates its layout and extraction breaks, the fix is to paste the URL again.

**Why this matters for India specifically:** Regional patient communities including Tamil Nadu cancer support communities, Marathi diabetes groups, and Hindi-language health aggregators like Sehat.com currently produce zero structured input into PvPI. Firecrawl renders any JavaScript stack natively and Claude analyzes forum structure regardless of the regional language of the interface. These communities become monitorable within two minutes with no engineering involvement.

---

## Data Sources

| Source | Method | Access Type |
|--------|--------|------------|
| Reddit | PRAW via OAuth2, registered API access | Read-only, public posts only |
| X / Twitter | twitterapi.io filtered stream | Read-only, public posts only |
| Patient Forums | Firecrawl MCP + Claude agent | Read-only, public pages only |
| 1mg / Practo | Firecrawl MCP | Read-only, public pages only |

---

## Compliance

**Reddit Policy**
Reddit content is accessed under an approved non-commercial API registration. No Reddit data is used to train or fine-tune any model — all NLP processing uses pre-trained model inference only. No user-level health characteristics are inferred or stored. Author identifiers are discarded at the anonymisation layer before any NLP step. All access stays within the 100 requests/minute free tier. No Reddit content is redistributed or displayed alongside advertisements.

**DPDP Act 2023 (India)**
Presidio-based PII redaction at pipeline entry covers PAN, UPI, GSTIN, and Aadhaar patterns. The Firecrawl self-hosting option under AGPL-3.0 eliminates all external data egress for organisations with strict data residency requirements.

**MedDRA & PvPI**
Symptom keywords are mapped to MedDRA Preferred Terms. Structured output is compatible with IPC ICSR submission format. Signal records are exportable to WHO Uppsala Monitoring Centre VigiBase format.

---

## Tech Stack

```
Frontend        Next.js 15, TypeScript, Tailwind CSS
Backend         FastAPI (Python), PostgreSQL, Redis
ML/NLP          BioBERT (BC5CDR), Twitter-roBERTa, medspaCy — inference only, no fine-tuning
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
- Approved Reddit Data API access (register at [reddit.com/wiki/api](https://www.reddit.com/wiki/api))

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
alembic upgrade head
uvicorn main:app --reload

# Frontend (new terminal)
cd ../frontend
npm install
npm run dev
```

### Environment Variables

```env
# Reddit Data API (requires approved non-commercial access)
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

*AlgoPharma is a non-commercial pharmacovigilance research tool. It does not provide medical advice. All signals require validation by a qualified drug safety professional before submission to regulatory bodies. Reddit data is accessed under approved non-commercial API terms and is never used for model training.*
