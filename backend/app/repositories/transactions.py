from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import asyncpg

_SELECT = """
    SELECT t.id, t.listing_id, l.title AS listing_title, l.status::text AS listing_status,
           c.name AS category_name, c.slug AS category_slug, c.unit, c.co2_factor_per_unit,
           l.producer_id, p.organization_name AS producer_organization, p.phone AS producer_phone,
           p.email AS producer_email,
           t.collector_id, col.organization_name AS collector_organization, col.phone AS collector_phone,
           col.email AS collector_email,
           loc.address_text, ST_Y(loc.geom) AS lat, ST_X(loc.geom) AS lng,
           t.agreed_quantity, t.final_weight, t.unit_price, t.total_amount,
           t.payment_status::text AS payment_status, t.escrow_reference, t.qr_verification_token,
           t.collected_at, t.qr_scanned_at, t.co2_saved_total, t.weighing_proof_url,
           t.collector_confirmed_at, t.producer_confirmed_at, t.bsdd_number,
           t.dispute_reason, t.resolution_note, t.created_at, t.updated_at
    FROM transactions t
    JOIN listings l ON l.id = t.listing_id
    JOIN waste_categories c ON c.id = l.category_id
    JOIN locations loc ON loc.id = l.location_id
    JOIN users p ON p.id = l.producer_id
    JOIN users col ON col.id = t.collector_id
"""


async def get(conn: asyncpg.Connection, tx_id: UUID, *, for_update: bool = False) -> dict[str, Any] | None:
    sql = f"{_SELECT} WHERE t.id = $1"
    if for_update:
        sql += " FOR UPDATE OF t"
    row = await conn.fetchrow(sql, tx_id)
    return dict(row) if row else None


async def list_for_user(
    conn: asyncpg.Connection, *, user_id: UUID, role: str, status: str | None
) -> list[dict[str, Any]]:
    if role == "admin":
        where = "($1::uuid IS NULL OR TRUE)"
    elif role == "producer":
        where = "l.producer_id = $1"
    else:
        where = "t.collector_id = $1"
    rows = await conn.fetch(
        f"{_SELECT} WHERE {where} AND ($2::text IS NULL OR t.payment_status::text = $2) "
        "ORDER BY t.created_at DESC LIMIT 200",
        user_id,
        status,
    )
    return [dict(r) for r in rows]


async def has_active_for_listing(conn: asyncpg.Connection, listing_id: UUID) -> bool:
    return bool(
        await conn.fetchval(
            """
            SELECT 1 FROM transactions
            WHERE listing_id = $1
              AND payment_status IN ('pending_escrow', 'escrow_locked', 'collected_pending_verification', 'disputed')
            LIMIT 1
            """,
            listing_id,
        )
    )


async def create(
    conn: asyncpg.Connection,
    *,
    listing_id: UUID,
    collector_id: UUID,
    agreed_quantity: Decimal,
    unit_price: Decimal,
    total_amount: Decimal,
    qr_token: str,
) -> UUID:
    return await conn.fetchval(
        """
        INSERT INTO transactions (listing_id, collector_id, agreed_quantity, unit_price, total_amount,
                                  payment_status, qr_verification_token)
        VALUES ($1, $2, $3, $4, $5, 'pending_escrow', $6)
        RETURNING id
        """,
        listing_id,
        collector_id,
        agreed_quantity,
        unit_price,
        total_amount,
        qr_token,
    )


async def lock_escrow(conn: asyncpg.Connection, tx_id: UUID, escrow_reference: str) -> None:
    await conn.execute(
        """
        UPDATE transactions SET payment_status = 'escrow_locked', escrow_reference = $2
        WHERE id = $1 AND payment_status = 'pending_escrow'
        """,
        tx_id,
        escrow_reference,
    )


async def mark_qr_scanned(conn: asyncpg.Connection, tx_id: UUID) -> None:
    await conn.execute(
        "UPDATE transactions SET qr_scanned_at = COALESCE(qr_scanned_at, NOW()) WHERE id = $1", tx_id
    )


async def record_collection(
    conn: asyncpg.Connection,
    tx_id: UUID,
    *,
    final_weight: Decimal,
    total_amount: Decimal,
    co2_saved_total: Decimal,
    weighing_proof_url: str | None,
    bsdd_number: str,
) -> None:
    await conn.execute(
        """
        UPDATE transactions
        SET final_weight = $2,
            total_amount = $3,
            co2_saved_total = $4,
            weighing_proof_url = $5,
            bsdd_number = COALESCE(bsdd_number, $6),
            collected_at = NOW(),
            collector_confirmed_at = NOW(),
            qr_scanned_at = COALESCE(qr_scanned_at, NOW()),
            payment_status = 'collected_pending_verification'
        WHERE id = $1
        """,
        tx_id,
        final_weight,
        total_amount,
        co2_saved_total,
        weighing_proof_url,
        bsdd_number,
    )


async def next_bsdd_number(conn: asyncpg.Connection, year: int) -> str:
    seq = await conn.fetchval("SELECT nextval('bsdd_number_seq')")
    return f"BSDD-{year}-{seq:06d}"


async def set_status(
    conn: asyncpg.Connection,
    tx_id: UUID,
    status: str,
    *,
    producer_confirmed_at: datetime | None = None,
    dispute_reason: str | None = None,
    resolution_note: str | None = None,
) -> None:
    await conn.execute(
        """
        UPDATE transactions
        SET payment_status = $2::transaction_status,
            producer_confirmed_at = COALESCE($3, producer_confirmed_at),
            dispute_reason = COALESCE($4, dispute_reason),
            resolution_note = COALESCE($5, resolution_note)
        WHERE id = $1
        """,
        tx_id,
        status,
        producer_confirmed_at,
        dispute_reason,
        resolution_note,
    )
