"""
AlgoPharma — SQLAlchemy 2.0 database engine and session factory.
Synchronous engine, SQLite, check_same_thread=False.
"""

import sys
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import JSONB
from config import get_settings


_settings = get_settings()

engine = create_engine(
    _settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in _settings.DATABASE_URL else {},
    echo=False,
)

# Enable WAL mode for better concurrency with SQLite
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _connection_record):
    if "sqlite" in _settings.DATABASE_URL:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Session:
    """FastAPI dependency — yields a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables from models.py Base metadata."""
    from models import Base
    Base.metadata.create_all(bind=engine)


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    init_db()
    with SessionLocal() as session:
        result = session.execute(__import__("sqlalchemy").text("SELECT 1"))
        assert result.scalar() == 1
    print("✅ Database engine OK — tables created")

