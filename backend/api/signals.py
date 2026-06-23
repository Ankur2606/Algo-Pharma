"""
AlgoPharma — Signals API router.
"""

import json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import csv

from database import get_db
from models import Signal, ProcessedPost, RawPost

router = APIRouter(prefix="/api", tags=["Signals"])


@router.get("/projects/{project_id}/signals")
def list_signals(
    project_id: int,
    days: int = Query(7, ge=1, le=365),
    strength: str = Query(None, description="Filter by strength: STRONG, MODERATE, WEAK"),
    db: Session = Depends(get_db),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    query = db.query(Signal).filter(
        Signal.project_id == project_id,
        Signal.last_updated >= cutoff,
    )
    if strength:
        query = query.filter(Signal.strength == strength.upper())

    signals = query.order_by(Signal.prr.desc()).all()
    return [
        {
            "id": s.id,
            "drug": s.drug,
            "symptom": s.symptom,
            "post_count": s.post_count,
            "prr": s.prr,
            "ror": s.ror,
            "chi_square": s.chi_square,
            "strength": s.strength,
            "first_seen": str(s.first_seen),
            "last_updated": str(s.last_updated),
        }
        for s in signals
    ]


@router.get("/signals/{signal_id}/drilldown")
def signal_drilldown(signal_id: int, db: Session = Depends(get_db)):
    signal = db.get(Signal, signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    # Get supporting posts
    try:
        post_ids = json.loads(signal.supporting_post_ids)
    except (json.JSONDecodeError, TypeError):
        post_ids = []

    supporting_posts = []
    for raw_post_id in post_ids[:10]:
        pp = db.query(ProcessedPost).filter(ProcessedPost.raw_post_id == raw_post_id).first()
        raw = db.get(RawPost, raw_post_id)
        if pp and raw:
            supporting_posts.append({
                "raw_post_id": raw_post_id,
                "title": raw.title,
                "redacted_text": pp.redacted_text[:300],
                "ae_confidence": pp.ae_confidence,
                "ae_reason": pp.ae_reason,
                "sentiment": json.loads(pp.sentiment_json) if pp.sentiment_json else {},
                "entities": json.loads(pp.entities_json) if pp.entities_json else {},
                "thread_color": pp.thread_color,
                "source_platform": raw.source_platform,
                "posted_at": str(raw.posted_at) if raw.posted_at else None,
            })

    return {
        "signal": {
            "id": signal.id,
            "drug": signal.drug,
            "symptom": signal.symptom,
            "post_count": signal.post_count,
            "prr": signal.prr,
            "ror": signal.ror,
            "chi_square": signal.chi_square,
            "strength": signal.strength,
        },
        "supporting_posts": supporting_posts,
        "reasoning_trace": {
            "signal_criteria": "PRR >= 2 AND chi² >= 4 AND count >= 3",
            "evans_minimum": 3,
            "prr_threshold_strong": 5,
            "prr_threshold_moderate": 2,
        },
    }


@router.get("/export/pvpi-csv")
def export_pvpi_csv(db: Session = Depends(get_db)):
    """Export signals in PvPI-compatible CSV format."""
    signals = db.query(Signal).order_by(Signal.prr.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "drug", "symptom", "post_count", "prr", "ror",
        "chi_square", "strength", "signal_date",
    ])

    for s in signals:
        writer.writerow([
            s.drug, s.symptom, s.post_count,
            round(s.prr, 4), round(s.ror, 4), round(s.chi_square, 4),
            s.strength, str(s.first_seen),
        ])

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=algopharma_pvpi_signals.csv"},
    )
