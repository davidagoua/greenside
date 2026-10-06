# EcoLoop / Circular Hub

Marketplace circulaire B2B/B2C pour la collecte, la valorisation et la traçabilité des déchets recyclables avec calcul d'impact carbone (PostGIS, FastAPI natif SQL, Nuxt 3 PWA, Openinary).

---

## 1. Architecture & Stack

* **Backend** : FastAPI (Python 3.12+), requêtes SQL directes et paramétrées via `asyncpg` (zéro ORM, interdiction du SDK Supabase).
* **Base de données** : PostgreSQL avec extensions `postgis` et `uuid-ossp` (compatible Supabase self-hosted).
* **Sécurité & Auth** : Hachage Argon2, tokens JWT applicatifs internes (`users` table), rôles : `producer`, `collector`, `admin`.
* **Frontend** : Nuxt 3 (SSR/PWA hybride), Tailwind CSS, Leaflet (carte interactive avec calcul de rayon géodésique), scanner caméra QR (`html5-qrcode`), générateur de QR Canvas.
* **Médias** : Service auto-hébergé Openinary (stockage d'images transformées à la volée / miniatures WebP) ou fallback local.
* **Traçabilité** : Bordereau de Suivi de Déchet Numérique (BSDD) téléchargeable en PDF (avec QR de vérification) ou JSON avec hash d'intégrité SHA-256.

---

## 2. Démarrage rapide avec Docker Compose

1. **Variables d'environnement** :
   ```bash
   cp .env.example .env
   ```
   Renseignez votre chaîne de connexion PostgreSQL / Supabase :
   ```env
   DATABASE_URL=postgresql://postgres:[PASSWORD]@[SUPABASE_HOST]:5432/postgres
   JWT_SECRET=un_secret_tres_long_et_securise
   ```

2. **Lancement de la stack multi-services** :
   ```bash
   docker compose up --build
   ```

3. **Accès aux services** :
   * **Frontend Nuxt PWA** : [http://localhost:3000](http://localhost:3000)
   * **Backend API & Swagger Docs** : [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
   * **Service Openinary** : [http://localhost:8080](http://localhost:8080)

---

## 3. Initialisation SQL de la Base de Données (Supabase)

Si vous utilisez l'éditeur SQL de Supabase ou un client `psql`, exécutez dans l'ordre les scripts du dossier [`backend/migrations/`](file:///Users/macbookpro/devspace/greenside/backend/migrations/) :

1. [`001_init.sql`](file:///Users/macbookpro/devspace/greenside/backend/migrations/001_init.sql) : extensions PostGIS, énumérations, tables (`users`, `locations`, `waste_categories`, `listings`, `transactions`), index GiST géographiques, durcissement RLS.
2. [`002_seed_categories.sql`](file:///Users/macbookpro/devspace/greenside/backend/migrations/002_seed_categories.sql) : catégories de déchets de référence (PET, PEHD, Huiles usagées, Carton, Métaux, Biomasse) et facteurs d'évitement CO₂ associés.

> *Note : Si `RUN_MIGRATIONS_ON_STARTUP=true`, le backend applique automatiquement ces scripts au démarrage.*

---

## 4. Création d'un administrateur

L'inscription publique est limitée aux rôles `producer` et `collector`. Pour initialiser un compte administrateur :

```bash
cd backend
.venv/bin/python -m app.cli create-admin admin@ecoloop.io 'MonMotDePasseFort123' '+221770000000'
```

---

## 5. Workflow de bout en bout

1. **Dépôt d'annonce** (`POST /api/v1/listings`) :
   * Le producteur spécifie la matière, le volume estimé, le tarif ou don gratuit, et géocode l'adresse.
2. **Recherche géolocalisée** (`GET /api/v1/listings/nearby?lat=...&lng=...&radius_km=25`) :
   * Le collecteur explore la carte interactive et filtre par rayon géographique via requête `ST_DWithin`.
3. **Réservation & Séquestre** (`POST /api/v1/transactions/reserve`) :
   * La transaction passe en statut `escrow_locked` (simulation de séquestre de fonds).
4. **Scan QR terrain** (`POST /api/v1/transactions/{id}/verify-qr`) :
   * Le producteur affiche le QR code dynamique depuis son écran.
   * Le collecteur scanne le QR code avec la caméra de son smartphone via la PWA.
5. **Pesée contradictoire** (`POST /api/v1/transactions/{id}/collect`) :
   * Le collecteur saisit le poids réel constaté (`final_weight`) et téléverse la photo du ticket de pesée.
   * Le CO₂ évité est automatiquement calculé (`final_weight * co2_factor_per_unit`).
6. **Validation & Clôture** (`POST /api/v1/transactions/{id}/confirm`) :
   * Le producteur valide la pesée ; les fonds séquestrés sont débloqués (`paid`).
   * Le bordereau BSDD (PDF ou JSON) est généré et téléchargeable.
7. **Dashboard RSE** (`GET /api/v1/analytics/producer/impact`) :
   * Total kg collectés, total CO₂ évité, arbres équivalents et répartition par flux.
