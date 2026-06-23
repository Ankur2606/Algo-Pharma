from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import jwt, JWTError
import bcrypt
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db
from models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    settings = get_settings()
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class UserRegister(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: Optional[str] = "admin"  # Default to admin for POC


@router.post("/register")
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email or user_data.username,
        hashed_password=hashed_password,
        role=user_data.role or "admin",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"status": "success", "message": "User created successfully"}


@router.post("/login")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == form_data.username).first()

    is_valid = False
    # POC Bypass: hardcoded admin credentials
    if form_data.username == "admin@example.com" and form_data.password == "admin123":
        is_valid = True
    elif user:
        try:
            is_valid = verify_password(form_data.password, user.hashed_password)
        except Exception:
            pass

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # If using the hardcoded admin bypass, ensure username is set
    username = user.username if user else form_data.username
    role = user.role if user else ("admin" if form_data.username == "admin@example.com" else "viewer")

    if user:
        user.last_login = datetime.now(timezone.utc)
        db.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username, "role": role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "role": role}
