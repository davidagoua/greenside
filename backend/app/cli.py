"""Utilitaires CLI.

Usage :
    python -m app.cli migrate
    python -m app.cli create-admin admin@ecoloop.io 'MotDePasse123' '+221770000000'
"""
from __future__ import annotations

import asyncio
import sys

from app import db
from app.repositories import users as users_repo
from app.security import hash_password


async def _migrate() -> None:
    await db.connect()
    try:
        await db.run_migrations()
        print("Migrations appliquées.")
    finally:
        await db.disconnect()


async def _create_admin(email: str, password: str, phone: str) -> None:
    await db.connect()
    try:
        async with db.get_pool().acquire() as conn:
            if await users_repo.email_exists(conn, email):
                await conn.execute("UPDATE users SET role = 'admin' WHERE lower(email) = lower($1)", email)
                print(f"Utilisateur existant promu admin : {email}")
                return
            user = await users_repo.create(
                conn,
                email=email,
                password_hash=hash_password(password),
                role="admin",
                organization_name="EcoLoop Admin",
                phone=phone,
            )
            print(f"Admin créé : {user['id']} ({email})")
    finally:
        await db.disconnect()


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "migrate":
        asyncio.run(_migrate())
    elif cmd == "create-admin" and len(sys.argv) == 5:
        asyncio.run(_create_admin(*sys.argv[2:5]))
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
