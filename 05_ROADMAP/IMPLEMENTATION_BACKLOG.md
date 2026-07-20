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

### T-042 — Distinguish Reviews empty and API error states
**Priority:** P2 | **Owner:** FE | **Estimate:** 1h | **Epic:** EPIC-09
**Dependencies:** None

**Description:** `SALON.md` documents two distinct states for the Reviews section — "No reviews available" (empty) and "Could not load reviews" with a retry link (API error) — but the current `useLazySection` hook in `SalonDetailClient.tsx` doesn't distinguish them: a failed fetch is caught and treated identically to a genuinely-empty result (`.catch(() => setLoading(false))`, leaving `data` as `[]`). In practice, the whole Reviews section (including its heading) renders nothing at all in either case — neither documented empty-state message actually appears. Found during T-012's implementation (its `googleReviewsSourceLabel` disclosure correctly stays hidden in both cases, since it only checks `reviewCount > 0`, but that's a side effect of the same missing error state, not a fix for it).

**Acceptance Criteria:**
- [ ] `useLazySection` (or a similar mechanism) tracks a distinct error state, not just loading/data
- [ ] Zero reviews (genuine empty result) shows "No reviews available"
- [ ] Failed reviews fetch shows "Could not load reviews" with a retry link
- [ ] Same distinction applied to Services, which shares the identical `useLazySection` hook and has the same gap (`"Service information not available"` per `SALON.md`, also not currently implemented)
- [ ] T-012's `googleReviewsSourceLabel` disclosure still stays hidden in both states

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
