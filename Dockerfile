FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh

WORKDIR /app

# Cache buster: forces re-clone when main branch changes
ADD https://api.github.com/repos/Ankur2606/Algo-Pharma/git/refs/heads/main /tmp/version.json

# Clone repo into /app
RUN git clone https://github.com/Ankur2606/Algo-Pharma .

# Install Python dependenciesgit add Dockerfile
RUN uv sync

# Pre-cache all NLP models so startup is fast
RUN uv run python -m spacy download en_core_web_sm
RUN uv run python nlp/models_loader.py
RUN uv run python setup_pii.py

# Make startup script executable
RUN chmod +x /app/start.sh

EXPOSE 7860

# Use exec-form CMD pointing to the shell script
# This ensures Docker's SIGTERM reaches the script and both processes are managed
CMD ["/app/start.sh"]
