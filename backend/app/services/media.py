"""Gestion des médias : validation stricte + upload vers Openinary (ou fallback local)."""
from __future__ import annotations

import io
import logging
import uuid
from pathlib import Path
from typing import Literal

import httpx
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.config import settings
from app.errors import AppError

logger = logging.getLogger(__name__)

ALLOWED_FORMATS = {"JPEG": ("jpg", "image/jpeg"), "PNG": ("png", "image/png"), "WEBP": ("webp", "image/webp")}
THUMB_TRANSFORM = "w_480,h_360,c_fill,f_webp"
LARGE_TRANSFORM = "w_1280,f_webp"
Folder = Literal["listings", "weighing"]


async def _read_limited(file: UploadFile) -> bytes:
    max_bytes = settings.media_max_size_mb * 1024 * 1024
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise AppError(413, "FILE_TOO_LARGE", f"Fichier trop volumineux (max {settings.media_max_size_mb} MB)")
    if not data:
        raise AppError(400, "EMPTY_FILE", "Fichier vide")
    return data


def _detect_format(data: bytes) -> tuple[str, str]:
    """Vérifie le contenu réel (magic bytes) et pas seulement l'extension."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            fmt = img.format
            img.verify()
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise AppError(415, "UNSUPPORTED_MEDIA_TYPE", "Image invalide ou corrompue")
    if fmt not in ALLOWED_FORMATS:
        raise AppError(415, "UNSUPPORTED_MEDIA_TYPE", "Formats acceptés : JPEG, PNG, WEBP")
    return ALLOWED_FORMATS[fmt]


async def upload_image(file: UploadFile, folder: Folder, owner_id: uuid.UUID) -> dict:
    data = await _read_limited(file)
    ext, content_type = _detect_format(data)
    filename = f"{uuid.uuid4().hex}.{ext}"
    subfolder = f"ecoloop/{folder}/{owner_id}"

    if settings.openinary_api_key:
        return await _upload_openinary(data, filename, subfolder, content_type)
    return _store_local(data, filename, subfolder, content_type)


async def _upload_openinary(data: bytes, filename: str, folder: str, content_type: str) -> dict:
    url = f"{settings.openinary_url.rstrip('/')}/upload"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {settings.openinary_api_key}"},
                files={"files": (filename, data, content_type)},
                data={"folder": folder, "transformations": [THUMB_TRANSFORM, LARGE_TRANSFORM]},
            )
    except httpx.HTTPError as exc:
        logger.error("Openinary injoignable : %s", exc)
        raise AppError(502, "MEDIA_SERVICE_UNAVAILABLE", "Service média indisponible")

    if resp.status_code not in (200, 207):
        logger.error("Openinary upload KO %s : %s", resp.status_code, resp.text[:500])
        raise AppError(502, "MEDIA_UPLOAD_FAILED", "Échec de l'envoi au service média")
    body = resp.json()
    files = body.get("files") or []
    if not files:
        err = (body.get("errors") or [{}])[0].get("error", "Upload refusé")
        raise AppError(400, "MEDIA_UPLOAD_REJECTED", err)

    stored = files[0]
    path = stored["path"].lstrip("/")
    base = settings.openinary_public_url.rstrip("/")
    return {
        "url": f"{base}/t/{LARGE_TRANSFORM}/{path}",
        "thumbnail_url": f"{base}/t/{THUMB_TRANSFORM}/{path}",
        "path": path,
        "size": stored.get("size", len(data)),
        "content_type": content_type,
    }


def _store_local(data: bytes, filename: str, folder: str, content_type: str) -> dict:
    """Fallback développement : stockage disque + miniature WebP générée par Pillow."""
    root = Path(settings.media_local_dir)
    target_dir = root / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / filename).write_bytes(data)

    thumb_name = f"{Path(filename).stem}_thumb.webp"
    with Image.open(io.BytesIO(data)) as img:
        img = img.convert("RGB")
        img.thumbnail((480, 360))
        img.save(target_dir / thumb_name, "WEBP", quality=80)

    base = f"{settings.public_api_url.rstrip('/')}/media/{folder}"
    return {
        "url": f"{base}/{filename}",
        "thumbnail_url": f"{base}/{thumb_name}",
        "path": f"{folder}/{filename}",
        "size": len(data),
        "content_type": content_type,
    }
