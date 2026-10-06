from typing import Any

import asyncpg
from fastapi import APIRouter, Depends, status

from app.db import get_conn
from app.errors import AppError, conflict
from app.repositories import users as users_repo
from app.schemas import ErrorResponse, LoginIn, RegisterIn, TokenOut, UserOut
from app.security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"], responses={401: {"model": ErrorResponse}})

# Hash factice pour lisser le temps de réponse quand l'email n'existe pas (anti-énumération)
_DUMMY_HASH = hash_password("dummy-password-for-timing-1")


def _token_response(user: dict[str, Any]) -> dict[str, Any]:
    token, expires_in = create_access_token(user["id"], user["role"])
    return {"access_token": token, "token_type": "bearer", "expires_in": expires_in, "user": user}


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED,
             responses={409: {"model": ErrorResponse}})
async def register(payload: RegisterIn, conn: asyncpg.Connection = Depends(get_conn)):
    if await users_repo.email_exists(conn, payload.email):
        raise conflict("EMAIL_ALREADY_USED", "Un compte existe déjà avec cet email")
    user = await users_repo.create(
        conn,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        organization_name=payload.organization_name,
        phone=payload.phone,
    )
    return _token_response(user)


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, conn: asyncpg.Connection = Depends(get_conn)):
    user = await users_repo.get_by_email_with_hash(conn, payload.email)
    if user is None:
        verify_password(payload.password, _DUMMY_HASH)
        raise AppError(401, "INVALID_CREDENTIALS", "Email ou mot de passe incorrect")
    if not verify_password(payload.password, user.pop("password_hash")):
        raise AppError(401, "INVALID_CREDENTIALS", "Email ou mot de passe incorrect")
    if not user["is_active"]:
        raise AppError(403, "ACCOUNT_DISABLED", "Compte désactivé")
    return _token_response(user)


@router.get("/me", response_model=UserOut)
async def me(user: dict = Depends(get_current_user)):
    return user
