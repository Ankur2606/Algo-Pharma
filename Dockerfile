FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml .
COPY .python-version .

# Install dependencies using UV
# We use --system to install directly to the system python environment
RUN uv pip install --system -r pyproject.toml

# Copy project files
COPY . .

# Set permissions for the startup script
RUN chmod +x start.sh

# Expose Hugging Face Space port
EXPOSE 7860

# Run the startup script (starts Celery + FastAPI)
CMD ["./start.sh"]
