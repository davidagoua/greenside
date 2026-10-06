from __future__ import annotations

from typing import Any
from uuid import UUID

import asyncpg

_COLS = """
    id, label, address_text,
    ST_Y(geom) AS lat, ST_X(geom) AS lng,
    created_at
"""


async def list_for_user(conn: asyncpg.Connection, user_id: UUID) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        f"SELECT {_COLS} FROM locations WHERE user_id = $1 ORDER BY created_at DESC", user_id
    )
    return [dict(r) for r in rows]


async def get_for_user(conn: asyncpg.Connection, location_id: UUID, user_id: UUID) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        f"SELECT {_COLS} FROM locations WHERE id = $1 AND user_id = $2", location_id, user_id
    )
    return dict(row) if row else None


async def create(
    conn: asyncpg.Connection, *, user_id: UUID, label: str | None, address_text: str, lat: float, lng: float
) -> dict[str, Any]:
    row = await conn.fetchrow(
        f"""
        INSERT INTO locations (user_id, label, address_text, geom)
        VALUES ($1, $2, $3, ST_SetSRID(ST_MakePoint($4, $5), 4326))
        RETURNING {_COLS}
        """,
        user_id,
        label,
        address_text,
        lng,
        lat,
    )
    return dict(row)


async def is_used(conn: asyncpg.Connection, location_id: UUID) -> bool:
    return bool(await conn.fetchval("SELECT 1 FROM listings WHERE location_id = $1 LIMIT 1", location_id))


async def delete(conn: asyncpg.Connection, location_id: UUID, user_id: UUID) -> bool:
    res = await conn.execute("DELETE FROM locations WHERE id = $1 AND user_id = $2", location_id, user_id)
    return res.endswith(" 1")
