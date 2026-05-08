"""
AlgoPharma — Celery task queue configuration.
Uses Redis as broker. Optional — system works without Celery via BackgroundTasks.
"""

import sys
import os

# Force FULL mode for Celery workers (they need all NLP models)
os.environ["FAST_MODE"] = "false"

# Add current directory to sys.path so Celery worker can import 'tasks' and 'nlp' modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from celery import Celery
from config import get_settings
from logger_config import setup_global_logging

setup_global_logging()

settings = get_settings()

# Isolate HF Space tasks from local dev workers.
# Set CELERY_TASK_QUEUE=hf_algopharma_queue in HF Space secrets.
# Local dev uses the default 'celery' queue, so tasks never cross-contaminate.
_task_queue = os.environ.get("CELERY_TASK_QUEUE", "celery")

celery_app = Celery(
    "algopharma",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Configure SSL for Upstash Redis
if settings.REDIS_URL.startswith("rediss://"):
    import ssl
    celery_app.conf.broker_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_REQUIRED
    }
    celery_app.conf.redis_backend_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_REQUIRED
    }

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue=_task_queue,
    # Fail fast when Redis is unavailable — the crawlers catch this exception
    # gracefully and continue without NLP queuing.  Without these two settings
    # Celery retries 20 times (~20 seconds) and floods stdout with retry lines
    # which corrupt the MCP JSONRPC stream.
    broker_connection_retry=False,
    broker_connection_retry_on_startup=False,
    broker_connection_timeout=2,
)


# Pre-load NLP models when worker starts
@celery_app.on_after_configure.connect
def setup_models(sender, **kwargs):
    """Load all NLP models when Celery worker starts."""
    # Only load models if we're actually running as a Celery worker
    # Not when celery_app is imported by other processes (like MCP server)
    import sys
    if 'celery' not in sys.argv[0].lower() and 'worker' not in ' '.join(sys.argv):
        return
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info("🔄 Loading NLP models for Celery worker...")
    
    try:
        from nlp.models_loader import load_all_models
        models = load_all_models()
        logger.info(f"✅ NLP models loaded | keys={list(models.keys())}")
    except Exception as e:
        logger.error(f"❌ Failed to load models: {e}")
        raise


@celery_app.task(name="algopharma.ingest_all")
def task_ingest_all(project_id: int = 1) -> dict:
    """Celery task wrapper for data ingestion (reads from JSON files)."""
    from tasks.ingest_existing import ingest_all
    return ingest_all(project_id)


@celery_app.task(name="algopharma.process_unprocessed")
def task_process_unprocessed(project_id: int = 1) -> dict:
    """
    Celery Phase 2 for the chat pipeline.
    Finds RawPosts with no ProcessedPost and runs the full NLP pipeline on them.
    Always triggers signal detection at the end, regardless of AE count.
    """
    from tasks.ingest_existing import process_unprocessed_raw_posts
    result = process_unprocessed_raw_posts(project_id)

    # Always run signal detection — even if ae_flagged=0, it should record empty
    # so the frontend polling can resolve to 'complete' status.
    try:
        from nlp.signal_detector import detect_signals
        signals = detect_signals(project_id)
        result["signals_detected"] = len(signals)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Signal detection failed: {e}")
        result["signals_detected"] = 0

    return result


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
    
    # Test Redis connection
    try:
        import redis
        from urllib.parse import urlparse
        
        parsed = urlparse(settings.REDIS_URL)
        is_ssl = parsed.scheme == "rediss"
        
        r = redis.Redis(
            host=parsed.hostname,
            port=parsed.port or 6379,
            password=parsed.password,
            ssl=is_ssl,
            ssl_cert_reqs="required" if is_ssl else None,
            decode_responses=True,
            socket_connect_timeout=5
        )
        r.ping()
        print("  ✅ Redis connection: SUCCESS")
        print(f"     Host: {parsed.hostname}")
        print(f"     Port: {parsed.port or 6379}")
        print(f"     SSL: {'Enabled' if is_ssl else 'Disabled'}")
    except Exception as e:
        print(f"  ❌ Redis connection: FAILED - {e}")
    
    print(f"  Tasks registered: {list(celery_app.tasks.keys())}")
    print("  Start worker: celery -A celery_app worker --loglevel=info")
