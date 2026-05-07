"""
AlgoPharma — Ingest existing JSON data files into DB + run NLP pipeline.

Two-phase ingestion design (post NLP-decoupling refactor):
  Phase 1 — *_raw() functions: store RawPosts only, no NLP/transformer calls.
             Called directly by crawlers so MCP/FastAPI returns immediately.
  Phase 2 — ingest_*_json() functions: load NLP models and run full pipeline.
             Called exclusively by Celery workers (task_ingest_all).
"""

import json
import sys
import hashlib
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _hash_author(author: str) -> str:
    """SHA-256 hash an author identifier."""
    return hashlib.sha256(author.encode("utf-8")).hexdigest()


# ── Phase 1: Lightweight raw-storage functions ────────────────────────────
# These functions are called by crawlers to store posts immediately.
# They do NOT import any NLP modules — no transformers, no spaCy, no models.
# Heavy NLP is dispatched asynchronously to Celery workers after these return.

def ingest_reddit_json_raw(project_id: int = 1) -> dict:
    """Phase 1 — Read reddit JSON → PII redact → store RawPosts only (no NLP).

    Decoupled from heavy NLP so crawlers / MCP can return immediately.
    The NLP pipeline (Phase 2) is triggered asynchronously via Celery.
    """
    from config import get_settings
    from database import SessionLocal
    from models import RawPost
    from nlp.pii_guard import redact_pii  # lightweight regex-based PII only

    settings = get_settings()
    path = settings.REDDIT_JSON_PATH

    try:
        with open(path, "r", encoding="utf-8") as f:
            posts = json.load(f)
    except FileNotFoundError:
        logger.error(f"Reddit JSON not found at {path}")
        return {"source": "reddit", "total": 0, "stored": 0, "skipped": 0}

    total = len(posts)
    stored = 0
    skipped = 0

    with SessionLocal() as session:
        for i, post in enumerate(posts):
            url = post.get("permalink", post.get("url", ""))
            thread_id = post.get("id", str(i))

            # Deduplicate — skip posts already stored
            existing = session.query(RawPost).filter(
                RawPost.project_id == project_id,
                RawPost.thread_id == thread_id,
                RawPost.source_platform == "reddit"
            ).first()
            if existing:
                skipped += 1
                continue

            title = post.get("title", "")
            description = post.get("description", "")
            text = f"{title} {description}".strip()

            if not text:
                skipped += 1
                continue

            # Language detection (fast, no model required)
            try:
                from langdetect import detect as lang_detect
                lang = lang_detect(text)
            except Exception:
                lang = "en"

            # PII redaction — regex-based, no heavy model needed in fast path
            pii_result = redact_pii(text, lang)
            redacted_text = pii_result["redacted_text"]

            author_hash = _hash_author(post.get("author", "anonymous"))

            posted_at = None
            created_utc = post.get("created_utc")
            if created_utc:
                try:
                    posted_at = datetime.fromtimestamp(float(created_utc), tz=timezone.utc)
                except (ValueError, TypeError, OSError):
                    pass

            raw_post = RawPost(
                project_id=project_id,
                thread_id=thread_id,
                url=url,
                title=title,
                body=redacted_text,
                author_hash=author_hash,
                lang=lang,
                source_platform="reddit",
                posted_at=posted_at,
            )
            session.add(raw_post)
            stored += 1

            # Batch commit every 50 to avoid large transactions
            if stored % 50 == 0:
                session.commit()

        session.commit()

    logger.info(f"[ingest_reddit_raw] stored={stored} skipped={skipped} total={total}")
    return {"source": "reddit", "total": total, "stored": stored, "skipped": skipped}


def ingest_twitter_json_raw(project_id: int = 1) -> dict:
    """Phase 1 — Read twitter JSON → PII redact → store RawPosts only (no NLP).

    Decoupled from heavy NLP so crawlers / MCP can return immediately.
    The NLP pipeline (Phase 2) is triggered asynchronously via Celery.
    """
    from config import get_settings
    from database import SessionLocal
    from models import RawPost
    from nlp.pii_guard import redact_pii  # lightweight regex-based PII only

    settings = get_settings()
    path = settings.TWITTER_JSON_PATH

    try:
        with open(path, "r", encoding="utf-8") as f:
            posts = json.load(f)
    except FileNotFoundError:
        logger.error(f"Twitter JSON not found at {path}")
        return {"source": "twitter", "total": 0, "stored": 0, "skipped": 0}

    total = len(posts)
    stored = 0
    skipped = 0

    with SessionLocal() as session:
        for i, post in enumerate(posts):
            url = post.get("url", post.get("permalink", ""))
            thread_id = post.get("id", str(i))

            # Deduplicate — skip posts already stored
            existing = session.query(RawPost).filter(
                RawPost.project_id == project_id,
                RawPost.thread_id == thread_id,
                RawPost.source_platform == "twitter"
            ).first()
            if existing:
                skipped += 1
                continue

            title = post.get("title", "")
            description = post.get("description", "")
            text = f"{title} {description}".strip()

            if not text:
                skipped += 1
                continue

            # Language detection (fast, no model required)
            try:
                from langdetect import detect as lang_detect
                lang = lang_detect(text)
            except Exception:
                lang = "en"

            # PII redaction — regex-based, no heavy model needed in fast path
            pii_result = redact_pii(text, lang)
            redacted_text = pii_result["redacted_text"]

            author_hash = _hash_author(post.get("author", "anonymous"))

            posted_at = None
            created_utc = post.get("created_utc", "")
            if created_utc:
                try:
                    if isinstance(created_utc, (int, float)):
                        posted_at = datetime.fromtimestamp(float(created_utc), tz=timezone.utc)
                    else:
                        posted_at = datetime.fromisoformat(str(created_utc).replace("Z", "+00:00"))
                except (ValueError, TypeError, OSError):
                    pass

            raw_post = RawPost(
                project_id=project_id,
                thread_id=thread_id,
                url=url,
                title=title,
                body=redacted_text,
                author_hash=author_hash,
                lang=lang,
                source_platform="twitter",
                posted_at=posted_at,
            )
            session.add(raw_post)
            stored += 1

            if stored % 50 == 0:
                session.commit()

        session.commit()

    logger.info(f"[ingest_twitter_raw] stored={stored} skipped={skipped} total={total}")
    return {"source": "twitter", "total": total, "stored": stored, "skipped": skipped}


# ── Phase 2: Full NLP pipeline functions (Celery workers only) ────────────
# These are called exclusively from Celery tasks (task_ingest_all).
# They load transformers/spaCy models and perform full NLP inference.
# Never call these from a crawler or MCP handler — they will block.

def ingest_reddit_json(project_id: int = 1) -> dict:
    """Read reddit JSON → PII redact → NLP pipeline → store in DB."""
    from config import get_settings
    from database import SessionLocal
    from models import RawPost, ProcessedPost
    from nlp.pii_guard import redact_pii
    from nlp.ae_detector import detect_ae
    from nlp.thread_scorer import score_thread
    from nlp.ner_pipeline import extract_entities
    from nlp.sentiment import analyze_sentiment

    settings = get_settings()
    path = settings.REDDIT_JSON_PATH

    try:
        with open(path, "r", encoding="utf-8") as f:
            posts = json.load(f)
    except FileNotFoundError:
        logger.error(f"Reddit JSON not found at {path}")
        return {"source": "reddit", "total": 0, "ingested": 0, "ae_flagged": 0, "skipped": 0}

    total = len(posts)
    ingested = 0
    ae_flagged = 0
    skipped = 0

    with SessionLocal() as session:
        for i, post in enumerate(posts):
            url = post.get("permalink", post.get("url", ""))
            thread_id = post.get("id", str(i))

            # Deduplicate
            existing = session.query(RawPost).filter(
                RawPost.project_id == project_id,
                RawPost.thread_id == thread_id,
                RawPost.source_platform == "reddit"
            ).first()
            if existing:
                skipped += 1
                continue

            title = post.get("title", "")
            description = post.get("description", "")
            text = f"{title} {description}".strip()

            if not text:
                skipped += 1
                continue

            # Language detection
            try:
                from langdetect import detect as lang_detect
                lang = lang_detect(text)
            except Exception:
                lang = "en"

            # PII redaction
            pii_result = redact_pii(text, lang)
            redacted_text = pii_result["redacted_text"]
            logger.info(f"[{thread_id}] [PII IN]: {text[:50]}... -> [PII OUT]: {redacted_text[:50]}...")

            # Translate to English for downstream NLP
            from nlp.translator import translate_to_english
            english_text = translate_to_english(redacted_text, lang)
            if english_text != redacted_text:
                logger.info(f"[{thread_id}] [TRANS IN ({lang})]: {redacted_text[:50]}... -> [TRANS OUT (en)]: {english_text[:50]}...")

            # Hash author
            author_hash = _hash_author(post.get("author", "anonymous"))

            # Parse posted_at
            posted_at = None
            created_utc = post.get("created_utc")
            if created_utc:
                try:
                    posted_at = datetime.fromtimestamp(float(created_utc), tz=timezone.utc)
                except (ValueError, TypeError, OSError):
                    pass

            # Insert RawPost (store native language redacted text)
            raw_post = RawPost(
                project_id=project_id,
                thread_id=thread_id,
                url=url,
                title=title,
                body=redacted_text,
                author_hash=author_hash,
                lang=lang,
                source_platform="reddit",
                posted_at=posted_at,
            )
            session.add(raw_post)
            session.flush()  # get raw_post.id

            # NLP pipeline (using English text)
            entities = extract_entities(english_text)
            logger.info(f"[{thread_id}] [NER OUT]: {len(entities['drugs'])} drugs, {len(entities['symptoms'])} symptoms")
            
            sentiment = analyze_sentiment(english_text, "en")
            logger.info(f"[{thread_id}] [SENTIMENT OUT]: {sentiment['label']} ({sentiment['score']})")
            
            ae_result = detect_ae(english_text, "en", entities=entities, sentiment=sentiment)
            logger.info(f"[{thread_id}] [AE OUT]: Flag={ae_result['ae_flag']}, Reason={ae_result['reason']}")
            
            thread_result = score_thread(ae_result, [])  # no replies in current data

            # Insert ProcessedPost
            processed = ProcessedPost(
                raw_post_id=raw_post.id,
                project_id=project_id,
                redacted_text=english_text,
                entities_json=json.dumps(entities, ensure_ascii=False),
                sentiment_json=json.dumps(sentiment, ensure_ascii=False),
                negation_json=json.dumps({
                    "non_negated": ae_result.get("symptoms_non_negated", []),
                    "negated": ae_result.get("symptoms_negated", []),
                }),
                ae_flag=ae_result["ae_flag"],
                ae_confidence=ae_result["confidence"],
                ae_reason=ae_result["reason"],
                thread_score=thread_result["final_confidence"],
                thread_color=thread_result["color"],
                pii_entities_found=json.dumps(pii_result["pii_entities_found"]),
            )
            session.add(processed)
            ingested += 1

            if ae_result["ae_flag"]:
                ae_flagged += 1

            # Batch commit every 50
            if ingested % 50 == 0:
                session.commit()

        session.commit()

    return {
        "source": "reddit",
        "total": total,
        "ingested": ingested,
        "ae_flagged": ae_flagged,
        "skipped": skipped,
    }


def ingest_twitter_json(project_id: int = 1) -> dict:
    """Read twitter JSON → PII redact → NLP pipeline → store in DB."""
    from config import get_settings
    from database import SessionLocal
    from models import RawPost, ProcessedPost
    from nlp.pii_guard import redact_pii
    from nlp.ae_detector import detect_ae
    from nlp.thread_scorer import score_thread
    from nlp.ner_pipeline import extract_entities
    from nlp.sentiment import analyze_sentiment

    settings = get_settings()
    path = settings.TWITTER_JSON_PATH

    try:
        with open(path, "r", encoding="utf-8") as f:
            posts = json.load(f)
    except FileNotFoundError:
        logger.error(f"Twitter JSON not found at {path}")
        return {"source": "twitter", "total": 0, "ingested": 0, "ae_flagged": 0, "skipped": 0}

    total = len(posts)
    ingested = 0
    ae_flagged = 0
    skipped = 0

    with SessionLocal() as session:
        for i, post in enumerate(posts):
            url = post.get("url", post.get("permalink", ""))
            thread_id = post.get("id", str(i))

            # Deduplicate
            existing = session.query(RawPost).filter(
                RawPost.project_id == project_id,
                RawPost.thread_id == thread_id,
                RawPost.source_platform == "twitter"
            ).first()
            if existing:
                skipped += 1
                continue

            title = post.get("title", "")
            description = post.get("description", "")
            text = f"{title} {description}".strip()

            if not text:
                skipped += 1
                continue

            # Language detection
            try:
                from langdetect import detect as lang_detect
                lang = lang_detect(text)
            except Exception:
                lang = "en"

            # PII redaction
            pii_result = redact_pii(text, lang)
            redacted_text = pii_result["redacted_text"]
            logger.info(f"[{thread_id}] [PII IN]: {text[:50]}... -> [PII OUT]: {redacted_text[:50]}...")

            # Translate to English for downstream NLP
            from nlp.translator import translate_to_english
            english_text = translate_to_english(redacted_text, lang)
            if english_text != redacted_text:
                logger.info(f"[{thread_id}] [TRANS IN ({lang})]: {redacted_text[:50]}... -> [TRANS OUT (en)]: {english_text[:50]}...")

            # Hash author
            author_hash = _hash_author(post.get("author", "anonymous"))

            # Parse posted_at
            posted_at = None
            created_utc = post.get("created_utc", "")
            if created_utc:
                try:
                    if isinstance(created_utc, (int, float)):
                        posted_at = datetime.fromtimestamp(float(created_utc), tz=timezone.utc)
                    else:
                        # Twitter uses ISO format strings
                        posted_at = datetime.fromisoformat(str(created_utc).replace("Z", "+00:00"))
                except (ValueError, TypeError, OSError):
                    pass

            # Insert RawPost
            raw_post = RawPost(
                project_id=project_id,
                thread_id=thread_id,
                url=url,
                title=title,
                body=redacted_text,
                author_hash=author_hash,
                lang=lang,
                source_platform="twitter",
                posted_at=posted_at,
            )
            session.add(raw_post)
            session.flush()

            # NLP pipeline (using English text)
            entities = extract_entities(english_text)
            logger.info(f"[{thread_id}] [NER OUT]: {len(entities['drugs'])} drugs, {len(entities['symptoms'])} symptoms")
            
            sentiment = analyze_sentiment(english_text, "en")
            logger.info(f"[{thread_id}] [SENTIMENT OUT]: {sentiment['label']} ({sentiment['score']})")
            
            ae_result = detect_ae(english_text, "en", entities=entities, sentiment=sentiment)
            logger.info(f"[{thread_id}] [AE OUT]: Flag={ae_result['ae_flag']}, Reason={ae_result['reason']}")
            
            thread_result = score_thread(ae_result, [])

            # Insert ProcessedPost
            processed = ProcessedPost(
                raw_post_id=raw_post.id,
                project_id=project_id,
                redacted_text=english_text,
                entities_json=json.dumps(entities, ensure_ascii=False),
                sentiment_json=json.dumps(sentiment, ensure_ascii=False),
                negation_json=json.dumps({
                    "non_negated": ae_result.get("symptoms_non_negated", []),
                    "negated": ae_result.get("symptoms_negated", []),
                }),
                ae_flag=ae_result["ae_flag"],
                ae_confidence=ae_result["confidence"],
                ae_reason=ae_result["reason"],
                thread_score=thread_result["final_confidence"],
                thread_color=thread_result["color"],
                pii_entities_found=json.dumps(pii_result["pii_entities_found"]),
            )
            session.add(processed)
            ingested += 1

            if ae_result["ae_flag"]:
                ae_flagged += 1

            if ingested % 50 == 0:
                session.commit()

        session.commit()

    return {
        "source": "twitter",
        "total": total,
        "ingested": ingested,
        "ae_flagged": ae_flagged,
        "skipped": skipped,
    }


def process_unprocessed_raw_posts(project_id: int = 1) -> dict:
    """
    Phase 2 NLP for the chat-triggered pipeline.

    The chat flow stores RawPosts immediately (Phase 1), then Celery calls
    this function to run the full NLP pipeline on any RawPost that does
    NOT yet have a ProcessedPost.  This avoids the double-insert skip problem
    where ingest_reddit_json() would re-read the JSON and skip every post
    because Phase 1 already stored them.
    """
    from database import SessionLocal
    from models import RawPost, ProcessedPost
    from nlp.pii_guard import redact_pii
    from nlp.ae_detector import detect_ae
    from nlp.thread_scorer import score_thread
    from nlp.ner_pipeline import extract_entities
    from nlp.sentiment import analyze_sentiment
    from nlp.translator import translate_to_english
    from sqlalchemy import outerjoin

    ingested = 0
    ae_flagged = 0
    skipped = 0

    with SessionLocal() as session:
        # Find RawPosts for this project that have no ProcessedPost yet
        unprocessed = (
            session.query(RawPost)
            .outerjoin(ProcessedPost, ProcessedPost.raw_post_id == RawPost.id)
            .filter(
                RawPost.project_id == project_id,
                ProcessedPost.id == None,  # noqa: E711
            )
            .all()
        )

        total = len(unprocessed)
        logger.info(f"[process_unprocessed] project={project_id} | unprocessed={total}")

        # ── Extract medicine name from Project name as a fallback drug hint ──
        # Project name is set by api/chat.py as "{medicine}_{source}[_{symptom}]_{ts}"
        # We use it so that if NER misses the drug (common for brand names),
        # we can still produce AE signals instead of returning "no_drug" for everything.
        from models import Project as _Project
        project_row = session.get(_Project, project_id)
        medicine_hint: str | None = None
        if project_row:
            # Name format: "Cetrizen_reddit_20260507_045123"
            parts = project_row.name.split("_")
            if parts:
                medicine_hint = parts[0].lower().strip()  # e.g. "cetrizen"
                logger.info(f"[process_unprocessed] medicine_hint='{medicine_hint}' from project name")



        for raw_post in unprocessed:
            try:
                text = raw_post.body or ""
                lang = raw_post.lang or "en"

                if not text.strip():
                    skipped += 1
                    continue

                # Translate to English for downstream NLP
                english_text = translate_to_english(text, lang)

                # PII redaction on English text
                pii_result = redact_pii(english_text, "en")
                redacted = pii_result["redacted_text"]

                # NLP pipeline
                entities  = extract_entities(redacted)

                # ── Medicine hint injection ──────────────────────────────────
                # If NER finds no drugs, inject the queried medicine as a known
                # drug entity so AE detection can still produce a signal.
                # This handles brand names / misspellings NER models don't know.
                if medicine_hint and not entities.get("drugs"):
                    entities["drugs"] = [{"text": medicine_hint, "label": "DRUG", "score": 0.8, "source": "query_hint"}]
                    logger.info(f"[process_unprocessed] [{raw_post.thread_id}] Drug hint injected: '{medicine_hint}'")

                sentiment = analyze_sentiment(redacted, "en")
                ae_result = detect_ae(redacted, "en", entities=entities, sentiment=sentiment)
                thread_result = score_thread(ae_result, [])


                logger.info(
                    f"[process_unprocessed] [{raw_post.thread_id}] "
                    f"AE={ae_result['ae_flag']} conf={ae_result['confidence']:.2f} "
                    f"drugs={[d['text'] for d in entities['drugs']]} "
                    f"symptoms={[s['text'] for s in entities['symptoms']]}"
                )

                processed = ProcessedPost(
                    raw_post_id=raw_post.id,
                    project_id=project_id,
                    redacted_text=redacted,
                    entities_json=json.dumps(entities, ensure_ascii=False),
                    sentiment_json=json.dumps(sentiment, ensure_ascii=False),
                    negation_json=json.dumps({
                        "non_negated": ae_result.get("symptoms_non_negated", []),
                        "negated":     ae_result.get("symptoms_negated", []),
                    }),
                    ae_flag=ae_result["ae_flag"],
                    ae_confidence=ae_result["confidence"],
                    ae_reason=ae_result["reason"],
                    thread_score=thread_result["final_confidence"],
                    thread_color=thread_result["color"],
                    pii_entities_found=json.dumps(pii_result["pii_entities_found"]),
                )
                session.add(processed)
                ingested += 1

                if ae_result["ae_flag"]:
                    ae_flagged += 1

                if ingested % 10 == 0:
                    session.commit()

            except Exception as e:
                logger.error(f"[process_unprocessed] Failed on raw_post {raw_post.id}: {e}")
                skipped += 1
                continue

        session.commit()

    logger.info(
        f"[process_unprocessed] DONE | project={project_id} | "
        f"processed={ingested} ae_flagged={ae_flagged} skipped={skipped}"
    )
    return {
        "project_id": project_id,
        "total_raw": total,
        "processed": ingested,
        "ae_flagged": ae_flagged,
        "skipped": skipped,
    }


def ingest_all(project_id: int = 1) -> dict:
    """Ingest both Reddit and Twitter JSON files."""
    reddit = ingest_reddit_json(project_id)
    twitter = ingest_twitter_json(project_id)
    return {
        "reddit": reddit,
        "twitter": twitter,
        "total_ingested": reddit["ingested"] + twitter["ingested"],
        "total_ae_flagged": reddit["ae_flagged"] + twitter["ae_flagged"],
    }




# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    import os
    os.environ["FAST_MODE"] = "false"

    from database import init_db
    init_db()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("=" * 55)
    print("  Ingest Existing Data — Self-test")
    print("=" * 55)

    result = ingest_all()

    r = result["reddit"]
    t = result["twitter"]
    print(f"\n  📥 Reddit:  {r['total']} total, {r['ingested']} ingested, "
          f"{r['ae_flagged']} AE flags, {r['skipped']} skipped")
    print(f"  📥 Twitter: {t['total']} total, {t['ingested']} ingested, "
          f"{t['ae_flagged']} AE flags, {t['skipped']} skipped")

    ae_rate = (result["total_ae_flagged"] / max(1, result["total_ingested"])) * 100
    print(f"\n  📊 Total: {result['total_ingested']} posts, "
          f"{result['total_ae_flagged']} AE flags ({ae_rate:.1f}%)")

    # Show first 3 flagged posts
    from database import SessionLocal
    from models import ProcessedPost
    with SessionLocal() as session:
        flagged = session.query(ProcessedPost).filter(ProcessedPost.ae_flag == True).limit(3).all()
        if flagged:
            print("\n  🔍 First 3 AE-flagged posts:")
            for pp in flagged:
                print(f"    • [{pp.thread_color}] conf={pp.ae_confidence:.2f} → {pp.redacted_text[:70]}...")

    print("─" * 55)
    ok = result["total_ingested"] > 0
    print(f"{'✅' if ok else '❌'} ingest_existing self-test {'PASS' if ok else 'FAIL'}")
