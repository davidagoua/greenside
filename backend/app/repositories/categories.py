from __future__ import annotations

from typing import Any
from uuid import UUID

import asyncpg

_COLS = "id, slug, name, unit, co2_factor_per_unit, suggested_price_per_unit"
_UPDATABLE = ("name", "unit", "co2_factor_per_unit", "suggested_price_per_unit")


async def list_all(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch(f"SELECT {_COLS} FROM waste_categories ORDER BY name")
    return [dict(r) for r in rows]


async def get(conn: asyncpg.Connection, category_id: UUID) -> dict[str, Any] | None:
    row = await conn.fetchrow(f"SELECT {_COLS} FROM waste_categories WHERE id = $1", category_id)
    return dict(row) if row else None


async def create(conn: asyncpg.Connection, data: dict[str, Any]) -> dict[str, Any]:
    row = await conn.fetchrow(
        f"""
        INSERT INTO waste_categories (slug, name, unit, co2_factor_per_unit, suggested_price_per_unit)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING {_COLS}
        """,
        data["slug"],
        data["name"],
        data["unit"],
        data["co2_factor_per_unit"],
        data["suggested_price_per_unit"],
    )
    return dict(row)


async def update(conn: asyncpg.Connection, category_id: UUID, data: dict[str, Any]) -> dict[str, Any] | None:
    fields = [(k, v) for k, v in data.items() if k in _UPDATABLE]
    if not fields:
        return await get(conn, category_id)
    # Les noms de colonnes proviennent d'une liste blanche, les valeurs sont paramétrées.
    set_clause = ", ".join(f"{k} = ${i}" for i, (k, _) in enumerate(fields, start=2))
    row = await conn.fetchrow(
        f"UPDATE waste_categories SET {set_clause} WHERE id = $1 RETURNING {_COLS}",
        category_id,
        *[v for _, v in fields],
    )
    return dict(row) if row else None


async def is_used(conn: asyncpg.Connection, category_id: UUID) -> bool:
    return bool(await conn.fetchval("SELECT 1 FROM listings WHERE category_id = $1 LIMIT 1", category_id))


async def delete(conn: asyncpg.Connection, category_id: UUID) -> bool:
    res = await conn.execute("DELETE FROM waste_categories WHERE id = $1", category_id)
    return res.endswith(" 1")
