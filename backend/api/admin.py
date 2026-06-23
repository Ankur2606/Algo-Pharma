"""
AlgoPharma — Admin API router.
Handles Source Management, User Management, and System Configuration.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import json

from database import get_db
from models import User, Project, Source, SourceHealth, PendingOnboarding, SystemConfig

router = APIRouter(prefix="/api/admin", tags=["admin"])

# --- Source Management Models ---
class SourceCreate(BaseModel):
    name: str
    platform: str
    url: str
    config_json: dict

class SourceUpdate(BaseModel):
    config_json: Optional[dict] = None

class TestConnectionReq(BaseModel):
    server_url: str
    config_json: dict

class ForumOnboardingReq(BaseModel):
    forum_url: str

# --- User Management Models ---
class UserInviteReq(BaseModel):
    email: str
    role: str = "viewer"

class UserRoleUpdate(BaseModel):
    role: str

class UserStatusUpdate(BaseModel):
    is_active: bool

# --- System Config Models ---
class ConfigUpdateReq(BaseModel):
    key_name: str
    encrypted_value: str


# ==========================================
# 1. Source Management
# ==========================================

@router.get("/sources")
def list_sources(db: Session = Depends(get_db)):
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
            "health_score": health.health_score if health else None,
            "last_updated": s.created_at
        })
    return result

@router.post("/sources")
def add_source(payload: SourceCreate, db: Session = Depends(get_db)):
    # Normalize platform: treat 'forum' as 'custom_forum' for consistency
    platform = payload.platform
    if platform == "forum":
        platform = "custom_forum"

    source = Source(
        name=payload.name,
        platform=platform,
        url=payload.url,
        config_json=json.dumps(payload.config_json)
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return {"status": "success", "source_id": source.id}

@router.post("/sources/test")
def test_source_connection(payload: TestConnectionReq):
    """Test if a source URL is reachable and scrapable via Firecrawl."""
    import logging
    log = logging.getLogger(__name__)

    if not payload.server_url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL")

    platform = payload.config_json.get("platform", "custom_forum")
    log.info(f"[source_test] ▶ Starting test | url={payload.server_url!r} | platform={platform!r}")

    if platform in ("reddit", "twitter"):
        log.info(f"[source_test] ✅ Platform '{platform}' uses its own crawler — no Firecrawl needed.")
        return {"status": "success", "message": f"'{platform}' uses its own live crawler. No Firecrawl test needed."}

    try:
        from config import get_settings
        settings = get_settings()

        if not settings.FIRECRAWL_API_KEY:
            log.error("[source_test] ❌ FIRECRAWL_API_KEY is not set in .env")
            raise HTTPException(
                status_code=503,
                detail="FIRECRAWL_API_KEY is not configured. Set it in .env to test forum sources."
            )

        log.info("[source_test] 🔑 Firecrawl API key found — initializing client...")
        from firecrawl import Firecrawl
        fc = Firecrawl(api_key=settings.FIRECRAWL_API_KEY)

        log.info(f"[source_test] 🌐 Sending scrape request to Firecrawl for: {payload.server_url}")
        result = fc.scrape(payload.server_url, formats=["markdown"])
        md = getattr(result, "markdown", "")

        if not md:
            log.warning(f"[source_test] ⚠️  Firecrawl returned empty content for {payload.server_url}")
            raise HTTPException(status_code=422, detail="Firecrawl returned empty content for this URL.")

        char_count = len(md)
        word_count = len(md.split())
        preview = md[:300].replace("\n", " ").strip()

        try:
            from langdetect import detect as lang_detect
            detected_lang = lang_detect(md[:1000])
        except Exception:
            detected_lang = "unknown"

        log.info(
            f"[source_test] ✅ Success | chars={char_count} | words={word_count} "
            f"| lang={detected_lang!r} | preview={preview[:80]!r}..."
        )

        return {
            "status": "success",
            "message": f"Firecrawl successfully scraped {char_count} characters of content.",
            "details": {
                "url": payload.server_url,
                "characters": char_count,
                "words": word_count,
                "detected_language": detected_lang,
                "content_preview": preview[:300],
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[source_test] ❌ Firecrawl test failed: {e}")
        raise HTTPException(status_code=422, detail=f"Firecrawl test failed: {str(e)}")

@router.put("/sources/{source_id}")
def update_source(source_id: int, payload: SourceUpdate, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if payload.config_json:
        source.config_json = json.dumps(payload.config_json)
    db.commit()
    return {"status": "success", "message": "Source updated"}

@router.patch("/sources/{source_id}/disable")
def disable_source(source_id: int, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.is_active = False
    db.commit()
    return {"status": "success", "message": "Source disabled"}

@router.get("/sources/available")
def get_available_sources(db: Session = Depends(get_db)):
    """
    Return all active custom forum sources.
    Called by the frontend chat UI to show users which forums are available to choose from.
    Accepts both 'custom_forum' and legacy 'forum' platform values.
    """
    sources = db.query(Source).filter(
        Source.is_active == True,
        Source.platform.in_(["custom_forum", "forum"])
    ).all()
    return [
        {"id": s.id, "name": s.name, "url": s.url, "platform": s.platform}
        for s in sources
    ]


@router.post("/onboarding/forum")
def run_forum_onboarding(payload: ForumOnboardingReq, db: Session = Depends(get_db)):
    sample_posts = [{"title": "Sample 1"}, {"title": "Sample 2"}, {"title": "Sample 3"}]
    req = PendingOnboarding(
        forum_url=payload.forum_url,
        sample_posts_json=json.dumps(sample_posts),
        status="pending"
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return {"status": "success", "onboarding_id": req.id, "samples": sample_posts}

@router.post("/onboarding/{req_id}/approve")
def approve_onboarding(req_id: int, db: Session = Depends(get_db)):
    req = db.get(PendingOnboarding, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = "approved"
    source = Source(name=f"Forum {req_id}", platform="forum", url=req.forum_url, config_json="{}")
    db.add(source)
    db.commit()
    return {"status": "success", "message": "Onboarding approved, source added."}

@router.post("/onboarding/{req_id}/reject")
def reject_onboarding(req_id: int, db: Session = Depends(get_db)):
    req = db.get(PendingOnboarding, req_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    req.status = "rejected"
    db.commit()
    return {"status": "success", "message": "Onboarding rejected."}


# ==========================================
# 2. User Management
# ==========================================

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    res = []
    for u in users:
        proj_count = db.query(Project).filter(Project.user_id == u.id).count()
        res.append({
            "id": u.id,
            "username": u.username,
            "email": u.email or u.username,
            "role": u.role,
            "last_login": u.last_login,
            "project_count": proj_count,
            "is_active": getattr(u, "is_active", True)
        })
    return res

@router.post("/users/invite")
def invite_user(payload: UserInviteReq, db: Session = Depends(get_db)):
    return {"status": "success", "message": f"Invite sent to {payload.email}"}

@router.patch("/users/{user_id}/role")
def change_user_role(user_id: int, payload: UserRoleUpdate, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.role = payload.role
    db.commit()
    return {"status": "success"}

@router.patch("/users/{user_id}/status")
def change_user_status(user_id: int, payload: UserStatusUpdate, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u.is_active = payload.is_active
    db.commit()
    return {"status": "success"}

@router.get("/users/{user_id}/projects")
def get_user_projects(user_id: int, db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.user_id == user_id).all()
    return [{"id": p.id, "name": p.name} for p in projects]


# ==========================================
# 3. System Configuration
# ==========================================

@router.put("/credentials")
def set_credentials(payload: ConfigUpdateReq, db: Session = Depends(get_db)):
    conf = db.query(SystemConfig).filter(SystemConfig.key_name == payload.key_name).first()
    if conf:
        conf.encrypted_value = payload.encrypted_value
    else:
        conf = SystemConfig(key_name=payload.key_name, encrypted_value=payload.encrypted_value)
        db.add(conf)
    db.commit()
    return {"status": "success"}

@router.put("/alerts/config")
def set_alerts_config(payload: ConfigUpdateReq, db: Session = Depends(get_db)):
    conf = db.query(SystemConfig).filter(SystemConfig.key_name == f"alert_{payload.key_name}").first()
    if conf:
        conf.encrypted_value = payload.encrypted_value
    else:
        conf = SystemConfig(key_name=f"alert_{payload.key_name}", encrypted_value=payload.encrypted_value)
        db.add(conf)
    db.commit()
    return {"status": "success"}
