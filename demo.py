"""
AlgoPharma — Standalone demo runner.
Calls everything in sequence without needing the API server.
"""

import sys
import json
import os


def run_demo():
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    if "FAST_MODE" not in os.environ:
        os.environ["FAST_MODE"] = "true"

    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║          🧬 AlgoPharma — Pharmacovigilance          ║")
    print("║        Social Listening Platform Demo                ║")
    print("║                                                      ║")
    print("║  Hackathon: AI for Bharat — HackerEarth (Theme 6)   ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    # ── 1. Seed database ─────────────────────────────────
    print("═" * 55)
    print("  STEP 1: Database Setup & Data Ingestion")
    print("═" * 55)
    from seed_demo_data import seed
    summary = seed()

    # ── 2. Signal summary table ──────────────────────────
    print()
    print("═" * 55)
    print("  STEP 2: Signal Summary")
    print("═" * 55)

    from database import SessionLocal
    from models import Signal

    with SessionLocal() as session:
        signals = session.query(Signal).order_by(Signal.prr.desc()).all()

        if signals:
            print(f"\n  {'Drug':<20s} {'Symptom':<20s} {'Count':>5s} {'PRR':>6s} {'ROR':>6s} {'χ²':>6s} {'Strength'}")
            print(f"  {'─'*20} {'─'*20} {'─'*5} {'─'*6} {'─'*6} {'─'*6} {'─'*10}")
            for s in signals:
                print(f"  {s.drug:<20s} {s.symptom:<20s} {s.post_count:>5d} "
                      f"{s.prr:>6.2f} {s.ror:>6.2f} {s.chi_square:>6.2f} {s.strength}")
        else:
            print("  No signals detected.")

    # ── 3. Top supporting posts per signal ───────────────
    print()
    print("═" * 55)
    print("  STEP 3: Top Supporting Posts per Signal")
    print("═" * 55)

    from models import ProcessedPost, RawPost

    with SessionLocal() as session:
        for signal in session.query(Signal).order_by(Signal.prr.desc()).limit(5).all():
            icon = {"STRONG": "🔴", "MODERATE": "🟡", "WEAK": "🟢"}.get(signal.strength, "⚪")
            print(f"\n  {icon} {signal.drug} + {signal.symptom} ({signal.strength})")
            print(f"  {'─'*50}")

            try:
                post_ids = json.loads(signal.supporting_post_ids)
            except (json.JSONDecodeError, TypeError):
                post_ids = []

            for pid in post_ids[:5]:
                pp = session.query(ProcessedPost).filter(ProcessedPost.raw_post_id == pid).first()
                raw = session.get(RawPost, pid)
                if pp and raw:
                    platform = raw.source_platform
                    text = pp.redacted_text[:80].replace("\n", " ")
                    print(f"    [{platform}] conf={pp.ae_confidence:.2f} → {text}...")

    # ── 4. Source health ─────────────────────────────────
    print()
    print("═" * 55)
    print("  STEP 4: Source Health")
    print("═" * 55)

    from models import Source
    with SessionLocal() as session:
        sources = session.query(Source).all()
        for s in sources:
            print(f"  {s.name:<25s} platform={s.platform:<10s} active={s.is_active}")

    # ── 5. Instructions ──────────────────────────────────
    print()
    print("═" * 55)
    print("  NEXT STEPS")
    print("═" * 55)
    print("  Start API server:  uv run python main.py")
    print("  API docs:          http://localhost:8000/docs")
    print("  Demo endpoint:     http://localhost:8000/api/demo/run")
    print("  Signal list:       http://localhost:8000/api/projects/1/signals")
    print("  PvPI CSV export:   http://localhost:8000/api/export/pvpi-csv")
    print()


if __name__ == "__main__":
    run_demo()
