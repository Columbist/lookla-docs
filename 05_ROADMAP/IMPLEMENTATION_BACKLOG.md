---
title: Implementation Backlog
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 05_ROADMAP/EPICS.md
  - 05_ROADMAP/MILESTONE_M01.md
  - 04_ARCHITECTURE/BACKEND_ARCHITECTURE.md
  - 04_ARCHITECTURE/FRONTEND_ARCHITECTURE.md
  - 04_ARCHITECTURE/DATABASE_SCHEMA.md
  - 04_ARCHITECTURE/API_SPECIFICATION.md
  - 08_REVIEWS/ARCHITECTURE_REVIEW.md
implementation_status: N/A — planning document; tasks are work to be done
---

# Implementation Backlog
**Lookla Beauty Marketplace — M-01 MVP Athens Launch**

> **Priority levels:**
> - `P0` — Blocker. Launch is impossible without this.
> - `P1` — Required. Launch without this violates an approved decision (DEC-NNN) or creates legal risk.
> - `P2` — Important. Degrades the experience but doesn't block launch.
>
> **Owner codes:** `BE` = backend, `FE` = frontend, `DB` = database/migration, `OPS` = operations/infrastructure, `BOTH` = backend + frontend
>
> **Estimate** is in hours of focused work, not calendar time. Does not include context-switching or review overhead.

---

## EPIC-01 — Database Foundations

### T-001 — Set up Alembic migrations
**Priority:** P0 | **Owner:** BE | **Estimate:** 3h | **Epic:** EPIC-01
**Dependencies:** None

**Why:** Without Alembic, any schema change is applied ad-hoc and not version-controlled. Recovery from a corrupted DB would lose the new columns. This must be done before ANY schema change (see ARCHITECTURE_REVIEW UNDER-01).

**Steps:**

> **WARNING (C-01):** Do NOT use `--autogenerate` for the baseline on an existing production DB. That compares ORM models (9 tables) against the real DB (~19 tables) and may generate DROP statements for undocumented tables. Use an empty baseline + stamp instead.

1. `pip install alembic` + add to `requirements.txt`
2. `alembic init alembic` in `/backend`
3. Configure `alembic.ini`: `sqlalchemy.url = %(DATABASE_URL)s`
4. Configure `env.py`: `target_metadata = Base.metadata`
5. Create **empty** baseline revision: `alembic revision -m "baseline"` (leave `upgrade()` and `downgrade()` bodies empty — both `pass`)
6. Stamp the production DB without running any migration: `alembic stamp head`
7. Verify: `alembic current` returns the baseline revision hash
8. Commit migration file

**Acceptance Criteria:**
- [ ] `alembic current` on production DB shows the baseline revision
- [ ] `alembic history` shows the baseline revision
- [ ] `alembic upgrade head` on the ALREADY-RUNNING production DB completes with "Running upgrade -> {hash}, baseline" and makes no schema changes
- [ ] `alembic downgrade -1` on a test DB does not error

---

### T-002 — Add address_district and address_region columns
**Priority:** P0 | **Owner:** DB | **Estimate:** 1h | **Epic:** EPIC-01
**Dependencies:** T-001 (Alembic must be set up first)

**Migration content:**
```sql
ALTER TABLE salons ADD COLUMN address_district VARCHAR(100);
ALTER TABLE salons ADD COLUMN address_region VARCHAR(100);
CREATE INDEX idx_salons_address_district ON salons (address_district);
```

**Acceptance Criteria:**
- [ ] Migration file created via `alembic revision -m "add_address_district_region"`
- [ ] `alembic upgrade head` adds both columns and index
- [ ] `alembic downgrade -1` removes both columns and index cleanly
- [ ] `SELECT column_name FROM information_schema.columns WHERE table_name='salons'` includes both new columns

---

### T-003 — Backfill address_district for existing salons
**Priority:** P0 | **Owner:** BE | **Estimate:** 2h | **Epic:** EPIC-01
**Dependencies:** T-002

**Description:** Create a Python migration script that populates `address_district` from `address_city` values for all existing Athens salons. This is a data backfill, not a schema change.

**Approach:**
```python
# backend/scripts/backfill_districts.py
# Maps known address_city values to address_district
CITY_TO_DISTRICT = {
    "Γλυφάδα": "Glyfada",
    "Glyfada": "Glyfada",
    "Κολωνάκι": "Kolonaki",
    "Kolonaki": "Kolonaki",
    "Μαρούσι": "Marousi",
    "Marousi": "Marousi",
    "Κηφισιά": "Kifissia",
    "Kifissia": "Kifissia",
    "Καλλιθέα": "Kallithea",
    "Kallithea": "Kallithea",
    "Νέα Σμύρνη": "Nea Smyrni",
    "Πειραιάς": "Piraeus",
    "Piraeus": "Piraeus",
    "Χαλάνδρι": "Chalandri",
    "Αθήνα": "Athens Center",
    "Athens": "Athens Center",
    # ... extend with all crawled city values
}
```

**Acceptance Criteria:**
- [ ] Script runs without errors against production DB
- [ ] ≥80% of Athens salons have a non-null `address_district` after backfill
- [ ] Script is idempotent (can be run twice without duplicating data)
- [ ] `SELECT count(*) FROM salons WHERE address_district IS NULL AND address_city IS NOT NULL` returns < 20% of total

---

### T-003a — Verify GIN index on FTS tsvector
**Priority:** ~~P0~~ **DEFERRED** | **Owner:** DB | **Epic:** EPIC-01
**Status:** ✅ Verified — Deferred (2026-07-10)

**Findings:**
- No GIN index exists on `salons` (all 9 indexes are btree).
- Direct expression index is blocked: `unaccent(text)` is STABLE, not IMMUTABLE. PostgreSQL rejects the index with `ERROR: functions in index expression must be marked IMMUTABLE`.
- The only endpoint using this FTS expression is `GET /api/search`.
- `GET /api/search` is a legacy/deprecated endpoint. The MVP frontend uses `GET /api/salons` (ILIKE-based).
- Creating a GIN index for a deprecated endpoint is technical debt, not MVP value.
- No database change is required for M-01.

**Decision:** GIN index deferred to T-037 (search consolidation, post-MVP).
See `docs/.reviews/T-003a-review.md` for full investigation results and alternatives considered.

---

## EPIC-02 — Location Hierarchy (Area Filter)

### T-004 — Add GET /api/areas endpoint
**Priority:** P0 | **Owner:** BE | **Estimate:** 2h | **Epic:** EPIC-02
**Dependencies:** T-003 (data must be backfilled before counts are meaningful)

**Description:** Add `GET /api/areas` to `categories.py` router (reference: ARCHITECTURE_REVIEW CONTRADICTION-02).

**Response format (from API_SPECIFICATION.md):**
```json
{
  "areas": [
    { "slug": "glyfada", "name_el": "Γλυφάδα", "name_en": "Glyfada", "name_ru": "Глифада", "salon_count": 142 },
    ...
  ]
}
```

**Acceptance Criteria:**
- [ ] `GET /api/areas` returns 200 with ≥ 8 areas
- [ ] Response root key is `"items"` (consistent with all other Lookla endpoints — NOT "areas")
- [ ] Each area item includes `slug`, `name_el`, `name_en`, `name_ru`, `name_uk`, `salon_count`, `region`
- [ ] `salon_count` only counts `is_active = true` salons
- [ ] Empty areas (salon_count = 0) are excluded
- [ ] Response matches the schema in `API_SPECIFICATION.md`
- [ ] Endpoint added to `categories.py` router
- [ ] Registered in `main.py` — no changes needed if using existing `categories` router

---

### T-005 — Add area param to GET /api/salons
**Priority:** P0 | **Owner:** BE | **Estimate:** 1.5h | **Epic:** EPIC-02
**Dependencies:** T-004

**Description:** Add `?area=` query parameter that filters on `address_district`. Backwards-compatible: `?city=` still works. Applies to both `GET /api/salons` and `GET /api/salons/map`.

**Filter logic:** `area` is a public district *slug* (e.g. `athens-center`), not
raw `address_district` text (e.g. `Athens Center`) — a raw `ILIKE` on the slug
does not work (hyphen vs. space, casing). Resolve the slug through the
`AREA_METADATA` reverse lookup first, then filter by exact equality on the
canonical `address_district` value:

```python
# app/data/area_metadata.py
AREA_SLUG_TO_DISTRICT = {meta["slug"]: district for district, meta in AREA_METADATA.items()}

def get_district_by_area_slug(slug: str) -> str | None:
    return AREA_SLUG_TO_DISTRICT.get(slug.strip().lower()) if slug else None

# app/routers/salons.py
if area:
    district = get_district_by_area_slug(area)
    query = query.filter(Salon.address_district == district) if district else query.filter(false())
elif city:  # legacy fallback
    query = query.filter(Salon.address_city.ilike(f"%{city}%"))
```

Exact equality (not substring) is used because the input is a controlled
slug resolved against a controlled canonical value — substring matching
would risk matching unrelated districts (e.g. "Kallithea" vs. "Nea
Kallithea") and can't use the `address_district` index as efficiently.

**Acceptance Criteria:**
- [x] `GET /api/salons?area=glyfada` filters by `address_district = "Glyfada"` (resolved via `AREA_METADATA`, exact equality)
- [x] `GET /api/salons?city=Athens` still works (backwards compat)
- [x] `GET /api/salons?area=glyfada&city=Athens` — `area` takes precedence
- [x] `GET /api/salons?area=nonexistent` returns `{"items": [], "total": 0}`, not 404 — an unresolvable area does not fall back to `city`
- [x] `GET /api/salons/map?area=glyfada` supports the same area filter (map accepts the same params as the list endpoint, minus pagination)
- [x] Legacy `city` param remains available during the transition

---

### T-006 — Russian/Ukrainian district query aliases for canonical /api/salons
**Priority:** P1 | **Owner:** BE | **Estimate:** 1h | **Epic:** EPIC-02
**Dependencies:** T-004 (AREA_METADATA is the runtime source of truth for district aliases, not T-003 directly)
**Status:** ✅ Completed (2026-07-12) — merged to `main`, CI green, verified in production (`q=Глифада`→76, `q=Гліфада`→76, `q=центр Афин`→143, `q=Пірей`→90 matching the earlier `area=piraeus` count, `q=афины`→142 via unchanged legacy path, `area=athens-center&q=Глифада` and `map?city=Athens&q=Глифада` both correctly empty on conflict)

**Architecture correction (2026-07-12):** the original description was wrong
on two counts, discovered during implementation. `CITY_SYNONYMS` is *not*
part of the deprecated search module — it already runs inside the
canonical `GET /api/salons` and `GET /api/salons/map` (see
`_translate_query` in `app/routers/salons.py`). The deprecated
`GET /api/search` has its own, entirely independent PostgreSQL FTS
(`tsvector`/`unaccent`) and never touches `CITY_SYNONYMS` at all. Several
Athens district names (e.g. "глифада") were already partially handled via
`CITY_SYNONYMS`, but through substring `ILIKE` on `address_city` with a
hand-maintained Greek string — not exact equality on the canonical
`address_district` via `AREA_METADATA`, which didn't exist when
`CITY_SYNONYMS` was written.

**Description:** Accept an exact, complete localized district name in `q`
(e.g. "Глифада", "Гліфада", "центр Афин") and resolve it through
`AREA_METADATA` to the canonical `address_district`, matched with exact
equality — not substring matching, no fuzzy/stemmed matching, and no
combined service+location parsing ("маникюр глифада" stays out of scope,
deferred to T-037). A new `apply_text_query_filter()` helper runs before
the legacy `CITY_SYNONYMS` path and takes precedence for exact district
matches (since it's strictly more precise); every other query — including
existing pure city-name synonyms — continues through the unchanged legacy
path.

**Overlap rule with legacy `CITY_SYNONYMS` (review round 2 decision,
2026-07-12):** the new alias table includes `name_ru`/`name_uk`/`name_el`/
`name_en`/slug/canonical district from `AREA_METADATA`, and some of those
strings already exist in the older, hand-maintained `CITY_SYNONYMS` dict
(e.g. Ukrainian "Пірей" → legacy `Πειραιάς` city ILIKE, and also the
`Piraeus` district's `name_uk`). This is intentional, not an oversight:
**any `q` that matches `DISTRICT_QUERY_ALIASES` always takes canonical
`address_district` exact-match semantics, even where an overlapping
`CITY_SYNONYMS` entry exists** — it does not fall through to the legacy
`address_city ILIKE` path. Only `q` values with *no* district-alias match
(e.g. "афины", which has no district-alias entry — "Athens Center"'s
Russian name is the different string "Центр Афин") continue through the
unchanged legacy path. Verified end-to-end with dedicated fixture rows
that share the same legacy Greek `address_city` but differ in
`address_district`, proving the new path does not silently widen to the
old substring match.

**Acceptance Criteria:**
- [x] Russian "Глифада" resolves through `AREA_METADATA` to district
      "Glyfada" and works in `/api/salons?q=Глифада` (exact equality, not
      substring)
- [x] Ukrainian "Гліфада" resolves the same way
- [x] Russian "центр Афин" → "Athens Center" works
- [x] Same interpretation applied in `GET /api/salons/map`
- [x] `area=` and district-alias `q=` combine consistently: matching →
      expected results, conflicting → empty result (not one silently
      overriding the other)
- [x] `city=` (legacy) and district-alias `q=` combine the same way —
      matching narrows, conflicting empties, on both list and map
- [x] Aliases overlapping with legacy `CITY_SYNONYMS` (e.g. "Пірей") use
      exact district semantics, not the old substring path; non-overlapping
      legacy synonyms (e.g. "афины") are unaffected
- [x] Unit tests added — 37 new tests (pure alias resolution + list + map
      endpoints, including the overlap and city-interaction cases above),
      no regression in the existing 108 T-005/T-038 tests (145 total)

---

### T-038 — Resolve GET /api/salons/map response shape drift
**Priority:** P0 | **Owner:** BE/DOCS | **Estimate:** 0.5h | **Epic:** EPIC-02
**Dependencies:** T-005
**Status:** ✅ Completed (2026-07-11)

**Description:** `API_SPECIFICATION.md` documents `GET /api/salons/map` as
returning `{"items": [...], "total": N}`. The actual, long-standing runtime
contract (confirmed unchanged by T-005 — see T-005 review) returns a bare
list: `[{"id": 1, ...}, ...]`. T-005 deliberately preserved the real runtime
shape rather than silently redesigning the endpoint. This drift must be
resolved — one way or the other — before T-007 ships a frontend that
consumes this endpoint, so the frontend is built against a confirmed
contract rather than an aspirational one.

**Decision recorded: Option A** — the runtime bare-list contract is
canonical; `API_SPECIFICATION.md` was updated to match, not the other
way around. Rationale: the endpoint has no pagination (`total` would
just duplicate `response.length`), and the existing frontend map
consumer (`app/[locale]/search/page.tsx`) already parses the response
as a bare array (`Array.isArray(d) ? d : []`) — changing to `{items,
total}` would be a breaking change to a working consumer for no
product benefit. Option B (redesign the endpoint) was rejected as
unnecessary migration/regression risk for a shape that was never
actually broken — only documented incorrectly.

Backend now declares this explicitly via a `response_model` (was
previously undeclared, returning a raw dict list) — verified
byte-identical JSON output against production before/after.

**Acceptance Criteria:**
- [x] Product/eng decision recorded (which option, and why) — Option A, see above
- [x] `API_SPECIFICATION.md` and the runtime response shape agree
- [x] Existing map caller (`app/[locale]/search/page.tsx`) confirmed already compatible — no frontend change needed

---

### T-007 — Update SearchFilters.tsx with area dropdown
**Priority:** P0 | **Owner:** FE | **Estimate:** 2h | **Epic:** EPIC-02
**Dependencies:** T-004 (API endpoint must exist), T-038 ✅ done — map response shape confirmed, unblocked
**Status:** ✅ Completed (2026-07-12) — merged to `main`, CI green, verified in production

**Description:** Replace the city filter with an area filter. Fetch areas from `/api/areas`. Populate dropdown. Change filter label.

**Note:** `SearchFilters.tsx` (named in the original ticket) is dead code —
not imported anywhere. The actual filter UI lives inline in
`app/[locale]/search/page.tsx`; that's the file edited.

**Label changes (in all 4 message files):**
- `en.json`: `"filterArea": "Area"` (was "City")
- `el.json`: `"filterArea": "Περιοχή"` (was "Πόλη")
- `ru.json`: `"filterArea": "Район"` (was "Город")
- `uk.json`: `"filterArea": "Район"` (was "Місто")

**URL state:** Writes `?area=glyfada` (lowercase slug), not `?city=Glyfada`.

**Acceptance Criteria:**
- [x] Area dropdown shows ≥ 8 Athens districts with salon counts
- [x] Selecting an area writes `?area=` to the URL
- [x] Filter label shows "Area" (en) / "Περιοχή" (el) / "Район" (ru) / "Район" (uk)
- [x] Empty state: "No salons found in [selected area]" (not a crash)
- [x] Old `?city=` URL still works (shows salons, possibly with "City" label)

**Review round 2 fix:** `buildAreaUrlParams` only dropped the legacy `city`
param when a new area slug was selected, not when clearing back to "All
areas" — a URL like `?area=glyfada&city=Athens` kept filtering by Athens
after the user reset to "All areas", with no visible indication in the UI.
Fixed so any explicit interaction with the Area control (select or clear)
drops `city`; a bare `?city=` link is left untouched until the user
actually touches the control. Re-verified in production.

---

### T-008 — Update homepage CityGrid → AreaGrid
**Priority:** P1 | **Owner:** FE | **Estimate:** 1.5h | **Epic:** EPIC-02
**Dependencies:** T-004
**Status:** ✅ Completed (2026-07-13) — merged to `main`, verified in production

**Description:** Rename `CityGrid.tsx` to `AreaGrid.tsx`. Populate from `/api/areas` endpoint. Change section heading.

**Heading changes:**
- `en.json`: `"popularAreas": "Popular Areas"` (was "Popular Cities")
- `el.json`: `"popularAreas": "Δημοφιλείς Περιοχές"`
- `ru.json`: `"popularAreas": "Популярные районы"`
- `uk.json`: `"popularAreas": "Популярні райони"`

**Link format:** Each area tile links to `/[locale]/search?area=[slug]`

**Acceptance Criteria:**
- [x] Component file renamed to `AreaGrid.tsx`
- [x] Section heading updated in all 4 locales
- [x] Area tiles link to `?area=` URLs (not `?city=`)
- [x] Areas fetched from `/api/areas` with `revalidate: 86400` (SSR cache)
- [x] At least 6 area tiles visible on homepage desktop

**Production verification (2026-07-13):** All 4 locales show real Attica salon counts — Athens Center 143, Piraeus 90, Glyfada 76, Nea Ionia, Kallithea, Peristeri, Marousi, Kifissia. No `?city=` links. Runtime item validation (`isAreaItem`), Attica filter inside `selectPopularAreas()`, and a 5s fetch timeout were added in review round 2.

**Related fix (same day, separate branch/commit `2e4d8fe`):** Found and fixed a pre-existing, unrelated infra bug during production smoke-test — `beauty_web` had no `API_INTERNAL_URL` set, so all SSR fetches to the backend (this section and Popular Categories) were silently failing and rendering fallback/empty content. Fixed via `docker-compose.yml`.

---

## EPIC-03 — Honest Salon Detail

### T-009 — Remove booking stub buttons (DEC-015)
**Priority:** P0 | **Owner:** FE | **Estimate:** 1h | **Epic:** EPIC-03
**Dependencies:** None
**Status:** ✅ Completed (2026-07-13) — reviewed, merged to `main` (PR #30), production verified

**Description:** Locate and remove all booking-related UI in `SalonDetailClient.tsx` and any related sub-components.

**Search for:** `book`, `reserve`, `appointment`, `schedule`, `booking` (case-insensitive) in all salon-related frontend files.

**Acceptance Criteria:**
- [x] No text containing "book", "reserve", "appointment", or "schedule" visible on salon detail page
- [x] No booking modal, booking form, or booking button exists in DOM (none existed anywhere in the codebase)
- [x] "Call salon", "WhatsApp", "Visit website" CTAs are all present and visible above the fold on mobile — preserved unchanged from the pre-T-009 implementation, not newly built by T-009

**T-009 also removed** `components/ContactButtons.tsx` — found to be completely unreachable (zero imports anywhere in the codebase) and containing the same fake Book/Request/Message buttons. See T-010 below: its description assumed this file would be the CTA implementation vehicle, but it was dead code duplicating `SalonDetailClient.tsx`'s own inline CTA markup.

**Gaps discovered during T-009, owned by T-010:**
- A working **Viber** button renders today but isn't among DEC-015's 3 approved actions — decide keep/remove.
- The documented "no contact information" empty state (message + Report link) is not implemented — CTA area currently renders empty if phone/whatsapp/website/viber are all absent.

---

### T-010 — Implement contact CTAs (DEC-015/016)
**Priority:** P0 | **Owner:** FE | **Estimate:** 1.5h | **Epic:** EPIC-03
**Dependencies:** T-009

**Description:** Verify the 3 required CTAs against the final contract below. **Note (post-T-009):** `ContactButtons.tsx` no longer exists — T-009 deleted it as unreachable dead code. The working Call/WhatsApp/Website markup lives inline in `SalonDetailClient.tsx`. T-010 can either keep it inline or extract a `ContactButtons.tsx` component — that architecture decision was explicitly out of T-009's scope.

**CTA specifications:**
```tsx
// Call salon
<a href={`tel:${salon.phone_primary}`}>Call salon</a>

// WhatsApp — clean phone number (remove +, spaces, dashes)
const wa_number = salon.phone_primary.replace(/[\s\-\+\(\)]/g, '');
<a href={`https://wa.me/${wa_number}`} target="_blank" rel="noopener noreferrer">Message on WhatsApp</a>

// Website
<a href={salon.website_url} target="_blank" rel="noopener noreferrer">Visit website</a>
```

**Important:** All 3 CTAs must work WITHOUT being logged in (DEC-016). No authentication check before displaying or enabling these buttons.

**Acceptance Criteria:**
- [ ] "Call salon" button: on mobile, tapping initiates a phone call; on desktop, shows the phone number
- [ ] "WhatsApp" button: opens `https://wa.me/{number}` in a new tab
- [ ] "Visit website": opens salon website in a new tab with `rel="noopener noreferrer"`
- [ ] All 3 buttons visible while logged out (incognito window test)
- [ ] If `phone_primary` is null: "Call salon" and "WhatsApp" buttons are hidden (not shown with null)
- [ ] If `website_url` is null: "Visit website" button is hidden

---

### T-011 — Replace ✓ badge with text label (DEC-014)
**Priority:** P0 | **Owner:** FE | **Estimate:** 1.5h | **Epic:** EPIC-03
**Dependencies:** ARCHITECTURE_REVIEW CONTRADICTION-01 resolution must be decided first

**Description:** Replace the ✓ icon with text label. Two labels depending on source:
- `is_verified = true` AND `EXISTS salon_owners` → "Owner verified" text
- `is_verified = true` AND NOT `EXISTS salon_owners` → "Information reviewed" text
- `is_verified = false` → no label

**Implementation requires backend support:**

Backend must include in `GET /api/salons/{id}` and `GET /api/salons` (list items) a new field:
```json
{
  "is_verified": true,
  "is_owner_claimed": false  // NEW: derived from salon_owners table
}
```

This requires a backend change: add LEFT JOIN check for `salon_owners` to the salon query.

**Frontend:**
```tsx
{salon.is_verified && (
  <span className="text-sm text-green-700">
    {salon.is_owner_claimed ? t('ownerVerified') : t('infoReviewed')}
  </span>
)}
```

**Label i18n:**
- `t('infoReviewed')`: en="Information reviewed" / el="Πληροφορίες επαληθεύτηκαν" / ru="Информация проверена"
- `t('ownerVerified')`: en="Owner verified" / el="Επαληθεύτηκε από τον ιδιοκτήτη" / ru="Подтверждено владельцем"

**Acceptance Criteria:**
- [ ] No ✓ checkmark icon visible on any verified salon
- [ ] Text "Information reviewed" appears on admin-verified salons (no salon_owners row)
- [ ] Text "Owner verified" appears on claimed salons (salon_owners row exists)
- [ ] Unverified salons show no badge/label
- [ ] Label appears on both `SalonCard` (search results) and `SalonDetailClient`
- [ ] `GET /api/salons` response includes `is_owner_claimed` boolean field

---

### T-012 — Add Google review source label (DEC-013)
**Priority:** P0 | **Owner:** FE | **Estimate:** 1h | **Epic:** EPIC-03
**Dependencies:** None

**Description:** Add a fixed header above the reviews section in `SalonDetailClient.tsx`.

**Required text:**
```
Source: Google Reviews / Imported: Yes / Original: No
```

Localized:
- el: "Πηγή: Google Reviews / Εισήχθη: Ναι / Πρωτότυπο: Όχι"
- ru: "Источник: Google Reviews / Импортировано: Да / Оригинал: Нет"
- uk: "Джерело: Google Reviews / Імпортовано: Так / Оригінал: Ні"

**Important:** This label must NOT be in a tooltip. NOT collapsible. NOT behind "read more." Visible immediately above the reviews.

**Acceptance Criteria:**
- [ ] Header text visible on any salon with reviews, without scrolling to reviews (it's a section header)
- [ ] Header is visible in all 4 locales
- [ ] Text matches exactly: "Source: Google Reviews / Imported: Yes / Original: No" (en)
- [ ] Label appears regardless of whether `source='google'` check — all MVP reviews are Google anyway

---

## EPIC-04 — Analytics Integration

### T-013 — Create GA4 property and obtain tracking ID
**Priority:** P0 | **Owner:** OPS | **Estimate:** 0.5h | **Epic:** EPIC-04
**Dependencies:** None (operations task, not code)

**Steps:**
1. Log into Google Analytics account
2. Create property: "Lookla"
3. Add data stream: Web → `https://lookla.gr`
4. Copy Measurement ID (`G-XXXXXXXXXX`)
5. Set `NEXT_PUBLIC_GA4_ID=G-XXXXXXXXXX` in `.env` and `.env.example`

**Acceptance Criteria:**
- [ ] GA4 Measurement ID exists (not placeholder "G-XXXXXXXXXX")
- [ ] `.env` file has `NEXT_PUBLIC_GA4_ID` set
- [ ] `.env.example` has `NEXT_PUBLIC_GA4_ID=G-XXXXXXXXXX` (placeholder)

---

### T-014 — Add GA4 script to Next.js root layout
**Priority:** P0 | **Owner:** FE | **Estimate:** 1h | **Epic:** EPIC-04
**Dependencies:** T-013, T-018 (cookie consent must be in place first — see EPIC-05)

**Script placement (from FRONTEND_ARCHITECTURE.md):**
```tsx
// app/[locale]/layout.tsx
import Script from 'next/script';

<Script
  src={`https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GA4_ID}`}
  strategy="afterInteractive"
/>
<Script id="ga4-init" strategy="afterInteractive">
  {`window.dataLayer=window.dataLayer||[];
    function gtag(){dataLayer.push(arguments);}
    gtag('js',new Date());
    gtag('config','${process.env.NEXT_PUBLIC_GA4_ID}');`}
</Script>
```

**Acceptance Criteria:**
- [ ] GA4 script loaded with `strategy="afterInteractive"` (not blocking render)
- [ ] GA4 Realtime shows pageview when manually browsing the site
- [ ] Script does NOT appear if `lookla_consent=0` cookie (conditional load — depends on T-018)
- [ ] `NEXT_PUBLIC_GA4_ID` is read from env (not hardcoded)
- [ ] PageSpeed Insights LCP is not degraded by GA4 script

---

### T-015 — Implement useAnalytics hook and contact_action events
**Priority:** P0 | **Owner:** FE | **Estimate:** 2h | **Epic:** EPIC-04
**Dependencies:** T-014

**Description:** Create `hooks/useAnalytics.ts` and use it in `ContactButtons.tsx`.

```typescript
// hooks/useAnalytics.ts
export function useAnalytics() {
  const trackContact = (action_type: 'phone' | 'whatsapp' | 'website', salon_id: number, salon_name: string) => {
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', 'contact_action', {
        action_type,
        salon_id,
        salon_name,
      });
    }
  };
  return { trackContact };
}
```

**Usage in ContactButtons.tsx:**
```tsx
const { trackContact } = useAnalytics();
// On CTA click:
onClick={() => trackContact('phone', salon.id, salon.name)}
```

**Acceptance Criteria:**
- [ ] `contact_action` event appears in GA4 Realtime when clicking "Call salon"
- [ ] `contact_action` event appears when clicking "Message on WhatsApp"
- [ ] `contact_action` event appears when clicking "Visit website"
- [ ] Each event includes `action_type`, `salon_id`, `salon_name` custom parameters
- [ ] No error in browser console when `gtag` is not loaded (conditional check)

---

### T-016 — Set up Google Search Console
**Priority:** P0 | **Owner:** OPS | **Estimate:** 0.5h | **Epic:** EPIC-04
**Dependencies:** None (operations task)

**Steps:**
1. Go to Google Search Console
2. Add property: `https://lookla.gr`
3. Verify via DNS TXT record (preferred over HTML file — survives rebuilds)
4. Submit sitemap if available

**Acceptance Criteria:**
- [ ] Property verified (shows "Verified" in Search Console)
- [ ] URL inspection works for `https://lookla.gr`

---

## EPIC-05 — Legal and Compliance

### T-017 — Create Privacy Policy page
**Priority:** P0 | **Owner:** FE | **Estimate:** 1h (code) + privacy policy content | **Epic:** EPIC-05
**Dependencies:** None

**Description:** Create `app/[locale]/privacy/page.tsx` with Privacy Policy content.

**Minimum required content:**
- What is collected: session data, contact events, registration email
- Third parties: Google Analytics, Google OAuth, Cloudflare
- User rights: email hello@lookla.gr for access/deletion
- Cookie types: session (auth), analytics (GA4)
- Retention: 14 months for GA4

**Acceptance Criteria:**
- [ ] `/el/privacy`, `/en/privacy`, `/ru/privacy` return 200
- [ ] Page is linked in footer of all layouts
- [ ] Page mentions "Google Analytics" by name
- [ ] Page mentions contact email `hello@lookla.gr` for data requests
- [ ] Page does not use a marketing tone (factual, simple language)

---

### T-018 — Create cookie consent banner
**Priority:** P0 | **Owner:** FE | **Estimate:** 1.5h | **Epic:** EPIC-05
**Dependencies:** T-017

**Description:** Minimal cookie consent banner. Appears on first visit. Sets `lookla_consent=1` cookie. GA4 script (T-014) checks this cookie before loading.

**Minimal implementation:**
```tsx
// components/CookieConsent.tsx
// Shows banner at bottom of page on first visit
// "This site uses cookies for analytics. Accept to continue."
// Two buttons: "Accept" (sets cookie) and "Privacy Policy" link
// Banner disappears after accept, does not reappear (30-day cookie)
```

**Acceptance Criteria:**
- [ ] Banner appears on first visit (no `lookla_consent` cookie)
- [ ] Banner disappears after clicking "Accept"
- [ ] `lookla_consent=1` cookie is set after accept
- [ ] Banner does not appear on subsequent visits within 30 days
- [ ] GA4 script only fires after `lookla_consent=1` is set
- [ ] Banner includes link to `/[locale]/privacy`
- [ ] Banner is accessible on mobile 375px without blocking salon content

---

### T-019 — Configure GA4 data privacy settings
**Priority:** P0 | **Owner:** OPS | **Estimate:** 0.25h | **Epic:** EPIC-05
**Dependencies:** T-013

**Dashboard tasks (not code):**
1. GA4 Admin → Data Settings → Data Retention → set to 14 months
2. GA4 Admin → Data Streams → lookla.gr → configure Google signals → Disable (reduces PII risk)
3. GA4 property: IP anonymization (enabled by default in GA4; verify)
4. GA4 Admin → Account → User management → add `columb@europe.com` as admin

**Acceptance Criteria:**
- [ ] GA4 data retention = 14 months (screenshot for documentation)
- [ ] IP anonymization: verified active (default in GA4 since 2022)

---

## EPIC-06 — New Static Pages

### T-020 — Create /about page
**Priority:** P1 | **Owner:** FE | **Estimate:** 1h | **Epic:** EPIC-06
**Dependencies:** None

**Reference:** `docs/03_PAGES/ABOUT.md`

**Acceptance Criteria:**
- [ ] `/el/about`, `/en/about`, `/ru/about`, `/uk/about` return 200 (SSR)
- [ ] Page is linked from footer in all layouts
- [ ] Content does not claim booking or reservation features
- [ ] Content mentions "no account required to search" (DEC-016)
- [ ] No link to `/pricing` or `/plans`

---

### T-021 — Create /contact page
**Priority:** P1 | **Owner:** FE | **Estimate:** 0.5h | **Epic:** EPIC-06
**Dependencies:** None

**Reference:** `docs/03_PAGES/CONTACT.md`

**Acceptance Criteria:**
- [ ] `/el/contact`, `/en/contact`, `/ru/contact`, `/uk/contact` return 200 (SSR)
- [ ] Page is linked from footer in all layouts
- [ ] Page directs salon owners to email `hello@lookla.gr`
- [ ] Page mentions the "Report" button on salon pages as the user-facing feedback channel
- [ ] No contact form (email-only; no form = no spam)

---

## EPIC-07 — Homepage Updates

### T-022 — Move language switcher to header (HOME.md spec)
**Priority:** P1 | **Owner:** FE | **Estimate:** 1h | **Epic:** EPIC-07
**Dependencies:** None

**Description:** Add the `LanguageSwitcher` component to `Header.tsx`. The footer instance may remain as a secondary option.

**Constraint:** Language switcher in header must be visible on mobile (375px) without scrolling.

**Acceptance Criteria:**
- [ ] Language switcher visible in header on desktop
- [ ] Language switcher visible on mobile 375px without scrolling
- [ ] Switching language in header preserves the current page path + locale segment
- [ ] Footer language switcher still works (secondary, not removed)
- [ ] `/pricing` link NOT present in header (verify while implementing, DEC-006)

---

### T-023 — Update "How it works" step 3 copy
**Priority:** P2 | **Owner:** FE | **Estimate:** 0.25h | **Epic:** EPIC-07
**Dependencies:** None

**Description:** Step 3 of "How it works" must mention that no registration is required to make contact (DEC-016). Update in all 4 locale message files.

**Acceptance Criteria:**
- [ ] Step 3 text (en) includes "no account required" or equivalent
- [ ] Updated in `messages/en.json`, `messages/el.json`, `messages/ru.json`, `messages/uk.json`

---

## EPIC-08 — Admin Enhancement

### T-024 — Backend: is_owner_claimed field in salon responses
**Priority:** P0 | **Owner:** BE | **Estimate:** 1h | **Epic:** EPIC-08
**Dependencies:** ARCHITECTURE_REVIEW CONTRADICTION-01 resolution (Option B selected: LEFT JOIN on salon_owners)

**Description:** Add a LEFT JOIN check on `salon_owners` to the salon queries. Add `is_owner_claimed` boolean to `SalonListSchema` and `SalonDetailSchema`.

**Query change:**
```python
# In salons service/router
.outerjoin(SalonOwner, SalonOwner.salon_id == Salon.id)
.add_columns(func.count(SalonOwner.id).label('owner_count'))
# Then: is_owner_claimed = owner_count > 0
```

**Note:** This task is also required by T-011 (frontend badge display).

**Acceptance Criteria:**
- [ ] `GET /api/salons` response items include `"is_owner_claimed": true/false`
- [ ] `GET /api/salons/{id}` response includes `"is_owner_claimed": true/false`
- [ ] Claimed salons (in `salon_owners` table) return `is_owner_claimed: true`
- [ ] Unclaimed salons return `is_owner_claimed: false`

---

### T-025 — Frontend: Admin inline edit form
**Priority:** P1 | **Owner:** FE | **Estimate:** 2h | **Epic:** EPIC-08
**Dependencies:** None (admin is already authenticated)

**Reference:** `docs/03_PAGES/ADMIN.md`

**Fields editable inline:** `phone_primary`, `address_street`, `address_city`, `address_district`

**Uses existing endpoint:** `PATCH /api/admin/salons/{id}` (already exists per API_SPECIFICATION.md)

**Acceptance Criteria:**
- [ ] Admin can edit phone_primary inline and save (appears as text field on row hover/click)
- [ ] Admin can edit address_street
- [ ] Save triggers `PATCH /api/admin/salons/{id}` and shows success/error state
- [ ] Changed values are reflected immediately in the admin list without page reload
- [ ] Admin can set `is_verified = true` via a "Mark reviewed" button
- [ ] No SQL errors in `docker logs beauty_api` after save

---

### T-026 — Configure daily pg_dump backup cron
**Priority:** P0 | **Owner:** OPS | **Estimate:** 0.5h | **Epic:** EPIC-08
**Dependencies:** None

**Server:** 10.10.0.1

**Cron command:**
```bash
# Add via: crontab -e
0 3 * * * docker exec beauty_db pg_dump -U postgres lookla | gzip > /opt/backups/lookla_$(date +\%Y\%m\%d).sql.gz
0 4 * * * find /opt/backups -name "*.sql.gz" -mtime +7 -delete
```

**Acceptance Criteria:**
- [ ] `crontab -l` shows pg_dump job at 03:00 daily
- [ ] `crontab -l` shows cleanup job at 04:00 daily
- [ ] `/opt/backups/` directory exists
- [ ] Manual test: run the pg_dump command once and verify the .sql.gz is created and valid (`zcat file.sql.gz | head`)

---

## EPIC-09 — Code Quality Foundations

### T-027 — Extract useMe() hook
**Priority:** P2 | **Owner:** FE | **Estimate:** 1h | **Epic:** EPIC-09
**Dependencies:** None

**Description:** Create `frontend/hooks/useMe.ts`. Replace inline fetch in 4 pages.

**Acceptance Criteria:**
- [ ] `hooks/useMe.ts` exists with proper TypeScript typing
- [ ] 4 pages updated to import `useMe` from the hook
- [ ] No inline `/api/auth/me` fetch code remaining in page components
- [ ] `useMe()` handles not-logged-in state (returns `null` for user, not throwing)

---

### T-028 — Extract localePrefix() utility
**Priority:** P2 | **Owner:** FE | **Estimate:** 0.5h | **Epic:** EPIC-09
**Dependencies:** None

**Description:** Create `frontend/lib/locale.ts` with `localePrefix(locale: string): string` helper.

**Acceptance Criteria:**
- [ ] `lib/locale.ts` exports `localePrefix()`
- [ ] 8 components updated to use it
- [ ] No inline `locale === 'el' ? '' : '/${locale}'` patterns remaining

---

### T-029 — Add React error boundary for SalonDetailClient
**Priority:** P1 | **Owner:** FE | **Estimate:** 1h | **Epic:** EPIC-09
**Dependencies:** None

**Description:** Wrap `SalonDetailClient` in an error boundary. The fallback must show at minimum: salon name, address, and contact buttons (from SSR props already in the page).

**Acceptance Criteria:**
- [ ] If SalonDetailClient throws, page shows a degraded fallback (not a blank page)
- [ ] Fallback includes salon name and address (from SSR data)
- [ ] Fallback includes contact buttons (phone, WhatsApp, website) if `salon.phone_primary` is available
- [ ] Fallback includes a "Try reloading" link

---

### T-030 — Write unit tests for 4 critical backend functions
**Priority:** P0 | **Owner:** BE | **Estimate:** 3h | **Epic:** EPIC-09
**Dependencies:** T-001 (Alembic/pytest setup)

**Description:** Create `backend/tests/` directory and write tests for the 4 highest-risk functions.

**Test files:**
- `tests/test_is_bot.py` — ≥5 cases: known bots (Googlebot, GPTBot, AhrefsBot, curl/0, python-requests), known browsers (Chrome 124, Safari 17, Firefox 125)
- `tests/test_open_now.py` — ≥4 cases: normal weekday, weekend, DST transition (last Sunday October), midnight edge case
- `tests/test_translate_query.py` — ≥5 cases: Russian service names, Ukrainian input, mixed Greek/Russian, empty string, no synonym match
- `tests/test_auth_refresh.py` — happy path: valid token → new access token issued; error: expired refresh token → 401

**Acceptance Criteria:**
- [ ] `pytest tests/` passes with all tests green
- [ ] Each test file has ≥ test cases as specified
- [ ] DST test in `test_open_now.py` uses a fixed datetime (not `datetime.now()`) to avoid flakiness

---

### T-031 — Add try/except in translate.py for OpenAI failures
**Priority:** P1 | **Owner:** BE | **Estimate:** 0.5h | **Epic:** EPIC-09
**Dependencies:** None

**Description:** Add error handling so that if OpenAI API is unreachable, the translation call returns the original Greek text instead of raising a 500 error.

**Pattern:**
```python
try:
    result = client.chat.completions.create(...)
    return parsed_translations
except openai.APIError as e:
    logger.warning(f"OpenAI translation failed: {e}")
    return original_names  # graceful degradation
except Exception as e:
    logger.error(f"Unexpected translation error: {e}")
    return original_names
```

**Acceptance Criteria:**
- [ ] Simulated OpenAI failure (e.g., wrong API key): endpoint returns Greek names, not 500
- [ ] Error is logged (not silently swallowed)
- [ ] Subsequent requests still attempt translation (failure is not permanently cached)

---

### T-039 — Re-enable CodeQL once GitHub Code Security is available
**Priority:** P2 | **Owner:** OPS | **Estimate:** 0.5h | **Epic:** EPIC-09
**Dependencies:** None (blocked on an external/account-level condition, not code)

**Description:** `.github/workflows/codeql.yml` was disabled to `workflow_dispatch`-only
on 2026-07-11 (see `04_ARCHITECTURE/SECURITY.md` §12) because
`lookla-platform` is a private repository without GitHub Code Security,
and CodeQL's `analyze` step fails with "Code scanning is not enabled
for this repository" regardless of workflow permissions. This task is
to restore automatic scanning once that's no longer true.

**Steps:**
1. Confirm GitHub Code Security is enabled for `lookla-platform` (or the repo has become public)
2. Restore `push`/`pull_request`/`schedule` triggers in `codeql.yml` (remove the `workflow_dispatch`-only restriction and the disabled-status comment block)
3. Trigger a run and confirm both matrix jobs pass
4. Update `04_ARCHITECTURE/SECURITY.md` §12 status from Disabled to Enabled

**Acceptance Criteria:**
- [ ] GitHub Code Security enabled for the repository
- [ ] CodeQL `Analyze (javascript-typescript)` job passes
- [ ] CodeQL `Analyze (python)` job passes
- [ ] Automatic pull-request scanning restored (triggers on `push`/`pull_request` again)
- [ ] Only after this: CodeQL may be added as a required branch-protection check — it is not one today

---

### T-040 — Harden production deployment
**Priority:** P1 | **Owner:** OPS | **Estimate:** 2h | **Epic:** EPIC-09
**Dependencies:** None

**Description:** `.github/workflows/deploy.yml` was switched to
`workflow_dispatch`-only with a typed `DEPLOY` confirmation input on
2026-07-11, since a push-triggered deploy would auto-deploy production
the instant `DEPLOY_SSH_KEY` is ever added as a secret, with no
review/approval gate — and GitHub's "required reviewers" environment
protection isn't available on this private repo's current plan. The
manual-dispatch + typed-confirmation gate is a stopgap, not a
production-grade deploy. Before `DEPLOY_SSH_KEY` is actually added:

**Steps:**
1. Deploy the exact commit SHA that was reviewed/merged, not a moving `git pull origin main` (avoid deploying commits landed after the deploy was triggered)
2. Pre-deploy backup (at minimum: `pg_dump`, or confirm the existing backup cadence covers this window)
3. Post-deploy health check (e.g. `GET /api/areas` returns 200 with the expected item count) before considering the deploy successful
4. Rollback path (previous image tag or commit SHA) if the health check fails
5. Deployment log (what SHA, when, by whom/what triggered it — at minimum the GitHub Actions run itself, ideally also a persisted log)

**Acceptance Criteria:**
- [ ] Deploy step pins to `github.sha` (or an explicit input), not a floating branch pull
- [ ] Pre-deploy backup step exists or is confirmed covered elsewhere
- [ ] Automated post-deploy health check gates "success"
- [ ] Rollback procedure documented (manual is acceptable, but must exist)
- [ ] `DEPLOY_SSH_KEY` is not added as a secret until this task is done

---

### T-041 — Fix Next.js internal API rewrite loopback fallback
**Priority:** P2 | **Owner:** FE | **Estimate:** 30m | **Epic:** EPIC-09
**Dependencies:** None
**Status:** ✅ Completed (2026-07-13), merged `fix/web-api-rewrite-docker`

**Description:** `next.config.mjs`'s `/api/:path*` rewrite destination and `lib/api.ts`'s SSR fetch fallback both defaulted to `http://127.0.0.1:8001` / `http://localhost:8001` — inside the `web` container that's the container itself, not the `api` service. **Production traffic was never affected**: nginx's own `/api/` location block proxies directly to the `api` container (correctly, since nginx runs on the host) before any request reaches Next.js, and container port 3000 isn't published externally. This only broke direct-container access — e.g. testing `beauty_web` on its own port, bypassing nginx — which is how it surfaced, during T-009's final production smoke-test. Fixed as defense-in-depth (a future architecture change that removes the nginx layer, or direct-container testing/staging, would otherwise hit it) via a shared `lib/apiInternalUrl.mjs` helper defaulting to Docker service DNS (`http://api:8001/api`).

**Acceptance Criteria:**
- [x] Rewrite destination and SSR fetch base default to `http://api:8001/api`, never loopback
- [x] `API_INTERNAL_URL` override still respected
- [x] Verified both request paths return 200: `https://lookla.gr/api/...` (nginx) and `http://127.0.0.1:3000/api/...` (direct container, was 500 before)
- [x] `api`/`db`/`redis`/`crawler` containers not restarted during verification

---

## EPIC-10 — Translation QA

### T-032 — Manual Russian translation quality review
**Priority:** P1 | **Owner:** OPS | **Estimate:** 2h | **Epic:** EPIC-10
**Dependencies:** T-005, T-006

**Description:** Manual review of 20 Athens salon service names in Russian. Check for machine-literal translations.

**Process:**
1. Open 5 different salon pages in Russian locale
2. Review service name translations (check 4 services per salon = 20 total)
3. Note any awkward or machine-literal translations
4. If any are wrong: update the `CATEGORY_KEYWORDS` dict or service synonym mapping

**Acceptance Criteria:**
- [ ] 20 Russian service translations reviewed
- [ ] Any machine-literal translations corrected in the backend dictionary
- [ ] Spot-check confirms `messages/ru.json` has no missing translation keys

---

## Implementation Freeze v1.0 Additions (2026-07-09)

*Tasks added after consistency audit. Resolves C-01, M-03, M-01, m-06.*

---

### T-033 — Connect slowapi to Redis
**Priority:** P1 | **Owner:** BE | **Estimate:** 0.5h | **Epic:** EPIC-09
**Dependencies:** None

**Why (M-03):** Without Redis, rate limits reset on every `docker compose restart api`. An attacker can bypass `/api/auth/register` limit (5/min) by forcing a restart.

**Change (single line in `app/main.py`):**
```python
# Before:
limiter = Limiter(key_func=get_remote_address)

# After:
limiter = Limiter(key_func=get_remote_address, storage_uri="redis://redis:6379")
```

**Acceptance Criteria:**
- [ ] `app/main.py` `Limiter()` call includes `storage_uri="redis://redis:6379"`
- [ ] After `docker compose restart api`: rate limit counters persist (test: send 5 register requests, restart, 6th still blocked)
- [ ] `docker logs beauty_api` shows no Redis connection errors on startup

---

### T-034 — Search page analytics MVP events
**Priority:** P1 | **Owner:** FE | **Estimate:** 1h | **Epic:** EPIC-04
**Dependencies:** T-014 (GA4 script must be loaded first)

**Events to implement (MVP Critical, per SEARCH.md):**

| Event | When | Parameters |
|---|---|---|
| `search_submitted` | User submits search bar | `query`, `locale`, `source: 'header' \| 'hero'` |
| `salon_card_clicked` | User clicks any SalonCard | `salon_id`, `salon_name`, `position_in_results` |

**Implementation:** Extend `useAnalytics()` hook (T-015) with new event types.

```typescript
// hooks/useAnalytics.ts additions
const trackSearch = (query: string, locale: string, source: 'header' | 'hero') => {
  window.gtag?.('event', 'search_submitted', { query, locale, source });
};

const trackCardClick = (salon_id: number, salon_name: string, position: number) => {
  window.gtag?.('event', 'salon_card_clicked', { salon_id, salon_name, position_in_results: position });
};
```

**Not in MVP:** `filter_applied`, `map_toggled`, `results_page_loaded`, `search_empty_state` — tracked in FUTURE_FEATURES.md.

**Acceptance Criteria:**
- [ ] Submitting search fires `search_submitted` in GA4 Realtime with `query` and `locale` params
- [ ] Clicking a SalonCard fires `salon_card_clicked` with `salon_id`, `salon_name`, `position_in_results`
- [ ] `position_in_results` is 0-indexed integer (first card = 0)
- [ ] Events only fire if `lookla_consent=1` cookie is present (GA4 consent check)

---

### T-035 — Deprecate GET /api/search
**Priority:** P2 | **Owner:** BE | **Estimate:** 0.5h | **Epic:** EPIC-09
**Dependencies:** None

**Description:** Add a deprecation header to `GET /api/search` to prevent new consumers from using it. Keep the endpoint functional (backwards compat). Update `search.py` router.

```python
# In search.py router
from fastapi import Response

@router.get("/search")
def search_salons(..., response: Response):
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "2027-01-01"
    response.headers["Link"] = '</api/salons>; rel="successor-version"'
    # ... existing logic unchanged
```

**Acceptance Criteria:**
- [ ] `GET /api/search` response includes `Deprecation: true` header
- [ ] `GET /api/search` continues to return valid results (not broken)
- [ ] `search.py` router file has comment: `# DEPRECATED — use /api/salons. Remove post-M-02.`

---

### T-036 — Create public/robots.txt (standalone task)
**Priority:** P0 | **Owner:** FE | **Estimate:** 0.25h | **Epic:** EPIC-09
**Dependencies:** None

**Description:** `robots.txt` was buried in T-029 acceptance criteria. Extracted as a separate P0 task since it has no dependency on error boundaries and must be live before crawlers discover the admin panel.

**File:** `frontend/public/robots.txt`

```
User-agent: *
Disallow: /admin
Disallow: /dashboard
Disallow: /account
Disallow: /api/
Allow: /

Sitemap: https://lookla.gr/sitemap.xml
```

**Note:** `sitemap.xml` does not yet exist (post-MVP). The Sitemap directive is forward-compatible — it causes no error if the file is absent.

**Acceptance Criteria:**
- [ ] `https://lookla.gr/robots.txt` returns 200 with correct content
- [ ] `Disallow: /admin` present
- [ ] `Disallow: /api/` present
- [ ] `User-agent: *` present as first rule
- [ ] robots.txt does NOT disallow `/` or `/salons/` or `/search` (those must be crawlable)
- [ ] Remove `robots.txt` from T-029 acceptance criteria (T-029 is error boundary only)

---

## Backlog Summary

| Task | Priority | Owner | Hours | Epic | Depends on |
|---|---|---|---|---|---|
| T-001 Alembic setup | P0 | BE | 3 | EPIC-01 | — |
| T-002 address_district column | P0 | DB | 1 | EPIC-01 | T-001 |
| T-003 Backfill address_district | P0 | BE | 2 | EPIC-01 | T-002 |
| T-003a Verify GIN index | ~~P0~~ DEFERRED | DB | — | EPIC-01 | — |
| T-004 GET /api/areas endpoint | P0 | BE | 2 | EPIC-02 | T-003 |
| T-005 area param on /api/salons | P0 | BE | 1.5 | EPIC-02 | T-004 |
| T-006 Russian/Ukrainian district query aliases | P1 | BE | 1 | EPIC-02 | T-004 |
| T-038 Resolve /api/salons/map response shape drift | P0 | BE/DOCS | 0.5 | EPIC-02 | T-005 |
| T-007 SearchFilters area dropdown | P0 | FE | 2 | EPIC-02 | T-004, T-038 |
| T-008 Homepage AreaGrid | P1 | FE | 1.5 | EPIC-02 | T-004 |
| T-009 Remove booking stubs | P0 | FE | 1 | EPIC-03 | — |
| T-010 Contact CTAs | P0 | FE | 1.5 | EPIC-03 | T-009 |
| T-011 Replace ✓ badge with text | P0 | BOTH | 1.5 | EPIC-03 | T-024 |
| T-012 Google review source label | P0 | FE | 1 | EPIC-03 | — |
| T-013 Create GA4 property | P0 | OPS | 0.5 | EPIC-04 | — |
| T-014 GA4 script in layout | P0 | FE | 1 | EPIC-04 | T-013, T-018 |
| T-015 useAnalytics + contact events | P0 | FE | 2 | EPIC-04 | T-014 |
| T-016 Google Search Console | P0 | OPS | 0.5 | EPIC-04 | — |
| T-017 Privacy Policy page | P0 | FE | 1 | EPIC-05 | — |
| T-018 Cookie consent banner | P0 | FE | 1.5 | EPIC-05 | T-017 |
| T-019 GA4 privacy settings | P0 | OPS | 0.25 | EPIC-05 | T-013 |
| T-020 /about page | P1 | FE | 1 | EPIC-06 | — |
| T-021 /contact page | P1 | FE | 0.5 | EPIC-06 | — |
| T-022 Language switcher to header | P1 | FE | 1 | EPIC-07 | — |
| T-023 "How it works" step 3 copy | P2 | FE | 0.25 | EPIC-07 | — |
| T-024 is_owner_claimed in API | P0 | BE | 1 | EPIC-08 | — |
| T-025 Admin inline edit form | P1 | FE | 2 | EPIC-08 | — |
| T-026 pg_dump backup cron | P0 | OPS | 0.5 | EPIC-08 | — |
| T-027 useMe() hook | P2 | FE | 1 | EPIC-09 | — |
| T-028 localePrefix() utility | P2 | FE | 0.5 | EPIC-09 | — |
| T-029 React error boundary | P1 | FE | 1 | EPIC-09 | — |
| T-030 Unit tests for 4 functions | P0 | BE | 3 | EPIC-09 | T-001 |
| T-031 try/except in translate.py | P1 | BE | 0.5 | EPIC-09 | — |
| T-032 Russian translation QA | P1 | OPS | 2 | EPIC-10 | T-005 |
| T-033 slowapi → Redis | P1 | BE | 0.5 | EPIC-09 | — |
| T-034 Search analytics events | P1 | FE | 1 | EPIC-04 | T-014 |
| T-035 Deprecate GET /api/search | P2 | BE | 0.5 | EPIC-09 | — |
| T-036 Create public/robots.txt | P0 | FE | 0.25 | EPIC-09 | — |
| T-037 Unify salon search (post-MVP) | post-MVP | BE | 4 | EPIC-10 | T-035 |
| T-039 Re-enable CodeQL (blocked on GH Code Security) | P2 | OPS | 0.5 | EPIC-09 | — |
| T-040 Harden production deployment | P1 | OPS | 2 | EPIC-09 | — |
| **Total** | | | **~42.25h (M-01)** | | |

---

### T-037 — Unify salon search implementation *(post-MVP)*
**Priority:** post-MVP | **Owner:** BE | **Estimate:** 4h | **Epic:** EPIC-10
**Dependencies:** T-035

**Scope:**
- Select one canonical search endpoint (expected: `/api/salons` with improved FTS).
- Remove or migrate all consumers of `GET /api/search` after the deprecation window (T-035).
- Define required search behaviour for `/api/salons` (currently ILIKE).
- Benchmark: ILIKE vs `pg_trgm` vs PostgreSQL FTS.
- If FTS is selected: use a dedicated text search configuration with the `unaccent` dictionary, or a trigger-maintained `tsvector` column. Do NOT use an `IMMUTABLE` wrapper over `unaccent()`.
- Create a GIN index only for the canonical production query.
- Remove `GET /api/search` after migration window.

**Trigger conditions (when to start T-037):**
- T-035 (Deprecation header) has been live for ≥ 30 days with no consumer traffic.
- OR search latency under real traffic exceeds an agreed threshold.
- OR a third search endpoint is proposed (scope freeze signal).

---

## P0 Critical Path (minimum viable launch sequence)

```
T-001 → T-002 → T-003 → T-004 → T-005  [database + area filter BE]
                         T-004 → T-007 ✅  [area filter FE — done]
                         T-005 → T-038 ✅ → T-007 ✅  [map response shape decision — done, FE done]
T-013 → T-019             [GA4 property + settings]
T-017 → T-018 → T-014 → T-015  [legal → GA4 deploy → events]
T-016                     [Search Console]
T-009 → T-010             [booking stubs removed → contact CTAs]
T-024 → T-011             [API owner_claimed field → badge fix]
T-012                     [review labels — independent]
T-026                     [backup cron — independent]
T-030                     [critical tests — before changing those functions]
```

*T-003a removed from P0 critical path. Status: Verified — Deferred. See T-037 (post-MVP).*

**All P0 tasks complete → Pre-launch gate → Manual QA J-01/J-02/J-03 → M-01 Launch**

---

*Last updated: 2026-07-09*
