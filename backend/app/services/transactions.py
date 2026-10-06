"""Workflow de transaction : réservation -> séquestre -> scan QR -> pesée -> double validation."""
from __future__ import annotations

import hmac
import secrets
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

import asyncpg

from app.config import settings
from app.errors import AppError, bad_request, conflict, forbidden, not_found
from app.repositories import listings as listings_repo
from app.repositories import transactions as tx_repo
from app.services.escrow import escrow_gateway

CENT = Decimal("0.01")
ACTIVE_STATUSES = {"pending_escrow", "escrow_locked", "collected_pending_verification", "disputed"}


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def viewer_role(tx: dict[str, Any], user: dict[str, Any]) -> str | None:
    if user["role"] == "admin":
        return "admin"
    if tx["producer_id"] == user["id"]:
        return "producer"
    if tx["collector_id"] == user["id"]:
        return "collector"
    return None


def to_out(tx: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in tx.items() if k != "qr_verification_token"}
    out["viewer_role"] = viewer_role(tx, user)
    return out


def qr_payload(tx_id: UUID, token: str) -> str:
    # URL profonde : scannable par l'app PWA ou par l'appareil photo natif du téléphone.
    return f"{settings.frontend_url.rstrip('/')}/transactions/{tx_id}/collect?token={token}"


async def get_visible(conn: asyncpg.Connection, user: dict[str, Any], tx_id: UUID, *, for_update=False):
    tx = await tx_repo.get(conn, tx_id, for_update=for_update)
    if tx is None or viewer_role(tx, user) is None:
        raise not_found("Transaction")
    return tx


def _check_token(tx: dict[str, Any], token: str) -> None:
    if not hmac.compare_digest(tx["qr_verification_token"].encode(), token.encode()):
        raise AppError(400, "INVALID_QR_TOKEN", "QR code invalide pour cette transaction")


async def reserve(
    conn: asyncpg.Connection, collector: dict[str, Any], listing_id: UUID, agreed_quantity: Decimal | None
) -> dict[str, Any]:
    async with conn.transaction():
        listing = await listings_repo.get_for_update(conn, listing_id)
        if listing is None:
            raise not_found("Annonce")
        if listing["producer_id"] == collector["id"]:
            raise forbidden("Impossible de réserver sa propre annonce")
        if listing["status"] != "published":
            raise conflict("LISTING_NOT_AVAILABLE", "Cette annonce n'est plus disponible")
        if await tx_repo.has_active_for_listing(conn, listing_id):
            raise conflict("LISTING_ALREADY_RESERVED", "Cette annonce est déjà réservée")

        quantity = agreed_quantity or listing["estimated_quantity"]
        if quantity > listing["estimated_quantity"]:
            raise bad_request("QUANTITY_EXCEEDS_ESTIMATE", "Quantité supérieure au gisement annoncé")

        unit_price = Decimal("0") if listing["is_free_donation"] else listing["price_per_unit"]
        total = _money(quantity * unit_price)

        tx_id = await tx_repo.create(
            conn,
            listing_id=listing_id,
            collector_id=collector["id"],
            agreed_quantity=quantity,
            unit_price=unit_price,
            total_amount=total,
            qr_token=secrets.token_urlsafe(32)[:43],
        )
        # Simulation séquestre : les fonds sont "bloqués" immédiatement.
        reference = await escrow_gateway.lock_funds(tx_id, total)
        await tx_repo.lock_escrow(conn, tx_id, reference)
        await listings_repo.set_status(conn, listing_id, "reserved")

        return await tx_repo.get(conn, tx_id)


async def verify_qr(conn: asyncpg.Connection, collector: dict[str, Any], tx_id: UUID, token: str):
    async with conn.transaction():
        tx = await get_visible(conn, collector, tx_id, for_update=True)
        if tx["collector_id"] != collector["id"]:
            raise forbidden("Seul le collecteur de la transaction peut scanner le QR code")
        _check_token(tx, token)
        if tx["payment_status"] != "escrow_locked":
            raise conflict("INVALID_STATE", "La transaction n'est pas en attente d'enlèvement")
        await tx_repo.mark_qr_scanned(conn, tx_id)
        await listings_repo.set_status(conn, tx["listing_id"], "in_transit")
        return await tx_repo.get(conn, tx_id)


async def collect(
    conn: asyncpg.Connection,
    collector: dict[str, Any],
    tx_id: UUID,
    *,
    token: str,
    final_weight: Decimal,
    weighing_proof_url: str | None,
):
    async with conn.transaction():
        tx = await get_visible(conn, collector, tx_id, for_update=True)
        if tx["collector_id"] != collector["id"]:
            raise forbidden("Seul le collecteur peut enregistrer la pesée")
        _check_token(tx, token)
        if tx["payment_status"] != "escrow_locked":
            raise conflict("INVALID_STATE", "La pesée a déjà été enregistrée ou la transaction est close")

        total = _money(final_weight * (tx["unit_price"] or Decimal("0")))
        co2 = _money(final_weight * tx["co2_factor_per_unit"])
        bsdd = await tx_repo.next_bsdd_number(conn, datetime.now(timezone.utc).year)

        await tx_repo.record_collection(
            conn,
            tx_id,
            final_weight=final_weight,
            total_amount=total,
            co2_saved_total=co2,
            weighing_proof_url=weighing_proof_url,
            bsdd_number=bsdd,
        )
        await listings_repo.set_status(conn, tx["listing_id"], "in_transit")
        return await tx_repo.get(conn, tx_id)


async def confirm(conn: asyncpg.Connection, producer: dict[str, Any], tx_id: UUID):
    async with conn.transaction():
        tx = await get_visible(conn, producer, tx_id, for_update=True)
        if tx["producer_id"] != producer["id"]:
            raise forbidden("Seul le producteur peut valider la remise")
        if tx["payment_status"] != "collected_pending_verification":
            raise conflict("INVALID_STATE", "Aucune pesée en attente de validation")
        await escrow_gateway.release_funds(tx["escrow_reference"], tx["total_amount"])
        await tx_repo.set_status(conn, tx_id, "paid", producer_confirmed_at=datetime.now(timezone.utc))
        await listings_repo.set_status(conn, tx["listing_id"], "completed")
        return await tx_repo.get(conn, tx_id)


async def dispute(conn: asyncpg.Connection, user: dict[str, Any], tx_id: UUID, reason: str):
    async with conn.transaction():
        tx = await get_visible(conn, user, tx_id, for_update=True)
        if viewer_role(tx, user) not in ("producer", "collector"):
            raise forbidden("Seules les parties peuvent ouvrir un litige")
        if tx["payment_status"] not in ("escrow_locked", "collected_pending_verification"):
            raise conflict("INVALID_STATE", "Un litige ne peut pas être ouvert à ce stade")
        await tx_repo.set_status(conn, tx_id, "disputed", dispute_reason=reason)
        return await tx_repo.get(conn, tx_id)


async def cancel(conn: asyncpg.Connection, user: dict[str, Any], tx_id: UUID):
    async with conn.transaction():
        tx = await get_visible(conn, user, tx_id, for_update=True)
        if viewer_role(tx, user) not in ("producer", "collector"):
            raise forbidden()
        if tx["payment_status"] not in ("pending_escrow", "escrow_locked") or tx["collected_at"]:
            raise conflict("INVALID_STATE", "Annulation impossible après la pesée")
        if tx["escrow_reference"]:
            await escrow_gateway.refund(tx["escrow_reference"])
        await tx_repo.set_status(conn, tx_id, "cancelled")
        await listings_repo.set_status(conn, tx["listing_id"], "published")
        return await tx_repo.get(conn, tx_id)


async def resolve(conn: asyncpg.Connection, admin: dict[str, Any], tx_id: UUID, resolution: str, note: str | None):
    async with conn.transaction():
        tx = await tx_repo.get(conn, tx_id, for_update=True)
        if tx is None:
            raise not_found("Transaction")
        if tx["payment_status"] != "disputed":
            raise conflict("INVALID_STATE", "La transaction n'est pas en litige")
        if resolution == "paid":
            if tx["final_weight"] is None:
                raise bad_request("NO_WEIGHING", "Impossible de clôturer en payé sans pesée enregistrée")
            await escrow_gateway.release_funds(tx["escrow_reference"], tx["total_amount"])
            await tx_repo.set_status(
                conn, tx_id, "paid", producer_confirmed_at=datetime.now(timezone.utc), resolution_note=note
            )
            await listings_repo.set_status(conn, tx["listing_id"], "completed")
        else:
            if tx["escrow_reference"]:
                await escrow_gateway.refund(tx["escrow_reference"])
            await tx_repo.set_status(conn, tx_id, "cancelled", resolution_note=note)
            await listings_repo.set_status(conn, tx["listing_id"], "published")
        return await tx_repo.get(conn, tx_id)
