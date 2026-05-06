"""
AlgoPharma — Model Setup Script
================================
Run this ONCE after `uv sync` to download all required models to disk.

    uv run python setup_models.py

What it does:
  1. Downloads the spaCy English pipeline (en_core_web_sm - 12 MB)
  2. Pre-caches all HuggingFace models used at runtime:
       - Drug NER   : OpenMed-NER-PharmaDetect-ModernClinical-149M
       - Disease NER: OpenMed-NER-DiseaseDetect-SuperClinical-184M
       - Sentiment  : cardiffnlp/twitter-roberta-base-sentiment-latest
       - PII (en)   : OpenMed-PII-SuperClinical-Small-44M-v1
       - PII (hi)   : OpenMed-PII-Hindi-SuperClinical-Small-44M-v1
       - PII (te)   : OpenMed-PII-Telugu-FastClinical-Small-82M-v1

All models are saved to the default HuggingFace cache
(~/.cache/huggingface/hub) so Celery workers pick them up instantly.
"""

import subprocess
import sys
import logging

# Ensure UTF-8 output on Windows (cp1252 can't handle ─ and ✅)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("setup_models")

DIVIDER = "─" * 60

# ── 1. spaCy model ────────────────────────────────────────────
# en_core_web_sm  →  12 MB  (tok2vec + tagger + parser + NER)
# This is already the smallest production-grade English pipeline.
# en_core_web_md  →  43 MB  (adds word vectors)
# en_core_web_lg  → 741 MB  (larger vectors)   ← do NOT use
SPACY_MODEL = "en_core_web_sm"

# ── 2. HuggingFace models ─────────────────────────────────────
HF_MODELS = [
    # (repo_id, description, pipeline_task)
    (
        "OpenMed/OpenMed-NER-PharmaDetect-ModernClinical-149M",
        "Drug NER – 149M params, CPU-friendly",
        "token-classification",
    ),
    (
        "OpenMed/OpenMed-NER-DiseaseDetect-SuperClinical-184M",
        "Disease NER – 184M params, CPU-friendly",
        "token-classification",
    ),
    (
        "cardiffnlp/twitter-roberta-base-sentiment-latest",
        "Sentiment – 125M RoBERTa, medical-social-media fine-tuned",
        "sentiment-analysis",
    ),
    (
        "OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1",
        "PII (English) – 44M DeBERTa, clinical de-identification",
        "token-classification",
    ),
    (
        "OpenMed/OpenMed-PII-Hindi-SuperClinical-Small-44M-v1",
        "PII (Hindi) – 44M, Hindi clinical de-identification",
        "token-classification",
    ),
    (
        "OpenMed/OpenMed-PII-Telugu-FastClinical-Small-82M-v1",
        "PII (Telugu) – 82M, Telugu clinical de-identification",
        "token-classification",
    ),
]


def _step(n: int, total: int, msg: str) -> None:
    logger.info(f"[{n}/{total}] {msg}")


def download_spacy(model: str) -> bool:
    """Download a spaCy model via subprocess (handles the pip-install step)."""
    logger.info(DIVIDER)
    logger.info(f"Downloading spaCy model: {model}")
    result = subprocess.run(
        [sys.executable, "-m", "spacy", "download", model],
        capture_output=False,
    )
    if result.returncode == 0:
        logger.info(f"✅ spaCy {model} ready")
        return True
    else:
        logger.error(f"❌ spaCy download failed for {model}")
        return False


def download_hf_model(repo_id: str, description: str, task: str) -> bool:
    """Warm the HuggingFace cache for a model by instantiating its pipeline."""
    logger.info(DIVIDER)
    logger.info(f"Downloading: {repo_id}")
    logger.info(f"  → {description}")
    try:
        from transformers import pipeline as hf_pipeline

        # force_download=False so re-runs are instant cache hits
        pipe = hf_pipeline(
            task,
            model=repo_id,
            device=-1,          # CPU only — no CUDA dependency
        )
        # Quick smoke-test to confirm model is functional
        if task == "token-classification":
            pipe("AlgoPharma setup test")
        else:
            pipe("This is a test")
        del pipe
        logger.info(f"✅ {repo_id} cached & verified")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to download {repo_id}: {e}")
        return False


def main() -> None:
    total_steps = 1 + len(HF_MODELS)
    failures: list[str] = []

    print()
    print("=" * 60)
    print("  AlgoPharma — Model Setup")
    print("  Run once after: uv sync")
    print("=" * 60)
    print()

    # Step 1: spaCy
    _step(1, total_steps, f"spaCy — {SPACY_MODEL}")
    if not download_spacy(SPACY_MODEL):
        failures.append(SPACY_MODEL)

    # Steps 2+: HuggingFace models
    for i, (repo_id, desc, task) in enumerate(HF_MODELS, start=2):
        _step(i, total_steps, repo_id)
        if not download_hf_model(repo_id, desc, task):
            failures.append(repo_id)

    print()
    print(DIVIDER)
    if failures:
        logger.warning(f"⚠️  {len(failures)} model(s) failed to download:")
        for f in failures:
            logger.warning(f"   • {f}")
        logger.warning("Re-run this script or download manually.")
    else:
        logger.info(f"✅ All {total_steps} models downloaded and cached.")
        logger.info("You can now start the MCP server and Celery worker.")
    print(DIVIDER)


if __name__ == "__main__":
    main()
