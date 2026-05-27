"""Database layer — asyncpg pool + schema application.

DATABASE_URL must be set in the environment (see .env.example).
"""

from __future__ import annotations

import os
from pathlib import Path

import asyncpg

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL environment variable not set")
    return url


async def create_pool() -> asyncpg.Pool:
    """Create an asyncpg pool from DATABASE_URL."""
    pool = await asyncpg.create_pool(database_url(), min_size=1, max_size=10)
    assert pool is not None
    return pool


async def init_schema(pool: asyncpg.Pool) -> None:
    """Apply schema.sql against the pool. Idempotent."""
    sql = _SCHEMA_PATH.read_text()
    async with pool.acquire() as conn:
        await conn.execute(sql)


async def truncate_events(pool: asyncpg.Pool) -> None:
    """Truncate the events table. Used by seed.py."""
    async with pool.acquire() as conn:
        await conn.execute("truncate table events restart identity")
