"""
AlgoPharma — Full End-to-End Demo Pipeline
============================================
Crawls 3 sources (Reddit, Twitter, Indian health forum),
then runs the complete NLP pipeline on each post:

  1. PII Guard     (redact personal information)
  2. NER Pipeline  (extract drugs + symptoms)
  3. Negation      (check if symptoms are negated)
  4. Sentiment     (classify text tone)
  5. AE Detector   (4-gate Adverse Event decision)

All input/output of every step is shown in console AND
written to logs/demo_pipeline_<timestamp>.log

Usage:
  uv run python demo_pipeline.py
  uv run python demo_pipeline.py --fast        # skip heavy NLP models
  uv run python demo_pipeline.py --posts 3     # how many posts per source to process
"""

import sys
import os
import re
import json
import logging
import urllib.request
import urllib.parse
import argparse
from datetime import datetime
from pathlib import Path

# ── Encoding fix for Windows terminal ─────────────────────
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

# ── Add project root to path ────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

# ── Args ───────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="AlgoPharma full demo pipeline")
parser.add_argument("--fast",  action="store_true", help="Use FAST_MODE (no heavy models)")
parser.add_argument("--posts", type=int, default=3, help="Max posts to process per source (default: 3)")
args = parser.parse_args()

if args.fast:
    os.environ["FAST_MODE"] = "true"
else:
    os.environ["FAST_MODE"] = "false"

# ── Logging setup (console + file) ─────────────────────────
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"demo_pipeline_{ts}.log"
RAW_LOG_FILE = LOG_DIR / f"demo_pipeline_{ts}_output.txt"

log_format = "%(asctime)s | %(levelname)-7s | %(name)-20s | %(message)s"
date_fmt = "%H:%M:%S"

# Root logger
logging.basicConfig(
    level=logging.DEBUG,
    format=log_format,
    datefmt=date_fmt,
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)

# Console handler — INFO+ only (we handle pretty-print ourselves)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_fmt))
logging.getLogger().addHandler(console_handler)

# Silence noisy third-party libraries
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("filelock").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger("demo_pipeline")

# ── Pretty-print helpers ───────────────────────────────────
DIVIDER = "─" * 70
SECTION  = "═" * 70

def print_and_log(msg: str, level: str = "info"):
    print(msg)
    # Also write raw output to the .txt file
    with open(RAW_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    getattr(logger, level)(msg)


def section(title: str):
    print_and_log("")
    print_and_log(SECTION)
    print_and_log(f"  {title}")
    print_and_log(SECTION)


def subsection(title: str):
    print_and_log("")
    print_and_log(f"  ── {title} {'─' * max(0, 55 - len(title))}")


def step_log(step: str, input_val: str, output_val: str):
    """Log a pipeline step with its full input and output (no trimming)."""
    block = f"""
┌─[STEP: {step}]
│  IN  → {input_val}
│  OUT → {output_val}
└{'─' * 60}"""
    print_and_log(block)
    logger.debug(f"[{step}] INPUT={input_val!r}")
    logger.debug(f"[{step}] OUTPUT={output_val!r}")


# ── Forum Crawler (Indian health forum via Firecrawl) ──────
def crawl_forum(query: str, max_posts: int) -> list[dict]:
    """
    Scrape 1mg.com Dolo-650 product Q&A page via Firecrawl.
    Falls back to realistic mock data if API not available.
    """
    from dotenv import load_dotenv
    load_dotenv()
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY", "")

    # Target a specific 1mg product page that has real user Q&A text
    target_url = "https://www.myupchar.com/medicine/dub-obsurge-p37086347"

    subsection("Forum Crawler — 1mg.com Q&A (Firecrawl)")
    print_and_log(f"  Query    : {query}")
    print_and_log(f"  Target   : {target_url}")
    logger.info(f"[forum_crawler] Starting crawl | url='{target_url}'")

    # ── Rich mock data — realistic Indian pharma forum posts ──
    MOCK_POSTS = [
        {
            "id": "forum_001",
            "title": "Dolo 650 causing severe dizziness and nausea after 3 days",
            "description": "I have been taking Dolo 650 for 3 days for viral fever. Since yesterday I am experiencing severe dizziness and nausea every time I take it. My stomach is also hurting badly. Should I stop the medicine?",
            "url": "https://www.1mg.com/drugs/dolo-650-tablet-88505#qa",
            "source": "1mg_forum",
        },
        {
            "id": "forum_002",
            "title": "Paracetamol 500mg stomach pain aur vomiting",
            "description": "Mere doctor ne paracetamol 500mg likh di thi fever ke liye. Iske baad se mujhe bahut stomach pain aur vomiting ho rahi hai. Kya ye side effect hai ya kuch aur problem hai?",
            "url": "https://www.1mg.com/drugs/paracetamol-500mg#qa",
            "source": "1mg_forum",
        },
        {
            "id": "forum_003",
            "title": "Ibuprofen skin rash and facial swelling — emergency",
            "description": "After taking ibuprofen 400mg tablet I developed a severe itchy skin rash all over my body and my face started swelling up. I had breathing difficulty and had to go to emergency room. Has anyone experienced this allergic reaction?",
            "url": "https://www.1mg.com/drugs/ibuprofen-400mg#qa",
            "source": "1mg_forum",
        },
        {
            "id": "forum_004",
            "title": "Combiflam gave me liver pain and jaundice symptoms",
            "description": "I took combiflam for 5 days for joint pain. Now I have liver pain, my urine is dark yellow, and my skin looks slightly yellow. Doctor said it could be drug-induced liver injury. Very scared.",
            "url": "https://www.1mg.com/drugs/combiflam#qa",
            "source": "1mg_forum",
        },
        {
            "id": "forum_005",
            "title": "No side effects from Dolo 650 — very effective",
            "description": "I took Dolo 650 for my high fever last week. It worked very well, my fever came down within 30 minutes. I did not experience any nausea or headache. Great medicine, highly recommend it.",
            "url": "https://www.1mg.com/drugs/dolo-650-tablet-88505#reviews",
            "source": "1mg_forum",
        },
    ]

    posts = []

    if not firecrawl_key:
        print_and_log("  ⚠️  FIRECRAWL_API_KEY not set — using realistic mock forum data")
        logger.warning("[forum_crawler] No Firecrawl key — using mock data")
        posts = MOCK_POSTS[:max_posts]
        print_and_log(f"  ✅ Loaded {len(posts)} mock forum posts (1mg Q&A style)")
        logger.info(f"[forum_crawler] Loaded {len(posts)} mock posts")
        return posts

    # Real Firecrawl request
    try:
        api_url = "https://api.firecrawl.dev/v1/scrape"
        payload = json.dumps({
            "url": target_url,
            "formats": ["markdown"],
            "onlyMainContent": True,
        }).encode("utf-8")
        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={
                "Authorization": f"Bearer {firecrawl_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        markdown = result.get("data", {}).get("markdown", "")
        logger.debug(f"[forum_crawler] Firecrawl markdown preview: {markdown[:500]!r}")

        # Extract Q&A paragraphs: lines > 80 chars that don't look like navigation
        nav_skip = {"[", "http", "menu", "search", "login", "cart", "©"}
        lines = [
            l.strip() for l in markdown.split("\n")
            if len(l.strip()) > 80
            and not any(l.strip().lower().startswith(skip) for skip in nav_skip)
        ]

        if lines:
            for i, line in enumerate(lines[:max_posts]):
                posts.append({
                    "id": f"forum_fc_{i:03d}",
                    "title": f"1mg User Review #{i+1}",
                    "description": line,
                    "url": target_url,
                    "source": "1mg_firecrawl",
                })
            print_and_log(f"  ✅ Scraped {len(posts)} content blocks from 1mg.com via Firecrawl")
            logger.info(f"[forum_crawler] Scraped {len(posts)} real posts")
        else:
            raise ValueError("No usable content lines found in Firecrawl response")

    except Exception as e:
        print_and_log(f"  ⚠️  Firecrawl returned unusable content ({e}) — using mock data")
        logger.warning(f"[forum_crawler] Firecrawl failed: {e} — falling back to mock")
        posts = MOCK_POSTS[:max_posts]

    return posts


# ── Reddit Crawler ─────────────────────────────────────────
def crawl_reddit(query: str, max_posts: int) -> list[dict]:
    from reddit_crawler import scrape_reddit

    subsection(f"Reddit Crawler — query: '{query}'")
    logger.info(f"[reddit_crawler] Starting | query='{query}' | max={max_posts}")
    print_and_log(f"  Fetching up to {max_posts} posts from Reddit API...")

    posts = scrape_reddit(query, max_items=max_posts)

    # Filter to posts that have actual text content
    posts = [p for p in posts if p.get("description") and len(str(p["description"])) > 30][:max_posts]

    print_and_log(f"  ✅ Got {len(posts)} posts with text content")
    logger.info(f"[reddit_crawler] Returned {len(posts)} usable posts")
    return posts


# ── Twitter Crawler ────────────────────────────────────────
def crawl_twitter(query: str, max_posts: int) -> list[dict]:
    from twitter_crawler import scrape_twitter

    subsection(f"Twitter Crawler — query: '{query}'")
    logger.info(f"[twitter_crawler] Starting | query='{query}' | max={max_posts}")
    print_and_log(f"  Fetching up to {max_posts} tweets from twitterapi.io...")

    posts = scrape_twitter(query, query_type="Top")
    posts = [p for p in posts if p.get("description") and len(str(p["description"])) > 20][:max_posts]

    print_and_log(f"  ✅ Got {len(posts)} tweets with text content")
    logger.info(f"[twitter_crawler] Returned {len(posts)} usable tweets")
    return posts


# ── Language detection helper ──────────────────────────────
def detect_language(text: str) -> str:
    """
    Detect language of text. Returns ISO 639-1 code.
    Uses langdetect if available, else heuristic Unicode check.
    """
    # Heuristic: check for Devanagari (Hindi/Marathi), Telugu, Tamil scripts
    if re.search(r'[\u0900-\u097F]', text):  # Devanagari
        return "hi"
    if re.search(r'[\u0C00-\u0C7F]', text):  # Telugu
        return "te"
    if re.search(r'[\u0B80-\u0BFF]', text):  # Tamil
        return "ta"
    if re.search(r'[\u0C80-\u0CFF]', text):  # Kannada
        return "kn"
    if re.search(r'[\u0900-\u097F]', text):  # Hindi again (broader)
        return "hi"
    try:
        from langdetect import detect
        lang = detect(text)
        return lang if lang else "en"
    except Exception:
        pass
    return "en"


# ── Sarvam translation helper ──────────────────────────────
def translate_to_english(text: str, lang: str) -> str:
    """
    Translate regional Indian language text to English using Sarvam AI.
    Falls back to original text if API is unavailable.
    """
    import urllib.request
    import json
    from dotenv import load_dotenv
    load_dotenv()

    sarvam_key = os.getenv("SARVAM_API_KEY", "")
    sarvam_lang_map = {
        "hi": "hi-IN", "ta": "ta-IN", "te": "te-IN", "kn": "kn-IN",
        "ml": "ml-IN", "mr": "mr-IN", "bn": "bn-IN", "gu": "gu-IN",
    }

    if not sarvam_key or lang not in sarvam_lang_map:
        return text

    try:
        payload = json.dumps({
            "input": text[:500],
            "source_language_code": sarvam_lang_map[lang],
            "target_language_code": "en-IN",
            "model": "mayura:v1",
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.sarvam.ai/translate",
            data=payload,
            headers={
                "api-subscription-key": sarvam_key,
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        translated = result.get("translated_text", text)
        logger.info(f"[sarvam] Translated from {lang}: '{text[:60]}' → '{translated[:60]}'")
        return translated
    except Exception as e:
        logger.warning(f"[sarvam] Translation failed ({e}) — using original text")
        return text


# ── NLP Pipeline for one post ──────────────────────────────
def run_nlp_pipeline(post: dict, source: str, post_idx: int) -> dict:
    """
    Run the full NLP pipeline on a single post.
    Returns a dict with all intermediate + final results.
    """
    from nlp.pii_guard import redact_pii
    from nlp.ner_pipeline import extract_entities
    from nlp.negation import check_negation
    from nlp.sentiment import analyze_sentiment
    from nlp.ae_detector import detect_ae

    raw_text = str(post.get("description") or post.get("title") or "").strip()
    if not raw_text:
        return {}

    print_and_log(f"\n  {'─' * 65}")
    print_and_log(f"  [{source.upper()} #{post_idx+1}] {post.get('title', 'No Title')}")
    print_and_log(f"  {'─' * 65}")
    print_and_log(f"  URL: {post.get('url', 'N/A')}")

    logger.info(f"[pipeline] Processing post [{source}#{post_idx}] len={len(raw_text)}")
    logger.debug(f"[pipeline] RAW TEXT: {raw_text!r}")

    result = {
        "source": source,
        "post_id": post.get("id", ""),
        "url": post.get("url", ""),
        "raw_text": raw_text,
    }

    # ── Step 0: Language Detection + Translation ───────────
    print_and_log("\n  📍 Step 0: Language Detection & Translation")
    detected_lang = detect_language(raw_text)
    print_and_log(f"     Detected Language : {detected_lang}")
    logger.info(f"[pipeline] Language detected: {detected_lang}")

    processing_text = raw_text
    if detected_lang != "en":
        print_and_log(f"     Translating from '{detected_lang}' → English via Sarvam AI...")
        translated = translate_to_english(raw_text, detected_lang)
        step_log("Language+Translation",
                 f"lang={detected_lang} | original='{raw_text}'",
                 f"translated='{translated}'")
        print_and_log(f"     Original   : {raw_text}")
        print_and_log(f"     Translated : {translated}")
        processing_text = translated
    else:
        print_and_log(f"     Language is English — no translation needed")
        step_log("Language Detection", f"text='{raw_text}'" , f"lang=en — no translation")
    result["detected_lang"] = detected_lang
    result["processing_text"] = processing_text

    # ── Step 1: PII Guard ──────────────────────────────────
    print_and_log("\n  📍 Step 1: PII Guard")
    pii_result = redact_pii(processing_text, lang=detected_lang)
    redacted_text = pii_result["redacted_text"]
    pii_found = pii_result["pii_entities_found"]

    step_log("PII Guard",
             f"text='{processing_text}'",
             f"redacted='{redacted_text}' | entities={[e['type'] for e in pii_found]}")

    print_and_log(f"     Input  : {processing_text}")
    print_and_log(f"     Output : {redacted_text}")
    if pii_found:
        types = [e['type'] for e in pii_found if e.get('layer') != 3]
        print_and_log(f"     PII    : {types if types else 'none detected'}")
    else:
        print_and_log("     PII    : none detected")
    result["pii"] = {"redacted_text": redacted_text, "entities": pii_found}

    # ── Step 2: NER Pipeline ───────────────────────────────
    print_and_log("\n  📍 Step 2: NER — Drug & Symptom Extraction")
    entities = extract_entities(redacted_text)
    drugs    = [d["text"] for d in entities.get("drugs", [])]
    symptoms = [s["text"] for s in entities.get("symptoms", [])]

    step_log("NER Pipeline",
             f"text='{redacted_text}'",
             f"drugs={drugs} | symptoms={symptoms}")

    print_and_log(f"     Input  : {redacted_text}")
    print_and_log(f"     Drugs  : {drugs if drugs else '[]'}")
    print_and_log(f"     Sympts : {symptoms if symptoms else '[]'}")
    result["entities"] = entities

    # ── Step 3: Negation ───────────────────────────────────
    print_and_log("\n  📍 Step 3: Negation Detection")
    neg_result = {}
    if entities.get("symptoms"):
        neg_result = check_negation(redacted_text, entities["symptoms"])
        negated     = [k for k, v in neg_result.items() if v]
        not_negated = [k for k, v in neg_result.items() if not v]

        step_log("Negation",
                 f"symptoms={symptoms}",
                 f"negated={negated} | active={not_negated}")

        print_and_log(f"     Input  : symptoms={symptoms}")
        print_and_log(f"     Active : {not_negated if not_negated else '[]'}")
        print_and_log(f"     Negated: {negated if negated else '[]'}")
    else:
        print_and_log("     Skipped (no symptoms found)")
    result["negation"] = neg_result

    # ── Step 4: Sentiment ──────────────────────────────────
    print_and_log("\n  📍 Step 4: Sentiment Analysis")
    # Always run sentiment on English text (post-translation)
    sentiment = analyze_sentiment(redacted_text, lang="en")

    step_log("Sentiment",
             f"text='{redacted_text}'",
             f"label={sentiment['label']} | score={sentiment['score']:.3f} | model={sentiment['model']}")

    emoji_map = {"NEGATIVE": "🔴", "POSITIVE": "🟢", "NEUTRAL": "🟡"}
    emoji = emoji_map.get(sentiment["label"], "⚪")
    print_and_log(f"     Input  : {redacted_text}")
    print_and_log(f"     Result : {emoji} {sentiment['label']} (score={sentiment['score']:.3f})")
    print_and_log(f"     Model  : {sentiment['model']}")
    result["sentiment"] = sentiment

    # ── Step 5: AE Detector ────────────────────────────────
    print_and_log("\n  📍 Step 5: Adverse Event Detection")
    ae = detect_ae(redacted_text, entities=entities, sentiment=sentiment)

    gate_info = f"gate {ae['gate_failed']} failed" if ae["gate_failed"] else "ALL 4 GATES PASSED"
    step_log("AE Detector",
             f"drugs={[d['text'] for d in entities.get('drugs',[])]} | symptoms={symptoms} | sentiment={sentiment['label']}",
             f"ae_flag={ae['ae_flag']} | conf={ae['confidence']} | reason={ae['reason']}")

    if ae["ae_flag"]:
        print_and_log(f"     🚨 ADVERSE EVENT DETECTED")
        print_and_log(f"     Drug        : {ae['drug']}")
        print_and_log(f"     Symptoms    : {ae['symptoms_non_negated']}")
        print_and_log(f"     Confidence  : {ae['confidence']:.3f}")
    else:
        print_and_log(f"     ✅ No AE — {gate_info}")
        print_and_log(f"     Reason      : {ae['reason']}")
    result["ae"] = ae

    logger.info(
        f"[pipeline] POST DONE [{source}#{post_idx}] "
        f"ae={ae['ae_flag']} drug={ae.get('drug')} "
        f"symptoms={ae.get('symptoms_non_negated')} conf={ae.get('confidence')}"
    )

    return result


# ── Main ───────────────────────────────────────────────────
def main():
    start_time = datetime.now()
    DRUG_QUERY = "dolo 650 paracetamol side effects"
    N = args.posts

    section("AlgoPharma — Full Pipeline Demo")
    print_and_log(f"  Query      : '{DRUG_QUERY}'")
    print_and_log(f"  Posts/src  : {N}")
    print_and_log(f"  FAST_MODE  : {os.getenv('FAST_MODE', 'false')}")
    print_and_log(f"  Log file   : {LOG_FILE}")
    print_and_log(f"  Start time : {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    logger.info(f"=== AlgoPharma Demo Pipeline START | query='{DRUG_QUERY}' | posts={N} ===")

    # ── Load NLP models ONCE upfront ──────────────────────
    section("Phase 1: Loading NLP Models")
    print_and_log("  Pre-loading all NLP models (this happens once)...")
    from nlp.models_loader import load_all_models
    models = load_all_models()
    fast = models.get("fast_mode", True)
    mode_label = "FAST (regex + VADER + keyword)" if fast else "FULL (OpenMed NER + RoBERTa)"
    print_and_log(f"  ✅ Models loaded — Mode: {mode_label}")
    logger.info(f"[models] fast_mode={fast} | loaded keys={list(models.keys())}")

    # ── Data Acquisition ───────────────────────────────────
    section("Phase 2: Data Acquisition (3 Sources)")
    all_results = {"reddit": [], "twitter": [], "forum": []}

    # Reddit
    try:
        reddit_posts = crawl_reddit(DRUG_QUERY, max_posts=N)
        all_results["reddit"] = reddit_posts
    except Exception as e:
        print_and_log(f"  ❌ Reddit crawler failed: {e}", "error")
        logger.error(f"[reddit] {e}")

    # Twitter
    try:
        twitter_posts = crawl_twitter(DRUG_QUERY, max_posts=N)
        all_results["twitter"] = twitter_posts
    except Exception as e:
        print_and_log(f"  ❌ Twitter crawler failed: {e}", "error")
        logger.error(f"[twitter] {e}")

    # Indian Forum (1mg.com via Firecrawl)
    try:
        forum_posts = crawl_forum(DRUG_QUERY, max_posts=N)
        all_results["forum"] = forum_posts
    except Exception as e:
        print_and_log(f"  ❌ Forum crawler failed: {e}", "error")
        logger.error(f"[forum] {e}")

    total_fetched = sum(len(v) for v in all_results.values())
    print_and_log(f"\n  📊 Total posts fetched: {total_fetched}")
    print_and_log(f"     Reddit : {len(all_results['reddit'])} posts")
    print_and_log(f"     Twitter: {len(all_results['twitter'])} posts")
    print_and_log(f"     Forum  : {len(all_results['forum'])} posts")

    # ── NLP Pipeline ──────────────────────────────────────
    section("Phase 3: NLP Pipeline (All Sources)")

    all_pipeline_results = []
    ae_summary = []

    for source, posts in all_results.items():
        if not posts:
            print_and_log(f"\n  ⚠️  No posts from {source} — skipping")
            continue

        subsection(f"Source: {source.upper()} ({len(posts)} posts)")
        logger.info(f"=== Processing source: {source} | count={len(posts)} ===")

        for i, post in enumerate(posts):
            try:
                result = run_nlp_pipeline(post, source=source, post_idx=i)
                if result:
                    all_pipeline_results.append(result)
                    if result.get("ae", {}).get("ae_flag"):
                        ae_summary.append({
                            "source": source,
                            "drug": result["ae"].get("drug"),
                            "symptoms": result["ae"].get("symptoms_non_negated", []),
                            "confidence": result["ae"].get("confidence", 0),
                            "url": result.get("url", ""),
                        })
            except Exception as e:
                print_and_log(f"\n  ❌ Pipeline error on post {i}: {e}", "error")
                logger.exception(f"[pipeline] Error on {source}#{i}: {e}")

    # ── Final Summary ──────────────────────────────────────
    section("Phase 4: Summary")
    elapsed = (datetime.now() - start_time).total_seconds()

    print_and_log(f"  Posts processed : {len(all_pipeline_results)}")
    print_and_log(f"  AE events found : {len(ae_summary)}")
    print_and_log(f"  Time elapsed    : {elapsed:.1f}s")
    print_and_log(f"  Full log saved  : {LOG_FILE}\n  Raw output saved: {RAW_LOG_FILE}")

    if ae_summary:
        print_and_log("\n  🚨 Adverse Events Detected:")
        for ae in ae_summary:
            print_and_log(
                f"     [{ae['source'].upper()}] Drug: {ae['drug']} | "
                f"Symptoms: {ae['symptoms']} | Conf: {ae['confidence']:.3f}"
            )
            print_and_log(f"       → {ae['url'][:80]}")
    else:
        print_and_log("\n  ✅ No adverse events detected in this batch.")

    logger.info(
        f"=== Demo Pipeline COMPLETE | posts={len(all_pipeline_results)} "
        f"| ae={len(ae_summary)} | elapsed={elapsed:.1f}s ==="
    )

    print_and_log(f"\n{DIVIDER}")
    print_and_log(f"  Demo complete. Full structured log → {LOG_FILE}")
    print_and_log(DIVIDER)


if __name__ == "__main__":
    main()
