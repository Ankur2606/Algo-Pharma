"""
AlgoPharma — Analytics API router.

Provides aggregated data endpoints to power frontend dashboard charts.
All endpoints are auth-protected and respect user/admin ownership rules.

Endpoints:
  GET /api/projects/{id}/analytics/ae-trend          — AE flag counts over time (line chart)
  GET /api/projects/{id}/analytics/sentiment         — Sentiment breakdown (pie/donut chart)
  GET /api/projects/{id}/analytics/top-symptoms      — Top N most-reported symptoms (bar chart)
  GET /api/projects/{id}/analytics/prr-chart         — PRR score vs symptom (pharmacovigilance chart)
  GET /api/projects/{id}/analytics/platform-breakdown — Post count by platform (pie/bar chart)
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.user_auth import get_current_user
from database import get_db
from models import ProcessedPost, Project, RawPost, Signal, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["Analytics"])


# ── Shared helpers ────────────────────────────────────────────────────────────

def _check_project_access(project_id: int, db: Session, current_user: User) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if current_user.role != "admin" and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this project")
    return project


def _as_dict(value) -> dict:
    """Safely parse JSONB dict or legacy JSON string into a Python dict."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


# ── 1. AE Trend ───────────────────────────────────────────────────────────────
@router.get("/{project_id}/analytics/ae-trend")
def ae_trend(
    project_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of past days to include"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns daily counts of AE-flagged vs non-AE posts over the last N days.
    Use this data to draw a time-series line chart on the dashboard.

    Response shape:
      [{"date": "2024-01-01", "ae_true": 5, "ae_false": 30, "total": 35}, ...]
    """
    _check_project_access(project_id, db, current_user)

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    posts = (
        db.query(ProcessedPost)
        .filter(
            ProcessedPost.project_id == project_id,
            ProcessedPost.processed_at >= cutoff,
        )
        .all()
    )

    by_day: dict[str, dict] = defaultdict(lambda: {"ae_true": 0, "ae_false": 0, "total": 0})
    for post in posts:
        day = (post.processed_at or datetime.now(timezone.utc)).date().isoformat()
        by_day[day]["total"] += 1
        if post.ae_flag:
            by_day[day]["ae_true"] += 1
        else:
            by_day[day]["ae_false"] += 1

    return {
        "project_id": project_id,
        "days": days,
        "total_ae":     sum(v["ae_true"] for v in by_day.values()),
        "total_non_ae": sum(v["ae_false"] for v in by_day.values()),
        "data": [
            {"date": day, **vals}
            for day, vals in sorted(by_day.items())
        ],
    }


# ── 2. Sentiment Breakdown ────────────────────────────────────────────────────
@router.get("/{project_id}/analytics/sentiment")
def sentiment_breakdown(
    project_id: int,
    ae_only: bool = Query(False, description="If true, only include AE-flagged posts"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns counts of Positive / Negative / Neutral / Unknown sentiments.
    Use this to draw a pie or donut chart on the dashboard.

    Response shape:
      {
        "labels": ["POSITIVE", "NEGATIVE", "NEUTRAL", "UNKNOWN"],
        "counts": [45, 120, 30, 5],
        "percentages": [22.5, 60.0, 15.0, 2.5],
        "total": 200
      }
    """
    _check_project_access(project_id, db, current_user)

    query = db.query(ProcessedPost).filter(ProcessedPost.project_id == project_id)
    if ae_only:
        query = query.filter(ProcessedPost.ae_flag == True)   # noqa: E712

    posts = query.all()

    counts: Counter = Counter({"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0, "UNKNOWN": 0})
    for post in posts:
        sentiment = _as_dict(post.sentiment_json)
        label = str(sentiment.get("label", "UNKNOWN")).upper()
        # Normalise short labels from some models
        if label in ("POS",):
            label = "POSITIVE"
        elif label in ("NEG",):
            label = "NEGATIVE"
        elif label in ("NEU",):
            label = "NEUTRAL"
        if label not in counts:
            label = "UNKNOWN"
        counts[label] += 1

    total = sum(counts.values()) or 1
    ordered_labels = ["POSITIVE", "NEGATIVE", "NEUTRAL", "UNKNOWN"]
    ordered_counts = [counts[l] for l in ordered_labels]

    return {
        "project_id": project_id,
        "ae_only": ae_only,
        "labels":      ordered_labels,
        "counts":      ordered_counts,
        "percentages": [round(c / total * 100, 1) for c in ordered_counts],
        "total":       sum(counts.values()),
    }


# ── 3. Top Symptoms ───────────────────────────────────────────────────────────
@router.get("/{project_id}/analytics/top-symptoms")
def top_symptoms(
    project_id: int,
    limit:   int  = Query(15, ge=1, le=50,  description="Max symptoms to return"),
    ae_only: bool = Query(True,              description="Only count AE-flagged posts"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the most frequently reported symptoms across processed posts.
    Use this data to draw a horizontal bar chart on the dashboard.

    Response shape:
      {
        "symptoms": ["headache", "nausea", ...],
        "counts":   [45, 30, ...],
        "total_unique_symptoms": 87
      }
    """
    _check_project_access(project_id, db, current_user)

    query = db.query(ProcessedPost).filter(ProcessedPost.project_id == project_id)
    if ae_only:
        query = query.filter(ProcessedPost.ae_flag == True)   # noqa: E712

    posts = query.all()

    symptom_counts: Counter = Counter()
    for post in posts:
        entities = _as_dict(post.entities_json)
        for symptom in entities.get("symptoms", []):
            name = (
                symptom.get("text", "") if isinstance(symptom, dict) else str(symptom)
            ).strip().lower()
            if name:
                symptom_counts[name] += 1

    top = symptom_counts.most_common(limit)
    return {
        "project_id": project_id,
        "ae_only":    ae_only,
        "symptoms":   [s for s, _ in top],
        "counts":     [c for _, c in top],
        "total_unique_symptoms": len(symptom_counts),
    }


# ── 4. PRR Chart (Primary Pharmacovigilance Chart) ────────────────────────────
@router.get("/{project_id}/analytics/prr-chart")
def prr_chart(
    project_id: int,
    min_prr: float = Query(0.0,  description="Minimum PRR score to include"),
    limit:   int   = Query(25, ge=1, le=100, description="Max drug-symptom pairs to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns PRR scores per drug-symptom pair — the PRIMARY pharmacovigilance chart.
    Plot symptom on X-axis, PRR score on Y-axis, color-coded by strength.

    Response shape:
      {
        "pairs": [
          {"drug": "dolo365", "symptom": "headache", "prr": 4.5, "ror": 3.2,
           "chi_square": 8.1, "strength": "STRONG", "post_count": 12},
          ...
        ],
        "total_signals": 8,
        "strength_summary": {"STRONG": 2, "MODERATE": 4, "WEAK": 2}
      }
    """
    _check_project_access(project_id, db, current_user)

    signals = (
        db.query(Signal)
        .filter(Signal.project_id == project_id, Signal.prr >= min_prr)
        .order_by(Signal.prr.desc())
        .limit(limit)
        .all()
    )

    pairs = [
        {
            "signal_id":  s.id,
            "drug":       s.drug,
            "symptom":    s.symptom,
            "prr":        round(s.prr, 3),
            "ror":        round(s.ror, 3),
            "chi_square": round(s.chi_square, 3),
            "strength":   s.strength,
            "post_count": s.post_count,
        }
        for s in signals
    ]

    strength_summary = Counter(s.strength for s in signals)
    return {
        "project_id": project_id,
        "pairs":      pairs,
        "total_signals": len(pairs),
        "strength_summary": {
            "STRONG":   strength_summary.get("STRONG", 0),
            "MODERATE": strength_summary.get("MODERATE", 0),
            "WEAK":     strength_summary.get("WEAK", 0),
        },
    }


# ── 5. Platform Breakdown ─────────────────────────────────────────────────────
@router.get("/{project_id}/analytics/platform-breakdown")
def platform_breakdown(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns post counts grouped by source platform (reddit, twitter, forum, etc.).
    Use this data to draw a pie or grouped bar chart.

    Response shape:
      {
        "platforms": ["reddit", "twitter", "forum"],
        "counts":    [120, 45, 30],
        "ae_counts": [30, 12, 8],
        "total_posts": 195,
        "total_ae": 50
      }
    """
    _check_project_access(project_id, db, current_user)

    raw_posts = (
        db.query(RawPost)
        .filter(RawPost.project_id == project_id)
        .all()
    )

    ae_platform_counts: Counter = Counter()
    total_platform_counts: Counter = Counter()

    raw_post_ids_with_platform = {rp.id: (rp.source_platform or "unknown").strip().lower()
                                   for rp in raw_posts}
    for platform in raw_post_ids_with_platform.values():
        total_platform_counts[platform] += 1

    # Fetch AE-flagged processed posts and join platform via raw_post_id
    ae_posts = (
        db.query(ProcessedPost)
        .filter(
            ProcessedPost.project_id == project_id,
            ProcessedPost.ae_flag == True,  # noqa: E712
        )
        .all()
    )
    for pp in ae_posts:
        platform = raw_post_ids_with_platform.get(pp.raw_post_id, "unknown")
        ae_platform_counts[platform] += 1

    platforms = sorted(total_platform_counts.keys())
    return {
        "project_id":  project_id,
        "platforms":   platforms,
        "counts":      [total_platform_counts[p] for p in platforms],
        "ae_counts":   [ae_platform_counts.get(p, 0) for p in platforms],
        "total_posts": sum(total_platform_counts.values()),
        "total_ae":    sum(ae_platform_counts.values()),
    }
