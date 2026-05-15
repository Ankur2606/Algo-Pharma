"""
AlgoPharma — SQLAlchemy ORM models. All 12 tables.
Uses DeclarativeBase (SQLAlchemy 2.0 style).
"""

import sys
from datetime import datetime, timezone
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# ── 1. Users ──────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# ── 2. Projects ──────────────────────────────────────────
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    # Periodic crawling fields — NULL means one-time crawl (existing behaviour)
    crawl_frequency: Mapped[str] = mapped_column(String(20), nullable=True, default=None)
    last_crawled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    keywords = relationship("Keyword", back_populates="project", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="project", cascade="all, delete-orphan")


# ── 3. Keywords ──────────────────────────────────────────
class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    term: Mapped[str] = mapped_column(String(200), nullable=False)
    synonyms: Mapped[str] = mapped_column(Text, default="")  # JSON list as text
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    project = relationship("Project", back_populates="keywords")


# ── 4. Sources ───────────────────────────────────────────
class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # reddit, twitter, forum
    url: Mapped[str] = mapped_column(String(500), default="")
    config_json: Mapped[str] = mapped_column(Text, default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# ── 5. ProjectSources (M2M) ─────────────────────────────
class ProjectSource(Base):
    __tablename__ = "project_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=False)


# ── 6. RawPosts ──────────────────────────────────────────
class RawPost(Base):
    __tablename__ = "raw_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=True)
    thread_id: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(String(500), default="")
    title: Mapped[str] = mapped_column(Text, default="")
    body: Mapped[str] = mapped_column(Text, default="")
    author_hash: Mapped[str] = mapped_column(String(64), default="")
    lang: Mapped[str] = mapped_column(String(10), default="en")
    source_platform: Mapped[str] = mapped_column(String(50), default="unknown")
    posted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    replies = relationship("PostReply", back_populates="raw_post", cascade="all, delete-orphan")
    processed = relationship("ProcessedPost", back_populates="raw_post", uselist=False,
                             cascade="all, delete-orphan")


# ── 7. PostReplies ───────────────────────────────────────
class PostReply(Base):
    __tablename__ = "post_replies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raw_post_id: Mapped[int] = mapped_column(Integer, ForeignKey("raw_posts.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")
    author_hash: Mapped[str] = mapped_column(String(64), default="")
    posted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    raw_post = relationship("RawPost", back_populates="replies")


# ── 8. ProcessedPosts ────────────────────────────────────
class ProcessedPost(Base):
    __tablename__ = "processed_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raw_post_id: Mapped[int] = mapped_column(Integer, ForeignKey("raw_posts.id"), unique=True, nullable=False)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    redacted_text: Mapped[str] = mapped_column(Text, default="")
    entities_json: Mapped[str] = mapped_column(Text, default="{}")    # JSON: {drugs:[], symptoms:[]}
    sentiment_json: Mapped[str] = mapped_column(Text, default="{}")   # JSON: {label, score, model}
    negation_json: Mapped[str] = mapped_column(Text, default="{}")    # JSON: {symptom: bool}
    ae_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    ae_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    ae_reason: Mapped[str] = mapped_column(Text, default="")
    thread_score: Mapped[float] = mapped_column(Float, default=0.0)
    thread_color: Mapped[str] = mapped_column(String(10), default="red")
    pii_entities_found: Mapped[str] = mapped_column(Text, default="[]")
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    raw_post = relationship("RawPost", back_populates="processed")


# ── 9. Signals ───────────────────────────────────────────
class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    drug: Mapped[str] = mapped_column(String(200), nullable=False)
    symptom: Mapped[str] = mapped_column(String(200), nullable=False)
    post_count: Mapped[int] = mapped_column(Integer, default=0)
    prr: Mapped[float] = mapped_column(Float, default=0.0)
    ror: Mapped[float] = mapped_column(Float, default=0.0)
    chi_square: Mapped[float] = mapped_column(Float, default=0.0)
    strength: Mapped[str] = mapped_column(String(20), default="WEAK")  # STRONG / MODERATE / WEAK
    supporting_post_ids: Mapped[str] = mapped_column(Text, default="[]")  # JSON list of post IDs
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    project = relationship("Project", back_populates="signals")


# ── 10. SourceHealth ─────────────────────────────────────
class SourceHealth(Base):
    __tablename__ = "source_health"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=False)
    health_score: Mapped[float] = mapped_column(Float, default=1.0)
    last_success: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_failure: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# ── 11. CrawlLog ────────────────────────────────────────
class CrawlLog(Base):
    __tablename__ = "crawl_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("sources.id"), nullable=False)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="started")  # started/success/failed
    posts_found: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


# ── 12. AuditLog ────────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# ── 13. SystemConfig ──────────────────────────────────────
class SystemConfig(Base):
    __tablename__ = "system_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    encrypted_value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# ── 14. PendingOnboarding ─────────────────────────────────
class PendingOnboarding(Base):
    __tablename__ = "pending_onboarding"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    forum_url: Mapped[str] = mapped_column(String(500), nullable=False)
    sample_posts_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/approved/rejected
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    from database import init_db, SessionLocal

    init_db()
    print("✅ All tables created")

    with SessionLocal() as session:
        p = Project(name="__test_project__", description="self-test")
        session.add(p)
        session.commit()
        session.refresh(p)
        assert p.id is not None
        fetched = session.get(Project, p.id)
        assert fetched is not None and fetched.name == "__test_project__"
        session.delete(fetched)
        session.commit()

    print("✅ CRUD round-trip PASS")
