"""Test de bout en bout du back-office administrateur.

Couvre les endpoints consommés par les pages `frontend/pages/admin/` :
`GET /analytics/global`, `GET|PATCH /admin/users`, `GET /admin/disputes`,
`POST /admin/transactions/{id}/resolve`, `GET /transactions` (vue admin) et le
CRUD `/categories`.

Nécessite une base PostgreSQL/PostGIS accessible :

    DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ecoloop_admin_check \
    MEDIA_LOCAL_DIR=./media python -m tests.smoke_admin
"""
from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal

import httpx

from app import db
from app.main import app
from app.repositories import users as users_repo
from app.security import hash_password

API = "/api/v1"


def _check(condition: bool, label: str, detail: object = "") -> None:
    if not condition:
        raise AssertionError(f"❌ {label} — {detail}")
    print(f"  ✓ {label}")


async def _register(c: httpx.AsyncClient, role: str, sfx: str) -> dict:
    r = await c.post(
        f"{API}/auth/register",
        json={
            "email": f"{role}-{sfx}@ecoloop.io",
            "password": "Secret123",
            "role": role,
            "organization_name": f"{role.title()} SA",
            "phone": "+221 77 000 00 00",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _listing(c: httpx.AsyncClient, headers: dict, category_id: str, title: str) -> dict:
    r = await c.post(
        f"{API}/listings",
        headers=headers,
        json={
            "category_id": category_id,
            "title": title,
            "estimated_quantity": "500",
            "price_per_unit": "150",
            "location": {
                "label": "Usine",
                "address_text": "Zone industrielle, Dakar",
                "lat": 14.7167,
                "lng": -17.4677,
            },
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


async def main() -> None:
    await db.connect()
    await db.run_migrations()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        sfx = uuid.uuid4().hex[:6]

        producer = await _register(c, "producer", sfx)
        collector = await _register(c, "collector", sfx)
        hp = {"Authorization": f"Bearer {producer['access_token']}"}
        hc = {"Authorization": f"Bearer {collector['access_token']}"}

        # Compte administrateur créé hors inscription publique (comme app.cli)
        async with db.get_pool().acquire() as conn:
            admin = await users_repo.create(
                conn,
                email=f"admin-{sfx}@ecoloop.io",
                password_hash=hash_password("AdminSecret123"),
                role="admin",
                organization_name="EcoLoop Admin",
                phone="+221 77 111 11 11",
            )
        r = await c.post(
            f"{API}/auth/login", json={"email": admin["email"], "password": "AdminSecret123"}
        )
        assert r.status_code == 200, r.text
        ha = {"Authorization": f"Bearer {r.json()['access_token']}"}

        pet = next(x for x in (await c.get(f"{API}/categories")).json() if x["slug"] == "pet")

        print("\n[1] Cloisonnement des routes admin")
        _check((await c.get(f"{API}/admin/users", headers=hp)).status_code == 403, "producteur refusé sur /admin/users")
        _check((await c.get(f"{API}/analytics/global", headers=hp)).status_code == 403, "producteur refusé sur /analytics/global")
        _check((await c.get(f"{API}/admin/disputes", headers=hc)).status_code == 403, "collecteur refusé sur /admin/disputes")
        _check((await c.get(f"{API}/admin/users", headers=ha)).status_code == 200, "admin autorisé sur /admin/users")
        _check((await c.post(f"{API}/categories", json={}, headers=hp)).status_code == 403, "création catégorie refusée au producteur")

        print("\n[2] Cycle complet jusqu'au litige (transaction pesée)")
        listing = await _listing(c, hp, pet["id"], "Bouteilles PET compactées")
        tx = (
            await c.post(
                f"{API}/transactions/reserve",
                headers=hc,
                json={"listing_id": listing["id"], "agreed_quantity": "450"},
            )
        ).json()
        token = (await c.get(f"{API}/transactions/{tx['id']}/qr", headers=hp)).json()["token"]
        await c.post(f"{API}/transactions/{tx['id']}/verify-qr", headers=hc, json={"token": token})
        r = await c.post(
            f"{API}/transactions/{tx['id']}/collect",
            headers=hc,
            json={"token": token, "final_weight": "432.50"},
        )
        assert r.status_code == 200, r.text
        r = await c.post(
            f"{API}/transactions/{tx['id']}/dispute",
            headers=hc,
            json={"reason": "Poids réel très inférieur à la quantité convenue."},
        )
        _check(r.status_code == 200 and r.json()["payment_status"] == "disputed", "litige ouvert par le collecteur")

        print("\n[3] Litiges (arbitrage « payé »)")
        disputes = (await c.get(f"{API}/admin/disputes", headers=ha)).json()
        _check(any(d["id"] == tx["id"] for d in disputes), "litige visible dans /admin/disputes")
        found = next(d for d in disputes if d["id"] == tx["id"])
        _check(found["final_weight"] is not None, "pesée disponible → option « payé » débloquée côté UI")
        _check(found["dispute_reason"] is not None, "motif du litige remonté à l'admin")
        r = await c.post(
            f"{API}/admin/transactions/{tx['id']}/resolve",
            headers=ha,
            json={"resolution": "paid", "note": "Pesée contradictoire confirmée par les deux parties."},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        _check(body["payment_status"] == "paid", "transaction clôturée en « payé »")
        _check(body["resolution_note"] is not None, "note de résolution enregistrée")
        _check((await c.get(f"{API}/listings/{listing['id']}", headers=hp)).json()["status"] == "completed", "annonce clôturée")
        _check((await c.get(f"{API}/admin/disputes", headers=ha)).json() == [], "file de litiges vidée")

        print("\n[4] Garde-fou : arbitrage « payé » sans pesée")
        listing2 = await _listing(c, hp, pet["id"], "Cartons à enlever")
        tx2 = (
            await c.post(f"{API}/transactions/reserve", headers=hc, json={"listing_id": listing2["id"]})
        ).json()
        await c.post(
            f"{API}/transactions/{tx2['id']}/dispute",
            headers=hp,
            json={"reason": "Le collecteur ne s'est jamais présenté sur site."},
        )
        r = await c.post(
            f"{API}/admin/transactions/{tx2['id']}/resolve", headers=ha, json={"resolution": "paid"}
        )
        _check(r.status_code == 400 and r.json()["code"] == "NO_WEIGHING", "refus 400 NO_WEIGHING sans pesée")
        r = await c.post(
            f"{API}/admin/transactions/{tx2['id']}/resolve",
            headers=ha,
            json={"resolution": "cancelled", "note": "Enlèvement non réalisé, remboursement du séquestre."},
        )
        assert r.status_code == 200, r.text
        _check(r.json()["payment_status"] == "cancelled", "litige arbitré en « annulé »")
        _check((await c.get(f"{API}/listings/{listing2['id']}", headers=hp)).json()["status"] == "published", "annonce republiée")

        print("\n[5] Supervision globale")
        stats = (await c.get(f"{API}/analytics/global", headers=ha)).json()
        _check(stats["open_disputes"] == 0, "compteur de litiges ouverts à 0")
        _check(stats["completed_transactions"] >= 1, "transactions clôturées comptabilisées")
        _check(Decimal(str(stats["total_co2_saved_kg"])) > 0, "CO₂ évité agrégé non nul")
        _check(stats["users_by_role"].get("admin", 0) >= 1, "répartition par rôle présente")
        _check(isinstance(stats["listings_by_status"], dict), "répartition des annonces présente")
        _check(len(stats["by_material"]) >= 1, "impact par matière présent")
        # Les NUMERIC sont sérialisés en chaînes : le frontend doit les normaliser
        _check(isinstance(stats["total_co2_saved_kg"], str), "NUMERIC sérialisé en chaîne (contrat frontend)")

        print("\n[6] Gestion des utilisateurs")
        rows = (await c.get(f"{API}/admin/users?role=producer", headers=ha)).json()
        _check(all(u["role"] == "producer" for u in rows), "filtre par rôle respecté")
        rows = (await c.get(f"{API}/admin/users?q={sfx}&limit=25&offset=0", headers=ha)).json()
        _check(len(rows) >= 2, "recherche textuelle fonctionnelle")
        # Un rôle vide (comme `?role=`) doit être refusé : l'UI n'envoie jamais ce cas
        _check((await c.get(f"{API}/admin/users?role=", headers=ha)).status_code == 422, "role vide rejeté (422)")

        r = await c.patch(f"{API}/admin/users/{collector['user']['id']}", headers=ha, json={"is_active": False})
        _check(r.status_code == 200 and r.json()["is_active"] is False, "collecteur désactivé")
        r = await c.post(
            f"{API}/auth/login", json={"email": collector["user"]["email"], "password": "Secret123"}
        )
        _check(r.status_code == 403 and r.json()["code"] == "ACCOUNT_DISABLED", "connexion refusée après désactivation")
        _check(
            (await c.get(f"{API}/transactions", headers=hc)).status_code == 401,
            "jeton existant refusé après désactivation",
        )
        r = await c.patch(f"{API}/admin/users/{collector['user']['id']}", headers=ha, json={"is_active": True})
        _check(r.status_code == 200 and r.json()["is_active"] is True, "collecteur réactivé")
        _check(
            (await c.post(f"{API}/auth/login", json={"email": collector["user"]["email"], "password": "Secret123"})).status_code
            == 200,
            "connexion rétablie après réactivation",
        )

        print("\n[7] Vue admin des transactions")
        all_tx = (await c.get(f"{API}/transactions", headers=ha)).json()
        _check(any(t["id"] == tx["id"] for t in all_tx), "vue admin : toutes les transactions visibles")
        _check(all(t.get("qr_verification_token") is None for t in all_tx), "jeton QR jamais exposé")
        _check(len((await c.get(f"{API}/transactions?status=cancelled", headers=ha)).json()) >= 1, "filtre par statut")

        print("\n[8] Référentiel des catégories")
        r = await c.post(
            f"{API}/categories",
            headers=ha,
            json={
                "slug": f"verre-{sfx}",
                "name": "Verre creux",
                "unit": "kg",
                "co2_factor_per_unit": "0.6500",
                "suggested_price_per_unit": "35.00",
            },
        )
        assert r.status_code == 201, r.text
        created = r.json()
        _check(created["slug"] == f"verre-{sfx}", "catégorie créée")
        _check((await c.post(f"{API}/categories", headers=ha, json={"slug": f"verre-{sfx}", "name": "Doublon", "unit": "kg", "co2_factor_per_unit": "1"})).status_code == 409, "slug unique (409)")
        r = await c.patch(
            f"{API}/categories/{created['id']}", headers=ha, json={"name": "Verre creux coloré", "co2_factor_per_unit": "0.7000"}
        )
        _check(r.status_code == 200 and r.json()["name"] == "Verre creux coloré", "catégorie mise à jour")
        _check(r.json()["slug"] == f"verre-{sfx}", "slug non modifiable")
        _check(
            (await c.patch(f"{API}/categories/{created['id']}", headers=ha, json={"co2_factor_per_unit": "-1"})).status_code == 422,
            "facteur CO₂ négatif rejeté (422)",
        )
        _check((await c.delete(f"{API}/categories/{pet['id']}", headers=ha)).status_code == 409, "suppression bloquée si annonces rattachées")
        _check((await c.delete(f"{API}/categories/{created['id']}", headers=ha)).status_code == 204, "catégorie inutilisée supprimée")
        _check(
            (await c.patch(f"{API}/categories/{created['id']}", headers=ha, json={"name": "Verre"})).status_code == 404,
            "mise à jour d'une catégorie supprimée → 404",
        )

        print("\n✅ Back-office administrateur : tous les contrats vérifiés.")

    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
