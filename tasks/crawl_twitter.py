"""
AlgoPharma — Live crawl wrapper for Twitter.
Calls twitter_crawler.py and ingests results into the DB.
"""

import sys
import json
import socket
import logging

logger = logging.getLogger(__name__)


def _redis_reachable(url: str, timeout: float = 0.1) -> bool:
    """Return True only if Redis TCP port is open — 100ms probe, no Celery import."""
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
        # Heavy transformer inference runs in a Celery worker, not here.
        # Fast 100ms TCP probe avoids the 2s Celery timeout when Redis is down.
        from config import get_settings as _gs
        if _redis_reachable(_gs().REDIS_URL):
            try:
                from celery_app import task_ingest_all, task_detect_signals
                res_ingest = task_ingest_all.delay(project_id)
                res_detect = task_detect_signals.delay(project_id)
                logger.info("✅ NLP tasks queued asynchronously via Celery")
                
                import threading
                def _track_celery(res, name):
                    try:
                        logger.info(f"⏳ Tracking Celery [{name}] in background...")
                        data = res.get(timeout=300)
                        logger.info(f"✅ Celery [{name}] COMPLETE: {data}")
                    except Exception as e:
                        logger.error(f"❌ Celery [{name}] FAILED/TIMEOUT: {e}")
                        
                threading.Thread(target=_track_celery, args=(res_ingest, "ingest_all"), daemon=True).start()
                threading.Thread(target=_track_celery, args=(res_detect, "detect_signals"), daemon=True).start()
            except Exception as celery_err:
                logger.warning(
                    f"⚠️  Celery dispatch failed: {celery_err}"
                )
        else:
            logger.info("ℹ️  Redis not running — NLP skipped (run task_ingest_all manually)")

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
