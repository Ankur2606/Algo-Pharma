"""
AlgoPharma — Centralised configuration via pydantic-settings.
All values read from .env automatically. Singleton via lru_cache.
"""

import sys
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────
    FAST_MODE: bool = False
    DATABASE_URL: str = "sqlite:///./algopharma.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "dev-secret-change-in-production"

    # ── Existing data files ───────────────────────────────
    REDDIT_JSON_PATH: str = "reddit_dolo365_results.json"
    TWITTER_JSON_PATH: str = "twitter_dolo365_results.json"

    # ── Reddit ────────────────────────────────────────────
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "AlgoPharma/1.0"

    # ── Twitter ───────────────────────────────────────────
    TWITTER_API_KEY: str = ""

    # ── Firecrawl ─────────────────────────────────────────
    FIRECRAWL_API_KEY: str = ""

    # ── Google Gemini ─────────────────────────────────────
    GEMINI_API_KEY: str = ""

    # ── Nvidia Nemotron ─────────────────────────────────────
    NVIDIA_API_KEY: str = ""
    NVIDIA_API_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_MODEL: str = "nvidia/nemotron-3-super-120b-a12b"

    # ── Sarvam AI ─────────────────────────────────────────
    SARVAM_API_KEY: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    s = get_settings()
    secrets = {"SECRET_KEY", "TWITTER_API_KEY", "FIRECRAWL_API_KEY",
               "GEMINI_API_KEY", "SARVAM_API_KEY", "REDDIT_CLIENT_SECRET", "NVIDIA_API_KEY"}

    print("=" * 55)
    print("  AlgoPharma — Configuration Check")
    print("=" * 55)
    for name, value in s.model_dump().items():
        if name.upper() in secrets:
            status = "✅ SET" if value and value != "dev-secret-change-in-production" else "⚠️  NOT SET"
        else:
            status = f"= {value}"
        print(f"  {name:30s} {status}")
    print("─" * 55)
    print("✅ Config OK")
