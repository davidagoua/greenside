"""Hachage Argon2 + JWT HS256 + dépendances d'autorisation par rôle."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

import asyncpg
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.db import get_conn
from app.errors import AppError
from app.repositories import users as users_repo

_hasher = PasswordHasher()
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(user_id: UUID, role: str) -> tuple[str, int]:
    expires_in = settings.jwt_expires_minutes * 60
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
        "iss": "ecoloop",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm), expires_in


def _unauthorized(detail: str = "Authentification requise") -> AppError:
    return AppError(401, "UNAUTHORIZED", detail, extra={})


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict[str, Any]:
    if creds is None or creds.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        payload = jwt.decode(
            creds.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm], issuer="ecoloop"
        )
        user_id = UUID(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise AppError(401, "TOKEN_EXPIRED", "Session expirée, veuillez vous reconnecter")
    except (jwt.PyJWTError, KeyError, ValueError):
        raise AppError(401, "INVALID_TOKEN", "Jeton d'authentification invalide")

    user = await users_repo.get_by_id(conn, user_id)
    if user is None or not user["is_active"]:
        raise AppError(401, "ACCOUNT_DISABLED", "Compte inexistant ou désactivé")
    return user


async def get_optional_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    conn: asyncpg.Connection = Depends(get_conn),
) -> dict[str, Any] | None:
    if creds is None:
        return None
    try:
        return await get_current_user(creds, conn)
    except AppError:
        return None


def require_roles(*roles: str) -> Callable[..., Any]:
    async def _dep(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if user["role"] not in roles:
            raise AppError(403, "INSUFFICIENT_ROLE", f"Rôle requis : {', '.join(roles)}")
        return user

    return _dep


require_producer = require_roles("producer")
require_collector = require_roles("collector")
require_admin = require_roles("admin")
