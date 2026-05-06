"""
AlgoPharma — Four-gate Adverse Event detector.
Fully explainable — every decision has a logged reason.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path for standalone script execution
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

logger = logging.getLogger(__name__)


def detect_ae(
    text: str,
    lang: str = "en",
    entities: dict | None = None,
    sentiment: dict | None = None,
) -> dict:
    """
    Four-gate AE detection.

    Gate 1: At least one drug entity found
    Gate 2: At least one symptom entity found
    Gate 3: Sentiment label is NEGATIVE
    Gate 4: Not all symptoms are negated

    Args:
        text: The (redacted) text to analyse.
        lang: Language code from ingestion.
        entities: Pre-computed {drugs, symptoms} or None.
        sentiment: Pre-computed {label, score, model} or None.

    Returns:
        Full AE result dict.
    """
    from nlp.ner_pipeline import extract_entities
    from nlp.sentiment import analyze_sentiment
    from nlp.negation import check_negation

    # ── Compute NLP components if not pre-provided ───────
    if entities is None:
        entities = extract_entities(text)
    if sentiment is None:
        sentiment = analyze_sentiment(text, lang)

    drugs = entities.get("drugs", [])
    symptoms = entities.get("symptoms", [])

    result = {
        "ae_flag": False,
        "confidence": 0.0,
        "gate_failed": None,
        "reason": "",
        "drug": None,
        "all_drugs": [d["text"] for d in drugs],
        "symptoms_non_negated": [],
        "symptoms_negated": [],
        "entities": entities,
        "sentiment": sentiment,
        "model_versions": {},
    }

    # ── Gate 1: Drug present ─────────────────────────────
    if not drugs:
        result["gate_failed"] = 1
        result["reason"] = "no_drug"
        return result

    # ── Gate 2: Symptom present ──────────────────────────
    if not symptoms:
        result["gate_failed"] = 2
        result["reason"] = "no_symptom"
        return result

    # ── Gate 3: Negative sentiment ───────────────────────
    if sentiment.get("label") != "NEGATIVE":
        result["gate_failed"] = 3
        result["reason"] = f"not_negative (got {sentiment.get('label')})"
        return result

    # ── Gate 4: Not all symptoms negated ─────────────────
    negation_results = check_negation(text, symptoms)
    non_negated = [s["text"] for s in symptoms if not negation_results.get(s["text"], False)]
    negated = [s["text"] for s in symptoms if negation_results.get(s["text"], False)]

    result["symptoms_non_negated"] = non_negated
    result["symptoms_negated"] = negated

    if not non_negated:
        result["gate_failed"] = 4
        result["reason"] = "all_negated"
        return result

    # ── All gates passed ─────────────────────────────────
    result["ae_flag"] = True
    result["confidence"] = round(sentiment.get("score", 0.5) * 0.9, 4)
    result["drug"] = drugs[0]["text"]
    result["gate_failed"] = None
    result["reason"] = "drug+symptom+negative_sentiment+no_negation"
    result["model_versions"] = {
        "sentiment": sentiment.get("model", "unknown"),
        "ner_drugs": drugs[0].get("source", "unknown"),
        "ner_symptoms": symptoms[0].get("source", "unknown"),
    }

    return result


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    import os
    os.environ["FAST_MODE"] = "flase"

    tests = [
        # (text, expected_ae_flag, expected_gate_or_None)
        ("Dolo 650 gave me terrible nausea and headache", True, None),
        ("The weather is nice today", False, 1),                      # no drug
        ("Dolo 650 is a popular medicine", False, 2),                 # no symptom
        ("Dolo 650 cured my headache completely, amazing!", False, 3), # positive sentiment
        ("No nausea or headache after taking Dolo 650, works great", False, 3),  # positive + negated
    ]

    print("=" * 55)
    print("  AE Detector — Self-test")
    print("=" * 55)
    all_pass = True
    for text, expected_flag, expected_gate in tests:
        result = detect_ae(text)
        ok = result["ae_flag"] == expected_flag
        if expected_gate is not None:
            ok = ok and result["gate_failed"] == expected_gate
        if not ok:
            all_pass = False
        gate_info = f"gate={result['gate_failed']}" if result['gate_failed'] else "ALL PASSED"
        print(f"  {'✅' if ok else '❌'} ae={result['ae_flag']} {gate_info:20s} → \"{text[:50]}\"")
        print(f"       reason: {result['reason']}")

    print("─" * 55)
    print(f"{'✅' if all_pass else '❌'} ae_detector self-test {'PASS' if all_pass else 'FAIL'}")
