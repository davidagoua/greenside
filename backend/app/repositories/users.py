from __future__ import annotations

from typing import Any
from uuid import UUID

import asyncpg

_PUBLIC_COLS = "id, email, role::text AS role, organization_name, phone, is_active, created_at"


async def get_by_id(conn: asyncpg.Connection, user_id: UUID) -> dict[str, Any] | None:
    row = await conn.fetchrow(f"SELECT {_PUBLIC_COLS} FROM users WHERE id = $1", user_id)
    return dict(row) if row else None


async def get_by_email_with_hash(conn: asyncpg.Connection, email: str) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        f"SELECT {_PUBLIC_COLS}, password_hash FROM users WHERE lower(email) = lower($1)", email
    )
    return dict(row) if row else None


async def email_exists(conn: asyncpg.Connection, email: str) -> bool:
    return bool(await conn.fetchval("SELECT 1 FROM users WHERE lower(email) = lower($1)", email))


async def create(
    conn: asyncpg.Connection,
    *,
    email: str,
    password_hash: str,
    role: str,
    organization_name: str | None,
    phone: str,
) -> dict[str, Any]:
    row = await conn.fetchrow(
        f"""
        INSERT INTO users (email, password_hash, role, organization_name, phone)
        VALUES (lower($1), $2, $3::user_role, $4, $5)
        RETURNING {_PUBLIC_COLS}
        """,
        email,
        password_hash,
        role,
        organization_name,
        phone,
    )
    return dict(row)


async def list_users(
    conn: asyncpg.Connection, *, role: str | None, search: str | None, limit: int, offset: int
) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        f"""
        SELECT {_PUBLIC_COLS} FROM users
        WHERE ($1::text IS NULL OR role::text = $1)
          AND ($2::text IS NULL OR email ILIKE '%' || $2 || '%' OR organization_name ILIKE '%' || $2 || '%')
        ORDER BY created_at DESC
        LIMIT $3 OFFSET $4
        """,
        role,
        search,
        limit,
        offset,
    )
    return [dict(r) for r in rows]


async def set_active(conn: asyncpg.Connection, user_id: UUID, is_active: bool) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        f"UPDATE users SET is_active = $2 WHERE id = $1 RETURNING {_PUBLIC_COLS}", user_id, is_active
    )
    return dict(row) if row else None
