# """
# AlgoPharma — Chat API router.

# POST /api/chat
#   - Receives {message, state} from frontend.
#   - Calls Nemotron slot-filler to update state.
#   - If state is READY (medicine + source filled):
#       * Creates a Project row in SQLite DB.
#       * Launches llm_agent as a FastAPI BackgroundTask.
#       * Returns {ready: true, project_id, bot_message}.
#   - Otherwise returns {ready: false, bot_message, state}.

# No session storage — the frontend owns and persists the state dict.
# """

# import logging
# from fastapi import APIRouter, BackgroundTasks, HTTPException
# from pydantic import BaseModel

# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/api", tags=["chat"])


# # ── Request / Response models ─────────────────────────────
# class ChatRequest(BaseModel):
#     message: str
#     state: dict = {"medicine": None, "source": None, "symptom": None}


# class ChatResponse(BaseModel):
#     ready: bool
#     bot_message: str
#     state: dict
#     project_id: int | None = None


# # ── Helpers ───────────────────────────────────────────────
# def _build_query(state: dict) -> str:
#     """Convert the gathered state dict into an llm_agent query string."""
#     med    = state["medicine"]
#     source = state["source"]
#     symp   = state.get("symptom")

#     q = f"Find side effects of {med} on {source}"
#     if symp:
#         q += f" focusing on {symp}"
#     return q


# def _create_project(name: str) -> int:
#     """Insert a new Project row and return its integer ID."""
#     from database import SessionLocal
#     from models import Project

#     with SessionLocal() as session:
#         # Avoid unique-constraint errors by appending a timestamp if needed
#         from datetime import datetime
#         ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
#         unique_name = f"{name[:120]}_{ts}"
#         project = Project(name=unique_name, description=f"Auto-created by chat pipeline: {name}")
#         session.add(project)
#         session.commit()
#         session.refresh(project)
#         return project.id


# # ── Endpoint ──────────────────────────────────────────────
# @router.post("/chat", response_model=ChatResponse)
# async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
#     """
#     Main chat endpoint.  Frontend calls this every time the user sends a message.
#     The frontend owns the `state` dict — it persists it in memory and sends it
#     back each turn.
#     """
#     from agentic.chat_manager import get_nemotron_response, READY_SIGNAL

#     # 1. Update state via Nemotron
#     try:
#         new_state, bot_message = get_nemotron_response(request.message, request.state)
#     except Exception as e:
#         logger.error(f"[/api/chat] chat_manager failed: {e}")
#         raise HTTPException(status_code=500, detail=f"LLM error: {e}")

#     # 2. Not ready yet — return next question
#     if bot_message != READY_SIGNAL:
#         return ChatResponse(
#             ready=False,
#             bot_message=bot_message,
#             state=new_state,
#         )

#     # 3. READY — create project + fire background pipeline
#     try:
#         med    = new_state.get("medicine", "unknown")
#         source = new_state.get("source",   "unknown")
#         symp   = new_state.get("symptom")

#         project_name = f"{med}_{source}" + (f"_{symp}" if symp else "")
#         project_id   = _create_project(project_name)
#         query        = _build_query(new_state)

#         logger.info(f"[/api/chat] Pipeline triggered | project_id={project_id} | query={query!r}")

#         # Fire-and-forget: runs llm_agent in the background so we respond immediately
#         from llm_module import llm_agent
#         background_tasks.add_task(llm_agent, query, project_id)

#         return ChatResponse(
#             ready=True,
#             bot_message="Analysis started! Redirecting to your dashboard...",
#             state=new_state,
#             project_id=project_id,
#         )

#     except Exception as e:
#         logger.error(f"[/api/chat] Pipeline launch failed: {e}")
#         raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")









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
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from models import User
from api.user_auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


# ── Request / Response models ─────────────────────────────
class ChatRequest(BaseModel):
    message: str
    state: dict = {"medicine": None, "source": None, "symptom": None}


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

    q = f"Find side effects of {med} on {source}"
    if symp:
        q += f" focusing on {symp}"
    return q


def _create_project(name: str, user_id: int) -> int:          # ← added user_id param
    """Insert a new Project row and return its integer ID."""
    from database import SessionLocal
    from models import Project

    with SessionLocal() as session:
        from datetime import datetime
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_name = f"{name[:120]}_{ts}"
        project = Project(
            name=unique_name,
            description=f"Auto-created by chat pipeline: {name}",
            user_id=user_id,                                   # ← added
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        return project.id


# ── Endpoint ──────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),            # ← added
):
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
        med    = new_state.get("medicine", "unknown")
        source = new_state.get("source",   "unknown")
        symp   = new_state.get("symptom")

        project_name = f"{med}_{source}" + (f"_{symp}" if symp else "")
        project_id   = _create_project(project_name, current_user.id)  # ← pass user_id
        query        = _build_query(new_state)

        logger.info(
            f"[/api/chat] Pipeline triggered | user={current_user.username} "
            f"project_id={project_id} | query={query!r}"
        )

        # Fire-and-forget: runs llm_agent in the background so we respond immediately
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