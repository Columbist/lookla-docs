---
title: Database Schema
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 04_ARCHITECTURE/DATA_FLOW.md
  - 04_ARCHITECTURE/BACKEND_ARCHITECTURE.md
  - 00_GOVERNANCE/DECISION_LOG.md
  - 06_ENGINEERING/AUDIT.md
implementation_status: Describes current schema + 2 new fields required for DEC-010
---

# Database Schema
**Lookla Beauty Marketplace**

> **Logical model — no SQL.** This document defines entities, attributes, relationships, constraints, and indexing strategy. SQL DDL belongs in migration files (Alembic), not in documentation.
>
> **Scope:** MVP entities only. Post-MVP entities are marked [Future].
>
> **Current state:** PostgreSQL 16, single instance, no read replicas. Schema was created via `db/init.sql`; subsequent changes applied as ad-hoc ALTER TABLE (no Alembic yet — highest technical debt item).

---

## Entity Map

```
Country → Region → City → District (Location Hierarchy, DEC-010)
                              │
                         ┌────▼────┐
                         │  Salon  │◄──── ClaimRequest ◄──── User
                         └────┬────┘
               ┌──────────────┼──────────────┐
               │              │              │
          SalonHours      Service         Review
               │              │              │
               │         ServiceCategory   (source=google, MVP)
               │
            Photo
            SocialLink
            Staff [Future exposed]
```

---

## Entity 1 — Salon

The central entity. Represents one Beauty Business listing.

### Attributes

| Column | Type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER | NO | serial | Primary key |
| `slug` | VARCHAR(200) | NO | — | URL-safe; unique; generated from name+city |
| `name` | VARCHAR(255) | NO | — | Original crawled name |
| `name_el` | VARCHAR(255) | YES | — | Greek name |
| `description` | TEXT | YES | — | Usually Greek |
| `description_ru` | TEXT | YES | — | On-demand translation (DEC-011) |
| `description_uk` | TEXT | YES | — | On-demand translation |
| `address_street` | VARCHAR(255) | YES | — | |
| `address_number` | VARCHAR(20) | YES | — | |
| `address_city` | VARCHAR(100) | YES | — | **Currently stores districts (Glyfada, Kolonaki) — DEC-010 migration pending** |
| `address_district` | VARCHAR(100) | YES | — | **NEW — required by DEC-010.** The neighbourhood/area (Glyfada, Kolonaki, Kallithea) |
| `address_region` | VARCHAR(100) | YES | — | **NEW — required by DEC-010.** Region (Attica, Central Macedonia) |
| `address_postal` | VARCHAR(10) | YES | — | |
| `lat` | DECIMAL(10,8) | YES | — | WGS84 latitude |
| `lng` | DECIMAL(11,8) | YES | — | WGS84 longitude |
| `phone_primary` | VARCHAR(30) | YES | — | Main contact phone |
| `phone_secondary` | VARCHAR(30) | YES | — | |
| `email` | VARCHAR(255) | YES | — | Salon email (for claiming token delivery) |
| `website` | VARCHAR(500) | YES | — | Full URL |
| `rating_google` | DECIMAL(3,1) | YES | — | Aggregated Google rating (0.0 – 5.0) |
| `rating_count` | INTEGER | YES | 0 | Number of Google reviews |
| `price_level` | SMALLINT | YES | — | 1–4 (from crawled data) |
| `is_verified` | BOOLEAN | NO | false | true = "Information reviewed" by admin (DEC-014). NOT owner-claimed. |
| `is_active` | BOOLEAN | NO | true | false = hidden from public listing |
| `needs_review` | BOOLEAN | NO | false | true = in admin moderation queue |
| `data_verified_at` | TIMESTAMPTZ | YES | — | When admin last reviewed this record |
| `google_place_id` | VARCHAR(100) | YES | — | For deduplication across crawl runs |
| `created_at` | TIMESTAMPTZ | NO | now() | |
| `updated_at` | TIMESTAMPTZ | NO | now() | Updated on any change |

### Relationships

- **Salon → SalonHours** (1:many, up to 7 rows per salon — one per weekday)
- **Salon → Photo** (1:many)
- **Salon → Service** (1:many)
- **Salon → ServiceCategory** (many:many via `salon_categories` junction)
- **Salon → Review** (1:many)
- **Salon → SocialLink** (1:many)
- **Salon → Staff** (1:many — data in DB; not displayed in MVP)
- **Salon → ClaimRequest** (1:many — [Future user-facing])
- **Salon → User** via `salon_owners` junction (many:many — [Future user-facing])

### Constraints

- `slug` UNIQUE
- `google_place_id` UNIQUE (nullable — NULLs are not considered duplicate)
- `rating_google` CHECK (0.0 <= rating_google <= 5.0)
- `price_level` CHECK (price_level IN (1, 2, 3, 4))
- `is_verified = true` is only set by admin (or after owner claim completes) — enforced at application layer, not DB

### Indexes

| Index | Columns | Type | Purpose |
|---|---|---|---|
| `idx_salons_slug` | `slug` | UNIQUE BTREE | Fast URL lookup |
| `idx_salons_is_active` | `is_active` | BTREE | Filter inactive salons in all queries |
| `idx_salons_address_city` | `address_city` | BTREE | Current city filter (to migrate to district) |
| `idx_salons_address_district` | `address_district` | BTREE | **NEW — required for DEC-010 area filter** |
| `idx_salons_rating` | `rating_google DESC, rating_count DESC` | BTREE | Default sort order |
| `idx_salons_geo` | `lat, lng` | BTREE | Haversine distance queries |
| `idx_salons_needs_review` | `needs_review` WHERE `needs_review = true` | PARTIAL | Admin moderation queue |
| `idx_salons_fts` | `to_tsvector('simple', unaccent(name || ' ' || name_el || ' ' || address_city))` | GIN | Full-text search |
| `idx_salons_google_place_id` | `google_place_id` | BTREE (partial, NOT NULL) | Deduplication |

**DEC-010 migration note:** When `address_district` is populated, the `address_city` filter in search must be updated to use `address_district` instead. The FTS index should also include `address_district`.

### Future-Proof Notes

- `is_verified` will need to distinguish "admin-reviewed" vs "owner-claimed" in the future. Current approach: derive owner-claimed state from presence of a row in `salon_owners` table. Avoid adding a third `is_owner_verified` column unless the join becomes too expensive.
- `lat/lng` is adequate for Haversine. PostGIS adds GEOGRAPHY type for more accurate queries — consider when search performance requires it.

---

## Entity 2 — SalonHours

Weekly operating schedule for a salon.

### Attributes

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | NO | Primary key |
| `salon_id` | INTEGER | NO | FK → Salon |
| `day_of_week` | SMALLINT | NO | 0=Monday, 6=Sunday (ISO weekday − 1) |
| `open_time` | TIME | YES | NULL when is_closed=true |
| `close_time` | TIME | YES | NULL when is_closed=true |
| `is_closed` | BOOLEAN | NO | true = closed all day |

### Constraints

- UNIQUE (`salon_id`, `day_of_week`) — one row per weekday per salon
- CHECK: `day_of_week` BETWEEN 0 AND 6
- CHECK: when `is_closed = false`, both `open_time` and `close_time` must be NOT NULL

### Indexes

- `idx_salon_hours_salon_id` on `salon_id` (FK index; used in `_batch_open_now()`)

---

## Entity 3 — Service

A specific service offered by a salon, with pricing.

### Attributes

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | NO | Primary key |
| `salon_id` | INTEGER | NO | FK → Salon |
| `category_id` | INTEGER | NO | FK → ServiceCategory |
| `name` | VARCHAR(255) | NO | Original (usually Greek) |
| `name_el` | VARCHAR(255) | YES | Greek |
| `name_en` | VARCHAR(255) | YES | English (on-demand translation) |
| `name_ru` | VARCHAR(255) | YES | Russian (on-demand translation, DEC-011) |
| `name_uk` | VARCHAR(255) | YES | Ukrainian (on-demand translation) |
| `description` | TEXT | YES | |
| `duration_min` | INTEGER | YES | Duration in minutes |
| `price_from` | DECIMAL(10,2) | YES | Minimum price |
| `price_to` | DECIMAL(10,2) | YES | Maximum price (NULL = fixed price) |
| `currency` | CHAR(3) | NO | 'EUR' |
| `is_active` | BOOLEAN | NO | true |

### Constraints

- `price_from >= 0`
- `price_to IS NULL OR price_to >= price_from`
- `currency = 'EUR'` (only EUR in MVP; extend later)

### Indexes

- `idx_services_salon_id` on `salon_id`
- `idx_services_category_id` on `category_id`
- `idx_services_price_from` on `price_from` WHERE `price_from >= 5` (minimum price calculation)
- `idx_services_name_fts` on `to_tsvector('simple', unaccent(name))` GIN (for category keyword search)

### Translation Note

Translation flow: first real-user request for `/api/salons/{id}/services?lang=ru` → check `name_ru IS NULL` → batch GPT-4o-mini call for all services of this salon → UPDATE services SET name_ru = ... → cache is permanent.

---

## Entity 4 — ServiceCategory

Hierarchical category tree for services.

### Attributes

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | NO | Primary key |
| `name` | VARCHAR(100) | NO | Internal name |
| `name_el` | VARCHAR(100) | YES | Greek label |
| `name_en` | VARCHAR(100) | YES | English label |
| `name_ru` | VARCHAR(100) | YES | Russian label |
| `name_uk` | VARCHAR(100) | YES | Ukrainian label |
| `slug` | VARCHAR(100) | NO | URL param: `?category=nail-salon` |
| `parent_id` | INTEGER | YES | FK → ServiceCategory (for subcategories) |
| `icon` | VARCHAR(100) | YES | Icon identifier for CategoryGrid |

### Constraints

- `slug` UNIQUE
- `parent_id` self-reference: no circular hierarchy (enforced at application layer)

---

## Entity 5 — Location (Hierarchy)

The location model per DEC-010. Replaces flat `address_city` filter.

**Implementation approach:** For MVP, location hierarchy is implemented as reference data (a lookup table or hardcoded mapping), not a relational structure. This avoids a complex FK chain in the salons table while still enabling the area filter.

**MVP implementation:** A mapping table (or application-layer dict) from district slug to `address_city` ILIKE pattern:

```
district_slug   → display_name (el/en/ru/uk) → address_city_pattern
"glyfada"       → Γλυφάδα / Glyfada / Глифада / Гліфада → "Glyfada"
"kolonaki"      → Κολωνάκι / Kolonaki / Колонаки / Колонаки → "Kolonaki"
"kallithea"     → Καλλιθέα / Kallithea / Каллифея / Калліфея → "Kallithea"
"marousi"       → Μαρούσι / Marousi / Маруси / Маруси → "Marousi"
...
```

**Future (post-MVP):** Dedicated `locations` table with full hierarchy, populated during salon data migration.

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER | Primary key |
| `slug` | VARCHAR(100) | URL param: `?area=glyfada` |
| `level` | ENUM | `country`, `region`, `city`, `district` |
| `name_el` | VARCHAR(100) | |
| `name_en` | VARCHAR(100) | |
| `name_ru` | VARCHAR(100) | |
| `name_uk` | VARCHAR(100) | |
| `parent_id` | INTEGER | FK → Location |
| `salon_count` | INTEGER | Cached count (updated by crawlers) |

---

## Entity 6 — Review

A salon review. In MVP: all reviews are imported from Google (source='google').

### Attributes

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | NO | Primary key |
| `salon_id` | INTEGER | NO | FK → Salon |
| `source` | VARCHAR(20) | NO | 'google' (only value in MVP) |
| `author_name` | VARCHAR(100) | YES | Name from Google |
| `rating` | SMALLINT | NO | 1–5 |
| `text` | TEXT | YES | Original language (usually Greek) |
| `text_el` | TEXT | YES | Greek |
| `text_en` | TEXT | YES | On-demand translation |
| `text_ru` | TEXT | YES | On-demand translation (DEC-011 priority) |
| `text_uk` | TEXT | YES | On-demand translation |
| `published_at` | TIMESTAMPTZ | YES | Original Google publish date |
| `is_verified` | BOOLEAN | NO | false | Legacy column; not surfaced |

### Constraints

- `rating` CHECK (rating BETWEEN 1 AND 5)
- `source` CHECK (source IN ('google', 'lookla')) — 'lookla' is reserved for future native reviews

### Indexes

- `idx_reviews_salon_id` on `salon_id`
- `idx_reviews_source` on `source` (for future filtering by review type)

### DEC-013 Note

`source = 'google'` triggers the "Source: Google Reviews / Imported: Yes / Original: No" display label in the UI. This is enforced at the application/presentation layer, not the DB.

### Future-Proof Notes

When Lookla-native reviews exist (`source = 'lookla'`):
- Add `user_id` FK column
- Add `is_approved` (moderation gate)
- Add `helpful_count` (upvotes)
- The UI must visually distinguish source='lookla' from source='google'

---

## Entity 7 — User

Registered platform user.

### Attributes

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | NO | Primary key |
| `email` | VARCHAR(255) | NO | Unique; login identifier |
| `password_hash` | VARCHAR(255) | YES | bcrypt; NULL when Google-only account |
| `name` | VARCHAR(100) | YES | Display name |
| `google_id` | VARCHAR(100) | YES | From Google OAuth |
| `role` | VARCHAR(20) | NO | 'user', 'salon_owner', 'professional', 'admin' |
| `preferred_language` | CHAR(2) | YES | 'el', 'en', 'ru', 'uk' |
| `is_email_verified` | BOOLEAN | NO | false | Required before some actions |
| `is_active` | BOOLEAN | NO | true | false = soft-deleted/banned |
| `avatar_url` | VARCHAR(500) | YES | From Google OAuth or upload |
| `created_at` | TIMESTAMPTZ | NO | now() |

### Relationships

- **User → RefreshToken** (1:many — stored as SHA-256 hashes)
- **User → EmailVerification** (1:many)
- **User → PasswordReset** (1:many)
- **User → ClaimRequest** (1:many — [Future user-facing])
- **User → SalonOwner** via `salon_owners` (many:many — after claim)
- **User → Report** (1:many)

### Constraints

- `email` UNIQUE
- `google_id` UNIQUE (nullable — NULLs not considered duplicate)
- `role` CHECK (role IN ('user', 'salon_owner', 'professional', 'admin'))

### Indexes

- `idx_users_email` UNIQUE on `email`
- `idx_users_google_id` on `google_id` WHERE `google_id IS NOT NULL`

---

## Entity 8 — ClaimRequest

A Salon Owner's request to take ownership of a listing. [Backend complete; not user-facing in MVP]

### Attributes

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER | NO | Primary key |
| `user_id` | INTEGER | NO | FK → User |
| `salon_id` | INTEGER | NO | FK → Salon |
| `token` | VARCHAR(10) | NO | 6-char hex verification code |
| `channel` | VARCHAR(20) | NO | 'email' (only working channel; sms/whatsapp not wired) |
| `expires_at` | TIMESTAMPTZ | NO | 1 hour from creation |
| `used_at` | TIMESTAMPTZ | YES | Set on successful verification |
| `created_at` | TIMESTAMPTZ | NO | now() |

### Constraints

- UNIQUE (`user_id`, `salon_id`) for active (unused, non-expired) tokens — enforce at application layer
- `channel` CHECK (channel IN ('email', 'sms', 'whatsapp'))

### Post-claim state

On successful verification:
- `used_at` is set on this ClaimRequest
- A row is inserted into `salon_owners` (user_id, salon_id)
- `users.role` is updated to 'salon_owner'
- `salons.is_verified` is set to true (representing owner-verified, distinct from admin-reviewed)

---

## Entity 9 — ContactAction (Analytics Event — not stored in DB)

The contact action is tracked in GA4, not in the database. This entity is documented here for completeness and for any future decision to add server-side event storage.

**If server-side storage is added (future):**

| Column | Type | Notes |
|---|---|---|
| `id` | BIGSERIAL | Primary key |
| `salon_id` | INTEGER | FK → Salon |
| `action_type` | VARCHAR(20) | 'phone', 'whatsapp', 'website' |
| `locale` | CHAR(2) | User's locale at time of click |
| `session_id` | VARCHAR(100) | GA4 session ID (anonymized) |
| `occurred_at` | TIMESTAMPTZ | |

**MVP:** This is a GA4 client-side event only. No DB table exists or is needed.

---

## SQL-Only Tables (no ORM model — existing technical debt)

These tables exist and are used via raw SQL in routers. They are not new — they are pre-existing technical debt documented in Audit §14.

| Table | Purpose | Used by router |
|---|---|---|
| `salon_owners` | User ↔ Salon ownership (many:many) | `owner.py` |
| `claiming_tokens` | Ownership verification codes | `owner.py` |
| `appointments` | Booking records [not user-facing] | `bookings.py` |
| `conversations` | Chat thread headers [not user-facing] | `chat.py` |
| `messages` | Individual chat messages | `chat.py` |
| `availability_requests` | Soft booking via chat | `chat.py` |
| `moderation_queue` | Content awaiting admin review | `admin.py` |
| `reports` | User-submitted data reports | `reports.py`, `admin.py` |
| `subscription_plans` | Stripe plan definitions [not user-facing] | `payments.py` |
| `subscriptions` | Active subscriptions [not user-facing] | `payments.py` |

**Recommended action (not MVP blocking):** Add SQLAlchemy ORM models for `salon_owners`, `claiming_tokens`, `reports` at minimum — these are touched by MVP flows. Booking, chat, and payment tables can wait.

---

## Support Tables

### Photo

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER | Primary key |
| `salon_id` | INTEGER | FK → Salon |
| `url` | VARCHAR(500) | Current URL (Google Places or cdn.lookla.gr) |
| `r2_key` | VARCHAR(300) | NULL until R2 migration completes |
| `is_primary` | BOOLEAN | true = used as hero image |
| `width` | INTEGER | px |
| `height` | INTEGER | px |
| `caption` | VARCHAR(255) | |
| `created_at` | TIMESTAMPTZ | |

Index: `idx_photos_salon_id` on `salon_id`; `idx_photos_primary` on `(salon_id, is_primary)` WHERE `is_primary = true`

---

### SocialLink

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER | |
| `salon_id` | INTEGER | FK → Salon |
| `platform` | VARCHAR(30) | 'instagram', 'facebook', 'tiktok', etc. |
| `url` | VARCHAR(500) | |

---

### RefreshToken

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER | |
| `user_id` | INTEGER | FK → User |
| `token_hash` | VARCHAR(64) | SHA-256 of raw refresh token |
| `expires_at` | TIMESTAMPTZ | |
| `revoked_at` | TIMESTAMPTZ | NULL = active |

Index: `idx_refresh_tokens_hash` UNIQUE on `token_hash`; `idx_refresh_tokens_user` on `user_id`

---

## Schema Evolution Policy

Until Alembic is set up:
1. Document every schema change in this file before applying it
2. Write the ALTER TABLE statement explicitly and test on a staging DB first
3. Never edit `db/init.sql` to reflect the change — it's the initial seed only
4. Log the change in git with the commit message `db: add address_district column`

After Alembic is set up:
- All changes via `alembic revision --autogenerate`
- Migration files committed with the feature branch
- `alembic upgrade head` run as part of deployment

---

*Last updated: 2026-07-09*
