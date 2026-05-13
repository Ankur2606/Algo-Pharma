from huggingface_hub import HfApi

api = HfApi()

dockerfile_content = """FROM python:3.12-slim

# Install system dependencies (including git to clone your repo)
RUN apt-get update && apt-get install -y \
    curl git \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh

# Set working directory
WORKDIR /app

# Clone your GitHub repository directly!
RUN git clone https://github.com/Ankur2606/Algo-Pharma .

# Install dependencies using UV
RUN uv pip install --system -r pyproject.toml

# Expose Hugging Face Space port
EXPOSE 7860

# Run both Celery and FastAPI in the background
CMD uv run celery -A celery_app worker --loglevel=info --pool=solo & uv run uvicorn main:app --host 0.0.0.0 --port 7860
"""

with open("Dockerfile_hf", "w") as f:
    f.write(dockerfile_content)

import time

for i in range(10):
    try:
        print(f"Uploading Dockerfile to Hugging Face (Attempt {i+1})...")
        api.upload_file(
            path_or_fileobj="Dockerfile_hf",
            path_in_repo="Dockerfile",
            repo_id="DecentSanage/Algo-Pharma",
            repo_type="space"
        )
        print("✅ Done! Hugging Face is now building from your GitHub repo.")
        break
    except Exception as e:
        print(f"Failed: {e}. Retrying in 2 seconds...")
        time.sleep(2)
