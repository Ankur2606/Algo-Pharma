"""
AlgoPharma — Demo data seeder.
Master setup script — run first on demo day.
"""

import sys
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def seed():
    """Seed database with demo project, sources, keywords, and ingested data."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    from database import init_db, SessionLocal
    from models import Project, Source, Keyword, ProjectSource
    from tasks.ingest_existing import ingest_all
    from nlp.signal_detector import detect_signals

    # ── 1. Create tables ─────────────────────────────────
    init_db()
    print("✅ Database ready")

    with SessionLocal() as session:
        # ── 2. Default project ───────────────────────────
        project = session.query(Project).filter(Project.name == "Dolo 650 Safety Monitor").first()
        if not project:
            project = Project(
                name="Dolo 650 Safety Monitor",
                description="Pharmacovigilance monitoring for Dolo 650 and related paracetamol formulations",
            )
            session.add(project)
            session.commit()
            session.refresh(project)
            print("✅ Created project: Dolo 650 Safety Monitor")
        else:
            print("ℹ️  Project already exists: Dolo 650 Safety Monitor")

        project_id = project.id

        # ── 3. Sources ───────────────────────────────────
        for name, platform, url in [
            ("Reddit Search", "reddit", "https://www.reddit.com/search.json"),
            ("Twitter Search", "twitter", "https://api.twitterapi.io"),
        ]:
            existing = session.query(Source).filter(Source.name == name).first()
            if not existing:
                source = Source(name=name, platform=platform, url=url)
                session.add(source)
                session.commit()
                session.refresh(source)
                # Link to project
                ps = ProjectSource(project_id=project_id, source_id=source.id)
                session.add(ps)
                session.commit()
                print(f"  ✅ Source: {name}")

        # ── 4. Keywords ──────────────────────────────────
        keywords = [
            ("Dolo 650", ["dolo", "dolo650"]),
            ("paracetamol 650", ["paracetamol", "acetaminophen"]),
            ("dolo side effects", []),
            ("dolo nausea", []),
            ("dolo fever", []),
            ("dolo liver", ["dolo liver damage"]),
        ]
        for term, synonyms in keywords:
            existing = session.query(Keyword).filter(
                Keyword.project_id == project_id, Keyword.term == term
            ).first()
            if not existing:
                kw = Keyword(
                    project_id=project_id,
                    term=term,
                    synonyms=json.dumps(synonyms),
                )
                session.add(kw)
        session.commit()
        print("  ✅ Keywords seeded")

    # ── 5. Ingest data ───────────────────────────────────
    print("\n📥 Loading Reddit data...")
    result = ingest_all(project_id)

    r = result["reddit"]
    t = result["twitter"]
    r_rate = (r["ae_flagged"] / max(1, r["ingested"])) * 100 if r["ingested"] else 0
    t_rate = (t["ae_flagged"] / max(1, t["ingested"])) * 100 if t["ingested"] else 0

    print(f"📊 Reddit: {r['ingested']} posts, {r['ae_flagged']} AE flags ({r_rate:.1f}%)")
    print(f"📊 Twitter: {t['ingested']} posts, {t['ae_flagged']} AE flags ({t_rate:.1f}%)")

    # ── 6. Detect signals ────────────────────────────────
    print("\n🔍 Detecting signals...")
    signals = detect_signals(project_id)

    for s in signals:
        icon = {"STRONG": "🔴", "MODERATE": "🟡", "WEAK": "🟢"}.get(s["strength"], "⚪")
        print(f"  {icon} {s['strength']:10s}: {s['drug']} + {s['symptom']} | PRR={s['prr']:.2f}")

    # ── 7. Summary ───────────────────────────────────────
    total = result["total_ingested"]
    total_ae = result["total_ae_flagged"]
    ae_rate = (total_ae / max(1, total)) * 100

    print(f"\n{'═'*55}")
    print(f"  📊 SUMMARY")
    print(f"{'═'*55}")
    print(f"  Total posts ingested : {total}")
    print(f"  AE flags             : {total_ae} ({ae_rate:.1f}%)")
    print(f"  Signals detected     : {len(signals)}")
    print(f"{'═'*55}")

    # ── 8. Instructions ──────────────────────────────────
    print(f"\n  Run: uv run python main.py")
    print(f"  API docs: http://localhost:8000/docs")
    print(f"  Demo endpoint: http://localhost:8000/api/demo/run")

    return {"total": total, "ae_flagged": total_ae, "signals": len(signals)}


if __name__ == "__main__":
    import os
    # Default to FAST_MODE for demo setup speed
    if "FAST_MODE" not in os.environ:
        os.environ["FAST_MODE"] = "true"
    seed()
