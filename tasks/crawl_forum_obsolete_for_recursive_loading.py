"""
AlgoPharma — Forum crawl pipeline.
Bridges forum_onboarding (Firecrawl + LLM) with the DB + Celery NLP pipeline.
Mirrors the crawl_reddit / crawl_twitter flow:
  1. Call forum_onboarding to scrape + extract posts
  2. Store extracted posts as RawPosts (Phase 1)
  3. Dispatch Celery task_process_unprocessed (Phase 2 — NLP + signals)
"""

import json
import hashlib
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def crawl_forum(project_id: int, forum_url: str, medicine: str = "", symptom: str = "") -> dict:
    """
    Run forum onboarding pipeline and feed results into the standard
    RawPost → ProcessedPost → Signal pipeline.
    """
    from database import SessionLocal
    from models import RawPost, CrawlLog, Source

    # ── Log crawl start ──────────────────────────────────────
    with SessionLocal() as session:
        source = session.query(Source).filter(Source.platform == "custom_forum").first()
        source_id = source.id if source else None

        log = CrawlLog(
            source_id=source_id or 0,
            project_id=project_id,
            status="started",
        )
        session.add(log)
        session.commit()
        log_id = log.id

    try:
        # ── Step 1: Forum onboarding (Firecrawl + LLM) ─────────────
        from agentic.forum_onboarding import onboard_forum
        result = onboard_forum(forum_url, medicine=medicine)

        if not result.get("success"):
            raise RuntimeError(f"Forum onboarding failed: {result.get('error', 'unknown')}")

        samples = result.get("samples", [])
        config = result.get("config", {})

        logger.info(
            f"[crawl_forum] Onboarding complete | url={forum_url} | "
            f"confidence={result.get('confidence', 0)} | samples={len(samples)} | "
            f"forum_type={config.get('forum_type', 'unknown')}"
        )

        # ── Step 2: Store samples as RawPosts ──────────────────────
        stored = 0
        with SessionLocal() as session:
            for i, sample in enumerate(samples):
                # Samples can be dicts with content/author/date from LLM extraction
                if isinstance(sample, dict):
                    title = sample.get("title", "")
                    body = sample.get("content", sample.get("markdown", ""))
                    author = sample.get("author", "forum_user")
                    url = sample.get("url", forum_url)
                else:
                    title = ""
                    body = str(sample)
                    author = "forum_user"
                    url = forum_url

                text = f"{title} {body}".strip()
                if not text:
                    continue

                thread_id = f"forum_{hashlib.md5(text[:200].encode()).hexdigest()[:12]}"

                # Deduplicate
                existing = session.query(RawPost).filter(
                    RawPost.thread_id == thread_id,
                    RawPost.project_id == project_id,
                ).first()
                if existing:
                    continue

                # Language detection
                try:
                    from langdetect import detect as lang_detect
                    lang = lang_detect(text)
                except Exception:
                    lang = "en"

                # PII redaction (lightweight regex path under FAST_MODE)
                try:
                    from nlp.pii_guard import redact_pii
                    pii_result = redact_pii(text, lang)
                    redacted_text = pii_result["redacted_text"]
                except Exception:
                    redacted_text = text

                author_hash = hashlib.sha256(author.encode("utf-8")).hexdigest()

                raw_post = RawPost(
                    project_id=project_id,
                    thread_id=thread_id,
                    url=url,
                    title=title[:200] if title else f"{medicine} forum post",
                    body=redacted_text,
                    author_hash=author_hash,
                    lang=lang,
                    source_platform="custom_forum",
                    posted_at=datetime.now(timezone.utc),
                )
                session.add(raw_post)
                stored += 1

            session.commit()

        logger.info(f"[crawl_forum] Stored {stored} RawPosts for project {project_id}")

        # ── Step 3: Dispatch Celery NLP (Phase 2) ──────────────────
        try:
            from celery_app import task_process_unprocessed
            res = task_process_unprocessed.delay(project_id)
            logger.info(f"✅ Forum NLP task queued | task_id={res.id}")

            import threading
            def _track(res):
                try:
                    data = res.get(timeout=300)
                    logger.info(f"✅ Celery [process_unprocessed] COMPLETE: {data}")
                except Exception as e:
                    logger.error(f"❌ Celery [process_unprocessed] FAILED: {e}")
            threading.Thread(target=_track, args=(res,), daemon=True).start()
        except Exception as celery_err:
            logger.warning(f"⚠️  Celery dispatch failed for forum: {celery_err}")

        # ── Update crawl log ────────────────────────────────────────
        with SessionLocal() as session:
            log = session.get(CrawlLog, log_id)
            if log:
                log.status = "success"
                log.posts_found = stored
                log.finished_at = datetime.now(timezone.utc)
                session.commit()

        return {
            "status": "success",
            "tool": "forum_onboarding",
            "forum_url": forum_url,
            "forum_type": config.get("forum_type", "unknown"),
            "confidence": result.get("confidence", 0),
            "posts_crawled": stored,
            "config": config,
        }

    except Exception as e:
        logger.error(f"Forum crawl failed: {e}")
        with SessionLocal() as session:
            log = session.get(CrawlLog, log_id)
            if log:
                log.status = "failed"
                log.error_message = str(e)
                log.finished_at = datetime.now(timezone.utc)
                session.commit()
        return {"status": "failed", "error": str(e)}
