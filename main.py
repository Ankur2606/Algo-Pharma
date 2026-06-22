"""
AlgoPharma — FastAPI application entry point.
Lifespan startup: init DB + load NLP models.
"""

import os
import sys

# ── Fix Intel MKL "forrtl: error (200)" crash on Ctrl+C (Windows) ──────────
# numpy/scipy ship with Intel MKL on Windows.  MKL's Fortran runtime installs
# its own Ctrl+C handler that kills the process with a noisy stack trace.
# Setting this env var BEFORE numpy is imported tells MKL to leave Ctrl+C alone.
os.environ.setdefault("FOR_DISABLE_CONSOLE_CTRL_HANDLER", "1")

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from logger_config import setup_global_logging
setup_global_logging()

import logging
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

# ── CORS (allow all origins for prototype) ───────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ─────────────────────────────────────
from api.projects import router as projects_router
from api.signals import router as signals_router
from api.health import router as health_router
from api.chat import router as chat_router
from api.results import router as results_router
from api.user_auth import router as auth_router
from api.admin import router as admin_router

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(signals_router)
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(results_router)
app.include_router(admin_router)

# ── Serve frontend static files ───────────────────────────
_static_dir = Path(__file__).parent / "static"
_static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


# ── Serve favicon ────────────────────────────────────────
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """Serve the favicon."""
    favicon_path = Path(__file__).parent / "static" / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(str(favicon_path))
    return FileResponse(str(Path(__file__).parent / "favicon.ico"))


# ── Root endpoint ────────────────────────────────────────
@app.get("/")
def root():
    """Serve the chatbot frontend."""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    # Fallback JSON if static file missing
    from config import get_settings
    settings = get_settings()
    return {
        "service": "AlgoPharma",
        "version": "0.1.0",
        "docs": "/docs",
        "ui": "Place index.html in static/ directory",
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
    uvicorn.run(
        "main:app", host="0.0.0.0", port=8000, reload=True,
        reload_excludes=["logs/*", "*.log", "logs/**/*"],
    )
