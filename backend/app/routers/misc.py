from typing import Literal
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from pydantic import BaseModel

from app.db import get_conn
from app.errors import not_found
from app.repositories import analytics as analytics_repo
from app.repositories import transactions as tx_repo
from app.repositories import users as users_repo
from app.schemas import GlobalStatsOut, ImpactOut, MediaOut, ResolveIn, TransactionOut, UserOut
from app.security import get_current_user, require_admin, require_collector, require_producer
from app.services import media
from app.services import transactions as svc

# --- Analytics -----------------------------------------------------------------------
analytics_router = APIRouter(prefix="/analytics", tags=["analytics"])


@analytics_router.get("/producer/impact", response_model=ImpactOut)
async def producer_impact(user: dict = Depends(require_producer), conn: asyncpg.Connection = Depends(get_conn)):
    return await analytics_repo.impact(conn, "producer", user["id"])


@analytics_router.get("/collector/impact", response_model=ImpactOut)
async def collector_impact(user: dict = Depends(require_collector), conn: asyncpg.Connection = Depends(get_conn)):
    return await analytics_repo.impact(conn, "collector", user["id"])


@analytics_router.get("/global", response_model=GlobalStatsOut, dependencies=[Depends(require_admin)])
async def global_stats(conn: asyncpg.Connection = Depends(get_conn)):
    data = await analytics_repo.impact(conn, "global", None)
    data.update(await analytics_repo.global_counters(conn))
    return data


# --- Médias --------------------------------------------------------------------------
media_router = APIRouter(prefix="/media", tags=["media"])


@media_router.post("/upload", response_model=MediaOut)
async def upload(
    file: UploadFile = File(...),
    folder: Literal["listings", "weighing"] = Form("listings"),
    user: dict = Depends(get_current_user),
):
    """Upload d'image (JPEG/PNG/WEBP, 5 MB max) -> Openinary, avec miniature optimisée."""
    return await media.upload_image(file, folder, user["id"])


# --- Administration ------------------------------------------------------------------
admin_router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


class UserActiveIn(BaseModel):
    is_active: bool


@admin_router.get("/users", response_model=list[UserOut])
async def list_users(
    role: Literal["producer", "collector", "admin"] | None = None,
    q: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    conn: asyncpg.Connection = Depends(get_conn),
):
    return await users_repo.list_users(conn, role=role, search=q, limit=limit, offset=offset)


@admin_router.patch("/users/{user_id}", response_model=UserOut)
async def set_user_active(user_id: UUID, payload: UserActiveIn, conn: asyncpg.Connection = Depends(get_conn)):
    user = await users_repo.set_active(conn, user_id, payload.is_active)
    if user is None:
        raise not_found("Utilisateur")
    return user


@admin_router.get("/disputes", response_model=list[TransactionOut])
async def list_disputes(admin: dict = Depends(get_current_user), conn: asyncpg.Connection = Depends(get_conn)):
    rows = await tx_repo.list_for_user(conn, user_id=admin["id"], role="admin", status="disputed")
    return [svc.to_out(r, admin) for r in rows]


@admin_router.post("/transactions/{tx_id}/resolve", response_model=TransactionOut)
async def resolve_dispute(
    tx_id: UUID,
    payload: ResolveIn,
    admin: dict = Depends(get_current_user),
    conn: asyncpg.Connection = Depends(get_conn),
):
    tx = await svc.resolve(conn, admin, tx_id, payload.resolution, payload.note)
    return svc.to_out(tx, admin)
