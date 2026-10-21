"""
Configuration — loads all settings from environment / .env file.
"""

from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env from project root with override=True to ensure .env settings take precedence
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env", override=True)


class Settings(BaseSettings):
    """Application settings bound to environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Supabase PostgreSQL ──────────────────────────────────
    supabase_db_host: str = "localhost"
    supabase_db_port: int = 5432
    supabase_db_name: str = "postgres"
    supabase_db_user: str = "postgres"
    supabase_db_password: str = ""
    supabase_db_sslmode: str = "require"

    # ── LLM Provider (Groq [FREE] or OpenAI) ─────────────────
    llm_provider: str = "groq"  # "groq" or "openai"
    groq_api_key: str = ""
    groq_chat_model: str = "qwen/qwen3.8-27b"

    # ── Embedding Provider (FastEmbed [FREE Local] or OpenAI) ──
    embedding_provider: str = "fastembed"  # "fastembed" or "openai"
    fastembed_model: str = "BAAI/bge-small-en-v1.5"

    # ── OpenAI (Alternative Paid Provider) ───────────────────
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"

    # ── RAG tuning ───────────────────────────────────────────
    chunk_size: int = 900
    chunk_overlap: int = 120
    retrieval_top_k: int = 5

    # ── Paths ────────────────────────────────────────────────
    regulations_dir: str = str(_PROJECT_ROOT / "data" / "regulations")

    database_url: str = ""

    # Derived helpers
    @property
    def dsn(self) -> str:
        """PostgreSQL connection string for psycopg."""
        if self.database_url and (not self.supabase_db_host or self.supabase_db_host in self.database_url):
            return self.database_url
        import urllib.parse
        user = urllib.parse.quote_plus(self.supabase_db_user)
        password = urllib.parse.quote_plus(self.supabase_db_password)
        dbname = urllib.parse.quote_plus(self.supabase_db_name.strip() or "postgres")
        return (
            f"postgresql://{user}:{password}"
            f"@{self.supabase_db_host}:{self.supabase_db_port}"
            f"/{dbname}?sslmode={self.supabase_db_sslmode}"
        )

    @property
    def regulations_path(self) -> Path:
        return Path(self.regulations_dir)

    @property
    def embedding_dimension(self) -> int:
        """Returns 384 for fastembed (bge-small-en-v1.5) or 1536 for OpenAI."""
        if self.embedding_provider == "fastembed":
            return 384
        return 1536


@lru_cache()
def get_settings() -> Settings:
    return Settings()
