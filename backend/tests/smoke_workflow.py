"""Test de bout en bout du workflow (nécessite une base PostgreSQL/PostGIS accessible).

    DATABASE_URL=postgresql://postgres:postgres@localhost:55432/postgres \
    MEDIA_LOCAL_DIR=./media python -m tests.smoke_workflow
"""
from __future__ import annotations

import asyncio
import io
import uuid

import httpx
from PIL import Image

from app import db
from app.main import app

API = "/api/v1"


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (800, 600), (5, 150, 105)).save(buf, "PNG")
    return buf.getvalue()


async def main() -> None:
    await db.connect()
    await db.run_migrations()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        sfx = uuid.uuid4().hex[:6]

        async def register(role: str) -> dict:
            r = await c.post(f"{API}/auth/register", json={
                "email": f"{role}-{sfx}@ecoloop.test", "password": "Secret123", "role": role,
                "organization_name": f"{role.title()} SA", "phone": "+221 77 000 00 00",
            })
            assert r.status_code == 201, r.text
            return r.json()

        prod, coll = await register("producer"), await register("collector")
        hp = {"Authorization": f"Bearer {prod['access_token']}"}
        hc = {"Authorization": f"Bearer {coll['access_token']}"}

        # Erreur normalisée
        r = await c.post(f"{API}/auth/login", json={"email": "x@y.zz", "password": "nope"})
        assert r.status_code == 401 and r.json()["code"] == "INVALID_CREDENTIALS", r.text
        r = await c.post(f"{API}/auth/register", json={"email": "bad"})
        assert r.status_code == 422 and r.json()["code"] == "VALIDATION_ERROR", r.text

        me = (await c.get(f"{API}/auth/me", headers=hp)).json()
        assert me["role"] == "producer"

        cats = (await c.get(f"{API}/categories")).json()
        pet = next(x for x in cats if x["slug"] == "pet")

        # Upload média (fallback local)
        r = await c.post(f"{API}/media/upload", headers=hp, files={"file": ("a.png", _png(), "image/png")})
        assert r.status_code == 200, r.text
        img = r.json()
        r = await c.post(f"{API}/media/upload", headers=hp, files={"file": ("a.png", b"<html>", "image/png")})
        assert r.status_code == 415, r.text

        # Annonce avec adresse inline (Dakar)
        r = await c.post(f"{API}/listings", headers=hp, json={
            "category_id": pet["id"], "title": "Bouteilles PET compactées", "estimated_quantity": "500",
            "price_per_unit": "150", "images_urls": [img["thumbnail_url"]],
            "pickup_availability": {"days": ["monday", "thursday"], "hours": "08:00-16:00"},
            "location": {"label": "Usine", "address_text": "Zone industrielle, Dakar", "lat": 14.7167, "lng": -17.4677},
        })
        assert r.status_code == 201, r.text
        listing = r.json()

        # Le collecteur ne peut pas créer d'annonce
        r = await c.post(f"{API}/listings", headers=hc, json={})
        assert r.status_code == 403, r.text

        # Recherche géolocalisée
        r = await c.get(f"{API}/listings/nearby", params={"lat": 14.70, "lng": -17.45, "radius_km": 25, "category": "pet"})
        assert r.status_code == 200, r.text
        near = [x for x in r.json() if x["id"] == listing["id"]]
        assert near and near[0]["distance_km"] < 5, r.json()
        far = (await c.get(f"{API}/listings/nearby", params={"lat": 48.85, "lng": 2.35, "radius_km": 25})).json()
        assert not [x for x in far if x["id"] == listing["id"]]

        # Réservation + escrow
        r = await c.post(f"{API}/transactions/reserve", headers=hc, json={"listing_id": listing["id"], "agreed_quantity": "450"})
        assert r.status_code == 201, r.text
        tx = r.json()
        assert tx["payment_status"] == "escrow_locked" and tx["escrow_reference"].startswith("MOCK-ESC-")
        assert "qr_verification_token" not in tx
        r = await c.post(f"{API}/transactions/reserve", headers=hc, json={"listing_id": listing["id"]})
        assert r.status_code == 409, r.text

        # QR : producteur seulement
        assert (await c.get(f"{API}/transactions/{tx['id']}/qr", headers=hc)).status_code == 403
        qr = (await c.get(f"{API}/transactions/{tx['id']}/qr", headers=hp)).json()
        token = qr["token"]
        assert token in qr["payload"]

        bad = await c.post(f"{API}/transactions/{tx['id']}/verify-qr", headers=hc, json={"token": "x" * 43})
        assert bad.status_code == 400 and bad.json()["code"] == "INVALID_QR_TOKEN"
        r = await c.post(f"{API}/transactions/{tx['id']}/verify-qr", headers=hc, json={"token": token})
        assert r.status_code == 200 and r.json()["transaction"]["listing_status"] == "in_transit", r.text

        # Pesée
        r = await c.post(f"{API}/transactions/{tx['id']}/collect", headers=hc, json={
            "token": token, "final_weight": "432.50", "weighing_proof_url": img["url"],
        })
        assert r.status_code == 200, r.text
        tx = r.json()
        assert tx["payment_status"] == "collected_pending_verification"
        assert float(tx["co2_saved_total"]) == round(432.5 * 1.5, 2)
        assert float(tx["total_amount"]) == 432.5 * 150
        assert tx["bsdd_number"].startswith("BSDD-")

        # Validation producteur
        r = await c.post(f"{API}/transactions/{tx['id']}/confirm", headers=hp)
        assert r.status_code == 200 and r.json()["payment_status"] == "paid", r.text
        assert r.json()["listing_status"] == "completed"

        # BSDD
        r = await c.get(f"{API}/transactions/{tx['id']}/bsdd", headers=hp, params={"format": "pdf"})
        assert r.status_code == 200 and r.content[:4] == b"%PDF", r.text[:200]
        r = await c.get(f"{API}/transactions/{tx['id']}/bsdd", headers=hc, params={"format": "json"})
        assert r.status_code == 200 and r.json()["environmental"]["co2_saved_kg"] == "648.75", r.text

        # Impact
        ip = (await c.get(f"{API}/analytics/producer/impact", headers=hp)).json()
        ic = (await c.get(f"{API}/analytics/collector/impact", headers=hc)).json()
        assert float(ip["total_co2_saved_kg"]) == 648.75 and ic["completed_transactions"] == 1, (ip, ic)
        assert (await c.get(f"{API}/analytics/global", headers=hp)).status_code == 403

        print("✅ Workflow complet OK — BSDD", tx["bsdd_number"], "| CO2 évité", tx["co2_saved_total"], "kg")
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
