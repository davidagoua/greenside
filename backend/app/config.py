from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "EcoLoop Circular Hub API"
    environment: str = "development"

    # Base de données (Supabase self-hosted, connexion PostgreSQL directe)
    database_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    db_pool_min_size: int = 1
    db_pool_max_size: int = 10
    # Mettre 0 si la connexion passe par un pooler en mode transaction (Supavisor/PgBouncer)
    db_statement_cache_size: int = 100
    run_migrations_on_startup: bool = False

    # Auth
    jwt_secret: str = "super_secret_jwt_key_change_in_production"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60 * 24

    # Médias (Openinary)
    openinary_url: str = "http://openinary:3000"  # URL interne (backend -> Openinary)
    openinary_public_url: str = "http://localhost:8080"  # URL publique (navigateur -> Openinary)
    openinary_api_key: str = ""
    media_max_size_mb: int = 5
    media_local_dir: str = "/app/media"  # fallback si aucune clé Openinary n'est configurée
    public_api_url: str = "http://localhost:8000"

    # Frontend
    frontend_url: str = "http://localhost:3000"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Géocodage
    geocoder_url: str = "https://nominatim.openstreetmap.org"
    geocoder_user_agent: str = "EcoLoop/1.0 (contact@ecoloop.local)"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
