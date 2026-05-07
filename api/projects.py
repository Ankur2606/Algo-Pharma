# """
# AlgoPharma — Projects API router.
# """

# import json
# from fastapi import APIRouter, Depends, HTTPException
# from pydantic import BaseModel
# from sqlalchemy.orm import Session

# from database import get_db
# from models import Project, Keyword

# router = APIRouter(prefix="/api/projects", tags=["Projects"])


# class ProjectCreate(BaseModel):
#     name: str
#     description: str = ""


# class KeywordCreate(BaseModel):
#     term: str
#     synonyms: list[str] = []


# @router.post("")
# def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
#     existing = db.query(Project).filter(Project.name == body.name).first()
#     if existing:
#         raise HTTPException(status_code=409, detail="Project with this name already exists")
#     project = Project(name=body.name, description=body.description)
#     db.add(project)
#     db.commit()
#     db.refresh(project)
#     return {"id": project.id, "name": project.name, "description": project.description}


# @router.get("")
# def list_projects(db: Session = Depends(get_db)):
#     projects = db.query(Project).all()
#     return [
#         {"id": p.id, "name": p.name, "description": p.description,
#          "created_at": str(p.created_at)}
#         for p in projects
#     ]


# @router.post("/{project_id}/keywords")
# def add_keyword(project_id: int, body: KeywordCreate, db: Session = Depends(get_db)):
#     project = db.get(Project, project_id)
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")
#     kw = Keyword(
#         project_id=project_id,
#         term=body.term,
#         synonyms=json.dumps(body.synonyms),
#     )
#     db.add(kw)
#     db.commit()
#     db.refresh(kw)
#     return {"id": kw.id, "term": kw.term, "synonyms": body.synonyms}


# @router.get("/{project_id}/keywords")
# def list_keywords(project_id: int, db: Session = Depends(get_db)):
#     project = db.get(Project, project_id)
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")
#     keywords = db.query(Keyword).filter(Keyword.project_id == project_id).all()
#     return [
#         {"id": k.id, "term": k.term, "synonyms": json.loads(k.synonyms) if k.synonyms else []}
#         for k in keywords
#     ]



"""
AlgoPharma — Projects API router (auth-protected).

All endpoints require a valid JWT Bearer token.
Users can only see/modify their own projects.
Admins can see all projects.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Project, Keyword, User
from api.user_auth import get_current_user, require_admin

router = APIRouter(prefix="/api/projects", tags=["Projects"])


class ProjectCreate(BaseModel):
    name: str
    description: str = ""


class KeywordCreate(BaseModel):
    term: str
    synonyms: list[str] = []


def _check_project_access(project: Project, current_user: User):
    """Raise 403 if a non-admin user tries to access another user's project."""
    if current_user.role != "admin" and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this project")


@router.post("")
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Project).filter(Project.name == body.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Project with this name already exists")

    project = Project(
        name=body.name,
        description=body.description,
        user_id=current_user.id,   # ← always taken from JWT, never from request body
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"id": project.id, "name": project.name, "description": project.description}


@router.get("")
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Admins see all projects. Regular users see only their own."""
    if current_user.role == "admin":
        projects = db.query(Project).all()
    else:
        projects = db.query(Project).filter(Project.user_id == current_user.id).all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "created_at": str(p.created_at),
            "user_id": p.user_id,
        }
        for p in projects
    ]


@router.get("/{project_id}")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _check_project_access(project, current_user)
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": str(project.created_at),
        "user_id": project.user_id,
    }


@router.post("/{project_id}/keywords")
def add_keyword(
    project_id: int,
    body: KeywordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _check_project_access(project, current_user)

    kw = Keyword(
        project_id=project_id,
        term=body.term,
        synonyms=body.synonyms,
    )
    db.add(kw)
    db.commit()
    db.refresh(kw)
    return {"id": kw.id, "term": kw.term, "synonyms": body.synonyms}


@router.get("/{project_id}/keywords")
def list_keywords(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _check_project_access(project, current_user)

    keywords = db.query(Keyword).filter(Keyword.project_id == project_id).all()
    return [
        {"id": k.id, "term": k.term, "synonyms": k.synonyms if k.synonyms else []}
        for k in keywords
    ]