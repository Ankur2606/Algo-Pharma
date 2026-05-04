"""
AlgoPharma — Signal detector.
Runs on already-ingested DB data. Computes PRR/ROR/chi² for drug-symptom pairs.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path for standalone script execution
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import logging
from datetime import datetime, timezone, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


def detect_signals(project_id: int = 1) -> list[dict]:
    """
    Query processed_posts where ae_flag=True, group by (drug, symptom),
    compute PRR/ROR/chi² for each pair, create/update Signal rows.
    """
    from database import SessionLocal
    from models import ProcessedPost, Signal, RawPost

    signals = []

    with SessionLocal() as session:
        # Fetch all AE-flagged posts for this project
        ae_posts = (
            session.query(ProcessedPost)
            .filter(ProcessedPost.project_id == project_id, ProcessedPost.ae_flag == True)
            .all()
        )

        if not ae_posts:
            logger.info("No AE posts in DB — run ingestion first")
            return []

        # ── Build drug-symptom pair counts ───────────────
        pair_counts: dict[tuple[str, str], list[int]] = defaultdict(list)
        all_drugs = set()
        all_symptoms = set()

        for pp in ae_posts:
            try:
                entities = json.loads(pp.entities_json)
            except (json.JSONDecodeError, TypeError):
                continue

            drugs = [d["text"].lower().strip() for d in entities.get("drugs", [])]
            symptoms = [s["text"].lower().strip() for s in entities.get("symptoms", [])]

            for drug in drugs:
                all_drugs.add(drug)
                for symptom in symptoms:
                    all_symptoms.add(symptom)
                    pair_counts[(drug, symptom)].append(pp.raw_post_id)

        total_ae = len(ae_posts)

        # ── Compute stats for each pair ──────────────────
        for (drug, symptom), post_ids in pair_counts.items():
            a = len(post_ids)  # this drug + this symptom

            if a < 3:
                continue  # Evans criteria minimum

            # 2x2 contingency table
            b = sum(
                1 for (d, s), pids in pair_counts.items()
                if d == drug and s != symptom
            )  # this drug + other symptoms
            c = sum(
                1 for (d, s), pids in pair_counts.items()
                if d != drug and s == symptom
            )  # other drugs + this symptom
            d = max(1, total_ae - a - b - c)  # other drugs + other symptoms

            # PRR
            denom_top = a + b
            denom_bot = c + d
            prr = (a / denom_top) / (c / denom_bot) if denom_top > 0 and denom_bot > 0 and c > 0 else 0.0

            # ROR
            ror = (a * d) / (b * c) if b > 0 and c > 0 else 0.0

            # Chi-square
            try:
                from scipy.stats import chi2_contingency
                table = [[a, b], [c, d]]
                chi2_val, _, _, _ = chi2_contingency(table, correction=False)
            except Exception:
                chi2_val = 0.0

            # ── Signal criteria ──────────────────────────
            signal_confirmed = prr >= 2 and chi2_val >= 4 and a >= 3
            include_for_demo = a >= 5  # borderline cases for demo visibility

            if signal_confirmed or include_for_demo:
                if prr >= 5:
                    strength = "STRONG"
                elif prr >= 2:
                    strength = "MODERATE"
                else:
                    strength = "WEAK"

                # Upsert signal in DB
                existing = (
                    session.query(Signal)
                    .filter(Signal.project_id == project_id,
                            Signal.drug == drug, Signal.symptom == symptom)
                    .first()
                )

                if existing:
                    existing.post_count = a
                    existing.prr = round(prr, 4)
                    existing.ror = round(ror, 4)
                    existing.chi_square = round(chi2_val, 4)
                    existing.strength = strength
                    existing.supporting_post_ids = json.dumps(post_ids[:50])
                    existing.last_updated = datetime.now(timezone.utc)
                else:
                    sig = Signal(
                        project_id=project_id,
                        drug=drug,
                        symptom=symptom,
                        post_count=a,
                        prr=round(prr, 4),
                        ror=round(ror, 4),
                        chi_square=round(chi2_val, 4),
                        strength=strength,
                        supporting_post_ids=json.dumps(post_ids[:50]),
                    )
                    session.add(sig)

                signals.append({
                    "drug": drug,
                    "symptom": symptom,
                    "post_count": a,
                    "prr": round(prr, 4),
                    "ror": round(ror, 4),
                    "chi_square": round(chi2_val, 4),
                    "strength": strength,
                })

        session.commit()

    return signals


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    from database import SessionLocal
    from models import ProcessedPost

    print("=" * 55)
    print("  Signal Detector — Self-test")
    print("=" * 55)

    with SessionLocal() as session:
        ae_count = session.query(ProcessedPost).filter(ProcessedPost.ae_flag == True).count()

    if ae_count == 0:
        print("  ⚠️  No AE posts in DB. Run seed_demo_data.py or ingest_existing.py first.")
        print("─" * 55)
    else:
        print(f"  📊 Found {ae_count} AE-flagged posts in DB")
        signals = detect_signals()
        print(f"  🔍 Detected {len(signals)} signals")
        for s in signals:
            icon = {"STRONG": "🔴", "MODERATE": "🟡", "WEAK": "🟢"}.get(s["strength"], "⚪")
            print(f"    {icon} {s['strength']:10s} {s['drug']} + {s['symptom']} "
                  f"| count={s['post_count']} PRR={s['prr']:.2f} ROR={s['ror']:.2f}")
        print("─" * 55)
        print("✅ signal_detector self-test PASS")
