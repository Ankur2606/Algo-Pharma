# ── AlgoPharma — Hugging Face Spaces Dockerfile ──────────────────────────────
# HF Spaces requires the app to listen on port 7860.
# Uses CPU-only PyTorch to keep the image size manageable (~2 GB vs ~8 GB GPU).
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Upgrade pip ───────────────────────────────────────────────────────────────
RUN pip install --upgrade pip --quiet

# ── Step 1: Install CPU-only PyTorch FIRST from the official PyTorch index ────
# This MUST be done separately before the rest of requirements to avoid the
# +cpu version tag issue that breaks standard pip installs.
RUN pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cpu --quiet

# ── Step 2: Install spaCy model ───────────────────────────────────────────────
RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl --quiet

# ── Step 3: Copy and install the rest of the dependencies ─────────────────────
COPY requirements-hf.txt .
RUN pip install -r requirements-hf.txt --quiet

# ── Step 4: Copy application code ─────────────────────────────────────────────
COPY . .

# ── Create necessary directories ──────────────────────────────────────────────
RUN mkdir -p static logs

# ── HF Spaces requires port 7860 ──────────────────────────────────────────────
EXPOSE 7860

# ── Health check ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:7860/api/health/sources || exit 1

# ── Entrypoint ────────────────────────────────────────────────────────────────
# HF Spaces uses port 7860. FAST_MODE=true skips heavy model loading on startup.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
