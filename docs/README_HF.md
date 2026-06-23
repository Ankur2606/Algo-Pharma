---
title: AlgoPharma Backend
emoji: 💊
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
short_description: Real-time pharmacovigilance social listening API
---

# AlgoPharma — Backend API

Real-time pharmacovigilance social listening platform powered by FastAPI.

## API Docs

Once deployed, visit `/docs` for the full interactive Swagger UI.

## Endpoints

| Group | Base URL |
|---|---|
| Auth | `/api/auth` |
| Projects | `/api/projects` |
| Signals | `/api/projects/{id}/signals` |
| Analytics | `/api/projects/{id}/analytics` |
| Results | `/api/results` |
| Chat | `/api/chat` |

## Environment Variables

Set these as **Secrets** in the HF Space settings:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (Supabase) |
| `SECRET_KEY` | JWT signing key (`openssl rand -hex 32`) |
| `NVIDIA_API_KEY` | NVIDIA NIM / Nemotron key |
| `GEMINI_API_KEY` | Google Gemini key |
| `SARVAM_API_KEY` | Sarvam AI key |
| `GROQ_API_KEY` | Groq API key |
| `APIFY_TOKEN` | Apify token for crawling |
| `FIRECRAWL_API_KEY` | Firecrawl key |
| `REDDIT_USER_AGENT` | e.g. `AlgoPharma/1.0` |
| `FAST_MODE` | Set `true` to skip NLP model loading on startup |
