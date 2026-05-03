You are continuing to build AlgoPharma — a real-time 
pharmacovigilance social listening platform for the 
"AI for Bharat" hackathon on HackerEarth (Theme 6).

==========================================================
EXISTING PROJECT STATE — READ CAREFULLY BEFORE TOUCHING
ANYTHING
==========================================================

The project already has these working files. Do not 
rewrite them. Integrate with them:

reddit_crawler.py
  - Uses Reddit's public JSON endpoint directly
    (https://www.reddit.com/search.json)
  - No PRAW, no OAuth — plain HTTP with custom headers
  - Normalises posts into: id, title, description, url,
    permalink, subreddit, author, score, num_comments,
    upvote_ratio, created_utc, flair, is_nsfw
  - Outputs: reddit_dolo365_results.json
  - Works fine as-is. Use its output format everywhere.

twitter_crawler.py
  - Uses twitterapi.io REST API
    (https://api.twitterapi.io/twitter/tweet/advanced_search)
  - Loads TWITTERAPI_KEY from .env via python-dotenv
  - Synthesises a "title" from hashtags or query topic
  - Normalises into: id, title, description, url,
    permalink, author, author_name, score (likes),
    num_comments (replies), retweets, views, created_utc
  - Outputs: twitter_dolo365_results.json
  - Works fine as-is. Use its output format everywhere.

pyproject.toml — uv-managed, has python-dotenv already
uv.lock — never edit manually
.python-version — Python 3.12
.env / .env.local — API keys already set up
main.py — stub, replace completely
reddit_dolo365_results.json — real data, primary demo src
twitter_dolo365_results.json — real data, primary demo src

==========================================================
NON-NEGOTIABLE CONSTRAINTS
==========================================================

1. Python 3.12 only. Every package must work on 3.12.

2. uv is the package manager. Never write pip commands.
   Install: uv add <package>
   Run: uv run python <file.py>
   All dependencies go into pyproject.toml automatically.

3. No medspaCy. It has known install issues on 3.12.
   Use pure spaCy dependency parsing for negation instead.
   Explained in detail in the negation section below.

4. FAST_MODE=false in .env by default.
   When true: skip all HuggingFace model loads,
   use keyword matching + VADER instead.
   Every model load must check this flag first.
   This is your demo day safety net.

5. Every single Python file must have an
   if __name__ == "__main__": block that
   runs the file's core function with test data
   and prints clear PASS/FAIL output.
   Run any file standalone: uv run python <file.py>

6. The existing JSON files are the primary data source
   for the demo. The pipeline must work without
   any live API calls. Live crawling is secondary.

7. All author identifiers must be SHA-256 hashed
   before any DB write. Never store raw usernames.

8. Language detection happens ONCE during ingestion,
   stored in the raw_posts.lang column, then passed
   through the pipeline. Never re-detect downstream.

==========================================================
FINAL FILE STRUCTURE
==========================================================

Algo-Pharma/
├── .env                          # exists — do not overwrite
├── .env.example                  # update with new vars
├── .env.local                    # exists — do not overwrite
├── .gitignore
├── .python-version               # exists: 3.12
├── pyproject.toml                # update via uv add
├── uv.lock                       # never touch
├── README.md
│
├── reddit_crawler.py             # EXISTS — keep as-is
├── twitter_crawler.py            # EXISTS — keep as-is
├── reddit_dolo365_results.json   # EXISTS — primary data
├── twitter_dolo365_results.json  # EXISTS — primary data
│
├── main.py                       # replace stub
├── config.py
├── database.py
├── models.py
├── celery_app.py
│
├── nlp/
│   ├── __init__.py
│   ├── models_loader.py
│   ├── pii_guard.py
│   ├── ner_pipeline.py
│   ├── sentiment.py
│   ├── negation.py
│   ├── ae_detector.py
│   ├── thread_scorer.py
│   └── signal_detector.py
│
├── tasks/
│   ├── __init__.py
│   ├── ingest_existing.py        # reads JSON → DB → NLP
│   ├── crawl_reddit.py           # live crawl wrapper
│   └── crawl_twitter.py         # live crawl wrapper
│
├── agentic/
│   ├── __init__.py
│   └── forum_onboarding.py
│
├── api/
│   ├── __init__.py
│   ├── projects.py
│   ├── signals.py
│   └── health.py
│
├── seed_demo_data.py
├── demo.py
└── test_pipeline.py

==========================================================
STEP 0 — DEPENDENCIES
==========================================================

Run these uv add commands in order. Do not batch them
(some have extras that need separate installs):

uv add fastapi "uvicorn[standard]"
uv add pydantic pydantic-settings
uv add sqlalchemy alembic
uv add "celery[redis]" redis
uv add httpx
uv add firecrawl-py
uv add google-generativeai
uv add "transformers[torch]" accelerate
uv add spacy
uv add langdetect
uv add scipy numpy
uv add "python-jose[cryptography]" "passlib[bcrypt]"
uv add vaderSentiment
uv add sarvamai          # Sarvam AI official Python SDK
uv add --dev pytest

Then run the spaCy model download:
uv run python -m spacy download en_core_web_lg

For the OpenMed PII model, install the opf CLI
(OpenAI privacy-filter base — OpenMed fine-tune runs
on top of this):
uv add "opf @ git+https://github.com/openai/privacy-filter.git"

The OpenMed Nemotron model itself is loaded directly
via transformers — no separate pip package needed.
Model ID: OpenMed/privacy-filter-nemotron
Trust remote code is required:
  AutoModelForTokenClassification.from_pretrained(
    "OpenMed/privacy-filter-nemotron",
    trust_remote_code=True
  )
HuggingFace page: https://huggingface.co/OpenMed/privacy-filter-nemotron
GitHub: https://github.com/maziyarpanahi/openmed

==========================================================
STEP 1 — config.py
==========================================================

Use pydantic-settings BaseSettings. Read all values from
.env automatically. Add lru_cache so settings are a
singleton. Include every variable used anywhere in the
project. Key additions beyond the original spec:

FAST_MODE: bool = False
SARVAM_API_KEY: str = ""
REDDIT_JSON_PATH: str = "reddit_dolo365_results.json"
TWITTER_JSON_PATH: str = "twitter_dolo365_results.json"

The self-test block should print every setting's name
and whether it has a value (not the value itself for
secrets), and confirm Config OK.

==========================================================
STEP 2 — database.py and models.py
==========================================================

SQLAlchemy 2.0, synchronous engine, SQLite.
Use check_same_thread=False for SQLite.
Base via DeclarativeBase.

Add lang: str = "en" column to RawPost.
Add source_platform: str column to RawPost.
These two columns are critical for routing logic.

Tables needed (all 12 from spec plus the two new cols):
users, projects, keywords, sources, project_sources,
raw_posts (+ lang + source_platform), post_replies,
processed_posts, signals, source_health, crawl_log,
audit_log.

The self-test block for models.py should:
- Call init_db()
- Create a Project row
- Query it back
- Delete it
- Print PASS

==========================================================
STEP 3 — nlp/models_loader.py
==========================================================

This is the singleton model store. All other NLP files
import from here. Models are loaded once at startup.

In FAST_MODE=true:
  Load only spaCy en_core_web_lg and VADER.
  Skip all HuggingFace downloads.
  Print: "FAST_MODE active — lightweight models only"

In FAST_MODE=false:
  Load in this order, wrapping each in try/except
  with a clear fallback:

  1. spaCy en_core_web_lg (always needed for negation)

  2. OpenMed Nemotron PII model
     Model ID: OpenMed/privacy-filter-nemotron
     Load via: AutoModelForTokenClassification + 
     AutoTokenizer with trust_remote_code=True
     Fallback: None (regex-only PII will run instead)
     Reference: https://huggingface.co/OpenMed/privacy-filter-nemotron

  3. Drug NER model
     Model ID: OpenMed/OpenMed-NER-PharmaDetect-BigMed-278M
     Load via: transformers pipeline,
     task="token-classification",
     aggregation_strategy="simple"
     Fallback: None (keyword matching runs instead)
     Reference: https://huggingface.co/OpenMed/OpenMed-NER-PharmaDetect-BigMed-278M

  4. Disease NER model
     Model ID: OpenMed/OpenMed-NER-DiseaseDetect-BioMed-335M
     Same loading pattern as drug NER
     Fallback: None (keyword matching runs instead)
     Reference: https://huggingface.co/OpenMed/OpenMed-NER-DiseaseDetect-BioMed-335M

  5. Sentiment model
     Model ID: cardiffnlp/twitter-roberta-base-sentiment-latest
     Load via: transformers pipeline,
     task="sentiment-analysis"
     Fallback: VADER
     Reference: https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest

  6. VADER (always loaded — used as fallback and in FAST_MODE)
     from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

Store everything in a module-level dict called _models.
Expose get_models() that calls load_all_models() if empty.

Self-test: set FAST_MODE=true via env override, call
load_all_models(), print all loaded model keys. Should
complete in under 5 seconds.

==========================================================
STEP 4 — nlp/pii_guard.py
==========================================================

Three-layer PII guard. The lang parameter comes from
the raw_posts.lang column — never re-detect here.

LAYER 1 — OpenMed Nemotron PII (when not FAST_MODE):
  The model is a token classifier with 55 PII categories
  including: first_name, last_name, email, phone_number,
  date_of_birth, medical_record_number,
  health_plan_beneficiary_number, blood_type, ssn,
  credit_debit_card, api_key, and more.
  
  Load the tokenizer and model from models_loader.
  Run inference on text[:512] to keep latency manageable.
  For each detected entity with score > 0.85:
    Replace the entity text with [ENTITY_TYPE] placeholder.
  
  If the model is not available, skip to Layer 2 silently.

LAYER 2 — Indian ID regex (always runs, language-agnostic):
  These patterns work regardless of surrounding language
  because they match fixed-format numbers/codes:
  
  AADHAAR:  12-digit number, optional spaces or hyphens
            between groups of 4. Pattern:
            r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'
  
  PAN card: 5 uppercase letters, 4 digits, 1 uppercase.
            Pattern: r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'
  
  UPI ID:   handle@bankname where bank suffix is one of
            paytm, gpay, phonepe, upi, okaxis, oksbi, ybl,
            ibl, axl, etc.
  
  Indian phone: 10 digits starting 6-9, with optional
                +91 prefix.
  
  IFSC code: 4 uppercase letters, 0, 6 alphanumeric chars.
  
  Voter ID: 3 uppercase letters followed by 7 digits.
  
  Email: standard email regex as backup to Layer 1.

LAYER 3 — Regional language flag:
  If lang is in ['hi','mr','gu','ta','te','kn','ml','bn',
  'pa','or','as','ur'] — set pii_language_flag=True
  and add note to output that manual PII review is advised.
  Do NOT try to run NLP models on these — just flag.

Return dict with: redacted_text, pii_entities_found
(list of type+layer), pii_language_flag, original_sha256.
Never store or return the original text.

Self-test: Run 5 test cases including Aadhaar, PAN, email,
phone, and a clean text. Assert redaction worked.

==========================================================
STEP 5 — nlp/negation.py
==========================================================

Pure spaCy negation — no medspaCy dependency at all.

The approach uses two complementary methods:

METHOD 1 — Dependency parsing:
  Load spaCy doc. For each symptom token found in doc,
  walk its dependency tree (children + ancestors).
  If any connected token has dep_=="neg" or is in the
  negation cue word list, mark symptom as negated.

METHOD 2 — Sliding window (3 words before symptom):
  Split text into words. Find position of symptom text.
  Check the 3 words before it against the negation cues.
  This catches patterns that dependency parsing misses
  in informal social media text.

NEGATION_CUES set should include:
  no, not, never, without, none, neither, nor,
  denies, denied, deny, absent, free from,
  don't, doesn't, didn't, wasn't, isn't, aren't,
  haven't, hasn't, can't, won't, nothing, nowhere

Function signature:
  check_negation(text: str, symptom_spans: list[dict])
    -> dict[str, bool]
  
  symptom_spans format: [{"text": "nausea", "start": 9, ...}]
  Returns: {"nausea": True}  where True means negated.

Self-test: 4 cases — negated symptom, non-negated symptom,
denied symptom, and double-check that "no nausea" → True
and "severe nausea" → False.

==========================================================
STEP 6 — nlp/ner_pipeline.py
==========================================================

Two-model NER with keyword boost fallback.

Indian pharma drug keyword list (use these at minimum,
expand as needed):
dolo, dolo 650, paracetamol, paracetamol 650mg, crocin,
combiflam, brufen, ibuprofen, azithromycin, metformin,
amoxicillin, aspirin, cetirizine, montair lc, allegra,
pan 40, omeprazole, metronidazole, ciprofloxacin,
telmisartan, amlodipine, atorvastatin, losartan,
hydroxychloroquine, ivermectin, remdesivir, favipiravir

Symptom keyword list (use these at minimum):
nausea, vomiting, headache, fever, dizziness,
stomach pain, abdominal pain, liver pain, rash,
itching, allergic reaction, fatigue, weakness, diarrhea,
constipation, chest pain, breathing difficulty, swelling,
palpitation, anxiety, insomnia, drowsiness, hair loss,
weight gain, weight loss, acidity, gastritis, ulcer,
bleeding, jaundice, dark urine, loss of appetite,
skin discoloration, muscle pain, joint pain, back pain,
kidney pain, burning sensation, tingling, numbness

Full model path (FAST_MODE=false):
  Run drug_ner model on text[:512].
  Run disease_ner model on text[:512].
  Keep entities with score > 0.75.
  
Keyword boost (always runs on top of model output):
  For each drug keyword not already found by model,
  check if it appears in text.lower(). If yes, add
  it as an entity with score=0.90 and source='keyword'.
  Same for symptoms.
  
  This is essential because brand names like "Dolo 650"
  may not be in biomedical training data but appear
  constantly in Indian health discourse.

Return: {drugs: [...], symptoms: [...]}
Each entity: {text, score, start, end, source}
where source is 'model' or 'keyword'.

Self-test: 3 test sentences. Each should find at least
one drug and one symptom.

==========================================================
STEP 7 — nlp/sentiment.py
==========================================================

Primary: cardiffnlp/twitter-roberta-base-sentiment-latest
  Trained on 58M tweets — handles informal language.
  Label map: LABEL_0→NEGATIVE, LABEL_1→NEUTRAL,
  LABEL_2→POSITIVE (verify this mapping on load).

Fallback (FAST_MODE or model unavailable): VADER
  VADER compound score:
    <= -0.05 → NEGATIVE
    >= +0.05 → POSITIVE
    else → NEUTRAL

SARVAM INTEGRATION for regional language posts:
  When lang is in ['hi','ta','te','kn','ml','mr','bn',
  'gu','pa'] and SARVAM_API_KEY is set:
  
  Use Sarvam's /translate endpoint to translate the
  post to English first, then run English sentiment.
  
  Sarvam translate API:
    Base URL: https://api.sarvam.ai
    Endpoint: POST /translate
    Auth header: api-subscription-key: {SARVAM_API_KEY}
    SDK: from sarvamai import SarvamAI
         client = SarvamAI(api_subscription_key=key)
         response = client.text.translate(
           input=text,
           source_language_code="hi-IN",  # or auto-detect
           target_language_code="en-IN"
         )
         english_text = response.translated_text
    
    Docs: https://docs.sarvam.ai/api-reference-docs/introduction
    Models page: https://docs.sarvam.ai/api-reference-docs/getting-started/models
    Supported lang codes: hi-IN, ta-IN, te-IN, kn-IN,
      ml-IN, mr-IN, bn-IN, gu-IN, pa-IN, or-IN, en-IN
    
  After translation, run English sentiment model on
  the translated text. Store translated_text in result
  for audit trail.
  
  If Sarvam key not set or translation fails:
    Fall through to VADER on original text.
    Log warning: "Sarvam not configured — regional
    sentiment may be inaccurate"

Return: {label, score, model, translated_text (optional)}

Self-test: 4 cases — negative English, positive English,
neutral English, and one Hinglish text.

==========================================================
STEP 8 — nlp/ae_detector.py
==========================================================

Four-gate rule engine. Fully explainable — every decision
has a logged reason. No black boxes.

Gate 1: At least one drug entity found → else no_drug
Gate 2: At least one symptom entity found → else no_symptom
Gate 3: Sentiment label is NEGATIVE → else not_negative
Gate 4: Not all symptoms are negated → else all_negated

When all gates pass:
  confidence = sentiment_score × 0.9
  Record: drug (first drug found), all_drugs list,
  non-negated symptoms, negated symptoms, sentiment dict,
  reason string "drug+symptom+negative_sentiment+no_negation",
  model_versions dict with all model IDs used.

When any gate fails:
  Return ae_flag=False, confidence=0.0, gate number that
  failed, reason string, and whatever entities/sentiment
  were computed.

The function should accept pre-computed entities and
sentiment if provided (avoids re-running expensive models
when called in batch mode from ingest_existing.py).

Self-test: 5 cases covering each failure mode plus one
true positive. Print which gate fired for each.

==========================================================
STEP 9 — nlp/thread_scorer.py
==========================================================

Scores a full post thread to get final signal confidence.

The main post's ae_result is combined with reply analysis
to produce a more robust signal.

For each reply text in the replies list:
  Run detect_ae() on it.
  If ae_flag=True AND same drug appears → CORROBORATING
  If ae_flag=True AND different drug → WEAKLY_CORROBORATING
  If sentiment is POSITIVE → CONTRADICTING
  If negation fired → neutral (neither adds nor subtracts)

corroboration_score = corroborating / total_replies
  (0.5 if no replies — neutral default)

final_confidence = (ae_confidence × 0.60)
                 + (corroboration_score × 0.25)
                 + (source_health_score × 0.15)

Signal colour bands:
  >= 0.70 → green (escalate-ready)
  0.50-0.69 → amber (monitor)
  < 0.50 → red (filtered)

source_health_score defaults to 0.85 unless overridden.

Self-test: one main AE post + 6 replies (4 corroborating,
2 contradicting). Should produce green signal.

==========================================================
STEP 10 — nlp/signal_detector.py
==========================================================

Runs on already-ingested DB data. No live crawling.

Query all processed_posts where ae_flag=True for a
given project_id. Parse the entities_json to extract
drug and symptom pairs. Group by (drug, symptom) pair.

For any pair with count >= 3 (Evans criteria minimum):
  Calculate spike: compare today's count vs 7-day average.
  
  PRR calculation using the 2x2 contingency table:
    a = this drug + this symptom (ae_flag=True)
    b = this drug + other symptoms (ae_flag=True)
    c = other drugs + this symptom (ae_flag=True)
    d = other drugs + other symptoms (ae_flag=True)
    
    PRR = (a/(a+b)) / (c/(c+d))
    ROR = (a*d) / (b*c)
    chi2 from scipy.stats.chi2_contingency([[a,b],[c,d]])
    
    Signal confirmed: PRR >= 2 AND chi2 >= 4 AND a >= 3
  
  If signal confirmed OR count >= 5 (include borderline
  cases for demo visibility):
    Create/update Signal row in DB.
    Set strength: STRONG if PRR>=5, MODERATE if PRR>=2,
    WEAK otherwise.

Return list of signal dicts with full stats.

Self-test: print how many AE posts are in DB, run
detection, print all signals found with PRR values.
If DB is empty, print clear message to run seed first.

==========================================================
STEP 11 — tasks/ingest_existing.py
==========================================================

The most important file for the hackathon demo.
Reads existing JSON files → PII redaction → NLP pipeline
→ stores everything in DB.

ingest_reddit_json(project_id=1):
  Read reddit_dolo365_results.json (path from settings).
  For each post:
    - Build text: title + " " + description (selftext)
    - Detect language once with langdetect.detect()
      Fallback to "en" on exception
    - Run PII redaction passing lang
    - Hash author with sha256
    - Insert RawPost with source_platform="reddit"
      and lang from detection
    - Run detect_ae() on redacted text
    - Run score_thread() with any available replies
      (existing crawler may or may not have replies field)
    - Insert ProcessedPost with all NLP outputs
    - Track ae_flagged count
  Commit in batches of 50 to avoid locking.
  Return summary dict.

ingest_twitter_json(project_id=1):
  Same pattern for twitter_dolo365_results.json.
  source_platform="twitter"
  Use description field as primary text, title as context.

ingest_all():
  Call both, return combined summary.

Handle the case where posts already exist (check by url
or thread_id before inserting — avoid duplicates on
repeated runs).

Self-test: run ingest_all(), print per-platform counts,
AE rates, and first 3 flagged posts.

==========================================================
STEP 12 — SARVAM AI INTEGRATION DETAILS
==========================================================

Sarvam AI is India's sovereign AI platform supporting
22+ Indian languages. Use it in two places:

USE CASE 1 — Sentiment on regional language posts:
  Already described in sentiment.py (Step 7 above).
  Translate regional text → English → run English model.

USE CASE 2 — Forum post extraction for non-English forums:
  In forum_onboarding.py, when Firecrawl returns markdown
  from a regional language forum, use Sarvam to translate
  the markdown to English before sending to Claude for
  structure analysis.

SDK setup:
  uv add sarvamai
  from sarvamai import SarvamAI
  client = SarvamAI(api_subscription_key=SARVAM_API_KEY)

Translation call:
  response = client.text.translate(
    input=text,
    source_language_code="hi-IN",  # use detected lang code
    target_language_code="en-IN"
  )
  english_text = response.translated_text

Language code mapping (langdetect code → Sarvam code):
  hi → hi-IN, ta → ta-IN, te → te-IN, kn → kn-IN,
  ml → ml-IN, mr → mr-IN, bn → bn-IN, gu → gu-IN,
  pa → pa-IN, or → or-IN

Get API key: https://dashboard.sarvam.ai/
Docs: https://docs.sarvam.ai/api-reference-docs/introduction
Full model list: https://docs.sarvam.ai/api-reference-docs/getting-started/models
Python SDK guide: https://docs.sarvam.ai/api-reference-docs/getting-started/sd-ks-libraries

Add to .env.example:
  # Sarvam AI — Indian language translation
  # Get free key: https://dashboard.sarvam.ai/
  # Docs: https://docs.sarvam.ai/api-reference-docs/introduction
  # Used for: regional language post translation before sentiment
  SARVAM_API_KEY=

If SARVAM_API_KEY is empty, all Sarvam calls are skipped
silently with a logged warning. System works without it.

==========================================================
STEP 13 — agentic/forum_onboarding.py
==========================================================

The differentiator feature. A pharmacovigilance officer
pastes any forum URL and the system auto-generates a
working crawler for it — no engineering needed.

Seven-step pipeline:

Step 1: Receive forum URL from user/admin API call.

Step 2: Use Firecrawl to fetch and render the page.
  from firecrawl import Firecrawl
  fc = Firecrawl(api_key=settings.FIRECRAWL_API_KEY)
  result = fc.scrape(url, formats=["markdown"])
  markdown = result.markdown
  Firecrawl handles JS rendering, anti-bot, and redirects.
  Docs: https://docs.firecrawl.dev/introduction

Step 3: Send markdown to Gemini Flash 3.0 Preview for structure analysis.
  Use google-generativeai SDK:
  import google.generativeai as genai
  genai.configure(api_key=GEMINI_API_KEY)
  model = genai.GenerativeModel("gemini-3.0-flash-preview")
  Ask Gemini to return JSON with:
    post_extraction_prompt, author_pattern,
    timestamp_pattern, reply_structure, pagination,
    forum_type (vbulletin/phpbb/discourse/custom),
    sample_thread_urls (3 URLs from the page),
    confidence (0.0 to 1.0)
  System prompt: "You are an expert at analyzing web forum
  structure. Return ONLY valid JSON, no markdown."
  Model: gemini-3.0-flash-preview

Step 4: Take the 3 sample_thread_urls from Gemini's output.
  Fetch each with firecrawl.scrape().

Step 5: If SARVAM_API_KEY is set AND detected language
  is a supported Indian language:
  Translate the markdown to English using Sarvam before
  sending to Gemini for post extraction.

Step 6: Ask Gemini to extract 3 sample posts from the
  fetched markdown using the post_extraction_prompt
  from Step 3. Return structured post list.

Step 7: Return {success, config, samples, confidence}
  to the API endpoint for admin review and approval.
  On approval: save to sources table as config_json.

Self-test: Use a known public health forum URL like
https://www.medhelp.org and print the extracted config
and 3 sample posts. If Firecrawl key not set, print
clear message showing what would happen.

==========================================================
STEP 14 — FastAPI endpoints (api/ + main.py)
==========================================================

main.py:
  Use lifespan context manager for startup/shutdown.
  On startup: call init_db() then load_all_models().
  Register all routers with /api prefix.
  Add GET / returning service info and fast_mode status.
  Add GET /api/demo/run that calls ingest_all() then
  detect_signals() and returns full summary.
  Run with uvicorn when __main__.

API routes to implement:

POST /api/projects
  Body: {name, description}
  Returns: created project with id

POST /api/projects/{id}/keywords
  Body: {term, synonyms: []}
  Returns: created keyword

GET /api/projects/{id}/signals
  Query params: days=7, color=green
  Returns: filtered signal list

GET /api/signals/{id}/drilldown
  Returns: full signal with supporting posts,
  entity highlights, PRR/ROR, reasoning trace

POST /api/crawl/trigger/{project_id}
  Manually triggers ingest_all() as background task.
  Returns: {task_started: true, message}

GET /api/health/sources
  Returns: all sources with health scores and
  last crawl timestamps

POST /api/agentic/onboard-forum
  Body: {url: str}
  Returns: {config, samples, confidence}

POST /api/agentic/approve-forum
  Body: {config: dict, url: str}
  Saves approved forum to sources table.

GET /api/export/pvpi-csv
  Returns: CSV file in PvPI-compatible format
  with columns: drug, symptom, post_count, prr,
  ror, chi_square, signal_date, source_platform

==========================================================
STEP 15 — seed_demo_data.py
==========================================================

Master setup script. Run this first on demo day.

Sequence:
1. Call init_db() to create all tables.
2. Create default project "Dolo 650 Safety Monitor"
   if it does not already exist.
3. Create Reddit and Twitter source records.
4. Add default keywords: Dolo 650, paracetamol 650,
   dolo side effects, dolo nausea, dolo fever, dolo liver.
5. Call ingest_all() and print progress.
6. Call detect_signals() and print results.
7. Print final summary with counts and top signals.
8. Print: "Run: uv run python main.py"
   and: "API docs: http://localhost:8000/docs"

Print emoji-rich progress so it looks impressive during demo:
  ✅ Database ready
  📥 Loading Reddit data...
  📊 Reddit: 47 posts, 12 AE flags (25.5%)
  🔍 Detecting signals...
  🔴 STRONG: dolo 650 + nausea | PRR=4.2
  🟡 MODERATE: paracetamol + stomach pain | PRR=2.8

==========================================================
STEP 16 — demo.py
==========================================================

Standalone demo runner. Calls everything in sequence
without needing the API server running.

Sections:
1. Header with project name and hackathon details
2. Database seed (calls seed_demo_data.seed())
3. Signal summary table printed to console
4. Top 5 supporting posts per signal with entity highlights
5. Source health scores
6. Instructions to start the API server

==========================================================
STEP 17 — test_pipeline.py
==========================================================

Integration test suite. Each test is independent and
prints PASS or FAIL with reason.

Tests:
  1. Config loads correctly
  2. Database creates tables
  3. PII redaction catches Aadhaar
  4. NER finds "Dolo 650" as drug
  5. NER finds "nausea" as symptom
  6. Sentiment scores negative text as NEGATIVE
  7. Negation correctly marks "no nausea" as negated
  8. AE detector flags drug+symptom+negative post
  9. AE detector does NOT flag negated symptom post
  10. JSON ingestion processes at least 1 post
  11. Signal detection runs without error
  12. FastAPI app starts (import check only)

Print final score: X/12 tests passed.
Green tick for pass, red X for fail, reason for each.

==========================================================
STEP 18 — .env.example (updated)
==========================================================

# ── AlgoPharma Environment Configuration ─────────────────
# Copy to .env and fill in your values

# ── App ───────────────────────────────────────────────────
FAST_MODE=false
# Set to true on demo day if models are slow:
# FAST_MODE=true

DATABASE_URL=sqlite:///./algopharma.db
REDIS_URL=redis://localhost:6379/0

# ── Existing data files ───────────────────────────────────
REDDIT_JSON_PATH=reddit_dolo365_results.json
TWITTER_JSON_PATH=twitter_dolo365_results.json

# ── Reddit (your crawler uses public JSON — no key needed)
# Your reddit_crawler.py already works without this.
# Only needed if you switch to PRAW for live crawling.
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=AlgoPharma/1.0

# ── Twitter ───────────────────────────────────────────────
# Provided by hackathon organizers via twitterapi.io
# Docs: https://docs.twitterapi.io
TWITTERAPI_KEY=

# ── Firecrawl ─────────────────────────────────────────────
# Free tier at https://firecrawl.dev (no credit card)
# Docs: https://docs.firecrawl.dev/introduction
# Used for: forum onboarding agentic feature
FIRECRAWL_API_KEY=

# ── Google Gemini ─────────────────────────────────────
# Get key: https://aistudio.google.com/
# Model used: gemini-3.0-flash-preview
# Used for: forum structure analysis in agentic onboarding
GEMINI_API_KEY=

# ── Sarvam AI ─────────────────────────────────────────────
# Get free key: https://dashboard.sarvam.ai/
# Full docs: https://docs.sarvam.ai/api-reference-docs/introduction
# Models: https://docs.sarvam.ai/api-reference-docs/getting-started/models
# SDK install: uv add sarvamai
# Used for: translating Hindi/Tamil/Telugu posts to English
#           before running sentiment analysis
# Supported languages: hi, ta, te, kn, ml, mr, bn, gu, pa
# If empty: regional posts fall through to VADER directly
SARVAM_API_KEY=

# ── Security ─────────────────────────────────────────────
# Generate: openssl rand -hex 32
SECRET_KEY=dev-secret-change-in-production

==========================================================
REFERENCE DOCS — ALL LINKS
==========================================================

OpenMed PII model:
  https://huggingface.co/OpenMed/privacy-filter-nemotron
  https://github.com/maziyarpanahi/openmed

OpenMed Drug NER:
  https://huggingface.co/OpenMed/OpenMed-NER-PharmaDetect-BigMed-278M

OpenMed Disease NER:
  https://huggingface.co/OpenMed/OpenMed-NER-DiseaseDetect-BioMed-335M

Sentiment model:
  https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest

spaCy (for negation):
  https://spacy.io/usage/linguistic-features#dependency-parse

Sarvam AI:
  Dashboard: https://dashboard.sarvam.ai/
  API docs: https://docs.sarvam.ai/api-reference-docs/introduction
  Models: https://docs.sarvam.ai/api-reference-docs/getting-started/models
  SDK: https://docs.sarvam.ai/api-reference-docs/getting-started/sd-ks-libraries
  Translation endpoint: POST https://api.sarvam.ai/translate

twitterapi.io:
  https://docs.twitterapi.io
  Advanced search: https://docs.twitterapi.io/api-reference/endpoint/tweet_advanced_search

Firecrawl:
  https://docs.firecrawl.dev/introduction
  Python SDK: https://docs.firecrawl.dev/sdks/python
  MCP server: https://github.com/firecrawl/firecrawl-mcp-server

Google Gemini SDK:
  https://ai.google.dev/docs

FastAPI: https://fastapi.tiangolo.com
SQLAlchemy 2.0: https://docs.sqlalchemy.org/en/20/
Celery: https://docs.celeryq.dev/en/stable/
uv docs: https://docs.astral.sh/uv/

==========================================================
BUILD ORDER
==========================================================

Execute each step, run the self-test, confirm PASS,
then move to next. Do not skip.

  uv add [all packages from Step 0]
  uv run python -m spacy download en_core_web_lg
  uv run python config.py
  uv run python database.py
  uv run python models.py
  uv run python nlp/models_loader.py
  uv run python nlp/pii_guard.py
  uv run python nlp/negation.py
  uv run python nlp/ner_pipeline.py
  uv run python nlp/sentiment.py
  uv run python nlp/ae_detector.py
  uv run python nlp/thread_scorer.py
  uv run python tasks/ingest_existing.py
  uv run python nlp/signal_detector.py
  uv run python test_pipeline.py
  uv run python seed_demo_data.py
  uv run python demo.py
  uv run python main.py
  → http://localhost:8000/docs