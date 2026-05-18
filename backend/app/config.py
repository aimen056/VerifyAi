"""
Application configuration — loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://verifyai:verifyai_secret@localhost:5432/verifyai_db"

    # ── Redis ─────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── CORS ──────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000"

    # ── App ───────────────────────────────────────────────────
    debug: bool = True
    app_name: str = "VerifyAI"
    app_version: str = "0.2.0"

    # ── ML Pipeline ───────────────────────────────────────────
    ml_model_name: str = "hamzab/roberta-fake-news-classification"
    ml_device: Optional[str] = None             # auto-detect if None
    ml_max_length: int = 512

    # ── OCR (Tesseract) ──────────────────────────────────────
    tesseract_cmd: Optional[str] = None         # e.g. "C:/Program Files/Tesseract-OCR/tesseract.exe"
    tesseract_lang: str = "eng"

    # ── Google Fact Check API ────────────────────────────────
    google_factcheck_api_key: str = ""
    factcheck_language: str = "en"
    factcheck_max_results: int = 5

    # ── SHAP Explainer ───────────────────────────────────────
    shap_max_tokens: int = 10
    shap_timeout_seconds: float = 60.0    # max SHAP computation time

    # ── Search APIs ──────────────────────────────────────────
    custom_search_api: str = ""
    custom_search_engine_id: str = ""
    serper_api: str = ""
    groq_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        protected_namespaces = ("settings_",)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
