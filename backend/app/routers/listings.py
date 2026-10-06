from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, Query, status

from app.db import get_conn
from app.errors import bad_request, conflict, forbidden, not_found
from app.repositories import categories as categories_repo
from app.repositories import listings as listings_repo
from app.repositories import locations as locations_repo
from app.repositories import transactions as tx_repo
from app.schemas import ListingCreate, ListingOut, ListingStatus, ListingUpdate, NearbyListingOut
from app.security import get_optional_user, require_producer

router = APIRouter(prefix="/listings", tags=["listings"])

EDITABLE_STATUSES = {"draft", "published"}


@router.get("/nearby", response_model=list[NearbyListingOut])
async def nearby(
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    radius_km: float = Query(default=25, gt=0, le=500),
    category: str | None = Query(default=None, max_length=50, description="Slug de catégorie (ex: pet)"),
    limit: int = Query(default=200, ge=1, le=500),
    conn: asyncpg.Connection = Depends(get_conn),
):
    return await listings_repo.nearby(conn, lat=lat, lng=lng, radius_km=radius_km, category=category, limit=limit)


@router.get("", response_model=list[ListingOut])
async def list_published(
    category: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    conn: asyncpg.Connection = Depends(get_conn),
):
    return await listings_repo.list_published(conn, category=category, limit=limit, offset=offset)


@router.get("/mine", response_model=list[ListingOut])
async def my_listings(
    status_filter: ListingStatus | None = Query(default=None, alias="status"),
    user: dict = Depends(require_producer),
    conn: asyncpg.Connection = Depends(get_conn),
):
    return await listings_repo.list_by_producer(conn, user["id"], status_filter)


@router.get("/{listing_id}", response_model=ListingOut)
async def get_listing(
    listing_id: UUID,
    user: dict | None = Depends(get_optional_user),
    conn: asyncpg.Connection = Depends(get_conn),
):
    listing = await listings_repo.get(conn, listing_id)
    if listing is None:
        raise not_found("Annonce")
    if listing["status"] != "published":
        allowed = user is not None and (user["role"] == "admin" or user["id"] == listing["producer_id"])
        if not allowed and user is not None:
            allowed = bool(
                await conn.fetchval(
                    "SELECT 1 FROM transactions WHERE listing_id = $1 AND collector_id = $2", listing_id, user["id"]
                )
            )
        if not allowed:
            raise not_found("Annonce")
    return listing


@router.post("", response_model=ListingOut, status_code=status.HTTP_201_CREATED)
async def create_listing(
    payload: ListingCreate, user: dict = Depends(require_producer), conn: asyncpg.Connection = Depends(get_conn)
):
    if await categories_repo.get(conn, payload.category_id) is None:
        raise bad_request("INVALID_CATEGORY", "Catégorie inconnue")

    async with conn.transaction():
        if payload.location_id:
            if await locations_repo.get_for_user(conn, payload.location_id, user["id"]) is None:
                raise bad_request("INVALID_LOCATION", "Adresse inconnue")
            location_id = payload.location_id
        else:
            loc = await locations_repo.create(conn, user_id=user["id"], **payload.location.model_dump())
            location_id = loc["id"]

        data = payload.model_dump(exclude={"location", "location_id"})
        if payload.pickup_availability is not None:
            data["pickup_availability"] = payload.pickup_availability.model_dump()
        listing_id = await listings_repo.create(conn, producer_id=user["id"], location_id=location_id, data=data)
    return await listings_repo.get(conn, listing_id)


@router.patch("/{listing_id}", response_model=ListingOut)
async def update_listing(
    listing_id: UUID,
    payload: ListingUpdate,
    user: dict = Depends(require_producer),
    conn: asyncpg.Connection = Depends(get_conn),
):
    async with conn.transaction():
        current = await listings_repo.get_for_update(conn, listing_id)
        if current is None or current["producer_id"] != user["id"]:
            raise not_found("Annonce")
        if current["status"] not in EDITABLE_STATUSES:
            raise conflict("LISTING_LOCKED", "Annonce non modifiable (réservée, en cours ou clôturée)")

        data = payload.model_dump(exclude_unset=True)
        if "pickup_availability" in data and payload.pickup_availability is not None:
            data["pickup_availability"] = payload.pickup_availability.model_dump()
        if data.get("category_id") and await categories_repo.get(conn, data["category_id"]) is None:
            raise bad_request("INVALID_CATEGORY", "Catégorie inconnue")
        if data.get("location_id") and await locations_repo.get_for_user(conn, data["location_id"], user["id"]) is None:
            raise bad_request("INVALID_LOCATION", "Adresse inconnue")
        if data.get("is_free_donation"):
            data["price_per_unit"] = 0
        if data.get("status") == "cancelled" and await tx_repo.has_active_for_listing(conn, listing_id):
            raise conflict("LISTING_HAS_ACTIVE_TRANSACTION", "Une transaction est en cours")

        await listings_repo.update(conn, listing_id, data)
    return await listings_repo.get(conn, listing_id)


@router.delete("/{listing_id}", response_model=ListingOut)
async def cancel_listing(
    listing_id: UUID, user: dict = Depends(require_producer), conn: asyncpg.Connection = Depends(get_conn)
):
    """Suppression logique : passe l'annonce en `cancelled` (préserve la traçabilité)."""
    async with conn.transaction():
        current = await listings_repo.get_for_update(conn, listing_id)
        if current is None:
            raise not_found("Annonce")
        if current["producer_id"] != user["id"]:
            raise forbidden()
        if current["status"] not in EDITABLE_STATUSES:
            raise conflict("LISTING_LOCKED", "Annonce non annulable dans son état actuel")
        await listings_repo.set_status(conn, listing_id, "cancelled")
    return await listings_repo.get(conn, listing_id)
