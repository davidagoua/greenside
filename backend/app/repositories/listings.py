from __future__ import annotations

from typing import Any
from uuid import UUID

import asyncpg

_SELECT = """
    SELECT l.id, l.producer_id, l.category_id, c.slug AS category_slug, c.name AS category_name, c.unit,
           l.location_id, loc.label AS location_label, loc.address_text,
           ST_Y(loc.geom) AS lat, ST_X(loc.geom) AS lng,
           l.title, l.description, l.estimated_quantity, l.price_per_unit, l.is_free_donation,
           l.pickup_availability, COALESCE(l.images_urls, '{}') AS images_urls, l.status::text AS status,
           u.organization_name AS producer_organization,
           l.created_at, l.updated_at
    FROM listings l
    JOIN waste_categories c ON c.id = l.category_id
    JOIN locations loc ON loc.id = l.location_id
    JOIN users u ON u.id = l.producer_id
"""

_UPDATABLE = (
    "category_id",
    "location_id",
    "title",
    "description",
    "estimated_quantity",
    "price_per_unit",
    "is_free_donation",
    "pickup_availability",
    "images_urls",
    "status",
)


async def get(conn: asyncpg.Connection, listing_id: UUID) -> dict[str, Any] | None:
    row = await conn.fetchrow(f"{_SELECT} WHERE l.id = $1", listing_id)
    return dict(row) if row else None


async def get_for_update(conn: asyncpg.Connection, listing_id: UUID) -> dict[str, Any] | None:
    """Verrou pessimiste sur l'annonce (à appeler dans une transaction SQL)."""
    row = await conn.fetchrow(
        """
        SELECT l.id, l.producer_id, l.status::text AS status, l.estimated_quantity,
               l.price_per_unit, l.is_free_donation
        FROM listings l WHERE l.id = $1 FOR UPDATE
        """,
        listing_id,
    )
    return dict(row) if row else None


async def list_by_producer(
    conn: asyncpg.Connection, producer_id: UUID, status: str | None
) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        f"{_SELECT} WHERE l.producer_id = $1 AND ($2::text IS NULL OR l.status::text = $2) "
        "ORDER BY l.created_at DESC",
        producer_id,
        status,
    )
    return [dict(r) for r in rows]


async def list_published(
    conn: asyncpg.Connection, *, category: str | None, limit: int, offset: int
) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        f"{_SELECT} WHERE l.status = 'published' AND ($1::text IS NULL OR c.slug = $1) "
        "ORDER BY l.created_at DESC LIMIT $2 OFFSET $3",
        category,
        limit,
        offset,
    )
    return [dict(r) for r in rows]


async def nearby(
    conn: asyncpg.Connection,
    *,
    lat: float,
    lng: float,
    radius_km: float,
    category: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    """Recherche géolocalisée PostGIS (ST_DWithin sur geography, distance en km)."""
    rows = await conn.fetch(
        """
        SELECT l.id, l.title, l.estimated_quantity, l.price_per_unit, l.is_free_donation,
               c.name AS category_name, c.slug AS category_slug, c.unit,
               ST_Distance(loc.geom::geography, ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography) / 1000
                   AS distance_km,
               ST_Y(loc.geom) AS lat, ST_X(loc.geom) AS lng, loc.address_text,
               (l.images_urls)[1] AS thumbnail_url
        FROM listings l
        JOIN locations loc ON l.location_id = loc.id
        JOIN waste_categories c ON l.category_id = c.id
        WHERE l.status = 'published'
          AND ST_DWithin(loc.geom::geography, ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography, $3 * 1000)
          AND ($4::text IS NULL OR c.slug = $4)
        ORDER BY distance_km ASC
        LIMIT $5
        """,
        lng,
        lat,
        radius_km,
        category,
        limit,
    )
    return [dict(r) for r in rows]


async def create(conn: asyncpg.Connection, *, producer_id: UUID, location_id: UUID, data: dict[str, Any]) -> UUID:
    return await conn.fetchval(
        """
        INSERT INTO listings (producer_id, category_id, location_id, title, description,
                              estimated_quantity, price_per_unit, is_free_donation,
                              pickup_availability, images_urls, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::listing_status)
        RETURNING id
        """,
        producer_id,
        data["category_id"],
        location_id,
        data["title"],
        data.get("description"),
        data["estimated_quantity"],
        data.get("price_per_unit", 0),
        data.get("is_free_donation", False),
        data.get("pickup_availability"),
        data.get("images_urls") or [],
        data.get("status", "published"),
    )


async def update(conn: asyncpg.Connection, listing_id: UUID, data: dict[str, Any]) -> None:
    fields = [(k, v) for k, v in data.items() if k in _UPDATABLE]
    if not fields:
        return
    parts = []
    for i, (k, _) in enumerate(fields, start=2):
        parts.append(f"{k} = ${i}::listing_status" if k == "status" else f"{k} = ${i}")
    await conn.execute(
        f"UPDATE listings SET {', '.join(parts)} WHERE id = $1", listing_id, *[v for _, v in fields]
    )


async def set_status(conn: asyncpg.Connection, listing_id: UUID, status: str) -> None:
    await conn.execute("UPDATE listings SET status = $2::listing_status WHERE id = $1", listing_id, status)
