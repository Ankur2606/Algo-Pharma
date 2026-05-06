"""
AlgoPharma — Sentiment analysis.
Primary: cardiffnlp/twitter-roberta-base-sentiment-latest
Fallback: VADER
Regional: Sarvam AI translation → English sentiment
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path for standalone script execution
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

logger = logging.getLogger(__name__)

# Label mapping for cardiffnlp model
ROBERTA_LABEL_MAP = {
    "LABEL_0": "NEGATIVE",
    "LABEL_1": "NEUTRAL",
    "LABEL_2": "POSITIVE",
    "negative": "NEGATIVE",
    "neutral": "NEUTRAL",
    "positive": "POSITIVE",
}

SARVAM_LANG_MAP = {
    "hi": "hi-IN", "ta": "ta-IN", "te": "te-IN", "kn": "kn-IN",
    "ml": "ml-IN", "mr": "mr-IN", "bn": "bn-IN", "gu": "gu-IN",
    "pa": "pa-IN", "or": "or-IN",
}

REGIONAL_LANGS = set(SARVAM_LANG_MAP.keys())


def _vader_sentiment(text: str, vader) -> dict:
    """Run VADER sentiment analysis."""
    scores = vader.polarity_scores(text)
    compound = scores["compound"]
    if compound <= -0.05:
        label = "NEGATIVE"
    elif compound >= 0.05:
        label = "POSITIVE"
    else:
        label = "NEUTRAL"
    return {"label": label, "score": abs(compound), "model": "vader"}


def analyze_sentiment(text: str, lang: str = "en") -> dict:
    """
    Analyse sentiment of text. Assumes text is already English if regional.
    Returns: {label, score, model}
    """
    from nlp.models_loader import get_models

    models = get_models()
    vader = models.get("vader")
    sentiment_model = models.get("sentiment_model")

    # ── Primary: RoBERTa sentiment model ─────────────────
    if sentiment_model is not None:
        try:
            result = sentiment_model(text[:512])[0]
            raw_label = result["label"]
            label = ROBERTA_LABEL_MAP.get(raw_label, raw_label.upper())
            output = {
                "label": label,
                "score": round(result["score"], 4),
                "model": "cardiffnlp/twitter-roberta-base-sentiment-latest",
            }
            return output
        except Exception as e:
            logger.warning(f"RoBERTa sentiment failed, falling back to VADER: {e}")

    # ── Fallback: VADER ──────────────────────────────────
    if vader is not None:
        output = _vader_sentiment(text, vader)
        return output

    return {"label": "NEUTRAL", "score": 0.0, "model": "none"}


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    import os
    os.environ["FAST_MODE"] = "false"

    tests = [
        ("Terrible side effects from this medicine, never again!", "en", "NEGATIVE"),
        ("This medicine worked great, feeling much better now!", "en", "POSITIVE"),
        ("I took the medicine as prescribed.", "en", "NEUTRAL"),
        ("dolo 650 se bahut zyada nausea ho raha hai bro", "en", "NEGATIVE"),
    ]

    print("=" * 55)
    print("  Sentiment Analysis — Self-test")
    print("=" * 55)
    all_pass = True
    for text, lang, expected in tests:
        result = analyze_sentiment(text, lang)
        ok = result["label"] == expected
        if not ok:
            all_pass = False
        print(f"  {'✅' if ok else '⚠️ '} \"{text[:45]}...\"")
        print(f"       → {result['label']} (score={result['score']:.2f}, model={result['model']}) expected={expected}")

    print("─" * 55)
    print(f"{'✅' if all_pass else '⚠️ '} sentiment self-test {'PASS' if all_pass else 'PARTIAL'}")
