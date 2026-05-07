"""
AlgoPharma — FastAPI application entry point.
Lifespan startup: init DB + load NLP models.
"""

import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from logger_config import setup_global_logging

# ─────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────
setup_global_logging()

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# APP LIFESPAN
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize DB + load NLP models."""

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    logger.info("🚀 AlgoPharma starting up...")

    # Initialize database tables
    from database import init_db

    init_db()

    logger.info("✅ Database tables ready")

    # Load NLP models
    from nlp.models_loader import load_all_models

    load_all_models()

    logger.info("✅ NLP models loaded")

    yield

    logger.info("👋 AlgoPharma shutting down")


# ─────────────────────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="AlgoPharma",
    description="Real-time pharmacovigilance social listening platform",
    version="0.1.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────
# REGISTER ROUTERS
# ─────────────────────────────────────────────────────────────
from api.user_auth import router as auth_router
from api.projects import router as projects_router
from api.signals import router as signals_router
from api.health import router as health_router
from api.chat import router as chat_router
from api.results import router as results_router
from api.analytics import router as analytics_router

# Public auth endpoints
app.include_router(auth_router)

# Protected/business endpoints
app.include_router(projects_router)
app.include_router(signals_router)
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(results_router)
app.include_router(analytics_router)


# ─────────────────────────────────────────────────────────────
# STATIC FILES
# ─────────────────────────────────────────────────────────────
_static_dir = Path(__file__).parent / "static"

_static_dir.mkdir(exist_ok=True)

app.mount(
    "/static",
    StaticFiles(directory=str(_static_dir)),
    name="static"
)


# ─────────────────────────────────────────────────────────────
# ROOT ENDPOINT
# ─────────────────────────────────────────────────────────────
@app.get("/")
def root():
    """Serve frontend UI."""

    html_path = Path(__file__).parent / "static" / "index.html"

    if html_path.exists():
        return FileResponse(str(html_path))

    return {
        "service": "AlgoPharma",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "running",
    }


# ─────────────────────────────────────────────────────────────
# DEMO PIPELINE ENDPOINT
# ─────────────────────────────────────────────────────────────
@app.get("/api/demo/run")
def run_demo():
    """
    Run full ingestion + signal detection pipeline.
    Useful for testing/debugging.
    """

    from tasks.ingest_existing import ingest_all
    from nlp.signal_detector import detect_signals

    logger.info("🚀 Starting demo pipeline")

    ingestion = ingest_all()

    logger.info("✅ Ingestion completed")

    signals = detect_signals()

    logger.info(f"✅ Signal detection completed: {len(signals)} signals found")

    return {
        "ingestion": ingestion,
        "signals": signals,
        "total_signals": len(signals),
    }


# ─────────────────────────────────────────────────────────────
# MANUAL CRAWL TRIGGER
# ─────────────────────────────────────────────────────────────
@app.post("/api/crawl/trigger/{project_id}")
def trigger_crawl(project_id: int, background_tasks: BackgroundTasks):
    """
    Trigger ingestion pipeline manually in background.
    """

    from tasks.ingest_existing import ingest_all

    logger.info(f"🚀 Crawl triggered for project {project_id}")

    background_tasks.add_task(ingest_all, project_id)

    return {
        "task_started": True,
        "project_id": project_id,
        "message": f"Ingestion started for project {project_id}",
    }


# ─────────────────────────────────────────────────────────────
# SERVER ENTRYPOINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )