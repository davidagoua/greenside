from uuid import UUID

import asyncpg
import httpx
from fastapi import APIRouter, Depends, Query, Response, status

from app.config import settings
from app.db import get_conn
from app.errors import AppError, conflict, not_found
from app.repositories import categories as categories_repo
from app.repositories import locations as locations_repo
from app.schemas import CategoryIn, CategoryOut, CategoryUpdate, GeocodeResult, LocationIn, LocationOut
from app.security import get_current_user, require_admin

router = APIRouter(tags=["reference"])


# --- Catégories (lecture publique, écriture admin) --------------------------------
@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(conn: asyncpg.Connection = Depends(get_conn)):
    return await categories_repo.list_all(conn)


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
async def create_category(payload: CategoryIn, conn: asyncpg.Connection = Depends(get_conn)):
    return await categories_repo.create(conn, payload.model_dump())


@router.patch("/categories/{category_id}", response_model=CategoryOut, dependencies=[Depends(require_admin)])
async def update_category(category_id: UUID, payload: CategoryUpdate, conn: asyncpg.Connection = Depends(get_conn)):
    cat = await categories_repo.update(conn, category_id, payload.model_dump(exclude_unset=True))
    if cat is None:
        raise not_found("Catégorie")
    return cat


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_admin)])
async def delete_category(category_id: UUID, conn: asyncpg.Connection = Depends(get_conn)):
    if await categories_repo.is_used(conn, category_id):
        raise conflict("CATEGORY_IN_USE", "Catégorie utilisée par des annonces")
    if not await categories_repo.delete(conn, category_id):
        raise not_found("Catégorie")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Adresses de l'utilisateur -----------------------------------------------------
@router.get("/locations", response_model=list[LocationOut])
async def my_locations(user: dict = Depends(get_current_user), conn: asyncpg.Connection = Depends(get_conn)):
    return await locations_repo.list_for_user(conn, user["id"])


@router.post("/locations", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
async def create_location(
    payload: LocationIn, user: dict = Depends(get_current_user), conn: asyncpg.Connection = Depends(get_conn)
):
    return await locations_repo.create(conn, user_id=user["id"], **payload.model_dump())


@router.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: UUID, user: dict = Depends(get_current_user), conn: asyncpg.Connection = Depends(get_conn)
):
    if await locations_repo.is_used(conn, location_id):
        raise conflict("LOCATION_IN_USE", "Adresse utilisée par une annonce")
    if not await locations_repo.delete(conn, location_id, user["id"]):
        raise not_found("Adresse")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Géocodage (proxy Nominatim, évite d'exposer l'User-Agent / CORS côté client) --
@router.get("/geocode", response_model=list[GeocodeResult])
async def geocode(q: str = Query(min_length=3, max_length=200), _: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{settings.geocoder_url.rstrip('/')}/search",
                params={"q": q, "format": "jsonv2", "limit": 5, "addressdetails": 0},
                headers={"User-Agent": settings.geocoder_user_agent, "Accept-Language": "fr"},
            )
            resp.raise_for_status()
    except httpx.HTTPError:
        raise AppError(502, "GEOCODER_UNAVAILABLE", "Service de géocodage indisponible")
    return [
        {"display_name": r["display_name"], "lat": float(r["lat"]), "lng": float(r["lon"])} for r in resp.json()
    ]
