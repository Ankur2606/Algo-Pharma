"""
AlgoPharma — Chat API router.

POST /api/chat
  - Receives {message, state} from frontend.
  - Calls Nemotron slot-filler to update state.
  - If state is READY (medicine + source filled):
      * Creates a Project row in SQLite DB.
      * Launches llm_agent as a FastAPI BackgroundTask.
      * Returns {ready: true, project_id, bot_message}.
  - Otherwise returns {ready: false, bot_message, state}.

No session storage — the frontend owns and persists the state dict.
"""

import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


# ── Request / Response models ─────────────────────────────
class ChatRequest(BaseModel):
    message: str
    state: dict = {"medicine": None, "source": None, "symptom": None, "forum_url": None, "source_id": None}


class ChatResponse(BaseModel):
    ready: bool
    bot_message: str
    state: dict
    project_id: int | None = None


# ── Helpers ───────────────────────────────────────────────
def _build_query(state: dict) -> str:
    """Convert the gathered state dict into an llm_agent query string."""
    med    = state["medicine"]
    source = state["source"]
    symp   = state.get("symptom")

    q = f"Side effects of Medicine: {med}\nSource: {source}"
    if symp:
        q += f" focusing on {symp}"
    return q


def _create_project(name: str, user_id: int | None = None, crawl_frequency: str | None = None) -> int:
    """Insert a new Project row and return its integer ID."""
    from database import SessionLocal
    from models import Project
    from datetime import datetime, timezone

    with SessionLocal() as session:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_name = f"{name[:120]}_{ts}"
        project = Project(
            name=unique_name,
            description=f"Auto-created by chat pipeline: {name}",
            user_id=user_id,
            crawl_frequency=crawl_frequency,
            # Mark first crawl time so periodic tick knows when to next fire
            last_crawled_at=datetime.now(timezone.utc) if crawl_frequency else None,
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        return project.id


def _get_user_id_from_request(request: Request) -> int | None:
    """Decode the JWT bearer token and return the user's DB id, or None."""
    from jose import jwt, JWTError
    from config import get_settings
    from database import SessionLocal
    from models import User

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        settings = get_settings()
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username:
            with SessionLocal() as s:
                user = s.query(User).filter(User.username == username).first()
                return user.id if user else None
    except JWTError:
        return None


async def _run_forum_pipeline(project_id: int, forum_url: str, medicine: str, symptom: str | None):
    """
    Background task for custom_forum.
    Bypasses Gemini tool-selection — we already know the tool is forum_onboarding.
    """
    import asyncio
    from tasks.crawl_forum import crawl_forum
    try:
        result = await asyncio.to_thread(
            crawl_forum,
            project_id=project_id,
            forum_url=forum_url,
            medicine=medicine,
            symptom=symptom or "",
        )
        logger.info(f"[forum_pipeline] Completed | project_id={project_id} | result={result}")
    except Exception as e:
        logger.error(f"[forum_pipeline] Failed | project_id={project_id} | error={e}")


# ── Endpoint ──────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, raw_request: Request, background_tasks: BackgroundTasks):
    """
    Main chat endpoint.  Frontend calls this every time the user sends a message.
    The frontend owns the `state` dict — it persists it in memory and sends it
    back each turn.
    """
    from agentic.chat_manager import get_nemotron_response, READY_SIGNAL

    # 1. Update state via Nemotron
    try:
        new_state, bot_message = get_nemotron_response(request.message, request.state)
    except Exception as e:
        logger.error(f"[/api/chat] chat_manager failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")

    # 2. Not ready yet — return next question
    if bot_message != READY_SIGNAL:
        return ChatResponse(
            ready=False,
            bot_message=bot_message,
            state=new_state,
        )

    # 3. READY — create project + fire background pipeline
    try:
        med       = new_state.get("medicine", "unknown")
        source    = new_state.get("source",   "unknown")
        symp      = new_state.get("symptom")
        forum_url = new_state.get("forum_url")
        # crawl_frequency: try new_state first, fall back to original request.state
        # (Groq may strip unknown fields even with setdefault)
        crawl_frequency = new_state.get("crawl_frequency") or request.state.get("crawl_frequency")

        project_name = f"{med}_{source}" + (f"_{symp}" if symp else "")
        user_id      = _get_user_id_from_request(raw_request)
        project_id   = _create_project(project_name, user_id=user_id, crawl_frequency=crawl_frequency)
        logger.info(f"[/api/chat] Project created | id={project_id} | freq={crawl_frequency!r}")

        # ── Route by source ──────────────────────────────────────
        # custom_forum → Direct pipeline (no Gemini tool-selection needed)
        # reddit/twitter → Gemini agent picks the right crawler
        source_id = new_state.get("source_id")

        # If forum_url not in state but source_id is set, look up URL from DB
        if source == "custom_forum" and not forum_url and source_id:
            from database import SessionLocal
            from models import Source as SourceModel
            with SessionLocal() as db_session:
                src = db_session.get(SourceModel, int(source_id))
                if src and src.url:
                    forum_url = src.url
                    logger.info(
                        f"[/api/chat] Resolved forum_url from source_id={source_id} | url={forum_url!r}"
                    )
                else:
                    logger.warning(f"[/api/chat] source_id={source_id} not found in DB")

        if source == "custom_forum" and forum_url:
            logger.info(
                f"[/api/chat] Forum pipeline triggered | project_id={project_id} | "
                f"url={forum_url!r} | medicine={med!r}"
            )
            background_tasks.add_task(
                _run_forum_pipeline, project_id, forum_url, med, symp
            )
        else:
            query = _build_query(new_state)
            logger.info(f"[/api/chat] LLM agent triggered | project_id={project_id} | query={query!r}")
            from llm_module import llm_agent
            background_tasks.add_task(llm_agent, query, project_id)

        return ChatResponse(
            ready=True,
            bot_message="Analysis started! Redirecting to your dashboard...",
            state=new_state,
            project_id=project_id,
        )

    except Exception as e:
        logger.error(f"[/api/chat] Pipeline launch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")
