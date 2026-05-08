#!/bin/bash
# start.sh - Run Celery worker and FastAPI server in Hugging Face Spaces

# Start Celery worker in the background
# We use pool=solo to keep memory usage low on the free tier
uv run celery -A celery_app worker --loglevel=info --pool=solo &

# Start the FastAPI web server on the port expected by HF Spaces (7860)
uv run uvicorn main:app --host 0.0.0.0 --port 7860
