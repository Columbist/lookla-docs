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
**Status:** ✅ Completed (2026-07-14) — reviewed (2 rounds, both flagged real edge cases now fixed: website URLs with embedded credentials, phone values containing letters), merged to `main` (PR #32), production verified

**Description:** Recreated `components/ContactButtons.tsx` (T-009 had deleted the previous unreachable version) as the single source of truth for the 3 approved salon-detail contact actions, backed by pure/unit-tested normalization helpers in `lib/contactActions.ts`.

**Final decisions (this task):**
- **Viber removed.** DEC-015 defines exactly 3 approved actions (Call, WhatsApp, Website); Viber was never part of that contract. Removed the user-facing button only — no backend/DB changes.
- **Empty state implemented:** "Contact information not available" + the existing `ReportButton`, shown only when all 3 actions are unavailable.
- **Website normalization:** bare hostnames get `https://`; `http://`/`https://` preserved; `javascript:`/`data:`/`file:`/other unrecognized schemes rejected (hidden, not rendered).
- **Phone normalization:** `normalizePhoneForCall` (keeps leading `+` for `tel:`) and `normalizePhoneForWhatsApp` (digits-only for `wa.me`) — neither invents a country code for a number stored without one.
- **Desktop displays the phone number** next to "Call" (mobile stays label-only, avoiding overflow on 375px).

**CTA specifications (implemented):**
```tsx
// Call salon — tel: with normalized digits, leading + preserved if present
<a href={`tel:${normalizePhoneForCall(phone)}`}>Call</a>

// WhatsApp — digits-only, no invented country code
<a href={`https://wa.me/${normalizePhoneForWhatsApp(phone)}`} target="_blank" rel="noopener noreferrer">WhatsApp</a>

// Website — https:// added to bare hostnames, unsafe schemes rejected
<a href={normalizeWebsiteUrl(website)} target="_blank" rel="noopener noreferrer">Website</a>
```

**Important:** All 3 CTAs work WITHOUT being logged in (DEC-016). No authentication check before displaying or enabling these buttons.

**Acceptance Criteria:**
- [x] "Call" button: on mobile, tapping initiates a phone call; on desktop, shows the phone number
- [x] "WhatsApp" button: opens `https://wa.me/{digits}` in a new tab
- [x] "Website": opens salon website in a new tab with `rel="noopener noreferrer"`
- [x] All 3 actions render while logged out (no auth dependency in `ContactButtons.tsx`)
- [x] If phone is null/unusable: Call and WhatsApp are hidden (not shown with a null/empty href)
- [x] If website is null/unsafe: Website action is hidden
- [x] Zero valid actions → empty state, not an empty container

**Note:** production data has 0/6320 salons with a `website` value, so the "phone + website" and "website only" combinations couldn't be verified against real data — verified instead via a local mock API proxy exercising the real SSR pipeline (not client-side route mocking, which doesn't intercept server-side fetches), plus full unit-test coverage of the same resolution logic the component uses.

---

### T-011 — Replace ✓ badge with text label (DEC-014)
**Priority:** P0 | **Owner:** FE | **Estimate:** 1.5h | **Epic:** EPIC-03
**Dependencies:** T-024 (backend `is_owner_claimed` field — done, merged). ARCHITECTURE_REVIEW CONTRADICTION-01 resolved alongside T-024.
**Status:** ✅ Completed (2026-07-15) — reviewed, merged to `main` (PR #35), production deployed and verified

**Description:** Replace the ✓ icon with text label. Two labels depending on source:
- `is_verified = true` AND `is_owner_claimed = true` → "Owner verified" text
- `is_verified = true` AND `is_owner_claimed = false` → "Information reviewed" text
- `is_verified = false` → no label

**Backend support — done by T-024, purely a frontend task from here:**

`GET /api/salons/{id_or_slug}` and `GET /api/salons` (list items) already include:
```json
{
  "is_verified": true,
  "is_owner_claimed": false
}
```

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
- [x] No ✓ checkmark icon visible on any verified salon
- [x] Text "Information reviewed" appears on admin-verified salons (no salon_owners row)
- [x] Text "Owner verified" appears on claimed salons (salon_owners row exists)
- [x] Unverified salons show no badge/label
- [x] Label appears on both `SalonCard` (search results) and `SalonDetailClient`
- [x] `GET /api/salons` response includes `is_owner_claimed` boolean field (done in T-024)

**Implementation notes:**
- Single pure helper `lib/verificationLabel.ts` used by both `SalonCard` and `SalonDetailClient` so the two call sites can never disagree on label choice. `is_owner_claimed` is the sole input; `is_verified` continues to gate whether any label renders at all (unchanged from prior behavior).
- Production has 0 verified salons and 0 owner claims as of this writing, so both positive label states were verified via a local mock API proxy exercising the real SSR pipeline (same technique as T-010), not against live data. The default "no label" state — what's actually live today — was verified directly against production.
- Found and fixed a real mobile viewport-overflow regression during manual verification: the new text labels are longer than the old "✓ Verified", causing horizontal overflow at 390px on the salon detail page. Fixed with `flex-wrap` on the header row; `SalonCard`'s badge got defensive `max-w-[85%] truncate` for the same reason.
- `salon.verified` i18n key removed from all 4 locale files (superseded by `infoReviewed`/`ownerVerified`); unrelated `account.verified`/`dashboard.verified` keys left untouched.

---

### T-012 — Add Google review source label (DEC-013)
**Priority:** P0 | **Owner:** FE | **Estimate:** 1h | **Epic:** EPIC-03
**Dependencies:** None
**Status:** ✅ Completed (2026-07-14) — reviewed, merged to `main` (PR #33), production verified

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
- [x] Header text visible on any salon with reviews, without scrolling to reviews (it's a section header)
- [x] Header is visible in all 4 locales
- [x] Text matches exactly: "Source: Google Reviews / Imported: Yes / Original: No" (en)
- [x] Label appears regardless of whether `source='google'` check — all MVP reviews are Google anyway (label is section-level, does not inspect per-review `source`)

**Tested rendering semantics:** section-level disclosure via `shouldShowReviewSourceLabel(loading, reviewCount)` — visible once loaded with ≥1 review, hidden while loading, hidden at 0 reviews (covers both a genuinely-empty result and a failed fetch, since the existing lazy-load hook collapses both to an empty array with no separate error flag — preserved as-is, not modified). Verified manually that a real salon's 5 actual reviews were reachable only with a real browser User-Agent — the reviews endpoint's bot protection (`is_bot()` in `translate.py`) flags `curl`, Python's `urllib`, and Playwright's default `HeadlessChrome`/`Playwright` UA strings as bots and returns `[]`; testing required overriding Playwright's context `user_agent` to a real Chrome UA.

---

## EPIC-04 — Analytics Integration

### T-013 — Create GA4 property and obtain tracking ID
**Priority:** P0 | **Owner:** OPS | **Estimate:** 0.5h (revised: needs a human with Google Analytics admin access — see below) | **Epic:** EPIC-04
**Dependencies:** None (operations task, not code)
**Status:** ✅ Completed (2026-07-21) — real GA4 property and web stream created by the user (coding agent has no Google account access, so this was always a human console task — see below), all privacy-relevant settings configured and confirmed. Original steps below were a stub that assumed API-key-style access. Correction to the original spec: it also skipped GA4's privacy-relevant settings (Enhanced Measurement, Google Signals, Ads Personalization, data retention, internal-traffic handling) entirely — those are captured below because Stage 2 activation should not silently inherit GA4's defaults (Google Signals and Ads Personalization default to a state that is not privacy-minimal).

**Actual configuration, as executed:**
- **Ownership:** new, dedicated Google account created specifically for this property (not reused from an existing account with other projects' data) — clean separation, no legacy account-level Data Sharing Settings inherited.
- **Property + stream:** created; real Measurement ID obtained. Per this checklist's own rule, the ID is **not** written into this file or any other repo/public-docs file — held only for direct entry into production `.env` at Stage 2 activation.
- **Enhanced Measurement** ("Улучшенная статистика" in the Russian console UI — same feature, different localized label than expected): confirmed disabled, verified by the user re-checking the toggle's actual position after an initial mix-up.
- **Google Signals** ("Сигналы Google"): confirmed disabled, same re-verification.
- **Data Sharing Settings:** all unchecked at account-creation time (new account, so nothing to inherit from unrelated prior projects).
- **No Google Ads link, no Search Console link, no BigQuery export, no advertising audiences** — none configured during setup.
- **Data retention:** event data and user data both aligned to **2 months** (the shortest GA4 offers), reset-on-new-activity **disabled**.
- **Internal/developer traffic filter:** not configured — no stable IP available for a reliable rule. Documented here as an accepted limitation, not an oversight.

**Correct sequencing (per architect review, supersedes the original T-013→T-015 order in earlier planning docs):** T-013 (this ticket) → **T-014 Stage 2 activation** (separate explicit approval, not part of this ticket) → T-015 (product events). T-014 Stage 1 (dormant infrastructure) already shipped and is verified in production — see T-014 above.

**Manual setup checklist (to be executed by a human with Google Analytics access):**

1. **Access and ownership** — decide which Google account/organisation will own the property; record administrators, recovery access, and whether ownership is personal or should move to a future Lookla legal entity. Do not put account emails in public docs.
2. **Create the property** — name `Lookla`, timezone `Greece`, currency `EUR`, closest accurate beauty/local-services industry category. Record property name, numeric property ID, creation date, timezone, currency. (The numeric property ID is not the Measurement ID.)
3. **Create the production web stream** — name `Lookla Production`, URL `https://lookla.gr`, exactly one stream. Record stream name, stream ID, and the Measurement ID (`G-XXXXXXXXXX`). Do not commit the Measurement ID to Git or public docs — store it only in the production `.env` (see wiring below).
4. **Enhanced Measurement** — recommended: disable entirely. T-014 already sends `page_view` explicitly with `send_page_view: false`; any Enhanced Measurement page-view/history tracking left on would double-count. If any sub-feature (site search, form interactions, video, downloads, outbound clicks, scroll) is left on, document why and prove it doesn't duplicate T-014/T-015 events or transmit unreviewed free-text data (GA4's built-in site-search tracking can capture raw query strings).
5. **Privacy-safe configuration** — verify and record: Google Signals disabled, Ads Personalization disabled, user-provided data collection disabled, data-sharing settings minimized, no Google Ads link, no Search Console link (unless separately approved), BigQuery export disabled (unless separately approved), no advertising audiences, cross-domain measurement disabled, internal-traffic filter decision documented.
6. **Data retention — decided: 2 months, for both event data and user data, reset-on-new-activity disabled.** The "14 months" previously written into `MILESTONE_M01.md` and `RELEASE_CHECKLIST.md` was a prior planning-stage assumption, not a confirmed setting — corrected in both files in this same change to match the actual decision. The Stage 2 Privacy Policy and Cookie Policy drafts (§10 below) must state 2 months, not 14, whenever they're written.
7. **Internal/developer traffic** — decide: stable-IP-based internal traffic definition (only if IPs are genuinely stable), a documented dev/test filtering mechanism, or explicitly leave unfiltered and document the limitation. Test any filter before setting it to "Active" (GA4 filters are not reversible after data is dropped).
8. **DebugView validation plan** — prepare a *temporary, controlled* validation method for Stage 2 (a separately built temporary image, or an explicit short activation window) to confirm: one initial `page_view`, one event per SPA navigation, no event before consent, no duplicates, withdrawal stops measurement, regrant resumes it, no private query parameters leak into event params, advertising consent stays denied. Do not leave GA4 DebugView/debug mode enabled for ordinary production visitors.
9. **Secret/build wiring (already confirmed from the live host, no admin access needed for this part):** production `.env` (`/root/beauty-gr/.env` on the deploy host, gitignored, not in this diff) currently has **no** `NEXT_PUBLIC_GA4_ID` or `NEXT_PUBLIC_ANALYTICS_CONSENT_ENABLED` line at all. `docker-compose.yml`'s `web.build.args` (added in T-014) already reads both as `${NEXT_PUBLIC_GA4_ID:-}` / `${NEXT_PUBLIC_ANALYTICS_CONSENT_ENABLED:-}` — no docker-compose.yml changes needed at Stage 2. Activation is: add both lines to that `.env` file, then rebuild `beauty_web` (they are build-time-inlined values — a running container will not pick them up without a rebuild, per T-014's architecture). No fallback/default ID exists anywhere in source.
10. **Stage 2 policy changes (draft only, do not deploy under this ticket)** — Cookie Policy needs to describe GA4 as optional/consent-gated, name Google as provider, state purpose, list the actual observed `_ga`/`_ga_*` cookies and measured lifetimes, describe consent/withdrawal, note international transfers, and state that prior transmissions can't be retracted by later withdrawal. Privacy Policy needs an analytics data-category section, purpose, legal basis (consent), Google as recipient, transfer safeguards, the retention setting from step 6, withdrawal rights, and a statement that no tracking happens before consent. Do not state GA4 is active anywhere while Stage 2 remains disabled.

**Acceptance Criteria:**
- [x] Real GA4 property + production web stream exist (not placeholder `G-XXXXXXXXXX`)
- [x] Enhanced Measurement configuration reviewed and documented — disabled, confirmed via re-check
- [x] Google Signals, Ads Personalization, data-sharing, BigQuery, Search Console, Google Ads link all reviewed and recorded — none enabled/linked
- [x] Data retention period chosen and recorded — 2 months (event + user data), reset disabled
- [x] Internal/developer traffic decision recorded — not configured, no stable IP, documented as an accepted limitation
- [x] Measurement ID stored only in the production `.env`, never committed to Git or public docs — not written anywhere in this repo; will be added directly to `.env` at Stage 2 activation
- [ ] **Not yet done:** Stage 2 Privacy/Cookie Policy changes drafted (not deployed) — needed before Stage 2 goes live, not before T-013 closes
- [ ] **Not yet done:** DebugView validation plan finalized for the Stage 2 activation window

**Explicitly out of scope for this ticket:** any application code change, backend/database change, rebuilding or redeploying `beauty_web`, enabling GA4 for real visitors, committing a Measurement ID, T-014 Stage 2 activation itself, T-015 product events.

---

### T-014 — GA4 infrastructure: physically cannot send a request before consent
**Priority:** P0 | **Owner:** FE | **Estimate:** 1h (revised: ~4h — see correction below) | **Epic:** EPIC-04
**Dependencies:** T-013, T-018 ✅ Completed
**Status:** ✅ Completed (2026-07-20) — reviewed, merged to `main` (PR #39), production deployed and verified. Stage 1 (dormant) only — see production verification note below. Page_view infrastructure only, per architect scoping. Product events (contact_action, search, salon_open, etc.) are explicitly out of scope — see T-015.

**Production verification (2026-07-20):** `beauty_web` rebuilt and redeployed alone (`docker compose build web` + `docker compose up -d --no-deps web`; API/DB/Redis/crawler/crawler_worker uptimes unchanged, confirmed untouched). Verified against the live site (`https://lookla.gr`) across 6 representative pages (`/`, `/en`, `/search`, `/en/search`, `/privacy`, `/cookies`): zero requests to `googletagmanager.com`/`google-analytics.com`, no `<script src=googletagmanager.com>`, no `window.gtag`, no `window.dataLayer`, no `_ga*` cookies, `lookla_consent` not auto-created (only `NEXT_LOCALE` present), no consent banner rendered anywhere (confirmed via direct DOM element search, not just text matching — the Cookie Policy page's own prose describing the banner mechanism produced one false positive in a naive text-based check, resolved by confirming no actual banner DOM node exists), exactly one `<footer>` per page with intact Privacy/Cookie Policy links, zero console errors. Production has no `NEXT_PUBLIC_GA4_ID` set (T-013 not done), so the entire pipeline ships completely inert, exactly as designed — this is Stage 1 of a two-stage rollout; Stage 2 (setting a real Measurement ID and enabling the consent feature flag) requires separate explicit approval and has not been done.

**Unrelated infrastructure observation, disclosed for transparency (consistent with the T-018 finding):** this task's `docker compose build web` on the production host ran far slower than local builds — `npm ci` alone took ~5 minutes, and `vmstat` during the build showed active swap thrashing (`si`/`so` in the thousands) with load average peaking around 8.5 on a 1.9GiB host. The build completed successfully with no OOM kill, but this is further evidence supporting the standing host-memory-pressure risk flagged in T-018, worth investigating in the planned T-051.

**Correction to the original spec below (rewritten before implementation, per architect review):** the original spec's own sample code loaded `gtag.js` unconditionally with `strategy="afterInteractive"`, contradicting its own acceptance criterion that the script "does NOT appear if `lookla_consent=0`" — `afterInteractive` fires regardless of consent state; there was no mechanism in the sample that could have honored it. The corrected goal, as re-scoped: build infrastructure that is **physically incapable** of sending any request to Google until consent is granted, not "load unconditionally and hope something suppresses it." Google's official Consent Mode v2 pattern (declare a `consent: default` denied state, then `consent: update` once granted) was deliberately **not** used — that pattern exists for sites that load `gtag.js` unconditionally and need the library itself to suppress network activity pre-consent. Here, the `<script>` tag is never rendered into the DOM until consent is granted, so there is nothing running that needs a declared default; the absence of the script *is* the denial. `gtag('consent', 'update', ...)` is used only for revoke/resume after the script has already loaded once. The original 1h estimate assumed only a layout edit; the actual scope also required building `NEXT_PUBLIC_*` build-time env wiring (Dockerfile `ARG`/`ENV` + `docker-compose.yml` `build.args`) that did not exist anywhere in the repo for any `NEXT_PUBLIC_*` variable before this task.

**Architecture:**
- `frontend/lib/analytics.ts` — `initGtagIfNeeded()` (idempotent, guarded by a module-level flag), `sendPageView()`, `updateAnalyticsConsent()`, `deleteGa4Cookies()`, `isGa4Configured()`. `send_page_view: false` at config time — GA4's automatic pageview measurement does not see Next.js App Router client-side navigations, so every `page_view` (initial and subsequent) is sent explicitly.
- `frontend/components/GoogleAnalytics.tsx` — client component, renders `null` unless `isGa4Configured() && isAnalyticsConsentFeatureEnabled()` and consent is granted. `shouldLoadScript` state only ever transitions false→true (never reset), so the `<script>` mounts exactly once per page lifecycle regardless of how many times consent is revoked/re-granted. The first `page_view` fires from the `<Script onLoad>` callback itself (guaranteed post-load), not a separate `useEffect` that could race ahead of script load and silently no-op. A `usePathname()`/`useSearchParams()` effect handles subsequent SPA navigations, guarded against double-firing via a `lastTrackedPath` ref. Wrapped in `<Suspense>` in `layout.tsx` (required for `useSearchParams()` in the App Router).
- Revoke calls `updateAnalyticsConsent(false)` + `deleteGa4Cookies()` (best-effort `_ga`/`_ga_*` deletion on the current host and, where applicable, the registrable parent domain — `gtag('consent','update',...)` stops future writes but does not clear existing cookies). Re-grant calls `updateAnalyticsConsent(true)` only — does not reload the script or resend the initial `page_view`.
- **New infrastructure:** `Dockerfile` `ARG`/`ENV` for `NEXT_PUBLIC_GA4_ID` and `NEXT_PUBLIC_ANALYTICS_CONSENT_ENABLED` (defaulting to `""`, safe/inert if unset), `docker-compose.yml`'s `web.build` changed from shorthand `./frontend` to an explicit `context`/`args` block. `NEXT_PUBLIC_*` vars are inlined at Next.js **build time** (webpack `DefinePlugin`), not read at container-start — a `docker-compose.yml` `environment:` entry has zero effect on them, which is why `NEXT_PUBLIC_API_URL` (pre-existing in `environment:`) turned out to be dead/unused config. This change also retroactively completes T-018's `NEXT_PUBLIC_ANALYTICS_CONSENT_ENABLED` wiring gap — that flag previously had no way to be enabled in a real deploy.

**Explicitly out of scope (per architect instruction) — see T-015:** `contact_click`, `search`, `salon_open`, `map_click`, `whatsapp_click`, `phone_click`, `owner_claim`, `booking`, and all other custom/product events. Enforced by a regression test asserting only `analytics.ts`/`GoogleAnalytics.tsx` reference `window.gtag`/`window.dataLayer` anywhere in the codebase.

**Out-of-scope finding, disclosed for transparency:** `SECURITY.md` flags a Content-Security-Policy as "required when adding GA4." No CSP exists anywhere in the stack (nginx, Next.js, or backend) today. Treated as a separate hardening task, not silently folded into this one's scope.

**Safe-by-construction regardless of T-013 status:** the real production `.env` has no `NEXT_PUBLIC_GA4_ID` set (T-013 not done yet). `isGa4Configured()` returns `false` and `GoogleAnalytics` renders `null` whenever the ID is absent, so this ships completely inert in production today — merge/deploy is safe independent of T-013's timeline.

**Verification:** 275/275 unit/source-pattern tests passing (hybrid direct-function + regex-on-source pattern, matching this codebase's established test infra — no jsdom/RTL). Isolated Playwright run (temporary build, placeholder `NEXT_PUBLIC_GA4_ID`, `NEXT_PUBLIC_ANALYTICS_CONSENT_ENABLED=true`, never deployed) against the exact behavioral contract: 19/19 checks passed — zero requests to `googletagmanager.com`/`google-analytics.com`, no `window.gtag`, no `window.dataLayer`, no `_ga*` cookies before consent; exactly one script tag + one `config()` call + one `page_view` after Accept; SPA navigation via real `<Link>` clicks (not `page.goto` reloads) sends exactly one additional `page_view` per navigation with no re-init; Reject issues `consent update(denied)`, deletes `_ga*` cookies, sends no further `page_view`s, leaves the script tag mounted; re-grant issues `consent update(granted)` only, with no duplicate script load, no duplicate `config()` call, and no duplicate `page_view`.

**Acceptance Criteria:**
- [x] No `<script src="googletagmanager.com/...">`, no `window.gtag`, no `window.dataLayer`, no `_ga*` cookies, and zero network requests to Google while consent is absent or rejected
- [x] After Accept: exactly one `gtag.js` load, GA4 initialized, exactly one `page_view` for the current page, then correct SPA-navigation tracking (one `page_view` per client-side route change, no re-init)
- [x] After Reject/Withdraw: no further events sent, consent set to `denied`, `_ga*` cookies deleted where possible
- [x] Re-consent resumes tracking without double-initializing (no duplicate script, no duplicate `page_view`)
- [x] `NEXT_PUBLIC_GA4_ID` is read from env, wired through Docker build-args (not hardcoded, not silently dead like the pre-existing `NEXT_PUBLIC_API_URL`)
- [x] No T-015-scoped product event exists anywhere in this task's files

---

### T-014 Stage 2 — real GA4 property activation
**Status:** ✅ Completed (2026-07-23) — `NEXT_PUBLIC_GA4_ID=G-HVQBFF0DNB` and `NEXT_PUBLIC_ANALYTICS_CONSENT_ENABLED=true` set in production `.env`, `beauty_web` rebuilt/redeployed alone three times across this activation (once per fix below), 24/24 production DebugView-equivalent checks passing (Playwright against `https://lookla.gr`, fresh browser contexts per scenario: Before/Reject/Accept-from-clean/Reload-with-existing-consent/Withdraw-on-apex-domain/Regrant), Cookie Policy updated with real measured attributes (PR #47). API/DB/Redis/crawler/crawler_worker untouched throughout (only `web` rebuilt each time).

**Three production-only defects found and fixed during activation** (none reproducible from source review or unit tests alone — all three only manifested against the real `gtag.js` library / real cookie-scoping behavior):

1. **Root cause of "GA4 script loads but never collects data" (PR #45):** `initGtagIfNeeded()`'s `gtag` stub built its queued dataLayer entry via a rest parameter (`function gtag(...args) { dataLayer.push(args) }`), which produces a real JS `Array`. `gtag.js` silently drops any dataLayer entry that is a real `Array` instead of an `Arguments` object — no error, no warning; the script still loads, `config`/`event` calls still land in `dataLayer` in the correct order, but `collect()` never fires and `_ga`/`_ga_<container-id>` cookies never get set. Root-caused via Playwright bisection on an isolated static HTML page with zero Next.js/React involved, changing one variable at a time until only `arguments` vs. `[...args]` remained as the differentiator. Fix: `function gtag() { dataLayer.push(arguments) }`.
2. **Duplicate initial `page_view` for a visitor whose consent was already granted at mount time** (PR #46): `activeRef.current` becomes `true` synchronously in the first `useEffect` when consent is pre-existing, and the route-change effect (deps `[pathname, searchParams]`) always runs once on mount regardless of whether its deps actually changed — so it and the `<Script onLoad>` callback both send `page_view` for the same initial path. Fixed by also checking `path === lastTrackedPath.current` inside `handleScriptLoad`, making the two mutually exclusive regardless of which runs first.
3. **`deleteGa4Cookies()` silently no-op on the apex domain** (PR #46): GA4 always writes `_ga`/`_ga_<id>` with `Domain=.lookla.gr` (leading dot), including when the current host *is* the apex domain (2 label parts) — not only on subdomains. The delete function only added a `Domain=` attribute to its clearing call when `parts.length > 2`, so on `lookla.gr` itself the deletion attempt never matched the cookie's actual scope. Fixed by changing the guard to `parts.length >= 2`.

**Real measured cookie attributes** (production verification, 2026-07-23): `_ga` and `_ga_HVQBFF0DNB`, both `Domain=.lookla.gr`, `Path=/`, `SameSite=Lax`, effective lifetime ~400 days (Chrome's own documented cap overriding the configured `cookie_expires: 63072000` / 2-year value — consistent with Chrome's publicly documented ~400-day maximum). `Secure` observed `false` in this testing environment but deliberately **not** committed to in the Cookie Policy as a fixed fact, since it is browser/environment-dependent rather than a Lookla-configured attribute. Cookie Policy (PR #47, all 4 locales) updated to state the ~400-day effective lifetime, `Domain=.lookla.gr`, and `SameSite=Lax` as facts observed during this production verification, while still explicitly hedging `Secure` as subject to change.

**24/24 production checks (2026-07-23):** Before choice (no script/dataLayer/collect/cookies) — 4/4. Reject (consent=0, no Google traffic after reload, no cookies, site functional) — 4/4. Accept from clean state (one script, one config, one initial `page_view`, both cookies created, SPA nav sends exactly one additional `page_view` — GA4 batches non-initial hits ~5-6s, verified 5/5 stable on repeat runs) — 6/6. Reload with already-granted consent (one script, one config, exactly one initial `page_view` — the PR #46 regression check) — 3/3. Withdraw on apex domain (both `_ga*` cookies fully removed, no new collect requests, necessary cookies preserved — the other PR #46 regression check) — 5/5. Regrant (no second script, tracking resumes) — 2/2. Final smoke against the PR #47-updated build: no console/hydration errors, no horizontal overflow, Before/Accept/Withdraw all correct — 9/9 (overlaps with above, counted once).

---

### T-015 — Consent-gated GA4 product events
**Priority:** P0 | **Owner:** FE | **Estimate:** 2h (revised — actual scope was a closed 5-event catalogue with a full PII-guard design, not a single hook) | **Epic:** EPIC-04
**Dependencies:** T-013 ✅, T-014 Stage 1 + Stage 2 ✅, T-018 ✅
**Status:** ✅ Completed (2026-07-23) — reviewed, merged to `main` (PR #48), `beauty_web` rebuilt/redeployed alone (API/DB/Redis/crawler/crawler_worker untouched), full production verification passing against `https://lookla.gr`.

**Correction to the original spec above (superseded before implementation, per architect review):** the original design's own sample code sent `salon_name` as a GA4 event parameter — personally/commercially identifying data that has no business leaving the browser in an analytics payload, and inconsistent with T-014/T-018's whole consent-gating design intent. The original also scoped only `contact_action` via a single `useAnalytics()` hook. The corrected, actually-implemented scope: a closed 5-event catalogue (`salon_open`, `contact_action`, `search_results_view`, `area_select`, `language_change`) behind one central `trackEvent()` function in `frontend/lib/analytics.ts` (T-014's existing transport module, not a new hook), with a two-layer PII guard (per-event parameter allowlist + a universal denylist) enforced inside `trackEvent` itself — not left to each call site to self-police.

**Full specification:** see `docs/06_ENGINEERING/ANALYTICS_EVENTS.md` — event table, exact parameter contracts, PII guard design, duplicate-prevention strategy per event, cardinality notes, and the GA4 Admin custom-dimension/key-event checklist (deliberately deferred, manual, not automated by this change).

**Architecture summary:**
- `trackEvent()` (`lib/analytics.ts`): TypeScript function overloads restrict callers to the 5 approved name/parameter-shape combinations at compile time; at runtime, an explicit `ANALYTICS_EVENT_NAMES` allowlist, per-event parameter schemas (numeric-id / canonical-slug / closed-enum validators), and a `DENIED_PARAM_KEYS` denylist plus a universal `isSafeGenericValue()` check (no whitespace/`@`/URL-scheme, bounded length) gate every call. No-ops unless `window.gtag` already exists (T-014 already initialized it — `trackEvent` never triggers initialization itself) and `getAnalyticsConsent()` reads `'granted'` live from the cookie at call time. Never queues a dropped call for later replay. Never throws.
- `salon_id` is always `String(salon.id)` — the numeric DB primary key — never `salon.slug`, which was found during implementation to typically embed the salon's business name (e.g. `harris-anagnostopoulos-12608`), which would have made it personally identifying.
- Component wiring: `SalonCard.tsx` (salon_open: search_list/homepage/masters), `MapView.tsx` (salon_open: search_map, from the marker preview's "view" link only — the preview's own phone quick-dial button is deliberately not instrumented, out of `contact_action`'s `page: 'salon_detail'`-only contract), `ContactButtons.tsx` (contact_action, 3 independent flat buttons, T-010's exact 3-action contract untouched, no Viber), `search/page.tsx` (search_results_view via a ref-based normalized-state-key dedup, not time-based debounce; area_select for the search filter, guarded against reselecting the already-active area), `AreaGrid.tsx` (area_select: homepage_grid), `LanguageSwitcher.tsx` (language_change, now takes an explicit `surface: 'header'|'footer'` prop since both `Header.tsx` and `Footer.tsx` render it, guarded against firing on a same-locale reselect).

**Verification:** 353/353 frontend tests passing (68 new for T-015, including a mocked-transport suite proving exact `trackEvent` payloads without any live GA4 property — consent gating, denied-key/nested-object/overlong-value/invalid-enum rejection, no-replay-after-regrant, and PII-shape denylist checks all run against a hand-rolled `window.gtag` mock, not a live network call). `npm run lint` and `npm run build` both clean, no new warnings. Explicit T-014 non-regression tests confirm the Stage 2 fixes (dataLayer `arguments` object, apex-domain cookie deletion, duplicate-initial-page_view guard) are untouched by this change.

**Production verification (2026-07-23):** Playwright against the live site (`https://lookla.gr`), fresh browser contexts per scenario, a real test salon (id 13671) and canonical area (`athens-center`). 19/19 before/salon_open/contact_action/search_results_view/area_select/language_change checks + 8/8 withdraw/regrant checks, all passing. Confirmed real payloads for all 5 events contain exactly their approved parameters and nothing else — e.g. `contact_action` → `{salon_id, channel, page, locale}` only, no phone number/WhatsApp URL/destination hostname; `salon_open` → `{salon_id, source, locale}` only. Withdraw removes `_ga*` and stops all further page_view/product events immediately; regrant resumes tracking with exactly one page_view (no duplicate) and no replay of anything from the withdrawn window.

**Verification-process finding, disclosed for future reference:** GA4 batches multiple hits fired close together (e.g. a click-triggered product event immediately followed by the new page's `page_view`) into a single POST request whose body is several newline-separated `en=<name>&...` fragments, rather than each hit being its own separate GET-style request with `en=` in the URL query string. An initial verification pass mis-read this as `salon_open`/`area_select` failing to fire, because it only inspected each request's URL query string. Corrected by parsing both the URL and, when present, each line of the POST body for event names/params. **This is a real trap for any future production analytics verification on this site — always check the POST body of batched `g/collect` requests, not just the URL.**

**Acceptance criteria:**
- [x] Only the 5 approved events are callable — enforced by both TypeScript overloads and a runtime allowlist
- [x] No event fires before consent, during rejection, or after withdrawal; no replay on regrant
- [x] No PII (name/email/phone/address/message/token/GPS/URL/etc.) reaches any event, enforced by a schema allowlist + universal denylist inside `trackEvent` itself, not by caller discipline
- [x] No duplicate firing — verified structurally (single click-owner per surface) plus, for `search_results_view`, a ref-based dedup key
- [x] T-010's ContactButtons contract (exactly phone/WhatsApp/website, no Viber) untouched
- [x] `trackEvent` never triggers GA initialization and never throws into the UI
- [x] Production DebugView-equivalent verification (real payloads, real consent states, real withdraw/regrant) — 27/27 checks passing
- [x] Independent review — approved (PR #48)

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
**Status:** ✅ Completed (2026-07-17) — reviewed across 3 rounds, merged to `main` (PR #37), production deployed and verified

**Description:** Create `app/[locale]/privacy/page.tsx` with Privacy Policy content.

**Correction to the original spec below (found during the mandatory pre-write audit):** this task was originally written assuming GA4 already exists and should be named in the policy. It does not — GA4 is T-013/T-014/T-015, which come *after* this task in the actual sequencing. The shipped policy explicitly states GA4, reCAPTCHA/Turnstile, Sentry, and OpenAI content moderation are **not** currently active, rather than asserting a service that doesn't exist. The "14 months for GA4" retention line was speculative and has been dropped — no GA4 exists to have a retention period.

**Pre-write audit (mandatory phase before any document text was written):** a full data-processing inventory was performed across the backend (every router, every SQLAlchemy model, raw-SQL-only tables with no ORM model), the frontend (storage, cookies, third-party scripts), and infrastructure (nginx, Docker, Cloudflare, backups, monitoring, CI), with every claim traced to a file:line or a live command-output check. Full findings: `docs/.reviews/T-017.diff` and the PR description. Headline discrepancies found and corrected rather than inherited into the policy:
- `SECURITY.md`'s own Personal Data Inventory table listed "GA4 session data" as a present-tense collected data type — GA4 does not exist in any frontend code.
- `SECURITY.md` claims "No location tracking (no GPS)" — false as written; the browser Geolocation API is used for the map's "near me" view. Coordinates are confirmed to never reach Lookla's backend or any third party (no `lat`/`lng` param on any salons query), so the policy states that narrower, accurate fact instead of either the false denial or an overstated claim.
- `DATA_FLOW.md` and `DATABASE_SCHEMA.md` both label `Conversation`/`Message` as `[Future]`/`not user-facing` — **incorrect**. `/account/messages` is a live page calling `/api/chat/conversations` and `/api/chat/.../messages`; message bodies, and for availability requests, client name/phone (submittable by anonymous visitors, not only logged-in users) are real, live data collection today. This is the single most significant correction from this audit.
- `SECURITY.md` claims 90-day nginx log retention; the live `logrotate.d/nginx` config is 14 days.
- Database backups are local-only today (`rclone` not installed) despite roadmap docs describing an active Backblaze B2 offsite copy.
- `OpenAI` content-moderation functions (`check_text`/`check_image`) exist in code but have zero call sites — not an active data flow.
- The exact OpenAI translation payload was verified: only the raw review/service text string and a target-language name — no reviewer name, rating, salon ID, or user identifier.

**Explicit non-goals for this task (per instruction), not built here:** Cookie Policy, cookie-consent banner, Terms of Service, GA4 Consent Mode, GA4 itself. Section 4 of the shipped policy (Cookies) discloses the four cookies that already exist today (`access_token`, `refresh_token`, `oauth_csrf`, `NEXT_LOCALE`) and explicitly defers the full Cookie Policy/consent banner to T-018/T-014.

**Undefined business/legal points** were initially marked `TODO (requires business/legal decision)` in the shipped text rather than invented — no fabricated GDPR legal basis, retention period, DPO, or processor agreement.

**Round 2 (2026-07-16, architect review):** all initial `TODO` markers were resolved via explicit approved MVP decisions, applied verbatim where exact wording was specified:
- **Controller identity** — Lookla is not operated by a company; the controller is disclosed as a natural person (Zhuykov Andrey, based in Greece), with no invented company name, VAT, or postal address, and a change-of-controller clause for if Lookla is later incorporated.
- **Lawful-basis matrix** — a new dedicated section maps each processing purpose to a specific GDPR basis (contract performance, legitimate interest, legal obligation), with the right to object to legitimate-interest processing disclosed. Contract-performance bases depend on a Terms of Service that doesn't exist yet — see T-045.
- **Retention matrix** — every data type now has an explicit target (14 days logs, 7 days local backups, 12 months messages/appointments/reports/claims, 30 days post-deletion-request), each honestly marked as manually-enforced today where no automated cleanup job exists — see T-047, T-048.
- **Full data-subject rights** (access, rectification, erasure, restriction, portability, objection, consent withdrawal, rights re: automated decisions, complaint to the Hellenic DPA, judicial remedy), the approved one-month response-timing statement, and the approved identity-verification statement.
- **Age policy** — 18+ for account features, catalog remains browsable by anyone; does not claim age verification exists yet — see T-044.
- **International transfers** — provider-specific safeguards (OpenAI Ireland, EU SCCs, EU–US DPF "where applicable"), replacing the generic TODO; Google is described as an independent authentication provider, not labeled as Lookla's processor without contractual evidence.
- **Remaining factual corrections applied**: Cloudflare's "all traffic passes through" claim replaced with an accurate one acknowledging the origin is also directly reachable (see T-049); token storage clarified as raw, not "or its hash"; exact cookie lifetimes stated (15 min / 30 days / 10 min); availability-requests/appointments disclosed as a backend capability not currently reachable through the production frontend; GPS vs. map-tile-area distinction sharpened; inactive-SDK (Sentry/moderation) discussion trimmed from the public-facing text; Resend fallback recipient-email logging disclosed rather than hidden (see T-050).

New follow-up tickets filed as a direct result of this review: **T-044** (age-confirmation control), **T-045** (Terms of Service, pre-launch blocker), **T-046** (legitimate-interest balancing assessments — ✅ completed as a pre-deployment blocker, not deferred), **T-047** (account-deletion workflow — automation of an already-operational manual SOP), **T-048** (retention cleanup jobs — automation of an already-operational manual SOP), **T-049** (restrict origin to Cloudflare IPs), **T-050** (remove recipient-email logging).

**Round 3 (2026-07-17, architect review):** the architect correctly identified that publishing retention/rights commitments backed only by "manual for now" is not itself sufficient — a real operational process must exist on day one, and the legitimate-interest assessments (T-046) must be completed *before* publication, not deferred as backlog polish. Delivered `docs/04_ARCHITECTURE/PRIVACY_OPERATIONS.md`: a manual data-subject-request SOP (§1, covering access/rectification/erasure/restriction, with concrete `psql`-level steps — anonymize-in-place rather than hard-delete, to avoid breaking FK-referenced conversation history for the other party), a manual retention-cleanup procedure (§2), a minor-account handling procedure (§3, with a 5-business-day action target distinct from the 1-month rights-request SLA), and the five completed LIAs (§4). T-046 is marked completed; T-047/T-048 are re-scoped as automating an already-operational manual process, not building the capability from zero.

**Round 4 (2026-07-17, final consistency pass):** the architect caught two remaining internal inconsistencies before approving. (1) A quarterly cleanup cadence against a 12-month retention target allowed actual retention up to ~15 months in the worst case — changed to **monthly** (§2), bounding the worst case to ~13 months. (2) The policy promised "12 months after a salon-owner claim ends," but `salon_owners` has no status/end-date column, so that clock could never actually start — reworded in all 4 locales to what is operationally true today (retained while the ownership link is active, removed manually on discovery it's invalid), with T-048 gaining an explicit criterion to add the missing schema field and restore the fixed target once it exists. The erasure SOP was also expanded into an explicit numbered checklist plus a dedicated, mandatory free-text review step (redacting personal data typed directly into message bodies/notes, without deleting the surrounding conversation). A stale "quarterly" leftover found in `PRIVACY_OPERATIONS.md` §5 during final review was fixed, and the regression test guarding it was corrected (a raw occurrence-count assertion was too naive, since the legitimate explanatory sentence uses the word "quarterly" twice by design).

**Production verification (2026-07-17):** `beauty_web` rebuilt and redeployed alone (API/DB/Redis/crawler untouched, uptimes confirmed unchanged; no automatic "Deploy Production" workflow triggered — only pre-existing unrelated Dependabot CI activity). All 4 locale URLs return 200 in production; verified via Playwright against the live site: 15 sequential sections in every locale, zero `TODO` markers, controller identity present, zero console/page errors, zero horizontal overflow (desktop).

**Outstanding launch check (does not block this merge, blocks public reliance on the page):** the controller name "Zhuykov Andrey" was supplied directly by the business owner and used verbatim, unchanged, in that exact word order, across all 4 locales — it has not been independently verified against an official Latin-script spelling on any ID/legal document, since no such document was provided to check against. Confirm this before treating the page as final for public/legal purposes.

**Acceptance Criteria:**
- [x] `/privacy` (el), `/en/privacy`, `/ru/privacy`, `/uk/privacy` return 200 (corrected from the original spec's 3-locale list — the site has 4 locales, `uk` included) — confirmed in production
- [ ] Page is linked in footer of all layouts — **not done**: no footer component exists anywhere in the codebase today (confirmed during this task); adding one is a separate, larger UI change out of scope for this ticket. Flagging as a follow-up, not silently building an unscoped footer here.
- [x] Page explicitly states whether Google Analytics is in use (corrected from "mentions Google Analytics by name" — it does not exist yet, so the policy says so plainly instead)
- [x] Page mentions contact email `hello@lookla.gr` for data requests
- [x] Page does not use a marketing tone (factual, plain language; zero `TODO` markers remain as of the final approved version — every point that was originally undecided now has an approved MVP decision)

---

### T-018 — Cookie Policy and analytics-consent foundation
**Priority:** P0 | **Owner:** FE | **Estimate:** 3h | **Epic:** EPIC-05
**Dependencies:** T-017 ✅ Completed
**Status:** ✅ Completed (2026-07-17) — reviewed, merged to `main` (PR #38), production deployed and verified

**Correction to the original spec below (renamed and rewritten before implementation, per architect review):** the original design was non-compliant on three counts the Hellenic DPA explicitly guards against — it offered only an Accept button with "Accept to continue" phrasing (a cookie wall, not a real choice), had no Reject action at the same level as Accept, and had no way to withdraw consent once given. It also implicitly assumed GA4/T-014 would already exist. None of that is carried forward. GA4 is **not** implemented by this task — see T-014.

**Description:** Build the Cookie Policy page (4 locales) and a dependency-free analytics-consent foundation (cookie contract + banner + persistent settings control) that T-014 can build on. At the end of this task, no analytics script or non-essential analytics cookie exists anywhere on the site — the consent mechanism ships dormant, gated behind a feature flag T-014 turns on only once GA4 is actually configured.

**Pre-write inventory (mandatory phase before any code was written):** every `document.cookie` write, every backend `Set-Cookie`, `localStorage`/`sessionStorage` usage, and Cloudflare-injected cookies were re-verified live — not assumed from the T-017 audit, which the review explicitly required re-checking. Findings: only `NEXT_LOCALE` (frontend, functional) plus `access_token`/`refresh_token`/`oauth_csrf` (backend, all necessary/security) exist; no `localStorage`/`sessionStorage`/`js-cookie` usage anywhere. Google OAuth start was tested live against production (never completing the flow — no account created), confirming `oauth_csrf`'s exact header (`HttpOnly; Max-Age=600; Path=/; SameSite=lax; Secure`). `access_token`/`refresh_token` use the identical `**COOKIE_OPTS` dict as the live-confirmed `oauth_csrf` (`auth.py:28`), so their flags are verified via that shared mechanism plus direct source reading, not a live login — creating a real production account solely to observe an already-verified cookie-setting mechanism was judged an unnecessary write. Cloudflare: tested live against `https://lookla.gr/` (fresh browser context) — no Cloudflare cookie observed under normal browsing; explicitly not claiming one never appears, since Cloudflare's bot-challenge cookies are heuristic-triggered and weren't safely reproducible in this testing.

**Canonical consent contract (`frontend/lib/consent.ts`):** cookie `lookla_consent`, values `1` (granted) / `0` (rejected) / anything else treated as unset. `Path=/`, `Max-Age=15552000` (180 days), `SameSite=Lax`, `Secure` only when served over HTTPS (conditional, not hardcoded — a hardcoded `Secure` would silently break local `http://` testing), **not** `HttpOnly` (the banner, settings control, and T-014's future GA4 loader must read it from client-side JS). Stores only the single digit — no identifier, timestamp, IP, user ID, locale, or fingerprint. A `lookla:consent-change` event (`{ analytics: boolean }` detail) fires on every write, so T-014 can react without reverse-engineering the banner. A separate `lookla:open-cookie-settings` event lets the footer's persistent "Cookie settings" control reopen the same UI later — accept can be changed to reject and back, exactly as easily as the original choice, per the DPA requirement that withdrawal be no harder than consent.

**Feature gate:** `NEXT_PUBLIC_ANALYTICS_CONSENT_ENABLED` — unset or not `"true"` (the shipped default): banner and settings control stay fully dormant, nothing renders. `true`: banner appears when consent is unset, footer settings control becomes visible. This flag is **not** enabled in this task — T-014 turns it on once GA4 is actually configured, per the explicit instruction not to ask users to consent to a service that doesn't exist yet.

**UX contract enforced (and regression-tested):** Accept and Reject render together, unconditionally, with an identical `className` (equal visual weight, equal click cost), no "Accept to continue" text anywhere, no preselected consent, no close icon on the *initial* unanswered banner (Escape and the × control only exist on the reopened settings view), rejecting never gates search/salon pages/map/contact CTAs/auth/messaging/locale selection.

**New global footer:** this is the first footer component in the codebase — previous tickets (T-011, T-020, T-021) each independently deferred "linked in footer" as out-of-scope since none existed. It became a hard functional requirement here (there is no other way to satisfy "withdraw consent as easily as you gave it" without a persistent, always-available control), so it was built now: Privacy Policy link, Cookie Policy link, and the feature-gated "Cookie settings" button, wired into `app/[locale]/layout.tsx` so it appears on every page. This surfaced a real pre-existing duplication: the homepage and `/masters` each already had their own page-local `<footer>` (copyright + `LanguageSwitcher`); merged that content into the new shared `Footer.tsx` and removed both local copies rather than shipping two stacked footers. Verified via Playwright across representative pages (home, search, salon detail, privacy, cookies) at desktop and 375px, in both feature-flag states, before merge: exactly one `<footer>` element per page, zero overflow, zero console errors.

**Final review findings (2026-07-17, architect review):** independently confirmed via fresh Playwright runs — `Max-Age=15552000` honored by the browser as exactly 180.00 days; the `Secure` flag's conditional logic (`window.location.protocol === 'https:'`) genuinely executes rather than being hardcoded, confirmed absent on `http://` which validates it will be present on real `https://`; focus returns to the *exact* footer trigger element (`document.activeElement === trigger`, not just "some button") after closing the reopened settings view; Cookie Policy §3 and Privacy Policy §5 list identical cookies, lifetimes, and flags with no drift between the two documents.

**Production verification (2026-07-17):** `beauty_web` rebuilt and redeployed alone (API/DB/Redis untouched, uptimes confirmed unchanged; `crawler_worker`'s restart was its own independent scheduled cycle, unrelated to `--no-deps web`; no automatic "Deploy Production" workflow triggered). All 4 `/cookies` locale URLs return 200 in production. Verified via Playwright against the live site across 6 representative pages: exactly one `<footer>` per page with locale-aware Privacy/Cookie Policy links and the copyright/language-switcher content preserved, no banner (feature flag correctly unset in production), only `NEXT_LOCALE` present as a cookie (`lookla_consent` correctly does not self-create), zero GA4/GTM requests, zero console errors, zero horizontal overflow.

**Unrelated infrastructure observation, disclosed for transparency:** during this task's isolated verification, `beauty_web`'s `RestartCount` was found at 7 (clean `ExitCode=0` each time) over the preceding ~5 hours, on a memory-constrained host (1.9GiB total, 146MiB free, 864MiB/2GiB swap in use at the time). Most likely cause: repeated concurrent `npm run build` runs during this task's own local verification work (Next.js builds are memory-heavy) put enough system-wide pressure on the host that the live container (300MB hard limit) was OOM-killed and auto-restarted by its `unless-stopped` policy. No extended downtime resulted. Not investigated further as an in-scope fix for T-018 — flagging as a standing host-memory-pressure risk worth a future look, not something this ticket caused a lasting problem from.

**Acceptance Criteria:**
- [x] `lookla_consent` cookie contract matches the canonical spec exactly (values, flags, 180-day lifetime, no identifying data)
- [x] Accept and Reject are visible simultaneously, equal effort, equal visual weight — no cookie wall, no preselection, no "Accept to continue"
- [x] Consent can be withdrawn/changed via the footer "Cookie settings" control, as easily as it was given
- [x] Rejecting analytics does not disable any existing site functionality
- [x] `/cookies` (el), `/en/cookies`, `/ru/cookies`, `/uk/cookies` return 200, structurally identical, cross-linked with `/privacy` — confirmed in production
- [x] No GA4/GTM script, no analytics request, no `_ga*` cookie anywhere — `NEXT_PUBLIC_ANALYTICS_CONSENT_ENABLED` is not enabled in production by this task — confirmed in production
- [x] T-017's Privacy Policy updated for factual consistency only: `lookla_consent` described, Cookie Policy linked instead of described as "planned"

---

### T-019 — Configure GA4 data privacy settings
**Priority:** P0 | **Owner:** OPS | **Estimate:** 0.25h | **Epic:** EPIC-05
**Dependencies:** T-013 ✅ Completed
**Status:** ✅ Completed — superseded by T-013, which already executed and recorded this same configuration (data retention, Google Signals) during property creation, per the architect-directed correction that folded GA4's privacy settings into T-013 rather than leaving them for a separate pass. Original steps below kept for historical reference; two are stale or outdated.

**Dashboard tasks (not code) — original stub, corrected:**
1. ~~GA4 Admin → Data Settings → Data Retention → set to 14 months~~ — done in T-013, actual value **2 months** (event + user data), not 14
2. GA4 Admin → Data Streams → lookla.gr → configure Google signals → Disable — done in T-013
3. ~~GA4 property: IP anonymization (enabled by default in GA4; verify)~~ — outdated Universal Analytics-era concept; GA4 has no such toggle
4. GA4 Admin → Account → User management → add admin — the property was created under a dedicated new Google account owned directly by the project owner; no separate admin-add step was needed

**Acceptance Criteria:**
- [x] GA4 data retention = **2 months** (not 14 — corrected)
- [x] ~~IP anonymization: verified active~~ — not applicable to GA4, removed as a real criterion

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
**Dependencies:** ARCHITECTURE_REVIEW CONTRADICTION-01 (resolved 2026-07-14 — Option B, via `EXISTS`, not the JOIN the contradiction's recommendation line originally suggested)
**Status:** ✅ Completed (2026-07-14) — reviewed, merged to `main` (PR #34), production verified

**Description:** Add `is_owner_claimed` boolean to `SalonListItem`/`SalonDetail` schemas (list and detail; **not** `SalonMapItem` — T-038's fixed 10-field contract stays untouched), computed via a correlated `EXISTS` against `salon_owners`.

**Actual implementation (replaces the stale `LEFT JOIN + COUNT` pseudocode above):**
```python
# app/routers/salons.py
def _owner_claimed_expr():
    return exists().where(SalonOwner.salon_id == Salon.id).correlate(Salon)
```
Embedded as an added column (`query.add_columns(_owner_claimed_expr().label("is_owner_claimed"))`) in the same list/detail queries — not a JOIN, not a separate ownership round-trip. `salon_owners` has no unique constraint on `salon_id` alone (only a composite PK on `(user_id, salon_id)`), so a join could duplicate a salon row; `EXISTS` cannot.

**Schema note:** `salon_owners` had no ORM model before this task (accessed via raw SQL elsewhere) and isn't tracked by Alembic — it predates migration tracking. Added a minimal read-only `SalonOwner` model (2 columns, matches the live table exactly: `user_id`, `salon_id`, composite PK, no status column). No migration; doesn't alter the table.

**Known limitation, not fixed here:** no index on `salon_owners.salon_id` alone. `EXPLAIN ANALYZE` against production (read-only transaction) showed no measurable cost today (~5ms for the full 6320-row active-salon scan) since the table is currently empty (0 rows); worth an index if real claims accumulate — separate task, not created under T-024.

**Acceptance Criteria:**
- [x] `GET /api/salons` response items include `"is_owner_claimed": true/false`
- [x] `GET /api/salons/{id_or_slug}` response includes `"is_owner_claimed": true/false` (both numeric ID and slug lookup)
- [x] Claimed salons (any row in `salon_owners`) return `is_owner_claimed: true`, including when a salon has more than one owner row (no duplication)
- [x] Unclaimed salons return `is_owner_claimed: false`
- [x] `GET /api/salons/map` unchanged (still exactly 10 fields)
- [x] No owner identity exposed through any public endpoint

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

### T-042 — Unified loading/empty/error/success state pattern (SQC-01A)
**Priority:** P0 (reprioritized from P2 — first ticket of the SQC-01A UX-foundation phase, per architect direction 2026-07-23) | **Owner:** FE | **Estimate:** 1h (revised: ~3h — scope expanded from Reviews-only to a shared primitive reused across Services, Reviews, and search results) | **Epic:** EPIC-09
**Dependencies:** None
**Status:** ✅ Completed (2026-07-23) — reviewed, merged to `main` (PR #49, then follow-up PR #50 for a bug found during production verification), `beauty_web` rebuilt/redeployed alone each time, full production verification passing against `https://lookla.gr`. First completed ticket of the SQC-01A UX-foundation phase.

**Original scope (superseded, expanded per architect instruction):** the original ticket only covered Reviews (and, per its own acceptance criteria, Services). Before implementation, the architect asked not to build a one-off fix scoped to those two sections, but a single reusable Loading/Empty/Error/Success pattern — since the identical gap (a failed fetch silently collapsing into "empty," with no way for a user to distinguish "nothing here" from "something broke") also existed, unfixed and undocumented, on the search page's list and map results (`searchError`/`mapError` state was added by T-015 purely for analytics gating and was never wired into the UI at all).

**Architecture:**
- `lib/asyncState.ts` — `AsyncStatus = 'loading'|'empty'|'error'|'success'` + pure `deriveAsyncStatus(loading, error, isEmpty)`. Precedence: loading > error > empty > success (a stale error/empty must not flash during a retry; a failed fetch is never reported as "genuinely nothing here").
- `components/AsyncSection.tsx` — the single place an `AsyncStatus` becomes UI. Deliberately unstyled/unopinionated (no fetch/analytics logic, no hardcoded className, **no wrapper `<div>` of its own**) — each call site supplies its own loading skeleton, empty message, and error message+retry, since Services/Reviews cards and the search results grid have different containers, and the search list's loading skeleton is itself a set of direct CSS Grid items that a shared wrapper would have broken. What's shared is the state machine, not the markup.
- `SalonDetailClient.tsx`'s `useLazySection` now tracks a distinct `error` boolean (a non-`ok` HTTP response throws, rather than being silently `.json()`-parsed as if it were valid data) and exposes a `retry` function (re-runs the same IntersectionObserver-triggered fetch on demand, not a full page reload). Services and Reviews both render through `<AsyncSection status={...}>`, with the section heading now visible in the empty/error states too (previously the whole section, heading included, rendered nothing in either case).
- `search/page.tsx`'s list and map fetches were refactored into `useCallback`-wrapped `loadSalons`/`loadMapSalons` (previously inline in `useEffect`, with no way to manually retry) — same `!response.ok` fix applied (a 500 with a JSON error body was previously indistinguishable from a genuine empty result, since `d.items || []` / `Array.isArray(d) ? d : []` both silently produce an empty array from a non-array error payload). The list view's existing friendly empty-state copy ("no salons in this area" + Clear filters button) is preserved unchanged; only the new error branch is new.
- T-015's `search_results_view` tracking effect is untouched — it still gates on the raw `loading`/`searchError`/`mapLoading`/`mapError` booleans directly, not on the new `listStatus`/`mapStatus` derived values.
- **Accessibility** (added during review, before merge — PR #49's second commit): error states use `role="alert"`/`aria-live="assertive"`; empty states use `role="status"`/`aria-live="polite"`; loading skeletons are `aria-hidden="true"` (decorative). A new shared hook, `lib/useFocusOnStatusRecovery.ts`, moves keyboard focus back into the recovered region after Retry — without it, the retry button the user just activated unmounts the instant status leaves `'error'`, dropping focus to `<body>` for keyboard/screen-reader users.
- **Focus-recovery bug, found during post-merge production verification and fixed in a same-day follow-up (PR #50):** the hook's ref was initially attached only to each state's own div, but `error` and its eventual destination (`loading`, then `success`/`empty`) are different DOM nodes — the error div unmounts the instant status leaves `'error'`, so `ref.current` was already `null` by the time the recovery effect ran. Fixed by having the hook track the *last settled (non-loading) status* rather than the literal previous one, and by moving the ref to an always-present **outer** wrapper for Search list/map specifically (the grid div itself, and a new wrapper around `<MapView>`) rather than any individual state — required because the list's loading skeletons and success-state salon cards are direct CSS Grid items, so a per-state wrapper there would have broken `grid-cols-3`.

**New translation keys (all 4 locales):** `salon.servicesNotAvailable`, `salon.servicesLoadError`, `salon.reviewsNotAvailable`, `salon.reviewsLoadError`, `salon.retry`; `search.results_load_error`, `search.map_load_error`, `search.retry`.

**Verification:** 399/399 frontend tests passing (46 new for T-042 across both PRs — `asyncState.test.ts` for the pure precedence logic, `AsyncSection.test.tsx` for the dispatch order and its no-wrapper guarantee, `useFocusOnStatusRecovery.test.ts` for the settle-tracking logic, extended `salonDetail.test.ts` and `searchPage.test.ts` for the wiring/accessibility/grid-safety, plus locale-key-parity checks across all 4 locales). `npm run lint` and `npm run build` both clean, no new warnings, on every commit.

**Production verification (2026-07-23):** Playwright against `https://lookla.gr` with mocked API responses (200/500/empty-array) to force each of the 4 states on demand, since production data alone can't reliably produce an error or empty result. 17/18 checks passing across all 4 surfaces (Services, Reviews, Search list, Search map) — both mouse- and keyboard-activated Retry confirmed to re-fetch and display real data, with focus never lost to `<body>` after either activation method; Search list confirmed to stay a genuine 3-column CSS Grid (not collapsed into one wrapper cell) through loading/error/success; no console/hydration errors (the one non-passing check was the test's own intentionally-mocked 500 response being logged by the browser, not an app defect); no horizontal overflow. One transient failure (map not yet rendered) seen in an earlier combined run was confirmed to be a timing flake under concurrent test load, not reproducible across 3 clean isolated reruns plus a full clean rerun of the entire suite.

**Acceptance Criteria:**
- [x] A shared `loading`/`empty`/`error`/`success` primitive exists (`lib/asyncState.ts` + `components/AsyncSection.tsx`), not a Reviews-specific fix
- [x] `useLazySection` (Services/Reviews) tracks a distinct error state, not just loading/data
- [x] Zero reviews (genuine empty result) shows "No reviews available for this salon"; zero services shows "Service information not available for this salon"
- [x] Failed reviews/services fetch shows "Could not load reviews"/"Could not load services" with a retry action
- [x] T-012's `googleReviewsSourceLabel` disclosure still stays hidden in both states (unchanged: `!loading && reviewCount > 0`)
- [x] Same pattern applied to search results (list and map) — not originally in scope, added per architect instruction: failed `/api/salons`/`/api/salons/map` requests now show a distinct "Could not load results"/"Could not load the map" message with retry, instead of silently looking like a zero-result search
- [x] Accessibility: `role`/`aria-live` on every non-success state, keyboard focus correctly returns to the recovered region after Retry (mouse and keyboard activation both verified)
- [x] Production verification — 17/18 checks passing (see above)
- [x] Independent review — approved (PR #49, PR #50)

---

### T-043 — Add index on salon_owners(salon_id)
**Priority:** P2 | **Owner:** BE | **Estimate:** 30m | **Epic:** EPIC-08
**Dependencies:** None

**Description:** `salon_owners` has only a composite PK on `(user_id, salon_id)` — no separate index on `salon_id` alone. T-024's `is_owner_claimed` runs a correlated `EXISTS (... WHERE salon_id = ?)` per salon on every list/detail request; `EXPLAIN ANALYZE` in production (2026-07-14) showed no measurable cost today (~5ms for a full 6320-row scan) because the table is currently empty (0 claimed salons). Flagged by review as non-blocking tech debt — revisit once real owner claims start accumulating, since a growing `salon_owners` table combined with no `salon_id` index will eventually show up in the query plan as a per-row sequential scan.

**Acceptance Criteria:**
- [ ] Alembic migration adding `CREATE INDEX idx_salon_owners_salon_id ON salon_owners(salon_id)`
- [ ] `EXPLAIN ANALYZE` confirms the T-024 `EXISTS` query plan uses the new index once `salon_owners` has enough rows to matter
- [ ] No change to `salon_owners`' existing composite PK or FK constraints

---

### T-054 — Search Results Context & Filter Recovery (SQC-01A)
**Priority:** P0 (second ticket of the SQC-01A UX-foundation phase) | **Owner:** FE | **Epic:** EPIC-09
**Dependencies:** T-007 ✅ Area URL-state, T-015 ✅ Search analytics baseline, T-042 ✅ Unified async states
**Status:** ✅ Completed (2026-07-24) — reviewed, merged to `main` (PR #51), `beauty_web` rebuilt/redeployed alone (API/DB/Redis/crawler/crawler_worker untouched), full production verification passing against `https://lookla.gr`.

**Goal:** make the search-results page immediately understandable and recoverable — a stable results summary with the canonical total, visible chips for every effective filter, individual filter removal, a clear-all action, and an actionable filtered-empty state. Frontend-only; no backend/ranking/filter/SalonCard/analytics-event changes.

**Search URL-state inventory (pre-implementation):** `area`/`city`/`q`/`category`/`min_rating` are all real, currently-applied filters sent to `/api/salons` and `/api/salons/map`; `view` (list/map) and `page` are not filters. Found three pre-existing gaps during inventory: (1) the results count showed a raw `${total} ${t('results')}` string-concatenation with no pluralization, and did not check `searchError` at all — a failed request displayed **"0 results"**, indistinguishable from a genuine empty search; (2) `clearFilters()` (the existing filter-dropdown's own clear button) never removed `q`, so "Clear filters" didn't actually clear the search query; (3) `city` was still sent to the API and could survive certain navigations even when `area` (canonical) was present, with no UI indication a hidden legacy filter was active.

**Effective-filter precedence:** canonical `area` is authoritative — `city` is only ever shown as its own chip when `area` is absent, so a user is never silently filtered by a hidden legacy param. Values are trimmed; whitespace-only/invalid values never produce a chip. Area/category slugs resolve to their localized name once the canonical metadata (`/api/areas`, `/api/categories`) has loaded; before it loads, a locale-agnostic humanized fallback (`athens-center` → `Athens Center`) is shown instead of either the raw slug or an artificial delay, per architect instruction to derive initial visible filter context from already-available URL state. If metadata has loaded and the slug still matches nothing, the chip is dropped entirely (never a misleading chip for a genuinely invalid slug).

**Result-count source:** the existing `total` state (set from the `/api/salons` response's `total` field) — never rendered-card-count, never map-marker-count. Reused as-is for both list and map views, since the list fetch already runs unconditionally regardless of which view is displayed. Rendered through a single ICU `{count, plural, ...}` message per locale (`search.results_summary`), verified directly against `intl-messageformat` (the library next-intl uses internally) for all 4 locales' correct CLDR plural categories, including Russian/Ukrainian one/few/many/other. Loading shows a fixed-height skeleton (not empty/collapsed, avoiding layout shift); error shows nothing (not "0").

**Architecture:**
- `lib/searchContext.ts` — pure, dependency-free `deriveActiveFilters()` (the `ActiveSearchFilter` model) plus per-filter-type and clear-all URL-mutation helpers (`removeQueryFilter`, `removeAreaFilter` — reuses T-007's `buildAreaUrlParams` so area removal already deletes legacy `city` too — `removeLegacyCityFilter`, `removeCategoryFilter`, `removeMinRatingFilter`, `removeActiveFilter` dispatcher, `clearAllActiveFilters`). `clearAllActiveFilters` fixes the pre-existing `q`-not-cleared bug; the existing filter-dropdown's own `clearFilters()` is deliberately left untouched (different, narrower, pre-existing scope) to avoid unrelated behavior change.
- `components/ActiveFilterChips.tsx` — one real `<button>` per chip inside a semantic `<ul aria-label="Active filters">`, no nested interactive controls, one click = one URL update via `router.push` (matching this page's existing, consistent strategy — no `router.replace` introduced).
- `lib/useFilterChipFocus.ts` — after a chip removal or clear-all, moves focus to the chip that shifted into the removed one's index, else the clear-all button, else the results-summary region — never `<body>`. Same "mark intent, act only once the count actually changed" pattern as T-042's `useFocusOnStatusRecovery`, so an unrelated render never steals focus.
- `search/page.tsx` — new `<h1>`"Search results" heading (page previously had no heading at all) + `aria-live="polite"` count region + chips + conditional clear-all, wired above the existing T-042 `AsyncSection`. The list/map `empty` branches now key off `activeFilters.length > 0` (previously only `area`), giving every filter type — not just area — the actionable "No salons found" / explanation / "View all salons" recovery contract; a genuinely filter-free zero-result case keeps the old neutral message with no recovery action. Retry (T-042, error-only) is completely untouched.
- New translation keys (all 4 locales): `search.results_heading`, `search.results_summary` (ICU plural, replaces the previously-dead `results_count`), `search.filter_query`, `search.clear_all_filters`, `search.remove_filter`, `search.no_matches_title`, `search.no_matches_description`, `search.view_all_salons`.

**Analytics invariants:** no new `trackEvent` call sites added anywhere in this change — `removeFilter`/`clearAll`/`ActiveFilterChips` contain zero analytics calls. `search_results_view` and `area_select` call sites are byte-identical to pre-T-054. A regression test asserts every `trackEvent` call in the page uses one of the 5 T-015-approved event names.

**Verification:** 473/473 frontend tests passing (74 new for T-054 — pure-function tests for `searchContext.ts`'s filter derivation and URL mutations, `intl-messageformat`-backed pluralization tests for all 4 locales' real CLDR plural categories, `useFilterChipFocus`/`ActiveFilterChips` behavior, and extensive `search/page.tsx` wiring/accessibility/analytics-invariant regression tests). `npm run lint` and `npm run build` both clean, no new warnings.

**Isolated production verification (2026-07-23):** built and ran the actual `next build` standalone production output (matching the deployed Dockerfile's runner stage exactly — same `public/`/`.next/static` layout) on a throwaway port, proxying to the real backend API, entirely separate from the live `beauty_web` container (confirmed unaffected — uptime unchanged throughout). 63/63 Playwright checks passing across all 15 required scenarios: unfiltered/area/query/legacy-city/area+query/area+city-together search, filtered zero-results (actionable, `role="status"`, no Retry), individual chip removal (URL + focus), clear-all (URL + focus), browser back/forward (correct filter-context restoration), list/map view (canonical total preserved in both), loading (no false zero), API error+retry, keyboard-only chip removal (Enter key, correct accessible name, focus preserved), 3 mobile breakpoints (320/375/768px — chips wrap, no horizontal overflow), and all 4 locales (correct heading/pluralization/localized chips, zero console/hydration errors) — including real production data exercising plural categories (90 → Russian "many", Ukrainian "many") beyond what the unit tests' synthetic values covered.

**Production verification (2026-07-24):** Playwright directly against `https://lookla.gr` (real deployed build, `beauty_web` rebuilt/redeployed alone; API/DB/Redis/crawler/crawler_worker uptime unchanged throughout), covering the three pre-existing gaps this ticket fixes plus the full acceptance-criteria set. 28/28 substantive checks passing:
- API 500 on `/api/salons`: count shows nothing (never "0"), error state is `role="alert"`, Retry restores a real total.
- Clear-all: removed `area`/`q`/`min_rating`/`page`, preserved `view=map`, focus landed on the results-summary region (never `<body>`).
- Removing the `area` chip when `area=piraeus&city=Athens` were both present: `city` was already correctly suppressed as a visible second filter beforehand, and removing `area` deleted `city` from the URL too — no silent reactivation.
- Canonical total (76) displayed correctly even with only 20 cards actually rendered on the page; list and map views showed the identical canonical total (90) for the same filters.
- Russian ("90 салонов найдено") and Ukrainian ("90 салонів знайдено") pluralization correct on real production data.
- No horizontal overflow at 320px/375px with a long free-text query chip.
- Browser back/forward correctly restored the prior filter context's chips and its own matching count.
- Analytics: exactly one `search_results_view` fired with exactly `{area, result_count_bucket, view, locale}` (no new field); `area_select` fired from the filter-panel's own area `<select>` with exactly `{area, source, locale}`; no event name outside the T-014 `page_view` + 5 T-015 product events appeared; the raw query value did not appear in any T-015 product event's own parameters (GA4's standard `dl`/document-location field on `page_view` naturally includes the full current URL, including `?q=...`, as normal page-context metadata — this is universal GA4 behavior on every hit type, not a T-015 product-event parameter, and was correctly excluded from this check once the two were properly distinguished).

**Acceptance Criteria:**
- [x] Stable results summary with the canonical total (never card-count/marker-count), correct locale-aware pluralization
- [x] Visible chips for every effective filter (query, area, legacy city, category, min_rating)
- [x] Individual filter removal (one click/keypress = one URL update, focus preserved)
- [x] Clear-all action, removing every effective filter including query (fixes the pre-existing `clearFilters()` gap)
- [x] Actionable filtered empty state, never framed as an error, never shows Retry
- [x] Legacy `city` handled correctly: authoritative `area` suppresses it as a second filter; standalone `city` remains visible so no hidden filter state
- [x] No backend/database/ranking/filter/SalonCard changes
- [x] No new GA4 events; existing `search_results_view`/`area_select`/`salon_open` untouched
- [x] Accessibility: polite count region, assertive error (unchanged from T-042), precise localized remove-button accessible names, predictable focus after removal/clear-all, keyboard flow verified
- [x] Production verification — 63/63 isolated checks + 28/28 live production checks passing (see above)
- [x] Independent review — approved (PR #51)

---

### T-055 — SalonCard Information Hierarchy & Click Target Optimization (SQC-01A) ✅ Completed
**Priority:** P0 (third ticket of the SQC-01A UX-foundation phase) | **Owner:** FE | **Epic:** EPIC-09
**Dependencies:** T-015 ✅ Search analytics baseline, T-054 ✅ Search results context
**Status:** Merged and deployed (PR #52, branch `feat/T-055-salon-card-hierarchy`). Production-verified 2026-07-24.

**Goal:** improve how information is organized inside `SalonCard.tsx` — accessible name, click target, and visual hierarchy — without touching data, ranking, the search API, or analytics. No backend/database/ranking/SalonCard-data-field/GA-taxonomy changes.

**Inventory findings (live audit against production, pre-implementation):** the card is a single outer `<Link>` with zero nested interactive elements (already correct — no change needed there). Without an explicit `aria-label`, the computed accessible name was the raw, unseparated concatenation of every descendant text node, e.g. `"OpenΚουρείο JUST HAIRΕιρήνης 15, Πειραιάς★★★★★5.0(520)"` — unusable for screen reader users. Sampling 72 live cards: rating present on 72/72, open/closed badge on 69/72 (96%), price on 0/72, verified badge on 0/72 — rating and open-status are near-universal signals; price/verified are rare, conditionally-rendered secondary elements that already reserve no empty space when absent (confirmed via raw HTML dump — zero DOM footprint, no placeholder branch). Longest real salon name on a live page: 62 characters, visually truncated to one line with no way to recover the full name.

**Accessible-name fix:** `buildCardAriaLabel()` builds `"{name}, {city}, {rating word} {rating}, {open/closed}"`, each clause included only when the underlying field is actually present (never a dangling separator, never a placeholder for missing data). Deliberately excludes street/number (redundant once city is present), the decorative star glyphs (screen readers announce them as literal Unicode character names), and the review count (available as plain visible/accessible text in the card body, not duplicated into the label). Verified against the actual computed accessible name (Playwright `getByRole('link', { name })`, not just attribute presence) across all 4 locales on the real built app.

**Name truncation:** salon name switches `line-clamp-1` → `line-clamp-2` with `title={salon.name}` added for pointer users, and the full name is always present in the card's `aria-label` regardless of visual truncation. Backed by a live DOM measurement (swapping the CSS class on the production DOM and measuring `getBoundingClientRect().height` before/after): height increase is uniform within any given grid row (263.5px → 281px, 0px variance) — a predictable, non-ragged cost. Mobile-viewport verification (320/375/390/768px) confirms no horizontal overflow at any breakpoint.

**Architecture:** all changes confined to `frontend/components/SalonCard.tsx` — `buildCardAriaLabel()` (exported, unit-tested directly), `aria-label={cardAriaLabel}` on the outer `<Link>`, `aria-hidden="true"` on the star-glyph `<span>` only (numeric rating/count remain plain accessible text, per instruction to keep them in the label *or* as separate accessible text, not both hidden), `title=` + `line-clamp-2` on the name `<h3>`. `handleOpen`'s `trackEvent('salon_open', ...)` call and the price/verified conditional-rendering blocks are byte-identical to before — no code change there, confirmed by regression tests.

**Analytics invariants:** zero new `trackEvent` call sites; `handleOpen` unchanged byte-for-byte (T-015 contract: `salon_id` always `String(salon.id)`, never `salon.slug`). A regression test asserts the exact source string of the `trackEvent` call site is unchanged.

**Verification:** 497/497 frontend tests passing (24 new for T-055 — `buildCardAriaLabel()` unit tests for all 4 locales and every present/absent field combination, plus source-level regression tests for the single-`<Link>`/no-nested-interactive contract, the byte-identical `trackEvent` call, and the still-conditional price/verified rendering). `npm run lint` and `npm run build` both clean, no new warnings (pre-existing `<img>`-vs-`next/image` warning on this file predates T-055).

**Isolated production verification:** built and ran the actual `next build` standalone production output (matching the deployed Dockerfile's runner stage — same `public/`/`.next/static` layout) on a throwaway port, proxying to the real backend API, entirely separate from the live `beauty_web` container. All 4 locales × 9 checks passing: computed accessible name is non-null, differs from the raw concatenation bug, and excludes star glyphs; `getByRole('link', { name: <computed aria-label> })` actually resolves the card (proving the label really is the accessible name, not just an attribute); zero nested interactive elements; star-glyph spans are `aria-hidden`; name heading has `title=` and `line-clamp-2`; card heights uniform within a row (0px variance); zero console/page errors. Mobile breakpoints (320/375/390/768px) confirmed no horizontal overflow; the height difference between 1-column and 2-column layouts at different breakpoints was traced to CSS Grid's default `align-items: stretch` equalizing cards within the same row (pre-existing behavior, not a regression). The `salon_open` GA4 beacon itself could not be observed in this isolated build (the measurement ID/consent flag are baked in only via the Docker build's env args, confirmed in T-054) — covered instead by the byte-identical source regression test, with the live beacon checked against production after deploy (see below).

**Merge and deploy (2026-07-24):** PR #52 approved and merged to `main` (CI green: backend + frontend both pass). Rebuilt and redeployed `beauty_web` only via `docker compose build web && docker compose up -d --no-deps web` (12m41s build, no errors) — `api`/`db`/`redis`/`crawler`/`crawler_worker` untouched throughout, uptime unaffected.

**Live production verification (2026-07-24):** against `https://lookla.gr`, all 4 locales × 5 widths (320/375/390/768/1280px) — zero horizontal overflow; every sampled `aria-label` structured, localized, and star-glyph-free (e.g. `"Harris Anagnostopoulos, Καλαμάτα, rating 5.0, Open"` / `"…, βαθμολογία 5.0, Ανοιχτό"` / `"…, рейтинг 5.0, Открыто"` / `"…, рейтинг 5.0, Відкрито"`); the 62-char long-name card's full name confirmed present in both `aria-label` and `title=`. Price rendering confirmed on a real priced salon (id 10647 "La Main Nail Salon", `min_price=5.0`) — renders `€` correctly; a priceless card's rating/price row has exactly 1 child, no reserved-space placeholder. Both mouse click and keyboard (Enter) activation each produced exactly one navigation to the salon detail page and exactly one `salon_open` push to `dataLayer` with the correct T-015 contract (`{"salon_id":"12608","source":"search_list","locale":"en"}`) — confirmed via `dataLayer` inspection after finding the raw GA4 `collect` network beacon unreliable to observe directly within a short window (GA4 batches non-initial hits with an observed multi-second delay, consistent with the same finding in T-054's verification). Zero console/page errors throughout. `is_verified` is currently `false` for all ~6,300 production salons (confirmed by scanning the live API) — the verified-badge rendering path has no real-data example to smoke-test today; that logic is untouched by T-055 and covered by the source-level regression test instead.

**Acceptance Criteria:**
- [x] Whole-card accessible name fixed: no longer the raw unseparated concatenation, verified as the actual computed accessible name (not just attribute presence) across all 4 locales
- [x] Decorative stars excluded from the accessible name via `aria-hidden`; numeric rating/count remain accessible text
- [x] Full salon name always reachable (aria-label + title=), visual truncation improved (line-clamp-2) with a measured, uniform height cost
- [x] Rating/open-status treated as primary constant hierarchy; price/verified remain conditional secondary elements with no reserved empty space
- [x] No removal of verified/min_price, no business-meaning change, no "Price unavailable" substitute text, no new data, no backend/type-contract change
- [x] Single outer `<Link>` preserved; no nested interactive elements introduced
- [x] No data/ranking/API/analytics-taxonomy changes; `salon_open` call site byte-identical, confirmed firing correctly in production for both mouse and keyboard activation
- [x] Isolated production verification — 4 locales × 9 checks passing (see above)
- [x] Live production verification — 4 locales × 5 widths + price/click/keyboard checks passing (see above)
- [x] Independent review — approved (PR #52)

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
**Status:** ✅ Completed (2026-07-15) — reviewed, merged to `main` (PR #36), production deployed and verified

**Description:** `robots.txt` was buried in T-029 acceptance criteria. Extracted as a separate P0 task since it has no dependency on error boundaries and must be live before crawlers discover the admin panel.

**File:** `frontend/public/robots.txt`

**Pre-existing state (found during inventory, not created by this task):** `frontend/public/robots.txt` already existed (`Allow: /`, `Disallow: /api/`, `Disallow: /api/media/photo/`, Sitemap directive) but did not disallow `/admin`, `/dashboard`, or `/account`. T-036 edits this existing single source rather than creating a new one.

Final content:
```
User-agent: *
Disallow: /admin
Disallow: /dashboard
Disallow: /account
Disallow: /api/
Disallow: /en/admin
Disallow: /en/dashboard
Disallow: /en/account
Disallow: /ru/admin
Disallow: /ru/dashboard
Disallow: /ru/account
Disallow: /uk/admin
Disallow: /uk/dashboard
Disallow: /uk/account
Allow: /
Sitemap: https://lookla.gr/sitemap.xml
```

`/api/media/photo/` was dropped as a separate line — it is a strict subpath of `/api/`, already covered, confirmed no semantic change.

**Locale-routing finding (isolated production build, `node server.js` per the Dockerfile's exact runtime, `NODE_ENV=production`):** `localePrefix: 'as-needed'` with default locale `el` unprefixed means `/admin`, `/dashboard`, `/account` (bare, `el`) and `/en|ru|uk/admin|dashboard|account` are all distinct, directly-served (`200`) paths — all 12 combinations require explicit `Disallow` rules. `/el/admin` (and `/el/dashboard`, `/el/account`) reliably 307-redirect to the bare path, confirmed via `curl`, so no `/el/`-prefixed rules were added (redundant — a crawler following the redirect lands on an already-disallowed bare path).

**Sitemap finding (factual correction — `sitemap.xml` was NOT absent):** `frontend/public/sitemap.xml` already exists, is tracked in git since the initial repository commit, and serves `200` with `Content-Type: application/xml`, ~21,900 real `<url>` entries (verified both by reading the file and by an isolated HTTP request). Prior notes here and in `FRONTEND_ARCHITECTURE.md` §14, `FUTURE_FEATURES.md`, and `AUDIT.md` describing it as "deferred"/"not implemented"/"post-MVP" were stale; corrected in this task as a factual correction (the sitemap's *content* is unchanged — T-036 does not generate, edit, or regenerate it).

**Known open item, not resolved by this task:** `frontend/public/sitemap.xml` currently lists `/login` and `/register` as indexed URLs. `FRONTEND_ARCHITECTURE.md` §14 separately specifies a robots.txt that would `Disallow: /login`, `/register`, `/pricing` — a real contradiction with both the sitemap's current content and this task's own canonical spec (which does not disallow those paths). T-036 intentionally implements only the canonical spec above and does not touch the indexing status of `/login`/`/register`/`/pricing` — that is a separate SEO decision for a future ticket, not a technical inevitability to be decided silently here.

**Production verification (2026-07-15):** `beauty_web` rebuilt and redeployed alone (API/DB/Redis/crawler untouched, uptimes confirmed unchanged). Direct-to-origin request (`curl http://127.0.0.1:3000/robots.txt`, bypassing Cloudflare) is byte-identical to the committed file. Public `https://lookla.gr/robots.txt` also returns 200 with our full ruleset intact, but Cloudflare's zone-level "Content Signals"/AI Crawl Control feature prepends its own bot-management `User-agent` block at the edge — pre-existing platform config, not introduced or controlled by this task, and does not override or conflict with our `Disallow` rules (RFC 9309 merges same-user-agent groups). `sitemap.xml` confirmed reachable publicly (200, `application/xml`, correct size). No automatic "Deploy Production" workflow triggered — only CI ran on the merge push.

**Acceptance Criteria:**
- [x] `https://lookla.gr/robots.txt` returns 200 with correct content
- [x] `Disallow: /admin` present
- [x] `Disallow: /api/` present
- [x] `User-agent: *` present as first rule
- [x] robots.txt does NOT disallow `/` or `/salons/` or `/search` (those must be crawlable)
- [x] Remove `robots.txt` from T-029 acceptance criteria (checked — T-029's current acceptance criteria contain no robots.txt reference; already clean, nothing to remove)

---

### T-044 — Age-confirmation control at registration (18+)
**Priority:** P0 | **Owner:** FE/BE | **Estimate:** 1h | **Epic:** EPIC-05
**Dependencies:** T-017

**Description:** T-017's Privacy Policy states an MVP age policy (approved by architect review, 2026-07-16): the public directory is browsable by anyone without an account; account registration, in-app messaging, availability requests, and appointments are intended only for users 18+; Lookla does not knowingly provide these features to children. The policy text is now live, but no enforcement exists yet — `POST /api/auth/register` has no age/date-of-birth field and no confirmation checkbox exists on the registration form.

**Required:**
- Add an "I confirm I am 18 or older" checkbox (or equivalent) to the registration form, required to submit.
- Backend: reject registration if the confirmation is missing (do not need to collect/store an actual birthdate — a confirmation checkbox is sufficient for the approved MVP policy; do not over-engineer a full age-verification/ID-check system, which was explicitly not requested).

**Already done (not blocking this ticket):** the manual minor-account-handling procedure referenced by the Privacy Policy's Children section is documented and operational — `docs/04_ARCHITECTURE/PRIVACY_OPERATIONS.md` §3 (trigger, reviewer, verification, 5-business-day action target, disposition of messages/appointments/salon-owner claims tied to the account, logging). This ticket is only the missing UI/backend confirmation checkbox — the process for what happens *after* a minor is identified already exists independent of it.

**Acceptance Criteria:**
- [ ] Registration form requires an explicit 18+ confirmation before submission
- [ ] Backend rejects registration requests missing the confirmation

---

### T-045 — Publish Terms of Service (pre-launch blocker)
**Priority:** P0 | **Owner:** OPS/Legal | **Estimate:** TBD | **Epic:** EPIC-05
**Dependencies:** T-017

**Description:** T-017's Privacy Policy lawful-basis matrix (approved by architect review, 2026-07-16) relies on "performance of a contract with you" as the legal basis for account registration, authentication, messaging, availability requests, and appointments. That basis presumes an actual contract — Lookla currently has no Terms of Service, so the contractual basis is not yet formally supported by user-facing terms. This is a legal/business-process ticket, not primarily an engineering one; flagging it so it is not silently forgotten before public launch.

**Acceptance Criteria:**
- [ ] Terms of Service drafted and reviewed (legal input required — do not have an AI agent invent binding contractual terms)
- [ ] `/terms` page published, linked from registration and the Privacy Policy
- [ ] Confirm with Greek counsel whether e-commerce/consumer-protection rules require additional disclosures (e.g. an operator postal address) beyond what GDPR Article 13 requires — this question was explicitly raised and deferred during T-017's review and is not resolved by this ticket alone

---

### T-046 — Document legitimate-interest balancing assessments
**Priority:** P0 | **Owner:** OPS/Legal | **Estimate:** 2h | **Epic:** EPIC-05
**Dependencies:** T-017
**Status:** ✅ Completed (2026-07-17) — treated as a pre-deployment blocker for T-017, not deferred post-launch work, per architect review

**Description:** T-017's Privacy Policy states that several processing activities rely on Lookla's "legitimate interest" as their GDPR legal basis. Stating a legitimate-interest basis in a public policy is not itself the balancing test GDPR expects a controller to have performed. The architect reviewing T-017 explicitly required this assessment to exist *before* the policy is published, not as a backlog improvement — a public commitment without the underlying reasoning behind it is not acceptable.

**Delivered:** `docs/04_ARCHITECTURE/PRIVACY_OPERATIONS.md` §4, a documented three-part assessment (purpose / necessity / balancing) for each of the five items, each referencing the actual Lookla data and code involved, not a generic template:
- Public reviewer names and review text
- Professional/staff names
- Business contact data
- Report/IP anti-abuse processing
- OpenAI translation of public review/service text

**Acceptance Criteria:**
- [x] A documented three-part balancing assessment exists for each of the five items above
- [x] Each assessment references the actual data involved (not a generic template)

---

### T-047 — Account-deletion workflow
**Priority:** P1 | **Owner:** BE | **Estimate:** 3h | **Epic:** EPIC-09
**Dependencies:** T-017

**Description:** T-017's Privacy Policy states a retention target of deleting account profile data within 30 days of a verified deletion request. No self-service or automated mechanism exists — confirmed via audit: no `DELETE`/deactivation endpoint for a user's own account exists anywhere in `backend/app/routers`, and no data-export endpoint exists either. A manual SOP for executing this by hand (`psql`, run by the controller) is documented in `docs/04_ARCHITECTURE/PRIVACY_OPERATIONS.md` §1 and is operational today, so the 30-day commitment is currently met without this ticket — this ticket is about replacing manual `psql` execution with a built (at minimum admin-triggerable) capability, not building the capability from scratch.

**Acceptance Criteria:**
- [ ] A documented (admin-triggerable at minimum) way to delete or irreversibly anonymize a user's account row, associated `refresh_tokens`, `email_verifications`, `password_resets`
- [ ] Decide and document what happens to the user's messages, reports, and appointments on account deletion (delete vs. anonymize the `sender_user_id`/`client_user_id` reference — the messages table has a `NOT NULL` FK via `JOIN users u ON m.sender_user_id = u.id` per `chat.py`, so straightforward row deletion of the user will break existing message history unless this is handled deliberately)
- [ ] 30-day target from a verified request is met in practice, even if enforced manually for now

---

### T-048 — Retention cleanup jobs: tokens, messages, appointments, reports, claim records
**Priority:** P1 | **Owner:** BE | **Estimate:** 3h | **Epic:** EPIC-09
**Dependencies:** T-017

**Description:** T-017's Privacy Policy states specific retention targets for which no *automated* enforcement currently exists. Confirmed via audit — zero scheduled cleanup jobs exist anywhere in `backend/app` for any of these tables (only ad-hoc single-row deletes tied to specific user actions, e.g. an owner removing one service). A manual **monthly** cleanup SOP is documented and operational (`docs/04_ARCHITECTURE/PRIVACY_OPERATIONS.md` §2 — deliberately monthly, not quarterly, because a quarterly cadence against a 12-month target allows actual retention up to ~15 months in the worst case; monthly bounds it to ~13 months) so the retention targets are currently met by hand — this ticket replaces the monthly manual `psql` run with a scheduled job. Needed:
- Expired/used `email_verifications` and `password_resets` rows — currently just become unusable at `expires_at`, never deleted.
- Expired/revoked `refresh_tokens` rows.
- `messages`/`conversations` older than 12 months past account closure or last activity.
- `availability_requests`/`appointments` older than 12 months past the relevant date.
- `reports` (including `reporter_ip`) older than 12 months past submission.
- **`salon_owners` schema change**: add a `status`/`ended_at` column (currently absent — `SalonOwner` has no such field at all, confirmed via `backend/app/models/salon.py`). The public policy's wording for claims was corrected (2026-07-17) specifically because this field doesn't exist yet — claims are described as retained while active, removed manually on discovery, not on a fixed post-end timer. This ticket should add the schema field *and* update the policy back to a fixed 12-month-post-end target once it exists and a job enforces it — until then, do not silently let the policy and the schema drift apart again.

**Acceptance Criteria:**
- [ ] A scheduled job (cron, Celery beat, or equivalent) exists that purges each of the above once past its retention target
- [ ] Each job is tested against a fixture with rows both inside and outside the retention window
- [ ] Confirm translation-cache columns (`Review.text_en/ru/uk`, `Service.name_en/ru/uk`) need no separate cleanup job — they are columns on the same row as the source content, so they are deleted automatically if/when the source row is deleted; no separate cache table exists
- [ ] `salon_owners` gains a `status`/`ended_at` column via an Alembic migration, and the Privacy Policy's claim-retention wording is updated back to a fixed 12-month-post-end target once this ships

---

### T-049 — Restrict origin server to Cloudflare IP ranges
**Priority:** P2 | **Owner:** OPS | **Estimate:** 1h | **Epic:** EPIC-09
**Dependencies:** None

**Description:** T-017's Privacy Policy review found that the origin server's ports 80/443 are reachable directly from the public internet, not only via Cloudflare (confirmed: `ufw status` inactive, no `iptables`/`nft` source-IP restriction, and live nginx access logs show scanner/bot traffic hitting the origin IP directly). This is a real security gap independent of the Privacy Policy wording fix (which now correctly states the origin "may also be technically reachable directly" rather than falsely claiming all traffic passes through Cloudflare).

**Acceptance Criteria:**
- [ ] Firewall rule (ufw or iptables) restricts inbound 80/443 to Cloudflare's published IP ranges (`https://www.cloudflare.com/ips/`)
- [ ] A documented process exists for updating the allowlist when Cloudflare rotates its IP ranges
- [ ] Deployed with a safe rollback plan (e.g. verify via a maintenance window, not a blind cutover) — a misconfigured rule here takes the entire site offline

---

### T-050 — Remove recipient-email logging from the Resend fallback path
**Priority:** P2 | **Owner:** BE | **Estimate:** 0.5h | **Epic:** EPIC-09
**Dependencies:** None

**Description:** `backend/app/services/email.py`'s no-API-key fallback path (`send_email`) currently prints the intended recipient's email address to stdout instead of sending the email (`print(f"[email] No API key — skipping: {template} to {to}")`). This is captured by Docker's default json-file logging driver, which has no configured size or rotation limit. T-017's Privacy Policy now discloses this behavior honestly rather than silently omitting it; this ticket is to fix the underlying behavior so the disclosure can eventually be removed from the policy.

**Acceptance Criteria:**
- [ ] The no-API-key fallback path no longer logs the recipient's full email address (log a redacted/hashed form, or omit the recipient entirely, if a log line is still useful for debugging)
- [ ] Docker's `beauty_api` logging driver has a configured `max-size`/`max-file` limit (currently unbounded) — separate, related hardening while touching this area
- [ ] Once fixed, update T-017's Privacy Policy (Section 10, Security) to remove the disclosure of this now-resolved behavior

---

### T-051 — Investigate beauty_web restart/OOM root cause
**Priority:** P1 | **Owner:** OPS/INFRA | **Estimate:** investigation only, no fix | **Epic:** EPIC-09
**Dependencies:** None
**Status:** ✅ Investigation completed (2026-07-20) — see `docs/06_ENGINEERING/T-051_MEMORY_OOM_INVESTIGATION.md` for the full RCA, live memory-profile experiment, Docker configuration audit, and mitigation comparison matrix. No fix implemented in this ticket, per explicit scope (evidence only).

**Headline finding:** the T-018 note's working assumption ("`beauty_web` OOM-killed by its 300MB limit") is **not supported by any available evidence** — zero kernel/cgroup OOM-kill events exist anywhere in the retained system logs for the entire relevant window, and the July 17 restarts were all clean `exitCode=0` exits, not kills. The exact trigger is now unrecoverable (the container's own logs no longer exist, having been recreated multiple times since). What **is** proven via a live reproduced worst-case build: a from-scratch `docker compose build --no-cache web` takes ~17m43s and pushes this 1.9GiB host to 90% RAM / 70% swap / load average 14+, while `beauty_web` itself — running the whole time — never used more than 25.6 MiB of its 300MB limit. The same build takes ~1m30s on GitHub Actions CI. The bottleneck is host-wide (unconstrained build process competing with ~1GB of already-committed container limits on 1.9GB total RAM), not `beauty_web`'s own configuration.

**Separate finding surfaced during this investigation (not fixed here — see T-052):** `beauty_crawler_worker` has been crash-looping continuously since its creation (2026-07-06) — 210+ restarts, still ongoing — due to a Redis authentication misconfiguration (`docker-compose.yml`'s `crawler_worker`/`crawler` `environment.REDIS_URL` hardcodes a passwordless URL that overrides `.env`'s correct password-bearing one). This means the Celery worker has never successfully consumed a single crawler task since deployment.

**Acceptance Criteria:**
- [x] RCA performed using real data only (journalctl, dmesg, docker inspect, docker events, cron/systemd audit) — no assumptions
- [x] Memory profile captured (idle/peak RSS for `beauty_web`, host-wide peak memory/swap/load average) via a live instrumented rebuild
- [x] Build profile captured (`npm ci`, `next build`, `node_modules` copy, image export each timed separately)
- [x] Docker configuration audited (memory limits, swap, restart policy, healthchecks, ulimits) for all 6 services
- [x] Mitigation options compared with pros/cons — nothing implemented
- [x] Production untouched: no restart, no compose change, no restart-policy change, no kernel/swap change (image was rebuilt for measurement purposes only, never deployed)

---

### T-052 — Fix beauty_crawler_worker Redis authentication crash loop
**Priority:** P1 | **Owner:** BE/INFRA | **Estimate:** 0.5h | **Epic:** EPIC-09
**Dependencies:** None
**Status:** ✅ Completed (2026-07-21) — reviewed, merged to `main`, deployed (only `crawler`/`crawler_worker` rebuilt and recreated; `web`/`api`/`db`/`redis` untouched), production-verified including a controlled end-to-end task run.

**Description:** `docker-compose.yml`'s `crawler_worker` and `crawler` services both hardcoded `environment.REDIS_URL: redis://redis:6379/0` (no password), which overrode the correct, password-bearing `REDIS_URL` supplied via `env_file: .env` (Compose's inline `environment:` always wins over `env_file` for the same key). Since `redis-server` runs with `--requirepass`, every connection attempt from these two services failed authentication.

**Confirmed via live logs (not assumed) — both services are affected identically:**
- `crawler_worker` (Celery worker): crash-looping since creation (2026-07-06), 210+ restarts, still ongoing at investigation time. Has never successfully processed a single task.
- `crawler` (the scheduler, running `celery beat` via `scheduler.py`'s subprocess wrapper): hits the identical `kombu.exceptions.OperationalError: Authentication required.` on every tick. Shows far fewer Docker-level restarts (13, not 210+) only because `scheduler.py` catches the subprocess failure and retries internally rather than letting the container itself exit — the underlying `celery beat` process is failing just as badly.

**Pre-fix inventory (mandatory before touching anything, per instruction):**
- Redis `celery` queue depth: **0** (`LLEN celery`). Only 3 keys exist total, all Kombu exchange/binding metadata — no actual task payloads. Since producers face the identical auth failure, nothing has ever successfully queued. **No backlog exists to flood after the fix.**
- `celerybeat-schedule` (the local persistent schedule-state file, bind-mounted from the host, GDBM/shelve format) has been continuously updated throughout — celery beat's own "last run" bookkeeping is intact and survives the restart loop. Celery's crontab-style `PersistentScheduler` fires an entry once when it next becomes due, not as a catch-up burst for missed periods — so no flood of "missed" runs is expected on restart. This is standard `PersistentScheduler` behavior, not independently verified by reading the shelve file's contents; it should still be watched directly during the post-deploy controlled test, not assumed with certainty.
- The beat schedule includes **cost-bearing external API calls**: `run_google` (~$9/run, monthly) and `run_google_full` (~$16/run, quarterly). The controlled post-deploy test task must be a free/harmless one (e.g., a lightweight non-Google spider or `send_daily_report`), never one of the Google Places jobs, to avoid an unintended charge during verification.
- `api` has the **identical-looking** hardcoded `REDIS_URL` bug (`docker-compose.yml`), but `backend/app/core/config.py`'s `redis_url` setting is dead code — never imported or used anywhere in the backend (same class of dead-config finding as T-014's `NEXT_PUBLIC_API_URL`). This is why `beauty_api` shows zero Redis errors despite an identical config pattern: nothing ever calls it. **Not fixed under T-052** (out of its narrow scope) — flagged here so T-033 (slowapi → Redis migration) fixes it at the same time it actually wires Redis into the API, rather than reintroducing this exact bug.

**Fix implemented:** removed the hardcoded `REDIS_URL` from both `crawler` and `crawler_worker`'s `environment:` blocks in `docker-compose.yml` so the correct value flows through from `env_file: .env`. No business logic changed. Verified via `docker compose config` that both services now resolve to the correct password-bearing `REDIS_URL`.

**Acceptance Criteria:**
- [x] `crawler_worker` and `crawler` no longer hardcode `REDIS_URL` in `docker-compose.yml`'s `environment:` block
- [x] Confirmed via `docker compose config` that both now resolve to the correct, password-bearing `REDIS_URL` from `.env`
- [x] Confirmed `crawler` (scheduler) was actually affected by the identical bug, not just `crawler_worker` — verified via live logs, not assumed
- [x] Confirmed Redis queue is empty before deploy — no backlog-flood risk
- [x] Both services connect to Redis successfully after redeploy — worker log: `Connected to redis://:**@redis:6379/0`; zero `Authentication required`/`NOAUTH`/`WRONGPASS` lines anywhere in either container's logs post-deploy
- [x] `RestartCount=0` on both containers, stable throughout the observation window (vs. 210+ and climbing before the fix)
- [x] One controlled, harmless test task (`send_daily_report`) ran successfully end-to-end post-deploy — task ID `661c5123-c085-402f-8871-d3930740d51c`: `received` → `succeeded in 10.9s`, external side effect (Telegram message) delivered exactly once, confirmed no duplicate, queue returned to 0, no `run_google`/`run_google_full` ever invoked
- [x] Beat schedule's pending due-dates: no action needed — confirmed empirically that Celery's crontab-style scheduler does not catch up on missed windows (two of today's own scheduled jobs, `vrisko-weekly` 02:00 and `xo-weekly` 04:00, had already passed while the system was broken and were correctly skipped rather than queued, matching pre-deploy inventory's theoretical expectation)

**Production verification (2026-07-21):** `crawler`/`crawler_worker` rebuilt (`docker compose build crawler crawler_worker`) and recreated (`docker compose up -d --no-deps crawler crawler_worker`) — `beauty_web`/`beauty_api`/`beauty_db`/`beauty_redis` uptimes confirmed unchanged throughout. Old (still-broken) containers briefly showed `ExitCode=137` during teardown — checked immediately via `journalctl -k`/`dmesg`, confirmed **not** an OOM (`OOMKilled=false`, zero kernel OOM events at that timestamp); this is normal Docker stop escalation (SIGTERM → 10s grace → SIGKILL) against a process that was mid-crash-loop when the recreate was issued, not a new incident. `celery -A beauty_crawler.celery_app inspect registered/active/reserved/scheduled` confirmed a clean slate before the controlled test; `inspect registered` confirmed `send_daily_report` and all crawler tasks correctly registered on the worker.

**Unrelated incident discovered during the controlled test, disclosed for transparency — see T-053:** the worker's HTTP client logged the full Telegram Bot API request URL, including the bot token, in cleartext at INFO level. Not part of T-052's scope; token value never repeated in this record, in commits, or in the diff. Immediate containment (token rotation via BotFather) and a permanent logging fix are tracked separately as **T-053**, filed as P0 Security.

---

### T-053 — Prevent secrets in crawler HTTP logs and rotate exposed Telegram token
**Priority:** P0 Security | **Owner:** BE/INFRA | **Estimate:** 1h (code fix) + manual token rotation | **Epic:** EPIC-09
**Dependencies:** None
**Status:** ✅ Completed (2026-07-21) — logging fix merged and deployed, token rotated by the user via BotFather, production-verified end to end.

**Incident record:**
```
Security Incident

Affected secret:      Telegram Bot Token
Exposure:              Container runtime logs (INFO-level HTTP request logging)
Public exposure:       No
Repository exposure:   No
Documentation exposure: No
CI exposure:            No (no plausible path; not independently verified via GitHub API)
Mitigation:             Token rotated via BotFather (user action, 2026-07-21)
Preventive fix:         Merged in T-053 (PR #43) — httpx/httpcore/urllib3/requests
                        pinned to WARNING via Celery's after_setup_logger signal;
                        RedactingFilter backstop for credential shapes in any
                        log record regardless of source
Status:                 Resolved
```
Note: this session's own tool-call transcript captured the old (now-revoked) token once, during T-052's live log inspection — disclosed for completeness in T-053's PR description; not independently fixable, and moot once the token was revoked.

**Incident summary:** during T-052's controlled production task, the crawler worker's HTTP client logged the full Telegram Bot API request URL — including the complete bot token, which Telegram's own Bot API design embeds directly in the URL path — in cleartext, at INFO level, to Docker's captured container logs. No token value is recorded in this entry, in any commit, diff, or test fixture.

**Root cause, confirmed by direct inspection (not assumed):** every one of `celery_app.py`'s 9 task wrappers (and most spider modules) calls `logging.basicConfig(level=logging.INFO)`. In practice this call is already a no-op by the time any task runs — Celery's own logging bootstrap (driven by the `--loglevel=info` flag in `docker-compose.yml`'s `command:`) has already attached a handler to the root logger before any task code executes, and `logging.basicConfig()` does nothing once `root.handlers` is non-empty. The real mechanism: Celery's `--loglevel=info` sets root's effective level to INFO, `httpx`'s internal logger (`httpx`/`httpcore`) has no explicit level of its own and inherits INFO by propagation, and httpx logs `"HTTP Request: {method} {url} ..."` at INFO by design — including any credential embedded directly in the URL.

**A second, structurally identical instance was found while investigating, currently latent (not yet triggered):** `crawler/beauty_crawler/spiders/facebook.py`'s Google Custom Search fallback passes its API key as a URL query parameter (`params={"key": api_key, ...}`) to `httpx.get(...)`, which would leak identically the moment it's configured. Checked directly: `GOOGLE_SEARCH_API_KEY`/`GOOGLE_CSE_CX`/`SERPER_API_KEY` are all currently unset in production `.env`, so this code path is presently inert. `FOURSQUARE_API_KEY` and `GOOGLE_PLACES_API_KEY` (both set) are passed via HTTP headers (`Authorization`, `X-Goog-Api-Key`), which httpx's default INFO-level request log does not include — confirmed not exposed by this mechanism. `DB_PASSWORD` is embedded in the SQLAlchemy connection URL (`models.py`) but SQLAlchemy's `echo` is not enabled, so it is not actively logged via that path.

**Fix implemented (`crawler/beauty_crawler/log_redaction.py`, new):**
1. `harden_logger()` pins `httpx`/`httpcore`/`urllib3`/`requests` loggers to `WARNING`, wired in via Celery's `after_setup_logger`/`after_setup_task_logger` signals (the correct hook for this Celery version — `after_setup_root_logger` does not exist in Celery 5.4, confirmed directly against the running container rather than assumed) in `celery_app.py`. This is the primary fix: the noisy request-level INFO logging never fires.
2. `RedactingFilter`, a `logging.Filter` attached to every handler on the Celery-configured logger, scrubs known credential shapes from any log record's final formatted message regardless of which logger produced it — a backstop for exception/error messages that could still embed a credential-bearing URL even at WARNING/ERROR level (e.g., `telegram_notify.py`'s own `logger.error("Telegram send error: %s", e)`, where httpx's exception `str()` representations typically include the full request URL). Covers: Telegram bot tokens in URL paths, `key=`/`api_key=`/`token=`/`access_token=` query parameters, `Authorization` header values, and `user:password@` credentials in `redis://`/`rediss://`/`postgres(ql)://` URLs.
3. `telegram_notify.py`: added a sanitized success log (`"Telegram request completed with HTTP %s", resp.status_code`) and fixed `send_daily_report()` unconditionally logging "Daily Telegram report sent" regardless of whether `send()` actually returned `True` — it now logs success/failure truthfully, matching what the redaction requirement implied should exist (real status, no raw URL).

**Not changed:** business logic, Telegram delivery behavior (verified via mocked tests — same `httpx.post` call, same arguments, same return semantics), Docker log rotation (flagged as a separate infra concern below, not implemented here per explicit scope).

**Tests added** (`crawler/beauty_crawler/test_log_redaction.py`, `test_telegram_notify.py`, 18 tests, all passing — run directly inside the crawler container against real dependencies): Telegram tokens (multiple distinct fake shapes, not one fixture) redacted from URL paths; `key`/`api_key`/`token`/`access_token` query parameters redacted; `Authorization` header values redacted; `redis://`/`postgresql://` embedded passwords redacted; sanitized status messages (e.g., "Telegram request completed with HTTP 200") pass through **unchanged** (redaction doesn't over-match); `RedactingFilter` never suppresses a record, only scrubs it; `harden_logger()` correctly pins noisy loggers and is idempotent (no duplicate filters on repeated calls); `send()`/`send_daily_report()` behavior (arguments, return values, real vs. fabricated success logging) verified unchanged via mocks, zero real network calls.

**Safe exposure review (counts/filenames only, no token value ever printed or repeated):**
- Current `beauty_crawler_worker` container log: 1 match (the known T-052 test occurrence)
- `beauty_crawler` (scheduler) log: 0
- Other/removed container log files on disk: 0 beyond the current container's own file (already counted above)
- `journald`: 0
- Crawler app log directory (bind-mounted): 0
- Root shell history: 0
- This repository's full history, all commits, all branches: 0
- `docs/.reviews/` diff artifacts: 0
- `/opt/backup` (DB dumps only, unrelated to app logs): 0
- Public `lookla-docs` repository, full history: 0 (verified directly via a fresh clone)
- CI logs: not independently verified via the GitHub API — no plausible exposure path exists, since the token was never part of any commit, diff, or workflow trigger; noted honestly as unverified rather than claimed

This session's own tool-call transcript (this conversation) also captured the full token once, when its logs were inspected live during T-052's verification — disclosed for completeness; not something retroactively fixable, but part of the honest exposure surface.

**Immediate containment — blocked on the user, coding agent has no Telegram/BotFather access:**
1. Revoke and regenerate the bot token via BotFather (user action required)
2. Update only the private production `.env` — recommend doing this directly via SSH so the token never enters this chat session at all, rather than pasting it here
3. Once done, the agent will recreate only `crawler`/`crawler_worker` (`docker compose up -d --no-deps --force-recreate crawler crawler_worker`, no rebuild needed for an `.env`-only change) and verify: old token invalid, new token delivers one controlled message successfully, new token does not appear in any newly generated log line

**Docker logging configuration audit (documented, not changed — a broader compose change belongs in its own infra ticket, consistent with T-050's existing unbounded-`beauty_api`-logs finding):** confirmed via `docker inspect` — `beauty_crawler_worker` uses the default `json-file` driver with an empty `Config` (no `max-size`/`max-file`); no `/etc/docker/daemon.json` exists, so no daemon-wide default either. Log growth is currently unbounded for every service on this host, not just the crawler.

**Acceptance Criteria:**
- [x] Exact logger/root cause identified via direct inspection, not assumed (Celery's `--loglevel` bootstrap + httpx's INFO-level request logging, not the red-herring `logging.basicConfig()` calls, which are already no-ops)
- [x] Third-party HTTP transport loggers pinned to WARNING in production
- [x] Redaction filter covers bot tokens, generic credential query params, Authorization headers, Redis/DB credential URLs — tested against multiple distinct fake values, not one fixture
- [x] Sanitized application-level status logging preserved/improved (real success/failure, no raw URL)
- [x] Application/Telegram-delivery behavior unchanged, verified via mocked tests
- [x] 18 new tests, all passing, run against real container dependencies
- [x] Safe exposure review completed — counts/filenames only, token never printed or repeated
- [x] Docker log rotation gap documented, not silently fixed under this ticket
- [x] BotFather token rotation — completed by the user directly in production `.env`, value never entered this session
- [x] Post-rotation production verification — see below

**Production verification (2026-07-21):** `crawler`/`crawler_worker` rebuilt (picking up T-053's code fix) and recreated with the new token — `beauty_web`/`beauty_api`/`beauty_db`/`beauty_redis` uptimes unchanged throughout, clean recreate with no stuck-container issue this time. `RestartCount=0` on both post-deploy. One controlled `send_daily_report` task run end-to-end: `received` → `succeeded in 17.9s`, log shows the new sanitized status line `Telegram request completed with HTTP 200` (no URL, no token) followed by a truthful `Daily Telegram report sent`; delivered exactly once (task ID appears exactly twice in logs — one `received`, one `succeeded`, not a repeat execution); queue returned to 0. Searched the entire fresh post-deploy log history on both containers for the pattern `/bot[0-9]` (a live token embedded in a URL path would match this): **zero matches on either container.** Zero Redis-auth-error lines anywhere in either log. No `run_google`/`run_google_full` ever received or executed. Old (revoked) token's invalidity is guaranteed by BotFather's `/revoke` semantics — not independently re-tested here, since the agent never retained the old token value to test with by design.

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
| T-051 Investigate beauty_web restart/OOM root cause | P1 | OPS/INFRA | investigation only | EPIC-09 | — |
| T-052 Fix crawler_worker Redis auth crash loop | P1 | BE/INFRA | 0.5 | EPIC-09 | — |
| T-053 Prevent secrets in crawler HTTP logs + rotate Telegram token | P0 Security | BE/INFRA | 1 (+ manual rotation) | EPIC-09 | — |
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
T-009 ✅ → T-010 ✅        [booking stubs removed → contact CTAs]
T-024 ✅ → T-011 ✅        [API owner_claimed field → badge fix]
T-012 ✅                  [review labels — independent]
T-026                     [backup cron — independent]
T-030                     [critical tests — before changing those functions]
```

*T-003a removed from P0 critical path. Status: Verified — Deferred. See T-037 (post-MVP).*

**All P0 tasks complete → Pre-launch gate → Manual QA J-01/J-02/J-03 → M-01 Launch**

---

*Last updated: 2026-07-09*
