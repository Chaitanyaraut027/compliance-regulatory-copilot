"""
Database connection pool using psycopg 3.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import get_settings

logger = logging.getLogger(__name__)

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """Return (and lazily create) the connection pool."""
    global _pool
    if _pool is None:
        settings = get_settings()
        logger.info("Creating connection pool → %s", settings.supabase_db_host)
        _pool = ConnectionPool(
            conninfo=settings.dsn,
            min_size=1,
            max_size=5,
            timeout=30,
            kwargs={"row_factory": dict_row},
        )
    return _pool


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    """Yield a connection from the pool (auto-returned on exit)."""
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
        logger.info("Connection pool closed.")


def check_connection() -> dict:
    """Quick connectivity check. Returns version info or error."""
    settings = get_settings()
    if not settings.supabase_db_password or settings.supabase_db_host in ("localhost", "127.0.0.1"):
        return {
            "status": "not_configured",
            "detail": "Supabase PostgreSQL credentials not configured in .env",
        }
    try:
        with get_connection() as conn:
            row = conn.execute("SELECT version()").fetchone()
            return {"status": "connected", "version": row["version"]}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
