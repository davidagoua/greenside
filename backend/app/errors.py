"""Erreurs normalisées : { "detail": "message", "code": "ERROR_CODE" }."""
from __future__ import annotations

import logging
from typing import Any

import asyncpg
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, status_code: int, code: str, detail: str, extra: dict[str, Any] | None = None):
        self.status_code = status_code
        self.code = code
        self.detail = detail
        self.extra = extra or {}
        super().__init__(detail)


def not_found(what: str = "Ressource") -> AppError:
    return AppError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", f"{what} introuvable")


def forbidden(detail: str = "Action non autorisée") -> AppError:
    return AppError(status.HTTP_403_FORBIDDEN, "FORBIDDEN", detail)


def conflict(code: str, detail: str) -> AppError:
    return AppError(status.HTTP_409_CONFLICT, code, detail)


def bad_request(code: str, detail: str) -> AppError:
    return AppError(status.HTTP_400_BAD_REQUEST, code, detail)


_HTTP_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
}


def _body(detail: str, code: str, **extra: Any) -> dict[str, Any]:
    return {"detail": detail, "code": code, **extra}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        return JSONResponse(status_code=exc.status_code, content=_body(exc.detail, exc.code, **exc.extra))

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "Erreur HTTP"
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(detail, _HTTP_CODES.get(exc.status_code, "HTTP_ERROR")),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        errors = [
            {"field": ".".join(str(p) for p in e.get("loc", []) if p != "body"), "message": e.get("msg")}
            for e in exc.errors()
        ]
        first = errors[0] if errors else {"field": "", "message": "Requête invalide"}
        detail = f"{first['field']}: {first['message']}" if first["field"] else first["message"]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_body(detail, "VALIDATION_ERROR", errors=errors),
        )

    @app.exception_handler(asyncpg.UniqueViolationError)
    async def _unique(_: Request, exc: asyncpg.UniqueViolationError):
        return JSONResponse(status_code=409, content=_body("Ressource déjà existante", "UNIQUE_VIOLATION"))

    @app.exception_handler(asyncpg.ForeignKeyViolationError)
    async def _fk(_: Request, exc: asyncpg.ForeignKeyViolationError):
        return JSONResponse(status_code=400, content=_body("Référence invalide", "FOREIGN_KEY_VIOLATION"))

    @app.exception_handler(asyncpg.CheckViolationError)
    async def _check(_: Request, exc: asyncpg.CheckViolationError):
        return JSONResponse(status_code=400, content=_body("Contrainte de données violée", "CHECK_VIOLATION"))

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        logger.exception("Erreur non gérée", exc_info=exc)
        return JSONResponse(status_code=500, content=_body("Erreur interne du serveur", "INTERNAL_ERROR"))
