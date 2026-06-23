# AlgoPharma — Setup Guide

Complete, command-by-command guide to running AlgoPharma locally from scratch.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | ≥ 3.12 | [python.org](https://python.org) |
| `uv` | latest | `pip install uv` |
| Node.js | ≥ 18 | [nodejs.org](https://nodejs.org) |
| Redis | any | See below |
| Git | any | [git-scm.com](https://git-scm.com) |

---

## 1. Clone & Enter the Repo

```bash
git clone https://github.com/Ankur2606/Algo-Pharma.git
cd Algo-Pharma
```

---

## 2. Set Up Environment Variables

```bash
# Copy the template
cp .env.example .env
```

Open `.env` and fill in **at minimum**:

| Key | Required | Where to get |
|-----|----------|--------------|
| `GROQ_API_KEY` | ✅ Yes | [console.groq.com](https://console.groq.com/) — free |
| `SECRET_KEY` | ✅ Yes | Run `openssl rand -hex 32` |
| `DATABASE_URL` | Optional | Defaults to `sqlite:///./db/algopharma.db` |
| `REDIS_URL` | Optional | Defaults to `redis://localhost:6379/0` |
| `TWITTER_API_KEY` | For Twitter crawling | [twitterapi.io](https://twitterapi.io) |
| `FIRECRAWL_API_KEY` | For forum onboarding | [firecrawl.dev](https://firecrawl.dev) |
| `SARVAM_API_KEY` | For Indic languages | [dashboard.sarvam.ai](https://dashboard.sarvam.ai) |
| `NVIDIA_API_KEY` | For slot filling | [build.nvidia.com](https://build.nvidia.com) |

> **Quick local setup** (SQLite + local Redis): only `GROQ_API_KEY` and `SECRET_KEY` are strictly required.

---

## 3. Install Redis

<!-- ### Windows (recommended)
```powershell
winget install Redis.Redis
# Then start Redis:
redis-server
```

### WSL / Linux
```bash
sudo apt-get install redis-server
sudo service redis-server start
``` -->

### Cloud (zero local setup)
Use [Upstash](https://upstash.com/) free tier and set:
```env
REDIS_URL=rediss://default:<password>@<host>.upstash.io:6379/
```

---

## 4. Install Python Dependencies

```bash
uv sync
```

This installs all packages from `pyproject.toml` including:
- FastAPI, Uvicorn, SQLAlchemy, Celery
- Transformers, spaCy, Torch (CPU-only)
- Groq, OpenMed, VADER Sentiment, Pydantic

### Download spaCy model (first time only)
```bash
uv run python -m spacy download en_core_web_sm
```

### Pre-download HuggingFace NLP models (optional but faster first run)
```bash
uv run python backend/scripts/setup_models.py
```

---

## 5. Initialise the Database

The database is created automatically on first start. To pre-seed with demo data:

```bash
# Create all tables
uv run python -c "import sys; sys.path.insert(0, 'backend'); from database import init_db; init_db()"

# (Optional) Seed demo data
uv run python backend/scripts/seed_demo_data.py
```

---

## 6. Create the Default Admin User

The UI authenticates against the backend. Insert the default admin:

```bash
uv run python -c "
import sys
sys.path.insert(0, 'backend')
from database import SessionLocal
from models import User
from passlib.context import CryptContext
pwd = CryptContext(schemes=['bcrypt'])
with SessionLocal() as db:
    if not db.query(User).filter_by(username='admin@example.com').first():
        db.add(User(username='admin@example.com', hashed_password=pwd.hash('admin123'), role='admin'))
        db.commit()
        print('Admin user created: admin@example.com / admin123')
    else:
        print('Admin already exists')
"
```

---

## 7. Run the Stack

Open **3 separate terminals**:

### Terminal 1 — FastAPI Backend + Static UI
```bash
uv run uvicorn backend.main:app --reload --port 8000
```
- API: `http://localhost:8000`
- Dashboard UI: `http://localhost:8000` (served from `backend/static/index.html`)
- API docs: `http://localhost:8000/docs`

### Terminal 2 — Celery NLP Worker
```bash
uv run celery -A backend.celery_app worker --loglevel=info --pool=solo
```
> `--pool=solo` is required on Windows (no fork support).
> The worker loads all HuggingFace models on startup (~60s first time).

### Terminal 3 — (Optional) React Frontend Dev Server
Only needed if developing the React frontend in `frontend/`:
```bash
cd frontend
npm install
npm run dev
```
React dev server runs at `http://localhost:5173`.
> The production static UI at port 8000 does not require this.

---

## 8. Verify Everything Works

```bash
# Check config keys are loaded
uv run python backend/config.py

# Verify Redis connection
uv run python backend/celery_app.py

# Run the full NLP pipeline on demo data
uv run python backend/scripts/demo_pipeline.py

# Run tests
uv run python backend/scripts/test_pipeline.py
```

---

## 9. Using the Application

1. Open `http://localhost:8000` in your browser
2. **Login** with `admin@example.com` / `admin123` (or your credentials)
3. **Chat** with the AI: tell it a medicine name and data source  
   e.g. *"I want to check paracetamol side effects on Reddit"*
4. The system will:
   - Use Groq (llama-3.3-70b) to extract intent and pick the right crawler tool
   - Crawl Reddit / Twitter for posts about that medicine
   - Dispatch NLP processing to the Celery worker
   - Show live results on the dashboard as analysis completes
5. **Dashboard** auto-polls every 4 seconds and shows charts, signals, and post details

---

## 10. Production Deployment Tips

- Replace `sqlite:///./algopharma.db` with a Supabase / Postgres `DATABASE_URL`
- Replace `redis://localhost` with Upstash `rediss://` URL
- Set a strong `SECRET_KEY` (never use the default)
- Set `FAST_MODE=false` to enable all NLP models
- Run Celery workers with `--concurrency=2` (remove `--pool=solo`)
- Serve via Gunicorn: `uv run gunicorn main:app -w 2 -k uvicorn.workers.UvicornWorker`

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `No module named 'psycopg2'` | `uv add psycopg2-binary` |
| `Redis not reachable` | Start `redis-server` or check `REDIS_URL` in `.env` |
| `NLP skipped` in Celery logs | Redis TCP probe timed out — check network, Upstash latency |
| `401 Unauthorized` on chat | Token expired — log out and log in again |
| `model_not_found` Groq error | Set `GROQ_API_KEY` in `.env` and verify model name |
| Dashboard stuck on "Crawling" | Celery worker may not be running — start Terminal 2 |
| HuggingFace download loops | Run `uv run python setup_models.py` once to pre-cache models |
| Clock drift warning in Celery | Another Celery worker on the same Redis (shared Upstash) — queue is isolated with `algopharma_ankur_queue` |
