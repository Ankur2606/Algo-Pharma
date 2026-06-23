"""
One-time migration: add crawl_frequency and last_crawled_at to the projects table.
SQLAlchemy create_all() won't add columns to existing tables, so we do it manually.
Safe to run multiple times — skips columns that already exist.
"""
import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "db" / "algopharma.db"

def migrate():
    if not DB_PATH.exists():
        print(f"DB not found at {DB_PATH} — skipping migration (init_db will create fresh tables).")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # Check existing columns
    cur.execute("PRAGMA table_info(projects)")
    existing_cols = {row[1] for row in cur.fetchall()}

    added = []
    if "crawl_frequency" not in existing_cols:
        cur.execute("ALTER TABLE projects ADD COLUMN crawl_frequency VARCHAR(20) DEFAULT NULL")
        added.append("crawl_frequency")

    if "last_crawled_at" not in existing_cols:
        cur.execute("ALTER TABLE projects ADD COLUMN last_crawled_at DATETIME DEFAULT NULL")
        added.append("last_crawled_at")

    conn.commit()
    conn.close()

    if added:
        print(f"[OK] Migration complete - added columns: {added}")
    else:
        print("[OK] Migration skipped - columns already exist.")


if __name__ == "__main__":
    migrate()
