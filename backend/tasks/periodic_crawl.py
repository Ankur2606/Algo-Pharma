"""
AlgoPharma — Periodic Crawl Tick Task.

Runs every 15 minutes via Celery Beat.
Checks all projects with crawl_frequency set and re-crawls any that are due.
Calls the EXACT same crawl tasks as the one-time pipeline — no new crawl logic.
"""
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# How many seconds each frequency interval represents
FREQUENCY_INTERVALS: dict[str, int] = {
    "realtime": 15 * 60,        # 15 minutes
    "daily":    24 * 60 * 60,   # 24 hours
    "weekly":   7 * 24 * 60 * 60,  # 7 days
}


def _is_due(project, now: datetime) -> bool:
    """Return True if this project's next crawl is overdue."""
    freq = project.crawl_frequency
    if freq not in FREQUENCY_INTERVALS:
        return False  # unknown frequency — skip

    interval = FREQUENCY_INTERVALS[freq]

    if project.last_crawled_at is None:
        # Never crawled periodically yet — but we do an immediate crawl on creation,
        # so treat 'never' as due only if the project is older than the interval.
        age = (now - project.created_at.replace(tzinfo=timezone.utc)).total_seconds()
        return age >= interval

    last = project.last_crawled_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)

    elapsed = (now - last).total_seconds()
    return elapsed >= interval


def periodic_crawl_tick() -> dict:
    """
    The Beat tick. Runs every 15 minutes.
    Finds all projects due for a periodic crawl and dispatches their crawl tasks.
    """
    from database import SessionLocal
    from models import Project

    now = datetime.now(timezone.utc)
    triggered = []
    skipped = 0

    logger.info("[periodic_tick] Starting periodic crawl check...")

    with SessionLocal() as session:
        # Only fetch projects with a crawl_frequency set
        projects = (
            session.query(Project)
            .filter(Project.crawl_frequency.isnot(None))
            .all()
        )

        logger.info(f"[periodic_tick] Found {len(projects)} project(s) with periodic crawl enabled.")

        for project in projects:
            if not _is_due(project, now):
                skipped += 1
                continue

            _dispatch_crawl(project)
            triggered.append(project.id)

            # Update last_crawled_at immediately to prevent double-firing
            project.last_crawled_at = now
            session.commit()

    result = {
        "triggered": triggered,
        "skipped": skipped,
        "checked_at": now.isoformat(),
    }
    logger.info(f"[periodic_tick] Done | triggered={triggered} | skipped={skipped}")
    return result


def _dispatch_crawl(project) -> None:
    """
    Dispatch the appropriate crawl task for a project.
    Reads medicine from the project name (format: medicine_source_YYYYMMDD_HHMMSS).
    Re-uses the same Celery tasks used by the one-time pipeline.
    """
    from celery_app import celery_app

    name_parts = project.name.split("_")
    # Strip the last two parts (date + time stamp)
    without_ts = name_parts[:-2]

    src_words = {"reddit", "twitter", "custom", "forum"}
    medicine = " ".join(p for p in without_ts if p.lower() not in src_words) or "unknown"
    source_raw = "_".join(p for p in without_ts if p.lower() in src_words) or ""

    logger.info(
        f"[periodic_tick] Dispatching crawl | project_id={project.id} | "
        f"medicine={medicine!r} | source={source_raw!r} | freq={project.crawl_frequency}"
    )

    if source_raw in ("custom_forum", "forum", "custom"):
        # Resolve the forum URL from the Source table via ProjectSource link
        _dispatch_forum_crawl(project, medicine)
    elif source_raw == "twitter":
        celery_app.send_task(
            "algopharma.crawl_twitter",
            kwargs={"project_id": project.id, "query": f"{medicine} side effects"},
        )
    else:
        # Default: reddit
        celery_app.send_task(
            "algopharma.crawl_reddit",
            kwargs={"project_id": project.id, "query": f"{medicine} side effects"},
        )


def _dispatch_forum_crawl(project, medicine: str) -> None:
    """Look up the forum URL and dispatch crawl_forum task."""
    from database import SessionLocal
    from models import ProjectSource, Source
    from tasks.crawl_forum import crawl_forum
    import threading

    forum_url = None
    with SessionLocal() as session:
        ps = (
            session.query(ProjectSource)
            .filter(ProjectSource.project_id == project.id)
            .first()
        )
        if ps:
            src = session.get(Source, ps.source_id)
            if src:
                forum_url = src.url

    if not forum_url:
        logger.warning(
            f"[periodic_tick] No forum URL found for project_id={project.id} — skipping."
        )
        return

    logger.info(f"[periodic_tick] Forum crawl | project_id={project.id} | url={forum_url!r}")
    # Run in a background thread (same pattern as the main pipeline)
    threading.Thread(
        target=crawl_forum,
        kwargs={
            "project_id": project.id,
            "forum_url": forum_url,
            "medicine": medicine,
            "symptom": "",
        },
        daemon=True,
    ).start()
