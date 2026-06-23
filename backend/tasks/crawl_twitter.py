"""
AlgoPharma — Live crawl wrapper for Twitter.
Calls twitter_crawler.py and ingests results into the DB.
"""

import sys
import json
import socket
import logging

logger = logging.getLogger(__name__)


def _redis_reachable(url: str, timeout: float = 3.0) -> bool:
    """Return True only if Redis TCP port is open — 3.0s probe for cloud Redis (e.g. Upstash)."""
    try:
        from urllib.parse import urlparse
        p = urlparse(url)
        host = p.hostname or "localhost"
        port = p.port or 6379
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def crawl_twitter(project_id: int = 1, query: str = "dolo 650 medicine side effects") -> dict:
    """Run Twitter crawler and ingest results."""
    from config import get_settings
    from database import SessionLocal
    from models import CrawlLog, Source
    from datetime import datetime, timezone

    settings = get_settings()

    with SessionLocal() as session:
        source = session.query(Source).filter(Source.platform == "twitter").first()
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
        import twitter_crawler
        twitter_crawler.SEARCH_QUERY = query
        twitter_crawler.OUTPUT_FILE = settings.TWITTER_JSON_PATH
        posts = twitter_crawler.scrape_twitter(query)

        if posts:
            with open(settings.TWITTER_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(posts, f, ensure_ascii=False, indent=2, default=str)

        # ── Phase 1: Store RawPosts immediately (no NLP, non-blocking) ──────
        # Decoupled from NLP so the crawler returns fast and MCP never hangs.
        from tasks.ingest_existing import ingest_twitter_json_raw
        raw_result = ingest_twitter_json_raw(project_id)

        # ── Phase 2: Dispatch NLP + signal detection asynchronously ─────────
        # IMPORTANT: Use task_process_unprocessed (same as crawl_reddit), NOT
        # task_ingest_all.  task_ingest_all calls ingest_all() which re-reads
        # BOTH the reddit and twitter JSON files from disk and ingests them all,
        # causing Reddit posts to bleed into Twitter projects.
        # task_process_unprocessed operates purely on RawPosts already stored in
        # the DB for this project_id — so source isolation is guaranteed by
        # whatever Phase 1 (ingest_twitter_json_raw) wrote, not by file paths.
        try:
            from celery_app import task_process_unprocessed
            res = task_process_unprocessed.delay(project_id)
            logger.info(f"✅ NLP task queued | task_id={res.id}")

            import threading
            def _track(res):
                try:
                    data = res.get(timeout=300)
                    logger.info(f"✅ Celery [process_unprocessed] COMPLETE: {data}")
                except Exception as e:
                    logger.error(f"❌ Celery [process_unprocessed] FAILED: {e}")
            threading.Thread(target=_track, args=(res,), daemon=True).start()
        except Exception as celery_err:
            logger.warning(f"⚠️  Celery dispatch failed: {celery_err}")

        with SessionLocal() as session:
            log = session.get(CrawlLog, log_id)
            if log:
                log.status = "success"
                log.posts_found = len(posts)
                log.finished_at = datetime.now(timezone.utc)
                session.commit()

        return {"status": "success", "posts_crawled": len(posts), "raw_storage": raw_result}

    except Exception as e:
        logger.error(f"Twitter crawl failed: {e}")
        with SessionLocal() as session:
            log = session.get(CrawlLog, log_id)
            if log:
                log.status = "failed"
                log.error_message = str(e)
                log.finished_at = datetime.now(timezone.utc)
                session.commit()
        return {"status": "failed", "error": str(e)}


if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    import os
    os.environ["FAST_MODE"] = "false"

    from database import init_db
    init_db()

    result = crawl_twitter()
    print(f"Result: {result}")
