"""Simulation de séquestre (escrow) en attendant le connecteur Mobile Money / Banque.

L'interface est volontairement minimale pour être remplacée par une vraie passerelle
(ex. Orange Money, Wave, MTN MoMo, Stripe Connect) sans toucher au workflow.
"""
from __future__ import annotations

import logging
import secrets
from decimal import Decimal
from uuid import UUID

logger = logging.getLogger(__name__)


class MockEscrowGateway:
    async def lock_funds(self, tx_id: UUID, amount: Decimal) -> str:
        reference = f"MOCK-ESC-{secrets.token_hex(6).upper()}"
        logger.info("[escrow] lock %s montant=%s ref=%s", tx_id, amount, reference)
        return reference

    async def release_funds(self, reference: str, amount: Decimal) -> None:
        logger.info("[escrow] release ref=%s montant=%s", reference, amount)

    async def refund(self, reference: str) -> None:
        logger.info("[escrow] refund ref=%s", reference)


escrow_gateway = MockEscrowGateway()
