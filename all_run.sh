#!/bin/bash

trap "kill 0" EXIT

uv run uvicorn main:app --reload --port 8000 &
uv run celery -A celery_app worker --loglevel=info --pool=solo &

cd frontend && npm run dev &

wait