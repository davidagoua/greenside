-- =============================================================================
-- EcoLoop / Circular Hub — Migration 001 : schéma initial
-- PostgreSQL 15+ / PostGIS 3+ (Supabase self-hosted compatible)
-- Idempotent : peut être ré-exécuté sans erreur.
-- =============================================================================

-- Extensions --------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Types énumérés ----------------------------------------------------------------
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('producer', 'collector', 'admin');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE listing_status AS ENUM ('draft', 'published', 'reserved', 'in_transit', 'completed', 'cancelled');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE transaction_status AS ENUM (
        'pending_escrow', 'escrow_locked', 'collected_pending_verification',
        'paid', 'disputed', 'cancelled'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Utilisateurs & Profils --------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email             VARCHAR(255) UNIQUE NOT NULL,
    password_hash     VARCHAR(255) NOT NULL,
    role              user_role NOT NULL DEFAULT 'producer',
    organization_name VARCHAR(255),
    phone             VARCHAR(30) NOT NULL,
    is_active         BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Adresses & Coordonnées PostGIS ------------------------------------------------
CREATE TABLE IF NOT EXISTS locations (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id      UUID REFERENCES users(id) ON DELETE CASCADE,
    label        VARCHAR(100),
    address_text TEXT NOT NULL,
    geom         GEOMETRY(Point, 4326) NOT NULL,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_locations_geom ON locations USING GIST(geom);
-- Index géographique (geography) pour accélérer ST_DWithin(geom::geography, ...)
CREATE INDEX IF NOT EXISTS idx_locations_geog ON locations USING GIST((geom::geography));
CREATE INDEX IF NOT EXISTS idx_locations_user ON locations(user_id);

-- Catégories de matières --------------------------------------------------------
CREATE TABLE IF NOT EXISTS waste_categories (
    id                       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug                     VARCHAR(50) UNIQUE NOT NULL,
    name                     VARCHAR(100) NOT NULL,
    unit                     VARCHAR(20) DEFAULT 'kg',
    co2_factor_per_unit      NUMERIC(8, 4) NOT NULL,
    suggested_price_per_unit NUMERIC(12, 2) DEFAULT 0
);

-- Annonces de gisements ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS listings (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    producer_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    category_id         UUID REFERENCES waste_categories(id),
    location_id         UUID REFERENCES locations(id),
    title               VARCHAR(200) NOT NULL,
    description         TEXT,
    estimated_quantity  NUMERIC(10, 2) NOT NULL CHECK (estimated_quantity > 0),
    price_per_unit      NUMERIC(12, 2) DEFAULT 0 CHECK (price_per_unit >= 0),
    is_free_donation    BOOLEAN DEFAULT FALSE,
    pickup_availability JSONB,
    images_urls         TEXT[] DEFAULT '{}',
    status              listing_status DEFAULT 'published',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_listings_status   ON listings(status);
CREATE INDEX IF NOT EXISTS idx_listings_producer ON listings(producer_id);
CREATE INDEX IF NOT EXISTS idx_listings_category ON listings(category_id);
CREATE INDEX IF NOT EXISTS idx_listings_location ON listings(location_id);

-- Transactions & Traçabilité (Bordereau numérique) ------------------------------
CREATE TABLE IF NOT EXISTS transactions (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id            UUID REFERENCES listings(id),
    collector_id          UUID REFERENCES users(id),
    agreed_quantity       NUMERIC(10, 2),
    final_weight          NUMERIC(10, 2),
    unit_price            NUMERIC(12, 2),
    total_amount          NUMERIC(12, 2),
    payment_status        transaction_status DEFAULT 'pending_escrow',
    escrow_reference      VARCHAR(100),
    qr_verification_token VARCHAR(64) UNIQUE NOT NULL,
    collected_at          TIMESTAMP WITH TIME ZONE,
    co2_saved_total       NUMERIC(10, 2),
    created_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Colonnes complémentaires nécessaires au workflow (double validation, preuve, BSDD, litiges)
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS qr_scanned_at          TIMESTAMP WITH TIME ZONE;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS weighing_proof_url     TEXT;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS collector_confirmed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS producer_confirmed_at  TIMESTAMP WITH TIME ZONE;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS bsdd_number            VARCHAR(40) UNIQUE;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS dispute_reason         TEXT;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS resolution_note        TEXT;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS updated_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_transactions_listing   ON transactions(listing_id);
CREATE INDEX IF NOT EXISTS idx_transactions_collector ON transactions(collector_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status    ON transactions(payment_status);

-- Numérotation séquentielle des bordereaux (BSDD-AAAA-000001)
CREATE SEQUENCE IF NOT EXISTS bsdd_number_seq START 1;

-- Une seule transaction "active" par annonce
CREATE UNIQUE INDEX IF NOT EXISTS uq_transactions_active_listing
    ON transactions(listing_id)
    WHERE payment_status IN ('pending_escrow', 'escrow_locked', 'collected_pending_verification', 'disputed');

-- Trigger updated_at ------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_listings_updated_at ON listings;
CREATE TRIGGER trg_listings_updated_at BEFORE UPDATE ON listings
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_transactions_updated_at ON transactions;
CREATE TRIGGER trg_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Table de suivi des migrations -------------------------------------------------
CREATE TABLE IF NOT EXISTS schema_migrations (
    version    VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Durcissement Supabase ---------------------------------------------------------
-- Le schéma "public" est exposé par PostgREST. Le backend se connecte en tant que
-- propriétaire des tables (bypass RLS) : on active RLS sans policy et on retire
-- tout droit aux rôles anon/authenticated pour que password_hash & co ne fuient pas.
ALTER TABLE users             ENABLE ROW LEVEL SECURITY;
ALTER TABLE locations         ENABLE ROW LEVEL SECURITY;
ALTER TABLE waste_categories  ENABLE ROW LEVEL SECURITY;
ALTER TABLE listings          ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions      ENABLE ROW LEVEL SECURITY;
ALTER TABLE schema_migrations ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE r TEXT;
BEGIN
    FOREACH r IN ARRAY ARRAY['anon', 'authenticated'] LOOP
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
            EXECUTE format(
                'REVOKE ALL ON users, locations, waste_categories, listings, transactions, schema_migrations FROM %I', r
            );
        END IF;
    END LOOP;
END $$;

INSERT INTO schema_migrations(version) VALUES ('001_init') ON CONFLICT DO NOTHING;
