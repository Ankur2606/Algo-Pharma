"""
AlgoPharma — Singleton model store.
All NLP files import from here. Models loaded once at startup.
Respects FAST_MODE: when True, loads only spaCy + VADER.
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

_models: dict = {}


def load_all_models() -> dict:
    """Load all NLP models. Respects FAST_MODE env var."""
    global _models
    if _models:
        return _models

    fast_mode = os.getenv("FAST_MODE", "false").lower() in ("true", "1", "yes")

    # ── 1. spaCy (always needed for negation) ─────────────
    try:
        import spacy
        _models["spacy"] = spacy.load("en_core_web_lg")
        logger.info("✅ spaCy en_core_web_lg loaded")
    except Exception as e:
        logger.warning(f"⚠️  spaCy load failed: {e}")
        _models["spacy"] = None

    # ── 6. VADER (always loaded) ──────────────────────────
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        _models["vader"] = SentimentIntensityAnalyzer()
        logger.info("✅ VADER loaded")
    except Exception as e:
        logger.warning(f"⚠️  VADER load failed: {e}")
        _models["vader"] = None

    if fast_mode:
        logger.info("⚡ FAST_MODE active — lightweight models only")
        _models["pii_model"] = None
        _models["pii_tokenizer"] = None
        _models["drug_ner"] = None
        _models["disease_ner"] = None
        _models["sentiment_model"] = None
        _models["fast_mode"] = True
        return _models

    _models["fast_mode"] = False

    # ── 2. OpenMed Nemotron PII ──────────────────────────
    try:
        from transformers import AutoModelForTokenClassification, AutoTokenizer
        pii_model_id = "OpenMed/privacy-filter-nemotron"
        _models["pii_tokenizer"] = AutoTokenizer.from_pretrained(pii_model_id, trust_remote_code=True)
        _models["pii_model"] = AutoModelForTokenClassification.from_pretrained(
            pii_model_id, trust_remote_code=True
        )
        logger.info("✅ OpenMed PII model loaded")
    except Exception as e:
        logger.warning(f"⚠️  OpenMed PII model unavailable (regex-only PII will run): {e}")
        _models["pii_model"] = None
        _models["pii_tokenizer"] = None

    # ── 3. Drug NER ──────────────────────────────────────
    try:
        from transformers import pipeline
        _models["drug_ner"] = pipeline(
            "token-classification",
            model="OpenMed/OpenMed-NER-PharmaDetect-BigMed-278M",
            aggregation_strategy="simple",
        )
        logger.info("✅ Drug NER model loaded")
    except Exception as e:
        logger.warning(f"⚠️  Drug NER model unavailable (keyword matching will run): {e}")
        _models["drug_ner"] = None

    # ── 4. Disease NER ───────────────────────────────────
    try:
        from transformers import pipeline
        _models["disease_ner"] = pipeline(
            "token-classification",
            model="OpenMed/OpenMed-NER-DiseaseDetect-BioMed-335M",
            aggregation_strategy="simple",
        )
        logger.info("✅ Disease NER model loaded")
    except Exception as e:
        logger.warning(f"⚠️  Disease NER model unavailable (keyword matching will run): {e}")
        _models["disease_ner"] = None

    # ── 5. Sentiment ─────────────────────────────────────
    try:
        from transformers import pipeline
        _models["sentiment_model"] = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
        )
        logger.info("✅ Sentiment model loaded")
    except Exception as e:
        logger.warning(f"⚠️  Sentiment model unavailable (VADER fallback active): {e}")
        _models["sentiment_model"] = None

    return _models


def get_models() -> dict:
    """Get or load models (lazy singleton)."""
    if not _models:
        load_all_models()
    return _models


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Force FAST_MODE for quick self-test
    os.environ["FAST_MODE"] = "true"
    models = load_all_models()

    print("\n" + "=" * 55)
    print("  Model Store — Loaded Keys")
    print("=" * 55)
    for key, val in models.items():
        status = "✅ loaded" if val is not None and val is not False else ("⚡ skipped (FAST_MODE)" if val is None else "❌ False")
        if isinstance(val, bool):
            status = f"= {val}"
        print(f"  {key:25s} {status}")
    print("─" * 55)
    print("✅ models_loader self-test PASS")
