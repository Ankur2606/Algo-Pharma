"""
AlgoPharma — Sentiment analysis.
Primary: cardiffnlp/twitter-roberta-base-sentiment-latest
Fallback: VADER
Regional: Sarvam AI translation → English sentiment
"""

import sys
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


def _translate_with_sarvam(text: str, lang: str, api_key: str) -> str | None:
    """Translate regional text to English using Sarvam AI SDK."""
    try:
        from sarvamai import SarvamAI
        client = SarvamAI(api_subscription_key=api_key)
        source_lang = SARVAM_LANG_MAP.get(lang)
        if not source_lang:
            return None
        response = client.text.translate(
            input=text[:500],  # keep API call small
            source_language_code=source_lang,
            target_language_code="en-IN",
        )
        return response.translated_text
    except Exception as e:
        logger.warning(f"Sarvam translation failed: {e}")
        return None


def analyze_sentiment(text: str, lang: str = "en") -> dict:
    """
    Analyse sentiment of text.
    Returns: {label, score, model, translated_text (optional)}
    """
    from nlp.models_loader import get_models
    from config import get_settings

    models = get_models()
    settings = get_settings()
    vader = models.get("vader")
    sentiment_model = models.get("sentiment_model")

    translated_text = None

    # ── Regional language → translate first ───────────────
    if lang in REGIONAL_LANGS and settings.SARVAM_API_KEY:
        translated = _translate_with_sarvam(text, lang, settings.SARVAM_API_KEY)
        if translated:
            translated_text = translated
            text = translated  # run sentiment on English translation
            logger.info(f"Translated {lang} → en via Sarvam")
        else:
            logger.warning("Sarvam translation failed — falling through to VADER on original text")
    elif lang in REGIONAL_LANGS:
        logger.warning("Sarvam not configured — regional sentiment may be inaccurate")

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
            if translated_text:
                output["translated_text"] = translated_text
            return output
        except Exception as e:
            logger.warning(f"RoBERTa sentiment failed, falling back to VADER: {e}")

    # ── Fallback: VADER ──────────────────────────────────
    if vader is not None:
        output = _vader_sentiment(text, vader)
        if translated_text:
            output["translated_text"] = translated_text
        return output

    return {"label": "NEUTRAL", "score": 0.0, "model": "none"}


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    import os
    os.environ["FAST_MODE"] = "true"

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
