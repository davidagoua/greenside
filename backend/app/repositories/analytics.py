"""Agrégations SQL directes pour le calculateur d'impact RSE."""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

import asyncpg

# Un arbre adulte absorbe en moyenne ~25 kg de CO2 par an (ordre de grandeur ADEME/FAO).
CO2_KG_PER_TREE_YEAR = Decimal("25")

Scope = Literal["producer", "collector", "global"]


def _scope_clause(scope: Scope) -> str:
    if scope == "producer":
        return "l.producer_id = $1"
    if scope == "collector":
        return "t.collector_id = $1"
    return "$1::uuid IS NULL"


_BASE_FROM = """
    FROM transactions t
    JOIN listings l ON l.id = t.listing_id
    JOIN waste_categories c ON c.id = l.category_id
"""

# Conversion en kg : tonne -> x1000 ; litre conservé tel quel (≈ kg pour les huiles).
_KG = "COALESCE(t.final_weight, 0) * CASE c.unit WHEN 'tonne' THEN 1000 ELSE 1 END"


async def impact(conn: asyncpg.Connection, scope: Scope, user_id: UUID | None) -> dict[str, Any]:
    where = f"{_scope_clause(scope)} AND t.payment_status = 'paid'"

    totals = await conn.fetchrow(
        f"""
        SELECT COALESCE(SUM({_KG}), 0)                 AS total_quantity_kg,
               COALESCE(SUM(t.co2_saved_total), 0)     AS total_co2_saved_kg,
               COALESCE(SUM(t.total_amount), 0)        AS total_financial_volume,
               COUNT(*)                                AS completed_transactions
        {_BASE_FROM}
        WHERE {where}
        """,
        user_id,
    )

    by_material = await conn.fetch(
        f"""
        SELECT c.slug AS category_slug, c.name AS category_name, c.unit,
               COALESCE(SUM(t.final_weight), 0)    AS total_quantity,
               COALESCE(SUM(t.co2_saved_total), 0) AS co2_saved,
               COALESCE(SUM(t.total_amount), 0)    AS financial_volume,
               COUNT(*)                            AS transactions_count
        {_BASE_FROM}
        WHERE {where}
        GROUP BY c.slug, c.name, c.unit
        ORDER BY co2_saved DESC
        """,
        user_id,
    )

    monthly = await conn.fetch(
        f"""
        SELECT to_char(date_trunc('month', t.collected_at), 'YYYY-MM') AS month,
               COALESCE(SUM({_KG}), 0)             AS quantity_kg,
               COALESCE(SUM(t.co2_saved_total), 0) AS co2_saved_kg,
               COALESCE(SUM(t.total_amount), 0)    AS financial_volume
        {_BASE_FROM}
        WHERE {where} AND t.collected_at >= date_trunc('month', NOW()) - INTERVAL '11 months'
        GROUP BY 1
        ORDER BY 1
        """,
        user_id,
    )

    co2 = Decimal(totals["total_co2_saved_kg"])
    return {
        "total_quantity_kg": totals["total_quantity_kg"],
        "total_co2_saved_kg": co2,
        "total_financial_volume": totals["total_financial_volume"],
        "completed_transactions": totals["completed_transactions"],
        "trees_equivalent": (co2 / CO2_KG_PER_TREE_YEAR).quantize(Decimal("0.1")),
        "by_material": [dict(r) for r in by_material],
        "monthly": [
            {
                "month": r["month"],
                "quantity_kg": float(r["quantity_kg"]),
                "co2_saved_kg": float(r["co2_saved_kg"]),
                "financial_volume": float(r["financial_volume"]),
            }
            for r in monthly
        ],
    }


async def global_counters(conn: asyncpg.Connection) -> dict[str, Any]:
    users = await conn.fetch("SELECT role::text AS role, COUNT(*) AS n FROM users GROUP BY role")
    listings = await conn.fetch("SELECT status::text AS status, COUNT(*) AS n FROM listings GROUP BY status")
    disputes = await conn.fetchval("SELECT COUNT(*) FROM transactions WHERE payment_status = 'disputed'")
    return {
        "users_by_role": {r["role"]: r["n"] for r in users},
        "listings_by_status": {r["status"]: r["n"] for r in listings},
        "open_disputes": disputes,
    }
