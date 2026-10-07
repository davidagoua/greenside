# EcoLoop / Circular Hub

Marketplace circulaire B2B/B2C pour la collecte, la valorisation et la traçabilité des déchets recyclables avec calcul d'impact carbone (PostGIS, FastAPI natif SQL, Nuxt 3 PWA, Openinary).

---

## 1. Architecture & Stack

* **Backend** : FastAPI (Python 3.12+), requêtes SQL directes et paramétrées via `asyncpg` (zéro ORM, interdiction du SDK Supabase).
* **Base de données** : PostgreSQL avec extensions `postgis` et `uuid-ossp` (compatible Supabase self-hosted).
* **Sécurité & Auth** : Hachage Argon2, tokens JWT applicatifs internes (`users` table), rôles : `producer`, `collector`, `admin`.
* **Frontend** : Nuxt 3 (SSR/PWA hybride), **design system IBM Carbon** (thème clair/sombre configurable), Tailwind CSS pour la mise en page, **icônes Lineicons**, Leaflet (carte interactive avec calcul de rayon géodésique), scanner caméra QR (`html5-qrcode`), générateur de QR Canvas, **back-office administrateur** (supervision, arbitrage des litiges, utilisateurs, référentiel matières).
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

Si vous utilisez l'éditeur SQL de Supabase ou un client `psql`, exécutez dans l'ordre les scripts du dossier [`backend/migrations/`](backend/migrations/) :

1. [`001_init.sql`](backend/migrations/001_init.sql) : extensions PostGIS, énumérations, tables (`users`, `locations`, `waste_categories`, `listings`, `transactions`), index GiST géographiques, durcissement RLS.
2. [`002_seed_categories.sql`](backend/migrations/002_seed_categories.sql) : catégories de déchets de référence (PET, PEHD, Huiles usagées, Carton, Métaux, Biomasse) et facteurs d'évitement CO₂ associés.

> *Note : Si `RUN_MIGRATIONS_ON_STARTUP=true`, le backend applique automatiquement ces scripts au démarrage.*

---

## 4. Création d'un administrateur

L'inscription publique est limitée aux rôles `producer` et `collector`. Pour initialiser un compte administrateur :

```bash
cd backend
.venv/bin/python -m app.cli create-admin admin@ecoloop.io 'MonMotDePasseFort123' '+221770000000'
```

Après connexion, un compte `admin` est redirigé vers le back-office [`/admin`](http://localhost:3000/admin). Le lien **Administration** apparaît dans la navigation (et remplace l'onglet Impact RSE, dont les endpoints sont réservés aux producteurs et collecteurs).

---

## 5. Back-office administrateur

Interface Nuxt sous `/admin`, protégée par le middleware [`frontend/middleware/admin.ts`](frontend/middleware/admin.ts) (session valide **et** rôle `admin`, sinon redirection vers `/auth?redirect=…` puis retour à la page demandée).

| Page | Route | Endpoints consommés |
| --- | --- | --- |
| Vue d'ensemble | `/admin` | `GET /analytics/global` |
| Transactions | `/admin/transactions` | `GET /transactions?status=` (vue admin = toutes les transactions) |
| Litiges | `/admin/disputes` | `GET /admin/disputes`, `POST /admin/transactions/{id}/resolve` |
| Utilisateurs | `/admin/users` | `GET /admin/users?role=&q=&limit=&offset=`, `PATCH /admin/users/{id}` |
| Catégories | `/admin/categories` | `GET|POST /categories`, `PATCH|DELETE /categories/{id}` |

Points d'attention implémentés côté interface :

* **Arbitrage** : l'option « libérer les fonds au producteur » est désactivée quand aucune pesée n'existe, car le backend refuse ce cas en `400 NO_WEIGHING`.
* **Comptes** : un administrateur ne peut pas désactiver son propre compte ; la désactivation est confirmée par une modale et invalide immédiatement les jetons existants.
* **Catégories** : le slug est immuable après création et la suppression est refusée (`409 CATEGORY_IN_USE`) si des annonces y sont rattachées.
* **Montants** : les `NUMERIC` PostgreSQL arrivent en **chaîne** depuis l'API ; le composable [`frontend/composables/useFormat.ts`](frontend/composables/useFormat.ts) normalise et formate toutes les valeurs en fr-FR.

---

## 6. Workflow de bout en bout

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

---

## 7. Tests de bout en bout

Deux scripts d'intégration exercent l'API réelle (transport ASGI, sans serveur HTTP) : ils nécessitent une base **PostgreSQL + PostGIS** accessible.

```bash
cd backend
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ecoloop_test
export MEDIA_LOCAL_DIR=./media

python -m tests.smoke_workflow   # workflow complet : annonce → QR → pesée → BSDD → impact
python -m tests.smoke_admin      # back-office : litiges, utilisateurs, catégories, stats globales
```

> Les scripts appliquent les migrations au démarrage. Utilisez une base dédiée : `smoke_workflow` et `smoke_admin` créent des comptes, annonces et transactions de test.
>
> Le domaine `@ecoloop.test` est rejeté par `email-validator` (TLD réservé) : les jeux de données de test utilisent `@ecoloop.io`.

---

## 8. Design system, thème et icônes

L'interface repose sur le **design system IBM Carbon** ([`@carbon/styles`](https://carbondesignsystem.com)), avec un thème clair/sombre configurable et des icônes **Lineicons**.

### Thème clair / sombre

Carbon définit 4 thèmes ; l'application en utilise deux, appliqués par une classe sur `<html>` :

| Thème | Classe Carbon | Fond |
| --- | --- | --- |
| Clair | `.cds--g10` | `#f4f4f4` |
| Sombre | `.cds--g100` | `#161616` |

* La préférence est stockée dans le cookie `ecoloop_theme` et lue par [`frontend/composables/useTheme.ts`](frontend/composables/useTheme.ts) → `useTheme()` expose `theme`, `isDark`, `themeClass`, `toggleTheme`.
* La classe est posée côté serveur dans [`frontend/app.vue`](frontend/app.vue) via `useHead({ htmlAttrs: { class: themeClass } })` : **le premier pixel est déjà dans le bon thème**, sans flash au chargement.
* Le sélecteur se trouve dans l'en-tête ([`frontend/layouts/default.vue`](frontend/layouts/default.vue)).

### Couleurs : jetons Carbon uniquement

Aucune couleur n'est écrite en dur. [`frontend/tailwind.config.js`](frontend/tailwind.config.js) expose les jetons Carbon comme utilitaires Tailwind :

```html
<div class="bg-cds-layer-01 border border-cds-border-subtle text-cds-text-primary">
  <span class="text-cds-text-secondary">…</span>
  <span class="text-cds-support-error">…</span>
</div>
```

> ⚠️ Les jetons Carbon sont des valeurs hex/rgba, pas des canaux séparés : **les modificateurs d'opacité Tailwind ne fonctionnent pas** (`bg-cds-layer-01/50`). Utiliser les jetons dédiés (`cds-overlay`, `cds-layer-hover-01`, `cds-background-selected`…).
>
> Les palettes `slate-*` et `eco-*` sont conservées comme alias vers des jetons Carbon (filet de sécurité pour du code ancien), mais tout nouveau code doit utiliser `cds-*`.

### Composants Carbon utilisés

Carbon est intégré via ses **classes CSS officielles** (`@carbon/styles`) sur des éléments natifs — et non via `@carbon/web-components` : ce dernier repose sur Lit sans `@lit-labs/ssr`, donc sans rendu serveur (contenu vide jusqu'à l'hydratation) et il embarque `@ibm/telemetry-js`. Les classes CSS donnent le même rendu avec une intégration Vue/SSR native.

`cds--btn` (+ `--primary`, `--secondary`, `--tertiary`, `--ghost`, `--danger`, `--sm`, `--full`), `cds--text-input`, `cds--text-area`, `cds--select`, `cds--checkbox`, `cds--label`, `cds--form-item`, `cds--tag` (+ variantes de couleur), `cds--data-table`, `cds--modal`.

**Deux pièges d'intégration à connaître :**

1. **Modales** — Carbon masque `.cds--modal:not(.cds--modal--enable-presence)` (`opacity: 0; visibility: hidden`). Les modales étant montées par `v-if`, elles doivent porter `cds--modal--enable-presence` (c'est aussi ce qui fournit l'animation d'entrée) :
   ```html
   <div v-if="open" class="cds--modal cds--modal--enable-presence">…</div>
   ```
2. **Cellules de tableau** — `.cds--data-table td` (spécificité 0,1,1) fixe `color` et `text-align: start`, ce qui neutralise les utilitaires Tailwind (0,1,0). Sur une cellule, forcer l'utilitaire avec le modificateur `!` de Tailwind : `class="!text-right !text-cds-link-primary"`.

### Icônes Lineicons

```ts
import { Lineicons } from '@lineiconshq/vue-lineicons'
import { Icons } from '~/utils/icons'

<Lineicons :icon="Icons.location" :size="18" color="currentColor" />
```

* [`frontend/utils/icons.ts`](frontend/utils/icons.ts) est la **seule** couche qui référence les icônes : les vues utilisent `Icons.<intention>`, ce qui permet de changer de style ou de passer au pack Pro en un seul endroit.
* Le pack **gratuit** (855 icônes « outlined ») ne contient pas d'icônes `Warning`, `Alert`, `Info`, `QrCode`, `Recycle` ni `Image` — des substituts sont utilisés et documentés dans le fichier.
* `@lineiconshq/vue-lineicons` n'a pas de champ `exports` et n'est publié qu'en bundles minifiés : il est déclaré dans `build.transpile` de [`frontend/nuxt.config.ts`](frontend/nuxt.config.ts), sans quoi Nitro l'externalise et le SSR échoue.
* Les icônes sont tree-shakées : seules celles réellement importées entrent dans le bundle.

### Typographie

**IBM Plex Sans / Mono**, la fonte de Carbon, auto-hébergée dans `frontend/public/fonts/` (4 fichiers `.woff2`, ~250 Ko) et précachée par le service worker (`globPatterns` inclut `woff2`) pour rester disponible hors ligne.

### Performances

`@carbon/styles` représente ~970 Ko de CSS (≈112 Ko gzip). `features.inlineStyles` est désactivé : la feuille est servie comme fichier externe cacheable et précaché, plutôt qu'inlinée dans chaque réponse HTML (ce qui portait le HTML SSR à ~1 Mo).
