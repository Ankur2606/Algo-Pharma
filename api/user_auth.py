"""
AlgoPharma — Authentication system.

Endpoints:
  POST /api/auth/register   — create account (admin or user role)
  POST /api/auth/login      — returns JWT access token
  GET  /api/auth/me         — returns current user info

JWT flow:
  - Login returns a Bearer token
  - Every protected endpoint calls get_current_user() dependency
  - Token carries user_id + role — no need to send them manually

Roles:
  admin — full access to everything
  user  — can only access their own projects/results
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated
from sqlalchemy.exc import SQLAlchemyError
import traceback
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import get_db
from models import User
from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# ── Crypto config ─────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

router = APIRouter(prefix="/api/auth", tags=["Auth"])


# ── Schemas ───────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "user"  # "user" or "admin"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    role: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    created_at: str


# ── Password helpers ──────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ───────────────────────────────────────────
def create_access_token(user_id: int, username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Auth dependency — use this in every protected endpoint ─
def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    user_id = int(payload.get("sub", 0))
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency — raises 403 if user is not admin."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ── Endpoints ─────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user. Role must be 'user' or 'admin'."""

    try:
        if body.role not in ("user", "admin"):
            logger.warning(f"[auth] Invalid role attempted: {body.role}")
            raise HTTPException(
                status_code=400,
                detail="Role must be 'user' or 'admin'"
            )

        if db.query(User).filter(User.email == body.email).first():
            logger.warning(f"[auth] Email already registered: {body.email}")
            raise HTTPException(
                status_code=409,
                detail="Email already registered"
            )


        user = User(
            username=body.username,
            email=body.email,
            hashed_password= body.password,
            role=body.role,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(
            f"[auth] New user registered: {user.username} (role={user.role})"
        )

        token = create_access_token(user.id, user.username, user.role)

        return TokenResponse(
            access_token=token,
            user_id=user.id,
            username=user.username,
            role=user.role,
        )

    except HTTPException as e:
        # Already meaningful errors
        logger.error(f"[auth] HTTP Error: {e.detail}")
        raise e

    except SQLAlchemyError as e:
        db.rollback()

        logger.exception("[auth] Database error during registration")

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

    except Exception as e:
        db.rollback()

        logger.exception("[auth] Unexpected registration error")

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"Unexpected server error: {str(e)}"
        )
@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Login with email + password.
    Use email in the 'username' field (standard OAuth2 form).
    Returns a JWT Bearer token.
    """
    user = db.query(User).filter(User.email == form.username).first()
    if not user or form.password != user.hashed_password:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id, user.username, user.role)
    logger.info(f"[auth] User logged in: {user.username} (role={user.role})")

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        role=user.role,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the currently logged-in user's info."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        created_at=str(current_user.created_at),
    )