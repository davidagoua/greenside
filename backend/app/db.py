"""Pool de connexions asyncpg — accès SQL natif, sans ORM ni SDK Supabase."""
from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


async def _init_connection(conn: asyncpg.Connection) -> None:
    # JSON/JSONB <-> dict Python
    for typ in ("json", "jsonb"):
        await conn.set_type_codec(typ, encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


async def connect() -> None:
    global _pool
    if _pool is not None:
        return
    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
        statement_cache_size=settings.db_statement_cache_size,
        init=_init_connection,
        command_timeout=30,
    )
    logger.info("Pool PostgreSQL initialisé")


async def disconnect() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Pool PostgreSQL non initialisé")
    return _pool


async def get_conn() -> AsyncIterator[asyncpg.Connection]:
    """Dépendance FastAPI : une connexion du pool par requête."""
    async with get_pool().acquire() as conn:
        yield conn


@asynccontextmanager
async def transaction(conn: asyncpg.Connection) -> AsyncIterator[asyncpg.Connection]:
    async with conn.transaction():
        yield conn


async def run_migrations() -> None:
    """Applique les fichiers migrations/*.sql non encore enregistrés dans schema_migrations."""
    async with get_pool().acquire() as conn:
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " version VARCHAR(50) PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT NOW())"
        )
        applied = {r["version"] for r in await conn.fetch("SELECT version FROM schema_migrations")}
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            version = path.stem
            if version in applied:
                continue
            logger.info("Application de la migration %s", version)
            async with conn.transaction():
                await conn.execute(path.read_text(encoding="utf-8"))
                await conn.execute(
                    "INSERT INTO schema_migrations(version) VALUES ($1) ON CONFLICT DO NOTHING", version
                )
