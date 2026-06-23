"""
AlgoPharma — Integration test suite.
Each test is independent and prints PASS or FAIL with reason.
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["FAST_MODE"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///./db/algopharma_test.db"


def run_tests():
    # Ensure a completely fresh test database at start
    try:
        os.remove("db/algopharma_test.db")
    except OSError:
        pass

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    results = []

    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║         🧪 AlgoPharma — Test Pipeline               ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    # ── Test 1: Config loads correctly ───────────────────
    try:
        from config import get_settings
        s = get_settings()
        assert s.FAST_MODE is False
        assert s.DATABASE_URL != ""
        results.append(("Config loads correctly", True, ""))
    except Exception as e:
        results.append(("Config loads correctly", False, str(e)))

    # ── Test 2: Database creates tables ──────────────────
    try:
        from database import init_db, SessionLocal
        init_db()
        with SessionLocal() as session:
            from sqlalchemy import text
            r = session.execute(text("SELECT 1"))
            assert r.scalar() == 1
        results.append(("Database creates tables", True, ""))
    except Exception as e:
        results.append(("Database creates tables", False, str(e)))

    # ── Test 3: PII redaction catches Aadhaar ────────────
    try:
        from nlp.pii_guard import redact_pii
        r = redact_pii("My Aadhaar is 1234 5678 9012")
        assert "[AADHAAR]" in r["redacted_text"]
        results.append(("PII catches Aadhaar", True, ""))
    except Exception as e:
        results.append(("PII catches Aadhaar", False, str(e)))

    # ── Test 4: NER finds Dolo 650 ──────────────────────
    try:
        from nlp.ner_pipeline import extract_entities
        ents = extract_entities("I took Dolo 650 yesterday")
        drug_names = [d["text"].lower() for d in ents["drugs"]]
        assert any("dolo" in d for d in drug_names), f"Got: {drug_names}"
        results.append(("NER finds 'Dolo 650' as drug", True, ""))
    except Exception as e:
        results.append(("NER finds 'Dolo 650' as drug", False, str(e)))

    # ── Test 5: NER finds nausea ────────────────────────
    try:
        from nlp.ner_pipeline import extract_entities
        ents = extract_entities("I had terrible nausea all day")
        symp_names = [s["text"].lower() for s in ents["symptoms"]]
        assert "nausea" in symp_names, f"Got: {symp_names}"
        results.append(("NER finds 'nausea' as symptom", True, ""))
    except Exception as e:
        results.append(("NER finds 'nausea' as symptom", False, str(e)))

    # ── Test 6: Sentiment scores negative ───────────────
    try:
        from nlp.sentiment import analyze_sentiment
        r = analyze_sentiment("This medicine gave me terrible side effects, worst experience ever")
        assert r["label"] == "NEGATIVE", f"Got: {r['label']}"
        results.append(("Sentiment scores negative", True, ""))
    except Exception as e:
        results.append(("Sentiment scores negative", False, str(e)))

    # ── Test 7: Negation marks 'no nausea' ──────────────
    try:
        from nlp.negation import check_negation
        r = check_negation("no nausea", [{"text": "nausea", "start": 3}])
        assert r.get("nausea") is True, f"Got: {r}"
        results.append(("Negation marks 'no nausea'", True, ""))
    except Exception as e:
        results.append(("Negation marks 'no nausea'", False, str(e)))

    # ── Test 8: AE detector flags positive case ─────────
    try:
        from nlp.ae_detector import detect_ae
        r = detect_ae("Dolo 650 gave me terrible nausea and headache")
        assert r["ae_flag"] is True, f"Got ae_flag={r['ae_flag']}, reason={r['reason']}"
        results.append(("AE detector flags drug+symptom+negative", True, ""))
    except Exception as e:
        results.append(("AE detector flags drug+symptom+negative", False, str(e)))

    # ── Test 9: AE detector rejects negated symptom ─────
    try:
        from nlp.ae_detector import detect_ae
        r = detect_ae("Dolo 650 is great, no nausea no headache at all, wonderful medicine!")
        # This should not flag (positive sentiment + negation)
        assert r["ae_flag"] is False, f"Got ae_flag={r['ae_flag']}, reason={r['reason']}"
        results.append(("AE detector rejects negated/positive", True, ""))
    except Exception as e:
        results.append(("AE detector rejects negated/positive", False, str(e)))

    # ── Test 10: JSON ingestion processes posts ─────────
    try:
        from database import init_db
        init_db()
        from tasks.ingest_existing import ingest_all
        r = ingest_all()
        assert r["total_ingested"] > 0, f"Ingested: {r['total_ingested']}"
        results.append(("JSON ingestion processes posts", True, f"{r['total_ingested']} posts"))
    except Exception as e:
        results.append(("JSON ingestion processes posts", False, str(e)))

    # ── Test 11: Signal detection runs ──────────────────
    try:
        from nlp.signal_detector import detect_signals
        signals = detect_signals()
        results.append(("Signal detection runs", True, f"{len(signals)} signals"))
    except Exception as e:
        results.append(("Signal detection runs", False, str(e)))

    # ── Test 12: FastAPI app imports ────────────────────
    try:
        from main import app
        assert app is not None
        assert app.title == "AlgoPharma"
        results.append(("FastAPI app starts (import)", True, ""))
    except Exception as e:
        results.append(("FastAPI app starts (import)", False, str(e)))

    # ── Print results ────────────────────────────────────
    print()
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)

    for i, (name, ok, detail) in enumerate(results, 1):
        icon = "✅" if ok else "❌"
        detail_str = f" ({detail})" if detail else ""
        print(f"  {icon} {i:2d}. {name}{detail_str}")

    print()
    print(f"  {'═'*50}")
    color = "✅" if passed == total else "⚠️ "
    print(f"  {color} {passed}/{total} tests passed")
    print(f"  {'═'*50}")

    # Cleanup test DB
    try:
        os.remove("db/algopharma_test.db")
    except OSError:
        pass

    return passed, total


if __name__ == "__main__":
    run_tests()
