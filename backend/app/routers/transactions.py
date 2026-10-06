from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, Query, Response, status

from app.db import get_conn
from app.errors import conflict, forbidden
from app.repositories import transactions as tx_repo
from app.schemas import (
    CollectIn,
    DisputeIn,
    QrOut,
    ReserveIn,
    TransactionOut,
    TransactionStatus,
    VerifyQrIn,
    VerifyQrOut,
)
from app.security import get_current_user, require_collector, require_producer
from app.services import bsdd
from app.services import transactions as svc

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/reserve", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def reserve(payload: ReserveIn, user: dict = Depends(require_collector), conn=Depends(get_conn)):
    tx = await svc.reserve(conn, user, payload.listing_id, payload.agreed_quantity)
    return svc.to_out(tx, user)


@router.get("", response_model=list[TransactionOut])
async def list_transactions(
    status_filter: TransactionStatus | None = Query(default=None, alias="status"),
    user: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_conn),
):
    rows = await tx_repo.list_for_user(conn, user_id=user["id"], role=user["role"], status=status_filter)
    return [svc.to_out(r, user) for r in rows]


@router.get("/{tx_id}", response_model=TransactionOut)
async def get_transaction(tx_id: UUID, user: dict = Depends(get_current_user), conn=Depends(get_conn)):
    return svc.to_out(await svc.get_visible(conn, user, tx_id), user)


@router.get("/{tx_id}/qr", response_model=QrOut)
async def get_qr(tx_id: UUID, user: dict = Depends(require_producer), conn=Depends(get_conn)):
    """QR code de remise : réservé au producteur (à présenter au collecteur sur site)."""
    tx = await svc.get_visible(conn, user, tx_id)
    if tx["producer_id"] != user["id"]:
        raise forbidden()
    if tx["payment_status"] != "escrow_locked":
        raise conflict("INVALID_STATE", "QR code disponible uniquement lorsque les fonds sont séquestrés")
    token = tx["qr_verification_token"]
    return {"transaction_id": tx_id, "token": token, "payload": svc.qr_payload(tx_id, token)}


@router.post("/{tx_id}/verify-qr", response_model=VerifyQrOut)
async def verify_qr(tx_id: UUID, payload: VerifyQrIn, user: dict = Depends(require_collector), conn=Depends(get_conn)):
    tx = await svc.verify_qr(conn, user, tx_id, payload.token)
    return {"valid": True, "transaction": svc.to_out(tx, user)}


@router.post("/{tx_id}/collect", response_model=TransactionOut)
async def collect(tx_id: UUID, payload: CollectIn, user: dict = Depends(require_collector), conn=Depends(get_conn)):
    tx = await svc.collect(
        conn,
        user,
        tx_id,
        token=payload.token,
        final_weight=payload.final_weight,
        weighing_proof_url=payload.weighing_proof_url,
    )
    return svc.to_out(tx, user)


@router.post("/{tx_id}/confirm", response_model=TransactionOut)
async def confirm(tx_id: UUID, user: dict = Depends(require_producer), conn=Depends(get_conn)):
    return svc.to_out(await svc.confirm(conn, user, tx_id), user)


@router.post("/{tx_id}/dispute", response_model=TransactionOut)
async def dispute(tx_id: UUID, payload: DisputeIn, user: dict = Depends(get_current_user), conn=Depends(get_conn)):
    return svc.to_out(await svc.dispute(conn, user, tx_id, payload.reason), user)


@router.post("/{tx_id}/cancel", response_model=TransactionOut)
async def cancel(tx_id: UUID, user: dict = Depends(get_current_user), conn=Depends(get_conn)):
    return svc.to_out(await svc.cancel(conn, user, tx_id), user)


@router.get("/{tx_id}/bsdd", responses={200: {"content": {"application/pdf": {}, "application/json": {}}}})
async def download_bsdd(
    tx_id: UUID,
    format: str = Query(default="pdf", pattern="^(pdf|json)$"),
    user: dict = Depends(get_current_user),
    conn=Depends(get_conn),
):
    """Bordereau de Suivi de Déchet Numérique (disponible après la pesée)."""
    tx = await svc.get_visible(conn, user, tx_id)
    if not tx["bsdd_number"]:
        raise conflict("BSDD_NOT_AVAILABLE", "Le bordereau est généré après la pesée sur site")
    filename = f"{tx['bsdd_number']}.{format}"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    if format == "json":
        import json

        body = json.dumps(bsdd.build_json(tx), ensure_ascii=False, indent=2)
        return Response(content=body, media_type="application/json", headers=headers)
    return Response(content=bsdd.build_pdf(tx), media_type="application/pdf", headers=headers)
