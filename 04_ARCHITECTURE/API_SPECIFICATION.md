---
title: API Specification
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-11
related_documents:
  - 04_ARCHITECTURE/BACKEND_ARCHITECTURE.md
  - 04_ARCHITECTURE/DATABASE_SCHEMA.md
  - 04_ARCHITECTURE/SECURITY.md
  - 03_PAGES/SALON.md
  - 03_PAGES/SEARCH.md
implementation_status: Documents current API + MVP-required additions
---

# API Specification
**Lookla Beauty Marketplace**

> **Approved.** Describes every API endpoint used in MVP user flows.
>
> **Base URL:** All endpoints under `/api/`. In production: `https://lookla.gr/api/` (via Nginx → FastAPI port 8001).
>
> **Convention:** Authentication via httpOnly cookie `access_token`. When noted as "Required", the request must include the cookie. Unauthenticated requests to protected endpoints return 401.
>
> **Not in MVP (documented for awareness):** Bookings, Chat, Payments endpoints exist in backend but are not called from MVP UI. Marked [Not user-facing].

---

## Salons

### GET /api/salons

**Purpose:** Paginated list of salons with search and filtering. Primary data source for the Search page.

**Authentication:** None (public)

**Query Parameters:**

| Param | Type | Required | Notes |
|---|---|---|---|
| `q` | string | No | Text search query. If `q` is an exact, complete localized district name (ru/uk, e.g. "Глифада", "Гліфада"), it's resolved via `AREA_METADATA` to the canonical `address_district` and matched with exact equality (T-006) — this takes precedence over the legacy path below. Otherwise, translated via SERVICE_SYNONYMS (ru/uk → en terms) and CITY_SYNONYMS (ru/uk/en → Greek city name, `address_city ILIKE`), unchanged. Combined service+location queries (e.g. "маникюр глифада") are not parsed — deferred to T-037. |
| `area` | string | No | **NEW (DEC-010).** District slug. Replaces old `city` param. Maps to `address_district` filter. |
| `city` | string | No | Legacy. Kept for backwards-compat during transition. Maps to `address_city ILIKE`. |
| `category` | string | No | Category slug. Mapped to keyword list via CATEGORY_KEYWORDS. |
| `min_rating` | float | No | Minimum `rating_google`. E.g. `4.0`. |
| `page` | integer | No | Default 0. Offset = page × 24. |
| `lang` | string | No | Not used for filtering; affects response field selection (future). |

**Response 200:**
```json
{
  "items": [
    {
      "id": 1234,
      "slug": "glyfada-nails",
      "name": "Glyfada Nails",
      "name_el": "Γκλιφάδα Νέιλς",
      "address_city": "Glyfada",
      "address_district": "Glyfada",
      "lat": 37.868,
      "lng": 23.754,
      "phone_primary": "+30 210 9641234",
      "rating_google": 4.7,
      "rating_count": 128,
      "price_level": 2,
      "is_verified": true,
      "is_owner_claimed": false,
      "is_open": true,
      "closes_at": "19:00",
      "min_price": 15.0,
      "primary_photo_url": "https://cdn.lookla.gr/salons/1234/primary.webp",
      "categories": ["nail-salon"]
    }
  ],
  "total": 47,
  "page": 0,
  "per_page": 24
}
```

**Errors:**
- 422 — invalid `min_rating` value (not a float)

**Notes:**
- `is_open` and `closes_at` are computed from `salon_hours` at Athens timezone (`Europe/Athens`)
- `min_price` is `MIN(price_from)` from services WHERE `price_from >= 5`
- Salons with `is_active = false` are excluded
- Default sort: `rating_google DESC, rating_count DESC`
- `area` param takes precedence over `city` param when both provided
- `area`/`city` and a district-alias `q` combine via ordinary AND, not
  override: a matching pair narrows to the same district (redundant but
  consistent); a conflicting pair (e.g. `area=athens-center&q=Глифада`,
  or `city=Athens&q=Глифада`) yields an empty result rather than either
  param silently winning (T-006)
- some district aliases overlap with older `CITY_SYNONYMS` entries (e.g.
  Ukrainian "Пірей" is both a legacy city synonym for `Πειραιάς` and the
  `Piraeus` district's `name_uk`). Overlapping aliases always take the new
  exact `address_district` semantics, never the legacy `address_city
  ILIKE` substring match — only `q` values with no district-alias match
  (e.g. "афины") continue through the unchanged legacy path (T-006)

**`is_owner_claimed` semantics (T-024, prerequisite for T-011's DEC-014 verification labels):**
- `true` when at least one row exists in `salon_owners` for this salon; `false` otherwise. `salon_owners` has no status/lifecycle column — presence of any row is the claimed signal, matching the existing claim flow in `app/routers/owner.py` (which already treats "any row for this salon_id" as "already claimed", raising 409 on a second claim attempt).
- Computed via a correlated SQL `EXISTS`, not a `LEFT JOIN + COUNT` — `salon_owners` has no unique constraint on `salon_id` alone (only a composite PK on `(user_id, salon_id)`), so a join could in principle duplicate a salon row; `EXISTS` always yields exactly one boolean per salon and cannot affect `total`/pagination.
- No owner identity (`user_id`, name, email) is exposed through this or any public salon endpoint — the field is a boolean only.
- **Not present in `GET /api/salons/map`** — that endpoint's compact, historically-fixed 10-field contract (Decision T-038) is intentionally not expanded by T-024.

---

### GET /api/salons/map

**Purpose:** Returns all matching salons (no pagination) with only map-relevant fields, for map rendering.

**Authentication:** None (public)

**Query Parameters:** Same as `/api/salons` (including `area`, per DEC-010) except no `page`/`limit` — this endpoint is not paginated.

**Response 200 — canonical contract: a bare JSON array, not `{items, total}`.**

```json
[
  {
    "id": 1234,
    "name": "Glyfada Nails",
    "slug": "glyfada-nails",
    "lat": 37.868,
    "lng": 23.754,
    "address_city": "Glyfada",
    "phone_primary": "+30 210 9641234",
    "rating_google": 4.7,
    "primary_photo": "https://cdn.lookla.gr/salons/1234/primary.webp",
    "is_open_now": true
  }
]
```

**Field notes:** all ten keys shown above are always present in every item; the
fields below may hold `null` — they are never absent:
- `rating_google` is `null` if the salon has no Google rating
- `primary_photo` is `null` when the salon has no photos
- `is_open_now` is computed from `salon_hours` at Athens timezone (`Europe/Athens`); it is `null` when opening-hours data is unavailable for the current day

**This is the confirmed, historically-accurate runtime contract (Decision T-038, 2026-07-11) — not an aspirational shape.** An earlier version of this document incorrectly specified `{"items": [...], "total": N}`; the endpoint has never actually returned that shape. Do not "fix" this endpoint to match a `{items, total}` wrapper — see the rationale below.

**Why a bare array, and not `{items, total}`:**
- The endpoint returns *all* matching points — there is no pagination to describe via a `total` separate from the payload
- `total` would be redundant with `response.length`
- The existing frontend map consumer (`app/[locale]/search/page.tsx`) already consumes this endpoint as a bare array (`Array.isArray(d) ? d : []`) — changing the shape would be a breaking change to a working consumer for no product benefit

**Filtering notes:**
- Only `is_active = true` salons with **non-null `lat` and `lng`** are returned — a salon can appear in `GET /api/salons` (which has no coordinate requirement) and correctly be absent from this endpoint
- `?area=glyfada` (and all other `GET /api/salons` filters — `city`, `q`, `category`, `min_rating`, `price_level`) apply identically here; `area` takes precedence over `city` exactly as in `GET /api/salons`
- An unresolvable `?area=` value returns `[]` with HTTP 200, not 404, and does not fall back to `city` — same contract as the list endpoint
- No pagination — returns all matching results (capped server-side at 2000 rows). Coordinate-only-plus-basics response keeps payload small for map rendering.

---

### GET /api/salons/{id_or_slug}

**Purpose:** Full salon detail. Used for salon detail page (SSR portion).

**Authentication:** None (public)

**Path:** `{id_or_slug}` accepts either numeric ID or string slug.

**Response 200:**
```json
{
  "id": 1234,
  "slug": "glyfada-nails",
  "name": "Glyfada Nails",
  "name_el": "Γκλιφάδα Νέιλς",
  "description": "Το καλύτερο σαλόνι...",
  "description_ru": "Лучший салон...",
  "address_street": "Λεωφόρος Βουλιαγμένης",
  "address_number": "12",
  "address_city": "Glyfada",
  "address_district": "Glyfada",
  "address_region": "Attica",
  "lat": 37.868,
  "lng": 23.754,
  "phone_primary": "+30 210 9641234",
  "website": "https://glyfadanails.gr",
  "rating_google": 4.7,
  "rating_count": 128,
  "price_level": 2,
  "is_verified": true,
  "is_owner_claimed": false,
  "is_open": true,
  "opens_at": null,
  "closes_at": "19:00",
  "hours": [
    { "day": 0, "open": "10:00", "close": "19:00", "is_closed": false },
    { "day": 6, "open": null, "close": null, "is_closed": true }
  ],
  "photos": [
    { "id": 1, "url": "https://cdn.lookla.gr/...", "is_primary": true }
  ],
  "social_links": [
    { "platform": "instagram", "url": "https://instagram.com/glyfadanails" }
  ],
  "categories": ["nail-salon"],
  "services": [],
  "reviews": []
}
```

**Notes:**
- `services` and `reviews` are always returned as `[]` in this response — loaded separately via lazy endpoints
- `is_open`, `closes_at`, `opens_at` computed at Athens timezone
- `is_owner_claimed` (T-024, DEC-014 prerequisite) — same `EXISTS`-based semantics as `GET /api/salons`, see above

**Errors:**
- 404 — salon not found or `is_active = false`

---

### GET /api/salons/{id}/services

**Purpose:** Returns translated service list. Lazy-loaded by frontend. Bot-protected.

**Authentication:** None (public)

**Query Parameters:**

| Param | Type | Required | Notes |
|---|---|---|---|
| `lang` | string | Yes | Target locale: `el`, `en`, `ru`, `uk` |

**Bot protection:** If `is_bot(user_agent)` returns true → returns empty array `[]` immediately. No translation triggered.

**Translation flow:**
1. Check `services.name_{lang}` — if NULL, trigger GPT-4o-mini batch for all salon services
2. Update DB with translated names
3. Return translated names

**Response 200:**
```json
{
  "items": [
    {
      "id": 10,
      "category_id": 3,
      "category_name": "Nail Care",
      "name": "Маникюр",
      "price_from": 15.0,
      "price_to": 25.0,
      "currency": "EUR",
      "duration_min": 60
    }
  ]
}
```

**Errors:**
- 404 — salon not found
- 503 — OpenAI translation failed (retry logic TBD; currently: return untranslated Greek name)

---

### GET /api/salons/{id}/reviews

**Purpose:** Returns translated reviews. Lazy-loaded. Bot-protected.

**Authentication:** None (public)

**Query Parameters:**

| Param | Type | Required | Notes |
|---|---|---|---|
| `lang` | string | Yes | Target locale |

**Bot protection:** Same as `/services` — returns `[]` for detected bots.

**Response 200:**
```json
{
  "source": "google",
  "items": [
    {
      "id": 5,
      "author_name": "Maria K.",
      "rating": 5,
      "text": "Εξαιρετική εξυπηρέτηση!",
      "text_translated": "Отличный сервис!",
      "is_translated": true,
      "published_at": "2026-03-15T00:00:00Z"
    }
  ]
}
```

**Note:** `source: "google"` is included at the response level — the frontend must display the DEC-013 label ("Source: Google Reviews / Imported: Yes / Original: No") whenever `source = "google"`.

**Errors:**
- 404 — salon not found

---

### GET /api/salons/{id}/photos

**Purpose:** All photos for a salon (for gallery rendering).

**Authentication:** None (public)

**Response 200:**
```json
{
  "items": [
    { "id": 1, "url": "https://cdn.lookla.gr/...", "is_primary": true, "width": 1200, "height": 800 }
  ]
}
```

---

## Search

### GET /api/search ⚠️ DEPRECATED

**Status:** Legacy — do not build new consumers against this endpoint.
**Canonical MVP endpoint:** `GET /api/salons`
**Deprecation task:** T-035 (add `Deprecation` header) → T-037 (removal after migration window)

**Purpose:** Unified search (salons + professionals in future). Supports Haversine geo-distance filtering. Currently returns salons only.

**Authentication:** None (public)

**Query Parameters:**

| Param | Type | Notes |
|---|---|---|
| `q` | string | Text query. Uses PostgreSQL FTS (`to_tsvector('simple', unaccent(...))`) — different from `/api/salons` ILIKE. |
| `lat`, `lng`, `radius` | float | Geo-distance filter (backend complete; no UI trigger in MVP per DEC-009) |
| `category` | string | Category slug |

**Notes:**
- Uses PostgreSQL FTS (`to_tsvector` / `plainto_tsquery` with `unaccent`). No GIN index exists (deferred to T-037).
- `GET /api/salons` is the canonical MVP search endpoint (used by Search page, map, all frontend).
- GIN index for this endpoint's FTS expression is blocked by `unaccent(text)` STABLE volatility and was deferred because this endpoint is deprecated. See `docs/.reviews/T-003a-review.md`.
- T-006's Russian/Ukrainian district query aliases target `GET /api/salons`/`GET /api/salons/map` only and do not depend on or modify this endpoint's independent FTS implementation.

**Response 200:** Same shape as `/api/salons`.

---

## Categories

### GET /api/categories

**Purpose:** Full category tree with i18n names. Used for filter dropdowns and CategoryGrid on homepage.

**Authentication:** None (public)

**Response 200:**
```json
{
  "items": [
    {
      "id": 1,
      "slug": "nail-salon",
      "name_el": "Νύχια",
      "name_en": "Nail Salon",
      "name_ru": "Салон ногтей",
      "name_uk": "Нейл-салон",
      "icon": "nail",
      "parent_id": null,
      "children": [...]
    }
  ]
}
```

**Caching:** This response rarely changes. Frontend should cache with `revalidate: 86400`.

---

## Areas (NEW — required for DEC-010)

### GET /api/areas

**Purpose:** Returns the list of Athens districts (and other areas) with salon counts. Used for area filter dropdown and AreaGrid on homepage.

**Status:** Implemented and verified in production (T-004, 2026-07-11).

**Authentication:** None (public)

**Query Parameters:**

| Param | Type | Notes |
|---|---|---|
| `region` | string | Optional. Filter by region slug (e.g. `attica`). Default: all. |

**Response 200:**
```json
{
  "items": [
    {
      "slug": "glyfada",
      "name_el": "Γλυφάδα",
      "name_en": "Glyfada",
      "name_ru": "Глифада",
      "name_uk": "Гліфада",
      "salon_count": 87,
      "region": "attica",
      "city": "athens"
    }
  ]
}
```

**Notes:**
- For MVP, this can be implemented as a hardcoded list in the backend (no dedicated DB table required)
- Post-MVP: derive from `locations` table when hierarchy migration is complete
- `salon_count` should reflect `is_active = true` salons only

---

## Auth

### POST /api/auth/register

**Authentication:** None

**Rate limit:** 5/minute, 20/hour

**Request:**
```json
{ "email": "...", "password": "...", "name": "...", "website_url": "" }
```

**Notes:** `website_url` is a honeypot — if non-empty, return 400 silently.

**Response 201:** Sets `access_token` + `refresh_token` httpOnly cookies.

**Errors:** 409 — email already registered; 400 — honeypot triggered; 422 — validation error

---

### POST /api/auth/login

**Authentication:** None

**Request:** `{ "email": "...", "password": "..." }`

**Response 200:** Sets auth cookies.

**Errors:** 401 — invalid credentials; 403 — account inactive

---

### POST /api/auth/logout

**Authentication:** Required

**Response 200:** Revokes refresh token in DB; clears cookies.

---

### POST /api/auth/refresh

**Authentication:** `refresh_token` cookie

**Response 200:** Issues new token pair; revokes old refresh token (rotation).

**Errors:** 401 — invalid or expired refresh token

---

### GET /api/auth/me

**Authentication:** Required

**Response 200:**
```json
{ "id": 1, "email": "...", "name": "...", "role": "user", "preferred_language": "ru" }
```

**Errors:** 401 — unauthenticated

---

### POST /api/auth/forgot-password

**Rate limit:** 3/minute, 10/hour

**Request:** `{ "email": "..." }`

**Response 200:** Always 200 (prevents email enumeration). Sends reset email if user exists.

---

### GET /api/auth/google/start

**Response 302:** Redirects to Google OAuth consent page with state cookie (CSRF).

---

### GET /api/auth/google/callback

**Response 302:** On success, sets auth cookies and redirects to `/account`.

---

## Reports

### POST /api/reports

**Purpose:** User submits "report incorrect information" for a salon.

**Authentication:** Required (DEC-016 — known friction; consider relaxing in future Change Request)

**Request:**
```json
{
  "salon_id": 1234,
  "report_type": "phone",
  "description": "The phone number is wrong, the correct one is +30..."
}
```

**`report_type` values:** `phone`, `hours`, `address`, `name`, `photos`, `other`

**Response 201:** `{ "message": "Report received" }`

**Errors:** 401 — unauthenticated; 404 — salon not found; 422 — invalid report_type

---

## Admin

All admin endpoints require `role = 'admin'`. Non-admin authenticated users receive 403.

### GET /api/admin/stats

**Response 200:**
```json
{
  "total_salons": 6320,
  "verified_salons": 128,
  "claimed_salons": 12,
  "needs_review": 43,
  "open_reports": 7,
  "total_users": 234
}
```

---

### GET /api/admin/salons

**Query Parameters:** `needs_review` (bool), `is_verified` (bool), `q` (string search)

**Response 200:** Paginated list of salons with admin flags.

---

### PATCH /api/admin/salons/{id}

**Purpose:** Update salon flags and content (for DEC-014 compliance and data quality).

**Request:**
```json
{
  "is_verified": true,
  "is_active": true,
  "needs_review": false,
  "phone_primary": "+30 210 9641234",
  "address_street": "Λεωφόρος Βουλιαγμένης"
}
```

**Notes:**
- All fields optional; only provided fields are updated
- `is_verified = true` sets `data_verified_at = now()`
- This is the primary way admin marks a salon as "Information reviewed" (DEC-014)

**Response 200:** Updated salon object.

---

### GET /api/admin/reports

**Query Parameters:** `status` ('open', 'resolved')

**Response 200:** Paginated list of reports with salon names.

---

### PATCH /api/admin/reports/{id}

**Request:** `{ "status": "resolved" }`

**Response 200:** `{ "id": 1, "status": "resolved" }`

---

### GET /api/admin/users

**Response 200:** Paginated list of users with email, role, created_at.

---

## Media

### GET /api/media/photo/{id}

**Purpose:** Lazy R2 migration proxy. On first call: fetches photo from Google Places URL, uploads to R2, updates DB. Subsequent calls for same photo: 301 redirect to `cdn.lookla.gr`.

**Authentication:** None (public)

**Response:** 
- First call: `200` + image bytes (proxied)
- Subsequent: `301` → `https://cdn.lookla.gr/salons/{id}/...`

**Bot handling:** No special bot handling here — photos are not translation-gated.

---

## Owner (Post-MVP — backend complete, not user-facing)

### POST /api/owner/claim/request

**Authentication:** Required

**Request:** `{ "salon_id": 1234 }`

**Behaviour:** Generates 6-char hex token → stores in `claiming_tokens` (1hr TTL) → sends email to `salons.email`

**Response 200:** `{ "message": "Verification code sent to salon email" }`

**Note:** Only `channel = 'email'` works. SMS/WhatsApp channel param exists but no API key configured.

---

### POST /api/owner/claim/verify

**Authentication:** Required

**Request:** `{ "salon_id": 1234, "token": "A3F9B2" }`

**Behaviour on success:**
- Sets `claiming_tokens.used_at`
- Inserts into `salon_owners` (user_id, salon_id)
- Updates `users.role = 'salon_owner'`
- Updates `salons.is_verified = true`

**Response 200:** `{ "message": "Salon claimed successfully" }`

**Errors:** 400 — invalid/expired token; 409 — salon already claimed

---

## Health

### GET /api/health

**Authentication:** None

**Response 200:** `{ "status": "ok", "db": "connected" }`

Used by Docker Compose healthcheck.

---

## Endpoints NOT in MVP UI (exist in backend)

| Router | Endpoints | Reason not in MVP |
|---|---|---|
| `bookings.py` | GET /slots, POST/GET/PATCH /bookings | DEC-015: no booking flow |
| `chat.py` | All conversation/message/availability-request | Chat not user-facing |
| `payments.py` | All Stripe endpoints | DEC-006: payments not user-facing |
| `masters.py` | PATCH /masters/me, portfolio, availability | Not in MVP scope |
| `professionals.py` | GET /professionals | Not in MVP scope |

These endpoints may return data if called directly but are not linked from any MVP UI surface.

---

## Error Response Format

All errors follow FastAPI's default format:

```json
{ "detail": "Human-readable error message" }
```

For validation errors (422):
```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "value is not a valid email", "type": "value_error.email" }
  ]
}
```

---

## Rate Limits

| Endpoint | Limit | Implementation |
|---|---|---|
| All endpoints | 200/minute per IP | slowapi (in-process; Redis pending) |
| POST /api/auth/register | 5/minute, 20/hour | slowapi |
| POST /api/auth/forgot-password | 3/minute, 10/hour | slowapi |
| All admin endpoints | No additional limit (requires auth) | — |

---

*Last updated: 2026-07-09*
