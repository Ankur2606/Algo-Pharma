#!/bin/bash

trap "kill 0" EXIT

uv run uvicorn backend.main:app --reload --port 8000 &
uv run celery -A backend.celery_app worker --loglevel=info --pool=solo &

cd frontend && npm run dev &

wait