#!/bin/bash
# start.sh - Robust dual-process launcher for Hugging Face Spaces
set -e

echo "===== AlgoPharma Starting at $(date) ====="

# Start Celery worker in background, capture PID
echo "[1/2] Starting Celery worker (pool=solo)..."
uv run celery -A backend.celery_app worker \
    --loglevel=info \
    --pool=solo \
    --queues=hf_algopharma_queue &
CELERY_PID=$!
echo "      Celery PID: $CELERY_PID"

# Start FastAPI server in background, capture PID
echo "[2/2] Starting FastAPI on port 7860..."
uv run uvicorn backend.main:app --host 0.0.0.0 --port 7860 &
UVICORN_PID=$!
echo "      Uvicorn PID: $UVICORN_PID"

echo "===== Both services running. Waiting... ====="

# Exit the moment either process dies so HF can restart the container
wait -n $CELERY_PID $UVICORN_PID
EXIT_CODE=$?

echo "===== A service exited (code=$EXIT_CODE). Shutting down. ====="
kill $CELERY_PID $UVICORN_PID 2>/dev/null || true
exit $EXIT_CODE
