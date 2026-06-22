@echo off
:: Start Uvicorn
start "Backend API" cmd /k "uv run uvicorn main:app --reload --port 8000"

:: Start Celery
start "Celery Worker" cmd /k "uv run celery -A celery_app worker --loglevel=info --pool=solo"

:: Start Frontend
cd frontend
start "Frontend Dev" cmd /k "npm run dev"

echo All services started in separate windows.
pause