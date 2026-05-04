"""
AlgoPharma — Live crawl wrapper for Reddit.
Calls reddit_crawler.py and ingests results into the DB.
"""

import sys
import json
import logging

logger = logging.getLogger(__name__)


def crawl_reddit(project_id: int = 1, query: str = "dolo 650 medicine side effects") -> dict:
    """Run Reddit crawler and ingest results."""
    from config import get_settings
    from database import SessionLocal
    from models import CrawlLog, Source
    from datetime import datetime, timezone

    settings = get_settings()

    # Log crawl start
    with SessionLocal() as session:
        source = session.query(Source).filter(Source.platform == "reddit").first()
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
        # Import and run the existing crawler
        import reddit_crawler
        reddit_crawler.SEARCH_QUERY = query
        reddit_crawler.OUTPUT_FILE = settings.REDDIT_JSON_PATH
        posts = reddit_crawler.scrape_reddit(query)

        if posts:
            with open(settings.REDDIT_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(posts, f, ensure_ascii=False, indent=2, default=str)

        # Now ingest the freshly crawled data
        from tasks.ingest_existing import ingest_reddit_json
        result = ingest_reddit_json(project_id)

        # Update crawl log
        with SessionLocal() as session:
            log = session.get(CrawlLog, log_id)
            if log:
                log.status = "success"
                log.posts_found = len(posts)
                log.finished_at = datetime.now(timezone.utc)
                session.commit()

        return {"status": "success", "posts_crawled": len(posts), "ingestion": result}

    except Exception as e:
        logger.error(f"Reddit crawl failed: {e}")
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
    os.environ["FAST_MODE"] = "true"

    from database import init_db
    init_db()

    result = crawl_reddit()
    print(f"Result: {result}")
