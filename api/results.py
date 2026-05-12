"""
AlgoPharma — Results polling router.

GET /api/results/{project_id}
  - Returns the current status + signals + processed posts for a project.
  - Frontend polls this every ~4 seconds after being redirected to dashboard.

Status values:
  "crawling"   — CrawlLog exists but no ProcessedPosts yet
  "analysing"  — ProcessedPosts exist but not all signals are detected
  "complete"   — At least one Signal exists in the DB for this project
  "not_found"  — Project ID does not exist

GET /api/results/list
  - Returns all projects (for the dashboard project picker).
"""

import json
import logging
import os
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/results", tags=["results"])

# ── JSON result logging ──────────────────────────────────────
_LOGS_DIR = Path(__file__).parent.parent / "logs" / "results"
_LOGS_DIR.mkdir(parents=True, exist_ok=True)

def _save_result_log(project_id: int, data: dict):
    """Save each poll result to logs/results/projectid_N.json (incrementing)."""
    try:
        existing = sorted(_LOGS_DIR.glob(f"{project_id}_*.json"))
        next_idx = len(existing) + 1
        filepath = _LOGS_DIR / f"{project_id}_{next_idx}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        logger.debug(f"[results] Saved log: {filepath}")
    except Exception as e:
        logger.warning(f"[results] Failed to save log: {e}")


def _serialize_post(pp, raw) -> dict:
    """Turn a ProcessedPost + RawPost pair into a clean dict for the frontend."""
    try:
        entities = json.loads(pp.entities_json or "{}")
    except Exception:
        entities = {}
    try:
        sentiment = json.loads(pp.sentiment_json or "{}")
    except Exception:
        sentiment = {}

    return {
        "id":           pp.id,
        "platform":     raw.source_platform if raw else "unknown",
        "title":        raw.title[:120] if raw else "",
        "text":         pp.redacted_text[:300] if pp.redacted_text else "",
        "ae_flag":      pp.ae_flag,
        "ae_confidence": round(pp.ae_confidence, 3),
        "ae_reason":    pp.ae_reason,
        "sentiment":    sentiment.get("label", "UNKNOWN"),
        "drugs":        [d["text"] for d in entities.get("drugs", [])],
        "symptoms":     [s["text"] for s in entities.get("symptoms", [])],
    }


@router.get("/list")
def list_projects():
    """Return all projects — lets the frontend populate a dropdown."""
    from database import SessionLocal
    from models import Project

    with SessionLocal() as session:
        projects = session.query(Project).order_by(Project.created_at.desc()).all()
        return [
            {"id": p.id, "name": p.name, "created_at": str(p.created_at)}
            for p in projects
        ]


@router.get("/{project_id}")
def get_results(project_id: int):
    """
    Polling endpoint.  Frontend calls this every 4 s after the pipeline starts.
    Returns live status + whatever signals/posts exist in the DB right now.
    """
    from database import SessionLocal
    from models import Project, CrawlLog, Signal, ProcessedPost, RawPost

    with SessionLocal() as session:

        # ── 1. Verify project exists ─────────────────────────────
        project = session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # ── 2. Determine status ──────────────────────────────────
        signals = (
            session.query(Signal)
            .filter(Signal.project_id == project_id)
            .order_by(Signal.prr.desc())
            .all()
        )

        processed_posts = (
            session.query(ProcessedPost)
            .filter(ProcessedPost.project_id == project_id)
            .limit(50)
            .all()
        )

        crawl_logs = (
            session.query(CrawlLog)
            .filter(CrawlLog.project_id == project_id)
            .order_by(CrawlLog.started_at.desc())
            .all()
        )

        total_raw = (
            session.query(RawPost)
            .filter(RawPost.project_id == project_id)
            .count()
        )

        # Count ALL processed posts for this project (not just the limited 50)
        total_processed = (
            session.query(ProcessedPost)
            .filter(ProcessedPost.project_id == project_id)
            .count()
        )

        ae_flagged_count = (
            session.query(ProcessedPost)
            .filter(ProcessedPost.project_id == project_id, ProcessedPost.ae_flag == True)
            .count()
        )

        if signals:
            status = "complete"
        elif total_processed >= min(total_raw, 1) and total_raw > 0:
            # NLP has finished processing all available posts → complete even if 0 signals
            status = "complete"
        elif processed_posts:
            status = "analysing"
        elif crawl_logs:
            status = "crawling"
        else:
            status = "crawling"


        # ── 3. Serialize signals ─────────────────────────────────
        signal_data = [
            {
                "drug":        s.drug,
                "symptom":     s.symptom,
                "post_count":  s.post_count,
                "prr":         round(s.prr, 3),
                "ror":         round(s.ror, 3),
                "chi_square":  round(s.chi_square, 3),
                "strength":    s.strength,
            }
            for s in signals
        ]

        # ── 4. Serialize processed posts ─────────────────────────
        post_data = []
        for pp in processed_posts[:20]:   # cap at 20 for the UI
            raw = session.get(RawPost, pp.raw_post_id)
            post_data.append(_serialize_post(pp, raw))

        # ── 5. Crawl log summary ─────────────────────────────────
        crawl_summary = [
            {
                "source_id":  cl.source_id,
                "status":     cl.status,
                "posts_found": cl.posts_found,
                "started_at": str(cl.started_at),
                "finished_at": str(cl.finished_at) if cl.finished_at else None,
            }
            for cl in crawl_logs[:5]
        ]

        response = {
            "project_id":   project_id,
            "project_name": project.name,
            "status":       status,
            # ── Top-level stats for frontend dashboard ────────────
            "total_raw":    total_raw,
            "processed":    total_processed,
            "ae_flagged":   ae_flagged_count,
            # ──────────────────────────────────────────────────────
            "signals":      signal_data,
            "posts":        post_data,
            "crawl_logs":   crawl_summary,
            "counts": {
                "signals":         len(signals),
                "processed_posts": total_processed,
                "crawl_logs":      len(crawl_logs),
                "total_raw":       total_raw,
                "ae_flagged":      ae_flagged_count,
            },
        }

        # Save result log only when status changes or periodically
        if status == "complete" or total_processed > 0:
            _save_result_log(project_id, response)

        return response
