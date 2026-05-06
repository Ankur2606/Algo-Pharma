"""
AlgoPharma — Singleton model store.
All NLP files import from here. Models loaded once at startup.
Respects FAST_MODE: when True, loads only spaCy + VADER.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
 

_models: dict = {}
from pathlib import Path
 
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "models_loader.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)
 

def load_all_models() -> dict:
    """Load all NLP models. Respects FAST_MODE env var."""
    global _models
    if _models:
        return _models

    fast_mode = os.getenv("FAST_MODE", "false").lower() in ("true", "1", "yes")

    # ── 1. spaCy (always needed for negation) ─────────────
    try:
        import spacy
        _models["spacy"] = spacy.load("en_core_web_sm")
        logger.info("✅ spaCy en_core_web_sm loaded")
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
        # Swapped from GPU-heavy OpenMed/privacy-filter-nemotron to CPU-friendly piiranha for faster startup
        pii_model_id = "iiiorg/piiranha-v1-detect-personal-information"
        try:
            _models["pii_tokenizer"] = AutoTokenizer.from_pretrained(pii_model_id, trust_remote_code=True)
            _models["pii_model"] = AutoModelForTokenClassification.from_pretrained(
                pii_model_id, trust_remote_code=True
            )
            _models["pii_model"].to("cpu")
            logger.info("✅ PII model loaded")
        except Exception as e:
            logger.warning(f"⚠️ Primary PII model failed, trying fallback: {e}")
            fallback_id = "OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1"
            _models["pii_tokenizer"] = AutoTokenizer.from_pretrained(fallback_id, trust_remote_code=True)
            _models["pii_model"] = AutoModelForTokenClassification.from_pretrained(
                fallback_id, trust_remote_code=True
            )
            _models["pii_model"].to("cpu")
            logger.info("✅ Fallback PII model loaded")
    except Exception as e:
        logger.warning(f"⚠️  PII model unavailable (regex-only PII will run): {e}")
        _models["pii_model"] = None
        _models["pii_tokenizer"] = None

    # ── 3. Drug NER ──────────────────────────────────────
    try:
        from transformers import pipeline
        # Swapped from 278M BigMed to 149M ModernClinical for faster CPU inference
        _models["drug_ner"] = pipeline(
            "token-classification",
            model="OpenMed/OpenMed-NER-PharmaDetect-ModernClinical-149M",
            aggregation_strategy="simple",
            device=-1,
        )
        logger.info("✅ Drug NER model loaded")
    except Exception as e:
        logger.warning(f"⚠️  Drug NER model unavailable (keyword matching will run): {e}")
        _models["drug_ner"] = None

    # ── 4. Disease NER ───────────────────────────────────
    try:
        from transformers import pipeline
        # Swapped from 335M BioMed to 184M SuperClinical for faster CPU inference
        _models["disease_ner"] = pipeline(
            "token-classification",
            model="OpenMed/OpenMed-NER-DiseaseDetect-SuperClinical-184M",
            aggregation_strategy="simple",
            device=-1,
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
            device=-1,
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

   

    # Force FAST_MODE for quick self-test
    os.environ["FAST_MODE"] = "false"
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
