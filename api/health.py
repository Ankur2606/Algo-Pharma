"""
AlgoPharma — Health & agentic API router.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Source, SourceHealth, ProjectSource

router = APIRouter(prefix="/api", tags=["Health & Agentic"])


@router.get("/health/sources")
def get_source_health(db: Session = Depends(get_db)):
    sources = db.query(Source).all()
    result = []
    for s in sources:
        health = db.query(SourceHealth).filter(SourceHealth.source_id == s.id).first()
        result.append({
            "id": s.id,
            "name": s.name,
            "platform": s.platform,
            "url": s.url,
            "is_active": s.is_active,
            "health_score": health.health_score if health else 1.0,
            "last_success": str(health.last_success) if health and health.last_success else None,
            "consecutive_failures": health.consecutive_failures if health else 0,
        })
    return result


class ForumOnboardRequest(BaseModel):
    url: str


class ForumApproveRequest(BaseModel):
    url: str
    config: dict


@router.post("/agentic/onboard-forum")
def onboard_forum_endpoint(body: ForumOnboardRequest):
    from agentic.forum_onboarding import onboard_forum
    result = onboard_forum(body.url)
    return result


@router.post("/agentic/approve-forum")
def approve_forum(body: ForumApproveRequest, db: Session = Depends(get_db)):
    # Save approved forum config to sources table
    existing = db.query(Source).filter(Source.url == body.url).first()
    if existing:
        existing.config_json = body.config  # JSONB — pass dict directly
        existing.is_active = True
        db.commit()
        return {"status": "updated", "source_id": existing.id}

    source = Source(
        name=body.config.get("forum_type", "custom") + " forum",
        platform="forum",
        url=body.url,
        config_json=body.config,  # JSONB — pass dict directly
        is_active=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return {"status": "created", "source_id": source.id}
