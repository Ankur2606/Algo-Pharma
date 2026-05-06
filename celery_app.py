"""
AlgoPharma — Celery task queue configuration.
Uses Redis as broker. Optional — system works without Celery via BackgroundTasks.
"""

import sys
import os

# Add current directory to sys.path so Celery worker can import 'tasks' and 'nlp' modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from celery import Celery
from config import get_settings
from logger_config import setup_global_logging

setup_global_logging()

settings = get_settings()

celery_app = Celery(
    "algopharma",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Fail fast when Redis is unavailable — the crawlers catch this exception
    # gracefully and continue without NLP queuing.  Without these two settings
    # Celery retries 20 times (~20 seconds) and floods stdout with retry lines
    # which corrupt the MCP JSONRPC stream.
    broker_connection_retry=False,
    broker_connection_retry_on_startup=False,
    broker_connection_timeout=2,
)


@celery_app.task(name="algopharma.ingest_all")
def task_ingest_all(project_id: int = 1) -> dict:
    """Celery task wrapper for data ingestion."""
    from tasks.ingest_existing import ingest_all
    return ingest_all(project_id)


@celery_app.task(name="algopharma.detect_signals")
def task_detect_signals(project_id: int = 1) -> list:
    """Celery task wrapper for signal detection."""
    from nlp.signal_detector import detect_signals
    return detect_signals(project_id)


@celery_app.task(name="algopharma.crawl_reddit")
def task_crawl_reddit(project_id: int = 1, query: str = "dolo 650") -> dict:
    """Celery task wrapper for Reddit crawling."""
    from tasks.crawl_reddit import crawl_reddit
    return crawl_reddit(project_id, query)


@celery_app.task(name="algopharma.crawl_twitter")
def task_crawl_twitter(project_id: int = 1, query: str = "dolo 650") -> dict:
    """Celery task wrapper for Twitter crawling."""
    from tasks.crawl_twitter import crawl_twitter
    return crawl_twitter(project_id, query)


if __name__ == "__main__":
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    print("✅ Celery app configured")
    print(f"  Broker: {settings.REDIS_URL}")
    print(f"  Tasks registered: {list(celery_app.tasks.keys())}")
    print("  Start worker: celery -A celery_app worker --loglevel=info")
