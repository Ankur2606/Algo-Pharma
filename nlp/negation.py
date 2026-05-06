"""
AlgoPharma — Pure spaCy negation detection.
Two methods: dependency parsing + sliding window.
No medspaCy dependency.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path for standalone script execution
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

logger = logging.getLogger(__name__)

NEGATION_CUES = {
    "no", "not", "never", "without", "none", "neither", "nor",
    "denies", "denied", "deny", "absent",
    "don't", "doesn't", "didn't", "wasn't", "isn't", "aren't",
    "haven't", "hasn't", "can't", "won't", "nothing", "nowhere",
    "dont", "doesnt", "didnt", "wasnt", "isnt", "arent",
    "havent", "hasnt", "cant", "wont",
}

# Two-word cues checked as bigrams
NEGATION_BIGRAMS = {"free from", "no longer"}


def check_negation(text: str, symptom_spans: list[dict]) -> dict[str, bool]:
    """
    Check whether each symptom span is negated in the text.

    Args:
        text: The full text.
        symptom_spans: List of dicts with at least {"text": "nausea", "start": int}.

    Returns:
        {symptom_text: True/False} where True means negated.
    """
    from nlp.models_loader import get_models
    nlp = get_models().get("spacy")

    results: dict[str, bool] = {}
    if not symptom_spans:
        return results

    text_lower = text.lower()

    # ── METHOD 1 — Dependency parsing ────────────────────
    if nlp is not None:
        doc = nlp(text)
        for span_info in symptom_spans:
            symptom_text = span_info["text"].lower()
            negated = False

            for token in doc:
                if token.text.lower() == symptom_text or symptom_text.startswith(token.text.lower()):
                    # Walk dependency tree — children + ancestors
                    connected = list(token.children) + list(token.ancestors)
                    connected.append(token)
                    for conn in connected:
                        if conn.dep_ == "neg" or conn.text.lower() in NEGATION_CUES:
                            negated = True
                            break
                    if negated:
                        break
            results[span_info["text"]] = negated
    else:
        # Initialise with False when spaCy unavailable — sliding window only
        for span_info in symptom_spans:
            results[span_info["text"]] = False

    # ── METHOD 2 — Sliding window (3 words before symptom) ─
    words = text_lower.split()
    for span_info in symptom_spans:
        symptom_text = span_info["text"].lower()
        symptom_words = symptom_text.split()
        # Find the symptom's position in the word list
        for i in range(len(words)):
            if words[i:i + len(symptom_words)] == symptom_words:
                window_start = max(0, i - 3)
                window = words[window_start:i]
                # Single-word cues
                for w in window:
                    if w in NEGATION_CUES:
                        results[span_info["text"]] = True
                        break
                # Bigram cues
                window_text = " ".join(window)
                for bigram in NEGATION_BIGRAMS:
                    if bigram in window_text:
                        results[span_info["text"]] = True
                break

    return results


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    import os
    os.environ["FAST_MODE"] = "false"

    tests = [
        ("no nausea", [{"text": "nausea", "start": 3}], True),
        ("severe nausea", [{"text": "nausea", "start": 7}], False),
        ("patient denied headache", [{"text": "headache", "start": 16}], True),
        ("experiencing nausea and vomiting", [{"text": "nausea", "start": 14}], False),
    ]

    print("=" * 55)
    print("  Negation Detection — Self-test")
    print("=" * 55)
    all_pass = True
    for text, spans, expected in tests:
        result = check_negation(text, spans)
        symptom = spans[0]["text"]
        got = result.get(symptom, False)
        ok = got == expected
        if not ok:
            all_pass = False
        print(f"  {'✅' if ok else '❌'} \"{text}\" → {symptom} negated={got} (expected {expected})")

    print("─" * 55)
    print(f"{'✅' if all_pass else '❌'} negation self-test {'PASS' if all_pass else 'FAIL'}")
