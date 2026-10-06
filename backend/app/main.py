import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import db
from app.config import settings
from app.errors import register_error_handlers
from app.routers import auth, listings, reference, transactions
from app.routers.misc import admin_router, analytics_router, media_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await db.connect()
    if settings.run_migrations_on_startup:
        await db.run_migrations()
    yield
    await db.disconnect()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Marketplace circulaire B2B/B2C — collecte, valorisation et traçabilité des déchets recyclables.",
    lifespan=lifespan,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_error_handlers(app)

API_PREFIX = "/api/v1"
for r in (
    auth.router,
    reference.router,
    listings.router,
    transactions.router,
    analytics_router,
    media_router,
    admin_router,
):
    app.include_router(r, prefix=API_PREFIX)

# Fallback médias local (utilisé uniquement si OPENINARY_API_KEY est vide)
_media_dir = Path(settings.media_local_dir)
_media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=_media_dir), name="media")


@app.get("/health", tags=["health"])
async def health():
    async with db.get_pool().acquire() as conn:
        postgis = await conn.fetchval("SELECT PostGIS_Version()")
    return {"status": "ok", "postgis": postgis}
