"""
AlgoPharma — FastAPI application entry point.
Lifespan startup: init DB + load NLP models.
"""

import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables and load models."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    logger.info("🚀 AlgoPharma starting up...")

    from database import init_db
    init_db()
    logger.info("✅ Database tables ready")

    from nlp.models_loader import load_all_models
    load_all_models()
    logger.info("✅ NLP models loaded")

    yield

    logger.info("👋 AlgoPharma shutting down")


app = FastAPI(
    title="AlgoPharma",
    description="Real-time pharmacovigilance social listening platform",
    version="0.1.0",
    lifespan=lifespan,
)

# ── Register routers ─────────────────────────────────────
from api.projects import router as projects_router
from api.signals import router as signals_router
from api.health import router as health_router

app.include_router(projects_router)
app.include_router(signals_router)
app.include_router(health_router)


# ── Root endpoint ────────────────────────────────────────
@app.get("/")
def root():
    from config import get_settings
    settings = get_settings()
    return {
        "service": "AlgoPharma",
        "version": "0.1.0",
        "description": "Real-time pharmacovigilance social listening platform",
        "hackathon": "AI for Bharat — Theme 6",
        "fast_mode": settings.FAST_MODE,
        "docs": "/docs",
    }


# ── Demo endpoint ───────────────────────────────────────
@app.get("/api/demo/run")
def run_demo():
    """Run full ingestion + signal detection pipeline and return summary."""
    from tasks.ingest_existing import ingest_all
    from nlp.signal_detector import detect_signals

    ingestion = ingest_all()
    signals = detect_signals()

    return {
        "ingestion": ingestion,
        "signals": signals,
        "total_signals": len(signals),
    }


# ── Crawl trigger ───────────────────────────────────────
@app.post("/api/crawl/trigger/{project_id}")
def trigger_crawl(project_id: int, background_tasks: BackgroundTasks):
    """Manually trigger ingestion as a background task."""
    from tasks.ingest_existing import ingest_all

    background_tasks.add_task(ingest_all, project_id)
    return {"task_started": True, "message": f"Ingestion started for project {project_id}"}


# ── Run server ───────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
