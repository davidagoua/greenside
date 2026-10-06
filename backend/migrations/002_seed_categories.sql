-- =============================================================================
-- EcoLoop / Circular Hub — Migration 002 : données de référence
-- Facteurs CO2 indicatifs (kg CO2e évités par unité recyclée) — à ajuster
-- selon votre référentiel (ADEME Base Empreinte, GHG Protocol, etc.).
-- =============================================================================

INSERT INTO waste_categories (slug, name, unit, co2_factor_per_unit, suggested_price_per_unit) VALUES
    ('pet',       'Plastique PET',        'kg',    1.5000,  150.00),
    ('pehd',      'Plastique PEHD',       'kg',    1.2000,  120.00),
    ('used-oil',  'Huiles usagées',       'litre', 2.6000,  100.00),
    ('cardboard', 'Carton & Papier',      'kg',    0.9000,   40.00),
    ('metals',    'Métaux (ferreux/alu)', 'kg',    2.5000,  250.00),
    ('biomass',   'Biomasse & Organique', 'kg',    0.3000,   10.00)
ON CONFLICT (slug) DO NOTHING;

INSERT INTO schema_migrations(version) VALUES ('002_seed_categories') ON CONFLICT DO NOTHING;
