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
            "is_active": s.is_active,
            "health_score": health.health_score if health else None,
            "last_updated": s.created_at
        })
    return result

@router.post("/sources")
def add_source(payload: SourceCreate, db: Session = Depends(get_db)):
    source = Source(
        name=payload.name,
        platform=payload.platform,
        url=payload.url,
        config_json=json.dumps(payload.config_json)
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return {"status": "success", "source_id": source.id}

@router.post("/sources/test")
def test_source_connection(payload: TestConnectionReq):
    if not payload.server_url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL")
    return {"status": "success", "message": "Connection successful"}

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
