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

### T-056 — Search Return-State Restoration (SQC-01A)
**Priority:** P0 (fourth ticket of the SQC-01A UX-foundation phase) | **Owner:** FE | **Epic:** EPIC-09
**Dependencies:** T-015 ✅ Product analytics, T-042 ✅ Unified async states, T-054 ✅ Search context and filter recovery, T-055 ✅ SalonCard hierarchy and click targets
**Status:** ✅ Completed. Merged via PR #53 (approved after the hard-reload-invariant review round), deployed to production (`beauty_web` rebuilt and restarted alone — no other service touched), live production verification passed.

**Problem, measured in production before implementation:** infinite scroll loads additional pages of search results; opening a salon card and pressing browser Back re-mounts the search page from scratch — page 1 only, scroll reset to top. Measured example: 48 loaded cards + `scrollY≈4088` before navigating away → 24 cards + `scrollY≈133` after Back. This penalizes exactly the users who explored deepest and were closest to converting (Search → Salon → back to browsing).

**Goal:** when returning via browser Back from a salon detail page, restore the same already-loaded cards, pagination state, canonical total, active filters/view (already free via existing URL persistence), and approximately the same scroll position — without touching backend, database, ranking, the search API contract, analytics taxonomy, or SalonCard.

**Storage mechanism — deliberately NOT sessionStorage:** the public Cookie Policy (`app/[locale]/cookies/content.ts`, all 4 locales, section 1) states "Lookla does not use any other form of browser storage (localStorage, sessionStorage)" — a factual claim already published and previously verified against the running site. Using sessionStorage for this ticket would have made that claim false without a docs update, which is out of this ticket's scope. Instead: an in-memory (module-scope `Map`) cache in `frontend/lib/searchReturnState.ts`, keyed by a per-history-entry id merged into `history.state` under a namespaced `__lookla` field (never replaces `history.state` wholesale — Next.js's own router state is preserved via spread). This satisfies every invalidation rule for free: a hard reload or a new tab starts a fresh JS realm with an empty cache (confirmed empirically: `window`-level state was directly verified to persist across a real search→detail→back round trip within the same tab, but not across a reload).

**History-entry identity:** `ensureEntryId()` reads `history.state.__lookla.entryId`; if present, reuses it (idempotent); if absent, generates one (`crypto.randomUUID()`, with a fallback) and merges it in via `history.replaceState`. A dedicated effect (`page.tsx`) keeps a `currentEntryIdRef` in sync with the CURRENT entry, keyed on `[view, area, city, q, category, minRating, locale]` — deliberately including `view`, even though it doesn't affect the search key, because every `update()` call (including a bare list/map toggle) uses `router.push`, which always creates a genuinely new history entry; a save made after such a toggle must be attributed to that new entry, not a stale one from before it (found via direct reproduction — see Map boundary below).

**Snapshot contract:** `SearchReturnSnapshot { version: 1; createdAt; entryId; searchKey; locale; view; salons; currentPage; hasMore; total; scrollY }`. `searchKey` is derived from `{area, city, q (trimmed), category, minRating}` — the same fields `buildParams()` sends to `/api/salons`, minus pagination; excludes `view` (list/map share the same underlying list identity) and any tracking parameter. `isValidSnapshot()` enforces: exact version match, `createdAt` within a 30-minute TTL and not in the future, locale in the 4 supported values, `view` is `'list'|'map'`, `salons` is an array of ≤500 well-shaped items (id: number, name: string), `currentPage ≥ 1`, `hasMore` boolean, `total`/`scrollY` finite non-negative numbers. Any failure discards the snapshot silently — never a UI error, never a thrown exception (`saveSnapshot`/`getValidSnapshot` are both wrapped, matching the existing codebase's defensive style).

**Save timing:** a single `useEffect(() => { return () => {...} }, [])` in `page.tsx` — the unmount cleanup fires identically whether the user left by mouse click, keyboard Enter, or any other navigation away, since both go through SalonCard's one existing `<Link>` (zero SalonCard changes, no second click handler). Reads the latest state via a ref (`latestForSaveRef`, kept current by a no-deps effect that runs after every render — an effect cleanup's closure would otherwise see stale values from mount time). scrollY comes from a separately-tracked `scrollYRef`, not a live `window.scrollY` read at cleanup time — **found necessary via direct instrumentation**: Next.js fires its own "scroll to top on navigation" as a real native `scroll` event (scrollY=0) on the OLD page as a navigation begins, strictly before the component unmounts. A passive `scroll` listener alone still gets clobbered by that later event; the actual fix is a document-level, capture-phase `click` listener that (a) freezes `scrollYRef` at the true pre-navigation position the instant a click on a salon-card link is detected (capture phase fires before Next's own Link handler even starts), and (b) sets a `frozen` flag that stops the passive listener from writing anything further, so Next's later scroll-to-top event can no longer overwrite the frozen value before save time.

**Restore timing — zero-flash:** `salons`/`total`/`loading`/`pageRef`/`hasMoreRef`/pending-scroll are all seeded via lazy `useState`/`useRef` initializers from a `useMemo(() => {...}, [])`-computed `initialSnapshot`, evaluated once for this component instance's very first render. This is hydration-safe by construction, not by luck: a matching snapshot can only exist in the in-memory cache after at least one prior save within the same JS realm, which by definition happens strictly after the one-time SSR/hydration pass on first page load (the cache starts empty every time a JS realm is created) — so the very first hydration-matching render can never see a snapshot, and there is nothing to mismatch against server-rendered HTML. A `skippedInitialRestoreRef` guard prevents the follow-up "restore-or-fetch" effect from redundantly re-applying what the lazy initializers already did on that same first run; from the second run onward (a genuinely new identity reached without an unmount — e.g. a same-instance back/forward hop between two distinct filter states) it makes its own restore-or-fetch decision. Scroll restoration fires at most once (`pendingScrollRestoreRef` nulled before the `scrollTo` call, guarding against a re-render during the async `requestAnimationFrame` callback), deferred one frame so the restored cards have already painted (correct document height), using `behavior: 'auto'` — never animated.

**Invalidation:** a fresh visit, hard reload, new tab, filter change (area/city/q/category/min_rating), or locale change all naturally compute either no cached snapshot (empty cache) or a non-matching `searchKey`/`locale`, falling through to the exact same `loadSalons()` fresh-fetch path that existed before this ticket — no new code branch for "invalidate," it falls out of the existing identity-matching logic.

**Pagination continuation:** `pageRef.current`/`hasMoreRef.current` are restored directly from the snapshot, so `loadMore()`'s existing `pageRef.current + 1` computation naturally continues from the correct page — no changes to `loadMore()` itself, no backend pagination semantics touched.

**Map boundary (Step 8):** `loadMapSalons`/`MapView` are completely untouched — map has no pagination concept to lose in the first place (single unfiltered fetch), and `view=map` already survives Back/Forward via the existing URL mechanism with zero new code. One genuine bug found and fixed during implementation: switching to `view=map` (a same-route `router.push`, no unmount) created a real new history entry that never got its own tracked id, so a save made after departing from map view was attributed to a stale entry the user could never actually return to — fixed by the dedicated `currentEntryIdRef`-tracking effect described above. Separately, and **not fixable within this ticket's scope**: `components/MapView.tsx`'s marker-popup "view salon" link is a plain `<a href>`, not a Next.js `<Link>` (pre-existing, predates T-056 entirely — confirmed via `grep`, no `next/link` import in that file at all). Clicking it causes a full hard browser navigation, which destroys the JS realm — and with it, any in-memory snapshot — before the save-on-unmount cleanup can survive it; confirmed via direct instrumentation (a page-global set on the search page was already gone by the time the destination page loaded, unlike every other navigation path tested, which reliably preserved it). No client-side approach (including sessionStorage) can restore state across a hard navigation by design. The correct, verified behavior for this one path is a safe fallback to the same fresh page-1 load a first-time visitor gets — confirmed via Playwright (24 cards, zero console errors) — not silent corruption or a crash. Fixing MapView's link type is out of scope here and belongs to the already-deferred, separate map-accessibility candidate.

**Analytics invariants:** zero new `trackEvent` call sites; the only 5 pre-existing T-015 event names appear anywhere in `page.tsx`; `salon_open` is fired exclusively by SalonCard's own `handleOpen` (this file never calls it directly for the list view); no internal identifier (`entryId`/`searchKey`/`snapshot`/`scrollY`) ever appears inside a `trackEvent(...)` call; `search_results_view` continues to gate on the exact same `loading`/`searchError`/`total`/`mapLoading`/`mapError` state variables as before — restoration reuses those variables directly, so it naturally participates in the pre-existing "fires once per materially distinct state" contract with no new code, and (per the ticket's own explicit allowance) may legitimately fire once more on a genuine return-navigation, exactly as it already did before this ticket for any state change.

**Accessibility:** no new `aria-live` regions (all 3 pre-existing `polite` regions and 2 pre-existing `assertive` regions are unchanged in count); restoration never calls `.focus()` on anything.

**Verification:** 581/581 frontend tests passing (77 new for T-056 — direct execution against real `history`-object mocks for `ensureEntryId`/`getValidSnapshot`/`saveSnapshot`/`computeSearchKey`/`isValidSnapshot` in `lib/searchReturnState.test.ts`, plus source-wiring regression tests in `app/[locale]/search/searchReturnRestoration.test.ts` covering save timing, scroll tracking, restoration sequence, invalidation, the map boundary, analytics invariants, accessibility, and the documented MapView limitation). `npm run lint` and `npm run build` both clean, no new warnings.

**Isolated production verification:** built and ran the actual `next build` standalone production output on a throwaway port, proxying to the real backend API. Root-caused two real bugs during this pass, both fixed and re-verified (not merely asserted from code review): (1) the Next.js scroll-to-top-on-navigation race described above, fixed via the capture-phase click freeze; (2) the `view=map`-toggle stale-entry-id bug described above, fixed via the dedicated tracking effect. Final clean run: all 8 primary scenarios (mouse click, keyboard Enter, 320px, 375px, and all 4 locales) passing every check — 48/48 cards restored with identical order, scroll restored to an exact pixel match (0px diff, measured against the same click-time baseline the product code itself uses), zero duplicate `page=1` fetches, zero console/page errors, correct next-page continuation, zero duplicate cards. The `view=map` boundary scenario confirmed both the URL-preservation fix and the safe MapView-hard-navigation fallback. One transient `/api/salons/map` 500 (host memory pressure under the unfiltered 2000-marker query, matching the standing, previously-documented host-resource-constraint pattern from T-014/T-051) was observed and is unrelated to this ticket's code — retried cleanly.

**Hard-reload invariant — explicit review round:** independent review correctly identified that the deliverables hadn't explicitly proven "hard reload must not restore a stale snapshot" as its own scenario, distinct from a fresh visit. Reproduced exactly as requested against the isolated standalone build: load 48 cards → open a salon → Back (confirms 48 restored, `history.state.entryId` recorded) → `page.reload()` → confirms exactly 24 cards (fresh page 1, not the stale 48), confirms a real `/api/salons?...page=1` request actually fired, confirms `history.state.entryId` is **unchanged** across the reload (the reviewer's premise about `history.state` surviving a reload is correct) yet restoration still correctly did not happen — because the in-memory `Map` the snapshot itself lives in does not survive the reload's fresh JS realm, unlike `history.state` (a separate, browser-native mechanism) or `sessionStorage` (deliberately not used — see Storage mechanism above). Matching identity alone was never what protected against reload; the storage mechanism is the actual load-bearing guarantee, now stated explicitly rather than left implicit. Additionally confirmed: the snapshot is retained (not deleted) after a successful restore — `Back → Forward → Back` restores correctly both times; visiting a second, different salon from an already-restored list still restores correctly on a subsequent Back. Added structural regression tests (`lib/searchReturnState.test.ts`) asserting no `sessionStorage`/`localStorage` reference exists anywhere in the actual code (only in the explanatory comment) and that the cache is a plain module-scope `Map` — guarding this exact property against a future silent regression. (A unit-test-level simulation of "a fresh JS realm" via a cache-busted dynamic `import()` was attempted first but abandoned: Node/`tsx`'s module loader resolved the cache-busted specifier back to the same underlying module instance, so it could not faithfully reproduce real reload isolation — the actual browser reproduction above is the authoritative proof, not a unit test standing in for it.) This ticket does not use `performance.getEntriesByType('navigation')` or any navigation-type detection at all — the design doesn't need to distinguish Back from reload by navigation type, since it relies purely on the realm-scoped lifetime of the in-memory cache, which is unaffected by that question either way.

**Live production verification (`https://lookla.gr`, post-deploy):** ran the measured scenario directly against production — 24 initial cards → scroll to load 48 → open a salon (index 30) → Back → hard reload. All checks passed, repeated across 5 separate runs for stability: 48/48 cards restored in identical order; scroll restored to an exact 0px diff against the true click-time baseline (`atClick=2728, after=2728`); zero duplicate `page=1` requests during restoration; exactly one `salon_open` gtag() call fired on open (`{salon_id, source: "search_list", locale}` — no leaked identifiers); Back fired zero synthetic `salon_open` calls and no event fired more than once; further load-more correctly requested `page=3` (continuing from the restored page); hard reload after a successful restoration correctly showed a fresh 24-card page 1 with a real `page=1` request fired — confirming the hard-reload invariant holds in production, not just the isolated build; no horizontal overflow at any point.

Two findings during this pass, both investigated to a root cause and confirmed **not** T-056 regressions:
1. `search_results_view`/`page_view` re-fire on every Back restoration. Traced to `page.tsx`'s pre-existing T-015 `lastTrackedSearchKey` dedup ref, which resets on any component remount — Back has always caused a full remount (even pre-T-056, when it also always re-fetched page 1 from scratch), so this dedup-reset-on-remount behavior predates this ticket entirely and is unchanged by it. The event now reports a bucket matching the actual 48-card restored state the user sees, which is arguably more accurate than the old pre-T-056 behavior (which would have reported a bucket for a transient, not-yet-scrolled 24-card page 1).
2. Intermittent `Failed to fetch RSC payload for .../[other-salon]... Falling back to browser navigation` console errors, reproduced on some but not all runs. Root-caused via timestamped instrumentation: these fire during rapid further-scrolling immediately after a 48-card single-shot restoration render, and do **not** occur on a fresh visit scrolled to the same or greater card count (72 cards, zero errors) — the difference is that restoration mounts 48 `<Link>` elements in one synchronous render (vs. gradual incremental mounts during normal scrolling), which can produce a burst of simultaneous Next.js Link-prefetch requests on this memory-constrained host. This is Next.js's own internal, self-documented graceful-degradation path (prefetch failure falls back to a normal browser navigation — confirmed navigation always still succeeded immediately after in every run) — not a hydration error, not a thrown exception, and no T-056 file is involved in Next's prefetch subsystem. Logged here as a known, minor, non-blocking characteristic rather than silently omitted; a possible future follow-up (unrequested, not started) would be batching/staggering the restored card list's mount to smooth this out.

**Acceptance Criteria:**
- [x] Back restores loaded results (card count, order) and pagination/`hasMore` state
- [x] Back restores approximately the same scroll position (verified to an exact match against the true click-time baseline)
- [x] Fresh visits, hard reloads, new tabs, filter changes, and locale changes all still start from page 1 — no stale-state leakage
- [x] Pagination continues from the correct next page after a restoration, with no duplicate or missing cards
- [x] `view=map` preserved through the existing URL mechanism; no new map-state cache; map's own pagination-free fetch untouched
- [x] No backend/database/ranking/API/URL-contract/GA4-taxonomy changes; SalonCard untouched
- [x] No sessionStorage/localStorage — in-memory only, consistent with the published Cookie Policy
- [x] Isolated production verification — 8/8 primary scenarios passing every check, plus the documented map-boundary safe fallback (see above)
- [x] Live production verification — passed on `https://lookla.gr`, 5/5 runs, see above
- [x] Independent review — approved (PR #53, after the hard-reload-invariant review round)

---

### T-057 — Search Controls Accessibility & Mobile Operability (SQC-01A)
**Priority:** P0 (fifth ticket of the SQC-01A UX-foundation phase) | **Owner:** FE | **Epic:** EPIC-09
**Dependencies:** T-042 ✅ Unified async states, T-054 ✅ Search context and filter recovery, T-055 ✅ SalonCard accessibility, T-056 ✅ Search return-state restoration
**Status:** ✅ Completed. Merged via PR #54 (approved after the `aria-haspopup` review round), deployed to production (`beauty_web` rebuilt and restarted alone — no other service touched), live production verification passed.

**Goal:** fix known accessibility and mobile-operability defects in the primary search controls — query input, submit, clear-query, filter popover trigger/lifecycle, List/Map switch, touch-target sizing — without touching search behavior, ranking, the API contract, filters, or map markers.

**Ownership inventory (Step 1):** all affected controls live entirely in `frontend/app/[locale]/search/page.tsx` (`SearchContent`). Query state comes from `useSearchParams()` (`q`, `area`, `city`, `category`, `min_rating`, `view`); URL mutation goes through the existing `update()`/`removeQueryFilter()`/`buildAreaUrlParams()` helpers (T-054's `lib/searchContext.ts`), untouched. `frontend/components/SearchFilters.tsx` (53 lines) confirmed still dead code — zero importers anywhere in the tree — left untouched per the ticket's own instruction not to refactor unrelated dead code.

**Search form (Step 2):** the query input and submit button are now wrapped in a single `<form role="search" onSubmit={handleSearchSubmit}>`. The old dual-path submission (`onKeyDown` for Enter + `onClick` for the button) is gone — native form submission (Enter or the `type="submit"` button) both funnel through one handler, so exactly one navigation fires per submission, never two. `handleSearchSubmit` calls `e.preventDefault()` (no full-page browser navigation) and trims the value before comparing against the current (also-trimmed) `q`, matching the canonical query form T-054's `deriveActiveFilters` and T-056's `computeSearchKey` already assume — submitting an unchanged query is a no-op, no redundant history entry.

**Accessible names (Steps 3–4):** the input has a real, visually-hidden `<label htmlFor="search-query-input">` (new `search.search_label` key, "Search salons" / localized) — independent of the placeholder, which remains present but is no longer the only naming source. The submit button's decorative 🔍 is wrapped in `aria-hidden="true"`; the button itself carries `aria-label={t('search_submit')}`.

**Clear-query (Step 5):** a new `type="button"` clear control (new `search.clear_search` key) renders only when `q.trim()` is non-empty — driven by the same URL-derived `q` the existing "query" active-filter chip already uses, so the two never disagree. Reuses T-054's `removeQueryFilter()` verbatim (deletes only `q` and `page`, preserving `area`/`category`/`min_rating`/`view`). Clears the input's value directly and refocuses it synchronously — safe because a searchParams-only navigation never unmounts this component (confirmed by T-056's own restore-or-fetch design), so there's no need for the effect-based focus-recovery pattern T-054's chip removal required. No new GA event; raw query is never read into the handler at all.

**Filter popover (Steps 6–7):** trigger now exposes `aria-expanded={filtersOpen}` and `aria-controls` pointing at a `useId()`-generated id (React 18, SSR-safe, collision-free across instances). **Review-round correction:** the first implementation also added `aria-haspopup="true"`, reasoned (incorrectly) as a generic "opens a popup" signal distinct from `"dialog"`/`"menu"`/`"listbox"`. Independent review correctly identified that per the WAI-ARIA spec, `aria-haspopup="true"` is *defined* as exactly equivalent to `aria-haspopup="menu"` — there is no generic/neutral value in this attribute's vocabulary. Since the filter panel is a plain group of form controls (a `<select>`×3 and a clear button, no menuitems, no roving-tabindex/arrow-key navigation), claiming `"true"`/`"menu"` would misrepresent it to screen readers as a menu widget. Fixed by removing `aria-haspopup` entirely — `aria-expanded` + `aria-controls` alone is the correct, spec-accurate pattern for a non-modal disclosure/panel toggle that isn't a true popup-widget button. The popover panel itself gets `role="group"` and a new `search.filters_region_label` key. Escape closes the popover and returns focus to the trigger via a **dedicated** `keydown` listener, deliberately separate from the pre-existing outside-click `mousedown` listener — different event types can't race each other. Escape never mutates a filter value, never calls `router.push`/`update()`, never fires an event. Outside-click deliberately does **not** force focus anywhere (the user is already interacting with whatever they clicked) — only the Escape path moves focus.

**List/Map (Step 8):** kept as plain toggle buttons (not converted to a tabs pattern, which would need `role="tablist"`/`role="tab"`/`aria-selected`/arrow-key handling — none of which the real implementation has). Both buttons now carry `aria-pressed` bound to `view`. Selecting the already-active view is now a guarded no-op (`view !== 'list' && update(...)`) — no redundant `router.push`, no redundant history entry, no redundant fetch.

**Touch targets (Step 9):** measured before (375px): Search 41×36, Filter 42×34, List 65×36, Map 75×36 — all short of 44px height. After: query input/submit/clear are all `h-11`/`w-11` (44px); filter trigger and List/Map get `min-h-[44px] min-w-[44px]`. No target overlap, no horizontal overflow at 320/375px (verified — see below). Purely additive sizing/padding changes — no broader visual redesign.

**Localization (Step 10):** 5 new keys per locale (`search_label`, `search_submit`, `clear_search`, `open_filters`, `filters_region_label`) added to all 4 locale files (el/en/ru/uk) — verified non-empty, distinct from the pre-existing `placeholder` key, and distinct from the English strings in the other 3 locales (no untranslated fallback).

**Analytics invariants (Step 11):** zero new `trackEvent` call sites anywhere in the affected controls — verified by regex-scanning every `trackEvent(...)` call in the file against the fixed 5-name T-015 allowlist. None of `search_cleared`/`filter_opened`/`view_switched`/`filter_closed` were introduced. `search_results_view` continues to gate purely on the pre-existing `loading`/`searchError`/`total`/`mapLoading`/`mapError` state, untouched by this ticket — form submission, clear-query, filter-popover open/close, and Escape none of them call `trackEvent` directly.

**T-056 compatibility (Step 12):** the filter popover's open/closed state is never written into a `SearchReturnSnapshot` (no `filtersOpen` field, verified by inspecting the exact `saveSnapshot({...})` call site). Opening/closing the popover never touches `currentEntryIdRef` or calls `ensureEntryId()`. List/Map still funnels through the same `update()` → `router.push()` path T-056's entry-id-tracking effect already watches (`view` remains in that effect's own deps, unmodified) — no snapshot-schema change was needed or made.

**Verification:** 635/635 frontend tests passing (51 new for T-057 in `app/[locale]/search/searchControlsA11y.test.ts`, covering form semantics, clear-query, popover keyboard lifecycle, List/Map `aria-pressed`, touch-target class assertions, localization, analytics invariants, and T-054/T-055/T-056 non-regression). `npm run lint` and `npm run build` both clean, no new warnings. One pre-existing T-056 regression test (`restoration never calls .focus() on anything`) initially collided with the new Escape-focus-return code purely because of source-file ordering (both fell inside the same slice boundary) — resolved by relocating the new Escape effect later in the file (a pure reordering, zero behavior change), not by weakening the T-056 test.

**Isolated production verification:** built and ran the actual `next build` standalone output on a throwaway port. All 4 locales × {desktop, 320px, 375px, 768px} passing every check: `role="search"` landmark resolvable exactly once; query input and submit button resolvable by computed accessible name; Enter submits exactly once (one `/api/salons` request); clear-query removes `q` from the URL while preserving other params, empties the input, keeps focus in the input, and disappears once empty; filter trigger's `aria-expanded` toggles correctly for both mouse and keyboard (Enter) activation, `aria-controls` resolves to a real rendered element; Escape closes the popover and returns focus to the trigger; outside-click closes without forcing focus; List/Map `aria-pressed` flips correctly, URL contract (`view=map`) holds, a redundant click on the already-active view causes no URL change, browser Back restores the previous view; all 5 measured touch targets are ≥44×44px; no horizontal overflow at 320/375px; zero console/page errors throughout. A dedicated T-056 integration scenario (load 48 cards → open a salon → Back → use the filter trigger) confirmed restoration still works unchanged and all controls remain fully operational post-restoration.

**Safety checklist:** Backend changed: No. Database changed: No. Search API changed: No. Ranking changed: No. New filter added: No. Map-marker behaviour changed: No. Public URL contract changed: No. New GA4 event added: No. Existing GA4 event renamed: No. Raw query sent to analytics: No. Search input has accessible name: Yes. Search landmark present: Yes. Submit button has accessible name: Yes. Clear-query control present when needed: Yes. Filter expanded state exposed: Yes. Escape closes filter popover: Yes. Focus returns correctly after Escape: Yes. List/Map active state exposed: Yes. All primary controls at least 44×44: Yes. T-056 restoration preserved: Yes. Production touched before review: No. PM2 used: No. `crawler/celerybeat-schedule` touched: No. Dependabot changes mixed into branch: No.

**Acceptance Criteria:**
- [x] Search region discoverable via `role="search"`; input and submit button resolvable by computed accessible name in all 4 locales
- [x] Enter and button click each submit exactly once; no duplicate navigation/fetch; unchanged query is a no-op
- [x] Clear-query control appears only when a query is applied, removes only `q`+`page` (preserves other filters/view), keeps focus in the input
- [x] Filter trigger exposes `aria-expanded`/`aria-controls` (no `aria-haspopup` — removed in review round, see above); popover exposes `role="group"` with a localized label
- [x] Escape closes the popover, returns focus to the trigger, mutates nothing, fires no navigation/event
- [x] Outside-click still closes the popover without forcing focus
- [x] List/Map expose `aria-pressed`; redundant re-selection of the active view causes no navigation; Back still restores the correct view
- [x] Search submit, clear-query, filter trigger, List, and Map all measure ≥44×44px; no overlap, no horizontal overflow at 320/375px
- [x] Zero new GA4 events; `search_results_view`/`salon_open`/`area_select` behavior unchanged
- [x] T-056 return-state restoration unaffected — regression-verified both in unit tests and an isolated Playwright integration scenario
- [x] Isolated production verification — 4 locales × 4 breakpoints, all checks passing (see above)
- [x] Live production verification — passed on `https://lookla.gr`, 4 locales × 4 breakpoints, see below
- [x] Independent review — approved (PR #54, after the `aria-haspopup` review round)

**Live production verification (`https://lookla.gr`, 2026-07-27):** ran the full isolated-verification scenario directly against production (4 locales × {desktop, 320px, 375px, 768px}, plus the T-056 integration scenario), with the `lookla_consent` cookie pre-granted and `gtag()` calls intercepted at the JS layer (raw `collect?` network sniffing is unreliable for this — see the T-056 production-verification note on GA4 batching delay). All checks passed: `role="search"` landmark resolvable once per page; input/submit resolvable by localized accessible name in all 4 locales (confirmed literal strings: "Αναζήτηση" / "Search" / "Поиск" / "Пошук"); Enter submits exactly once (exactly one `/api/salons` request); clear-query removes only `q`, keeps focus in the input, disappears once empty; filter trigger confirmed to have **no `aria-haspopup` attribute at all** (the review-round fix, explicitly asserted); `aria-expanded` cycles `false → true → false` correctly for mouse and keyboard; `aria-controls` resolves to a real rendered `role="group"` panel; Escape closes and returns focus to the trigger; outside-click closes without forcing focus back; List/Map `aria-pressed` flips correctly, a redundant click on the already-active view causes no URL change, browser Back restores the previous view; all 5 measured targets ≥44×44px; no horizontal overflow at 320/375px; zero console/hydration errors. Analytics invariants re-verified live: no `search_cleared`/`filter_opened`/`view_switched`/`filter_closed` events; every fired T-015 product event is one of the 5 approved names; no raw query text in any product-event payload (T-014's separate `page_view` infra event — which legitimately includes the full path+query string by design, unrelated to T-015's narrower product-event contract — was correctly excluded from this check after an initial test-script false positive). T-056 integration scenario confirmed restoration (48/48 cards) and full control operability still hold in production after this ticket's changes.

---

### T-058 — Prevent Duplicate Search Results Analytics on Back Restoration
**Priority:** P0 (analytics data-quality cleanup, prerequisite for SQC-01B baseline collection) | **Owner:** FE | **Epic:** EPIC-09
**Dependencies:** T-014 ✅ GA4 infrastructure, T-015 ✅ Product analytics events, T-054 ✅ Search results context, T-056 ✅ Search return-state restoration, T-057 ✅ Search controls accessibility
**Status:** ✅ Completed. Merged via PR #55, deployed to production (`beauty_web` rebuilt and restarted alone — no other service touched), live production verification passed.

**Problem:** returning via browser Back from a salon detail page correctly restores the search results (T-056), but also re-emitted `search_results_view` for the exact same result state the user had already seen. Root cause: `page.tsx`'s T-015 dedup state (`lastTrackedSearchKey`) was a component-local `useRef`, reset to `null` on every remount — and Back has always remounted the search page (true before T-056 too, when Back also always re-fetched from page 1). Not a UX defect and not a T-056 regression, but it inflates `search_results_view` counts and distorts the Search→Salon CTR denominator SQC-01B's ranking work will depend on.

**Event lifecycle inventory (Step 1):** `search_results_view` is owned by a single `useEffect` in `page.tsx`, gated on `[view, loading, searchError, total, mapLoading, mapError, mapSalons.length, area, locale]`, firing only when `!loading && !searchError` (list) or `!mapLoading && !mapError` (map) — timing was already correct pre-T-058 (never fires while loading, never on error, never with a stale total, since `total`/`loading` are seeded together atomically by T-056's lazy initializers on a restoration). The only defect was WHERE the "already reported" memory lived.

| Scenario | Component mount | Data source | Old dedup state | Event before T-058 | Event after T-058 |
|---|---|---|---|---|---|
| Fresh direct search | fresh | list fetch | ref (empty) | fires once | fires once |
| Query change | same instance | list fetch | ref (same instance) | fires once | fires once |
| Area change | same instance (new history entry) | list fetch | ref (same instance) | fires once | fires once |
| List → Map | same instance (new history entry) | map fetch | ref (same instance) | fires once | fires once |
| Salon open → Back | **remount** | T-056 restored snapshot | ref reset → **fires again (bug)** | fires again (bug) | **suppressed** |
| Back to a different search state | remount | T-056 restored snapshot or fresh fetch | ref reset | fires (correct, different key) | fires (correct — different entry, no prior record) |
| Forward to salon → Back again | remount | T-056 restored snapshot (still valid) | ref reset → fires again | fires again (bug) | **suppressed** (same entry, same key already recorded) |
| Hard reload | fresh JS realm | fresh fetch | ref (empty), fresh realm | fires once | fires once (dedup store also realm-scoped, empty) |
| API error → Retry success | same instance | list fetch | ref (same instance) | fires once (only on success) | fires once (unchanged) |

**Canonical event identity (Step 2):** unchanged — reused `buildSearchResultsViewKey(area, bucket, view, locale)` and `bucketResultCount(total)` from `lib/analytics.ts` verbatim, no new key format invented. Never includes raw query, exact count, scroll position, page number, salon IDs, or the history-entry id.

**Dedup ownership (Step 3):** moved the "already reported" memory to a new, deliberately separate module, `frontend/lib/searchResultsViewDedup.ts` — a small in-memory `Map<entryId, materialKey>` (same realm-scoped invalidation rationale as T-056's snapshot cache: wiped on hard reload/new tab, never sessionStorage/localStorage/cookies). `hasReportedSearchResultsView(entryId, key)` / `markSearchResultsViewReported(entryId, key)`, bounded at 500 entries (oldest evicted first) so a very long single-tab session can't grow it unboundedly. The tracking effect now does a **two-layer check**: the original `lastTrackedSearchKey` ref first (cheap same-mount short-circuit, unchanged), then the entryId-scoped store (the actual T-058 fix — survives a T-056 restoration remount, which resets the ref but never touches the store). `entryId` comes from the same `currentEntryIdRef` T-056 already maintains — no new identity concept, no second UUID scheme.

**Separation from T-056 (Step 4):** deliberately a **separate small metadata map**, not a new field on `SearchReturnSnapshot` — confirmed by a regression test that `searchReturnState.ts` contains no reference to `lastTrackedSearchKey`/`searchResultsView`/`reportedKeys`. This means an invalid/expired/rejected T-056 snapshot has zero effect on the dedup store's correctness, and vice versa — a materially-identical state can be correctly deduped for analytics purposes even in a hypothetical future where UI restoration itself is skipped for some other reason.

**History-entry semantic rule (Step 6):** **one `search_results_view` per materially distinct successful result state per browser history entry** — confirmed as the correct interpretation (no scope deviation needed). `Search A → Salon → Back to Search A` suppresses correctly (same entryId, same key, already recorded). `Search A → Search B` fires once for B (new history entry via `router.push`, fresh entryId, no prior record). `Search A → Search B → Back to Search A` correctly restores A's own event history (browser-native `history.state` is per-entry, so A's original entryId — and its dedup record — come back intact on Back, not sharing state with B).

**Consent (Step 9):** untouched — `trackEvent()`'s own consent gate (`lib/analytics.ts`) is unchanged and re-checks live consent on every call regardless of dedup state; dedup happens entirely before `trackEvent()` is ever invoked, so a denied/withdrawn/rejected consent state still drops the call exactly as before, and no "replay" logic of any kind was added.

**Verification:** 668/668 frontend tests passing (33 new for T-058: 10 direct unit tests for `hasReportedSearchResultsView`/`markSearchResultsViewReported` in `lib/searchResultsViewDedup.test.ts`, 23 source-wiring regression tests in `app/[locale]/search/searchResultsViewDedupWiring.test.ts` covering event identity, dedup ownership, privacy, timing, and T-054/T-055/T-056/T-057 non-regression). Three pre-existing tests needed their fixed-length source-slice windows widened (1200→2200 chars) after the new explanatory comment lengthened the tracking effect's surrounding text — a pure test-fixture adjustment, not a behavior change. `npm run lint` and `npm run build` both clean.

**Isolated production verification:** built and ran the actual `next build` standalone output **with real `NEXT_PUBLIC_GA4_ID`/`NEXT_PUBLIC_ANALYTICS_CONSENT_ENABLED` build args** (matching the Docker image's real values) — unlike T-056/T-057, which had to defer all GA4-specific verification to production because the default local build has no measurement ID baked in, this let the isolated pass genuinely exercise live `gtag()` call interception. All scenarios passing: fresh search emits exactly 1 `search_results_view` (4 locales + 375px mobile); Back restoration after loading 48 cards and opening a salon emits **zero** duplicate events (still exactly 1 total) while T-056 restoration itself still works correctly; a real area change (via the filter popover UI) and a real query change (via the search input) each emit exactly 1 new event, with no raw query text in any payload; list→map emits exactly 1 new event per the existing T-015 contract, and re-clicking the already-active view emits none; hard reload emits exactly 1 fresh event (not cumulative with the pre-reload count); a simulated API failure emits zero events, and a successful Retry emits exactly 1; no consent and rejected consent both correctly prevent `gtag` from ever initializing; and a mid-session consent withdrawal correctly prevents a subsequent new material state from firing (existing T-014/T-015 semantics, unmodified).

**Safety checklist:** Backend changed: No. Database changed: No. Search API changed: No. Ranking changed: No. Default ordering changed: No. Public URL contract changed: No. New GA4 event added: No. Existing GA4 event renamed: No. Event parameters changed: No. Raw query sent to analytics: No. Exact total sent to analytics: No. History entry ID sent to analytics: No. Back restoration duplicates results event: No. Fresh hard reload emits results event: Yes. New material search state emits event: Yes. T-056 restoration preserved: Yes. T-057 controls preserved: Yes. Production touched before review: No. PM2 used: No. `crawler/celerybeat-schedule` touched: No. Dependabot changes mixed into branch: No.

**Acceptance Criteria:**
- [x] Back restoration to the same history entry and material state emits no duplicate `search_results_view`
- [x] A genuinely new material state (query/area/rating/clear-all/list-map/hard-reload/direct-nav/Retry-success) still emits exactly one event
- [x] History-entry id never reaches the GA4 payload — used only as a local dedup Map key
- [x] No new/renamed GA4 events, no changed event parameters, no raw query or exact count in any payload
- [x] Dedup state is a separate small in-memory store, not a change to the T-056 snapshot schema
- [x] Consent semantics (no consent/rejected/withdrawn/regrant) unchanged — no new replay logic
- [x] T-056 restoration and T-057 controls both regression-verified, unit tests and isolated Playwright
- [x] Isolated production verification — real GA4 build args, 4 locales + mobile, all scenarios passing (see above)
- [x] Live production verification — passed on `https://lookla.gr`, see below
- [x] Independent review — approved (PR #55)

**Live production verification (`https://lookla.gr`, 2026-07-27):** ran the full scenario directly against production via `gtag()` interception (consent pre-granted). Exact captured sequence for the core reproduction: `search load → search_results_view ×1` → load 48 cards → open a salon → `salon_open ×1` (`{"salon_id":"15278","source":"search_list","locale":"en"}`) → Back → T-056 restoration confirmed (48/48 cards) → `search_results_view` after Back: **×0 additional** (still exactly 1 total) — the T-058 fix holds live. Legitimate-event checks: area change fires exactly 1 new `search_results_view` + exactly 1 `area_select`; query change fires exactly 1 new `search_results_view` with no raw query in any payload; list→map fires at most 1 new event per the existing contract. Hard reload fires exactly 1 fresh event. A simulated API 500 fires zero events; a successful Retry fires exactly 1. Consent: withdrawal mid-session stops a subsequent new material state from firing; regrant alone (no new state) does not replay the denied-period view; a genuinely new state after regrant is tracked correctly. Payload inspection on a real (zero-result) query confirmed the product-event payload contains only the 4 approved keys (`area`, `result_count_bucket`, `view`, `locale`), no raw query text, `result_count_bucket` is always one of the 5 approved bucket labels (never an exact count — including the `'0'` bucket for a genuinely empty result, correctly distinguished from "looks like a raw number" in the verification script itself), and no UUID-shaped value (history entry id) anywhere in the payload. Zero console/hydration errors throughout.

---

### SQC-01A — Deferred candidates (unnumbered, not yet tickets)

Recorded from the SQC-01A search-page inventory/scoring pass (2026-07-24) plus a T-056 production-verification finding (2026-07-27). None of these have an assigned ticket number, branch, or implementation spec yet — listed here so they aren't lost before SQC-01B planning.

- ~~Combined search-controls accessibility ticket~~ — became **T-057 — Search Controls Accessibility & Mobile Operability** (see full entry above), implemented 2026-07-27.
- ~~**Map accessibility (keyboard/screen-reader navigation of `MapView`).**~~ — **formally reserved and implemented as T-063** (see the T-063 entry in EPIC-09 below). The number had shifted twice (T-061 → T-062 collision → T-063) before being claimed. The plain-`<a href>` marker-popup link that T-056 documented as a known limitation is **still open**: T-063 made the preview keyboard-operable but did not change that link's hard-navigation behaviour, so it still discards the in-memory search-return snapshot on click.
- ~~`search_results_view` re-fires on every Back-restoration~~ — became **T-058 — Prevent Duplicate Search Results Analytics on Back Restoration** (see full entry above), implemented 2026-07-27.

---

## Visual Baseline v1 (new phase, 2026-07-28)

The current production UI was audited (inventory-only Visual Baseline Audit, 2026-07-27/28 — no code changed) and found to visually communicate "unfinished" through specific, evidenced mechanisms: zero photography anywhere on the homepage, one saturated colour (`pink-600`) simultaneously carrying brand/every action/focus/active state, seven visually identical white boxes stacked on the salon detail page, three unrelated icon systems in simultaneous use (platform emoji, hand-authored SVG, Unicode symbols), and no consolidated spacing/radius/shadow system. Two genuine i18n bugs were also found live in production and are tracked for their respective future page-level tickets (not fixed standalone): a hardcoded Greek `Όλες οι αξιολογήσεις` placeholder in the rating filter regardless of locale, and a hardcoded Greek `+N φωτογραφίες` gallery overlay on the salon detail page regardless of locale.

**Why this phase exists before SQC-01B:** every conversion number the product produces today (`search_results_view → salon_open → contact_action`) is filtered through a UI that visually undermines trust through concrete, specific mechanisms — establishing SQC-01B's ranking baseline against that UI would measure the visual system, not the search relevance it's meant to measure.

**Approved direction:** Direction B — Clean Marketplace (of three audited directions — A/Editorial Beauty, B, C/Friendly Local Discovery). Chosen for its resilience to incomplete data (most listings currently lack a price or verification), lowest implementation risk against the completed T-042–T-058 functional/accessibility contracts, and safest long-term fit for a future owner dashboard and booking flow.

**Sequence (foundational-first, 7 tickets, none redesigning the whole site at once):** (1) visual tokens/typography/icon foundation, (2) header/footer + global shell, (3) homepage, (4) search shell + controls, (5) SalonCard, (6) salon detail, (7) shared async/legal/cookie alignment + final production-baseline verification. The official **Beta Visual Baseline** date (the point after which conversion analytics is treated as measuring the real product, not a visually unfinished one) begins only after ticket 7 deploys — not after ticket 1.

**Protected throughout every ticket in this phase:** backend, database, API contracts, search ranking/default ordering, URL/query-parameter state, consent logic, GA4 event taxonomy and parameters, and every accessibility/analytics contract established by T-055–T-058 (accessible names, `aria-expanded`/`aria-pressed`, keyboard lifecycles, 44px touch targets, T-056 restoration, T-058 dedup).

**Ranking/default ordering** remains unnumbered and deferred, now additionally gated on the Beta Visual Baseline date, not just on GA4 traffic accumulation — starting that baseline clock before the visual refresh completes would mix pre- and post-refresh behaviour in the same cohort.

### T-059 — Visual Foundations: Tokens, Typography & Icon System
**Priority:** P0 (first ticket of the Visual Baseline v1 phase) | **Owner:** FE | **Epic:** EPIC-09
**Dependencies:** T-042 ✅, T-054 ✅, T-055 ✅, T-056 ✅, T-057 ✅, T-058 ✅ (functional/accessibility/analytics foundation); Visual Baseline Audit (2026-07-27/28, inventory-only) for the approved Direction B token proposal
**Status:** ✅ Completed. Merged via PR #56, deployed to production (`beauty_web` rebuilt and restarted alone — no other service touched), live production verification passed.

**Scope:** semantic colour/shape/depth tokens, a self-hosted Inter typeface with verified 4-locale glyph coverage, one icon system (`lucide-react`), a shared `Button`/`Icon` primitive pair, and a shared focus-ring class — established as CSS custom properties (`app/globals.css`) aliased into Tailwind (`tailwind.config.ts`), with zero duplication across CSS/Tailwind/TypeScript. No page-level redesign. Full specification, token table, contrast matrix, and migration ownership map: `docs/06_ENGINEERING/VISUAL_BASELINE_V1.md`.

**Direction B token palette — transcribed from the approved audit artifact, not reinterpreted.** Two audit-proposed values failed WCAG contrast validation and were strengthened (never softened): `--text-muted` (`#9C938C` → `#7C7069`, 3.01:1 → 4.80:1) and `--focus` (`#D98CAE` → `#B84B7C`, 2.53:1 → 4.84:1 vs. surface). Several categories the audit left undefined were added to complete the semantic set the ticket required (`--danger`/`--danger-soft`, `--brand-active`/`--brand-soft`, `--accent-strong`, `--text-inverse`, `--surface-subtle`, `--border-strong`) — all documented with their derivation in the spec doc.

**Proving surface:** a new internal, unlinked, `noindex` route (`/design-system-preview`) demonstrates every token, all 10 typography roles, both button variants, the icon system, and status pills using real localized product strings (never lorem) across all 4 locales. Applying the new tokens directly to any real shipped page (e.g. Header) was deliberately avoided — the new `--brand` colour differs from the still-present `pink-600`, and mixing both on one real page would create exactly the "visibly broken hybrid" the ticket warned against. The only real-page changes: the global font swap (uniform sitewide, confirmed via computed-style check on production homepage/search) and Header's mobile-menu icon (glyph-source swap only — same size, same colour, same accessible name, no token/colour change).

**Verification:** 96 new tests (775/775 total, including all pre-existing T-042–T-058 suites unchanged since no shared source file was touched). Includes a real, reusable WCAG contrast function (`lib/colorContrast.ts`) that live-extracts token hex values from `globals.css` and asserts every required pair — not just a documentation table, a regression test that fails if a future token edit weakens contrast. `npm run lint` and `npm run build` clean. Isolated Playwright verification: 4 locales × {320, 375, 768, 1024, 1440}px on the preview route (font applied, no overflow, 20+ swatches rendered, 44px button height, disabled state, keyboard-Tab reachability, no long-running animations, zero console errors) plus Header-icon-migration checks in 2 locales; a direct screenshot comparison of the real homepage/search pages post-build showed the font change applied cleanly with zero other visual difference.

**Acceptance Criteria:**
- [x] Semantic colour tokens implemented, aliased through Tailwind, no raw hex/Tailwind-palette duplication
- [x] Typography foundation implemented (Inter, 4 weights, `display: swap`, verified 4-locale glyph coverage)
- [x] One icon system established (`lucide-react`), decorative-by-default contract, no accessible-name invention
- [x] Contrast validated for every required pair, enforced by an automated test against the live token values
- [x] Controlled proving surface demonstrates the system without creating a hybrid look on any real page
- [x] No page-level redesign; homepage/search/SalonCard/salon-detail/header/footer/cookie-UI structurally untouched
- [x] All protected contracts (search, SalonCard, salon detail, analytics, consent, accessibility) verified unaffected
- [x] Performance impact measured and bounded (7 woff2 files, ~218KB total build output, self-hosted, no new blocking runtime request)
- [x] Live production verification — passed on `https://lookla.gr`, see below
- [x] Independent review — approved (PR #56)

**Live production verification (`https://lookla.gr`, 2026-07-28):** verified against production directly. All 4 locales × {320, 375, 768, 1024, 1440}px on `/design-system-preview`: Inter applied, zero runtime requests to `fonts.googleapis.com`/`fonts.gstatic.com` (confirmed self-hosted), no horizontal overflow, headings render in clean line-height multiples at every width (no diacritic-clipping signal — the first check attempt used an overly strict heuristic that flagged 320px's legitimate 4-line wrap as a false positive; corrected to check for clean whole-line multiples instead of an arbitrary ratio ceiling), `noindex` meta present, 28 token swatches render, buttons meet 44px, focus-visible produces a real 2px solid outline in the `--focus` colour. Font delivery: exactly 4 same-origin `.woff2` files loaded on the real homepage, zero external font requests. CLS measured at 0.0028 (well under the 0.1 threshold) on the real homepage. GA4/consent/T-058: `search_results_view` still fires exactly once on a fresh load, T-056 restoration still restores 48/48 cards after Back, and T-058's dedup still holds (zero duplicate `search_results_view` after Back) — confirmed live, not just via the existing test suite.

**One finding, confirmed pre-existing (not a T-059 regression):** the header's mobile-menu button measures 40×40px, short of the 44×44px target. Verified byte-for-byte against the pre-T-059 source (`git show`) that this is unchanged — the old inline `<svg className="w-6 h-6">` (24px) inside a `p-2` (8px padding) button produces the identical 40px math as the new `<Icon size={24}>` swap. T-059's icon migration was a glyph-source swap only, deliberately not a sizing change (matching its own non-goals). Flagged as a concrete input for T-060, which fixes it (see below).

---

### T-060 — Header, Footer & Global Shell Visual Refresh
**Priority:** P0 (second ticket of the Visual Baseline v1 phase) | **Owner:** FE | **Epic:** EPIC-09
**Dependencies:** T-059 ✅ Visual Foundations
**Status:** ✅ Completed. REQUEST CHANGES round resolved (Option 1 — shell unified), re-reviewed, **APPROVE**, merged via PR #57 (`6588881` on `main`), `beauty_web` rebuilt and restarted alone — API/DB/Redis/crawler/crawler_worker untouched — production smoke passed on `https://lookla.gr`.

```text
T-060 regressions: 0
Known pre-existing SearchBar 320px overflow: unchanged, deferred
```

**Scope:** applies Direction B tokens to one shared `Header.tsx`/`Footer.tsx`/`LanguageSwitcher.tsx` shell and the `[locale]/layout.tsx` wrapper. Fixes the known 40×40 burger touch-target gap (now 44×44), adds programmatic active-nav-state, keyboard/focus lifecycle for the mobile menu, and a query-preservation bug found live in production (switching locale previously dropped `?area=...&view=map`-style filter state entirely). No homepage/search/SalonCard/salon-detail *content* touched. Full contract, variant table, and legacy-boundary report: `docs/06_ENGINEERING/VISUAL_BASELINE_V1.md`.

**Round 1 → REQUEST CHANGES → Round 2 (accepted fix):** the first implementation only refreshed `Header.tsx` as used by the homepage, leaving search/salon-detail/legal pages on three separate independent inline headers — reviewed and correctly rejected as not actually "global." Two blocking issues: (1) the shell wasn't unified across surfaces; (2) no page had a real `<main>` landmark, and the HTML-AAM-based justification for omitting one was rejected as insufficient. Both are now fixed:
1. `Header.tsx` gained a `variant?: 'default' | 'search' | 'detail' | 'legal'` prop (+ `backHref`, `children`) — the exact names the reviewer suggested. All variants share logo, language switcher, mobile burger+panel, tokens, and touch-target rules; only inline desktop chrome differs. Homepage and `/masters` use `default`; `/search` uses `search` (the T-057-protected toolbar renders as `children`, after `</header>`, keeping its own pre-existing sticky behaviour); `/salons/[slug]` uses `detail`; `/privacy`/`/cookies` use `legal`. `/masters` was a bonus zero-new-code fix — it had its own fourth ad hoc header, still on the pre-T-059 palette; folding it into `variant="default"` cost nothing extra.
2. Each of those 6 pages now wraps its own real content in its own `<main id="main-content">`, as a sibling right after its own `<Header ... />` call. The shared layout still uses a plain `<div>` (not `<main>`) to avoid double-nesting `<main>` on pages that now own one. `Header` additionally sets `role="banner"` **explicitly**, since it can end up nested inside a page's own `<main>` — which per HTML-AAM would otherwise silently suppress the implicit banner role. This was the direct, targeted fix, not a restructuring of routing/layouts.

**Key fixes (all rounds):**
- Burger touch target: `p-2` (40×40) → `p-2.5` (44×44), no icon-size change.
- Burger accessible name: was a hardcoded English `"Menu"` string regardless of locale — now genuinely localized (`nav.menu`, added to all 4 locale files). New `nav.back` key added for the `detail`/`legal` back arrow, also localized in all 4.
- **No `aria-haspopup`** on the burger — the T-057 lesson applied explicitly (`"true"` is spec-equivalent to `"menu"`, would misrepresent a plain nav disclosure).
- Mobile menu classified as an inline disclosure (not an overlay) after inspection — Escape closes + returns focus (T-057 pattern), deliberately no outside-click handler (documented reasoning: no overlaid content to dismiss), no body-scroll lock, no focus trap. Identical panel markup across all 4 variants — one real shared component, not four look-alikes.
- **Locale-switch query-loss bug fixed:** `router.replace(pathname, {locale})` dropped the query string because next-intl's `usePathname()` is query-free by design; new `lib/localeSwitchHref.ts` re-attaches `useSearchParams()` before the swap. Same `router.replace()` call, so T-056's entry-id mechanism is unaffected. Re-verified working on `/search` after the unification fix.
- Active nav state: new `lib/activeRoute.ts`, `aria-current="page"` plus a non-colour cue (border-bottom desktop / background mobile) — never colour-only.
- Sticky-footer shell (`flex min-h-screen flex-col` + a `flex-1` wrapper) so short pages don't leave the footer floating.
- All footer links/language-switcher buttons brought to 44px (were ~20px tall / ~15-19px wide).

**Verification:** 851/852 local tests passing (the one non-pass is `[320] horizontal overflow`, the pre-existing, documented, unrelated `SearchBar.tsx` finding below — must not be described as a passed visual check). One pre-existing test bug found and fixed as a direct consequence (`lib/cookieConsentUi.test.ts`'s file-exclusion regex excluded `.test.ts` but not `.test.tsx`, causing a false positive against the new `Footer.test.tsx`). Lint/build clean (`next build` type-checks and compiles clean; bundle-size note: `privacy`/`cookies`/`masters` grew from near-static 141B–1.72kB to 4.22–5.51kB First Load JS, an expected consequence of now sharing one interactive client shell). Isolated Playwright verification, post-unification-fix: all 6 unified-shell pages checked for exactly one `role="banner"` header, exactly one `<main id="main-content">`, exactly one footer, no horizontal overflow, zero console/hydration errors — all pass, at both a desktop and a mobile width. Mobile menu re-verified reachable and functional on every variant. `nav.back`/`nav.menu` localization re-verified across all 4 locales. Locale-switch query preservation, search map-view width (unchanged — confirmed via `git diff` that the `<div>`→`<main>` retag touched no `className`), and T-056 Back-restoration (48/48 cards) all re-confirmed against the corrected build.

**Live production verification (`https://lookla.gr`, 2026-07-28, post-deploy):** all 6 unified-shell pages (home/search/masters/privacy/cookies/salon-detail) × {1280, 375}px — exactly one `role="banner"` header, exactly one `<main id="main-content">` (not duplicated), exactly one footer, zero console/hydration errors. Mobile disclosure re-verified live on 4 surfaces (default via home/masters, search, legal via privacy): single burger, 44×44, opens, no duplicated focusable nav DOM, Escape closes and returns focus. `aria-current="page"` confirmed correct on the two `default`-variant pages (`/masters` marks "Professionals" current and NOT "Salons & Studios"; homepage marks neither). Locale switch on `/search` still preserves `?area=athens-center&view=map` across `en`→`ru`. Search map view width unchanged (1120px, same as pre-T-060). T-056 restoration confirmed live: 48/48 cards **and** scroll position both restored after Back. Footer Privacy/Cookie Policy links confirmed live. The known 320px homepage overflow was re-measured at 13px — **unchanged from before this deploy, not improved and not worsened** — see the explicit status block above; this is not being reported as a passing check, only as confirmed non-regression.

**One finding, confirmed unrelated to T-060 (all rounds, including live post-deploy):** a horizontal overflow at 320px on the homepage, traced to `SearchBar.tsx`'s own search-submit button — verified byte-identical on current production both before and after this deploy, independent of any shell file. Flagged for the homepage visual-refresh ticket.

**Acceptance Criteria:**
- [x] Burger touch target ≥44×44 (was 40×40)
- [x] Burger accessible name localized, `aria-expanded`/`aria-controls` correct, no `aria-haspopup`
- [x] Escape closes the mobile menu and returns focus to the trigger
- [x] Active route programmatically exposed (`aria-current`), never colour-only
- [x] Locale switch preserves query/filter state (found-live bug, fixed)
- [x] Footer legal links, cookie settings, and all destinations preserved
- [x] No homepage/search/SalonCard/salon-detail *content* redesigned (chrome-only changes)
- [x] One unified shell contract (variants) reaches homepage, search, salon detail, and legal pages — not independent per-page re-implementations
- [x] Exactly one `<main id="main-content">` landmark per unified-shell page, Header/Footer outside it, no nested `<main>`s
- [x] T-056 restoration, T-057 control semantics, T-058 dedup, and search map-view width all re-verified unaffected post-unification
- [x] Four locales verified at 6 breakpoints
- [x] Live production verification — passed on `https://lookla.gr`
- [x] Independent review — REQUEST CHANGES on round 1 (PR #57), Option 1 fix implemented, **APPROVE** on round 2

---

### T-062 — Homepage Visual Refresh
**Priority:** P0 (third ticket of the Visual Baseline v1 phase) | **Owner:** FE | **Epic:** EPIC-09
**Dependencies:** T-059 ✅ Visual foundations, T-060 ✅ Header, Footer & Global Shell
**Status:** ✅ Completed. Reviewed, **APPROVE**, merged via PR #58 (`50c6c87` on `main`), `beauty_web` rebuilt and restarted alone — API/DB/Redis/crawler/crawler_worker untouched — production smoke passed on `https://lookla.gr`.

**Ticket-identity note:** requested as "T-061," which collided with an already-existing informal, unreserved backlog placeholder ("map accessibility," see the note further up this document). Per the collision protocol: reported, not reused — assigned **T-062**, the next genuinely unused ID, preserving the requested title/scope verbatim. The map-accessibility placeholder's own informal working number shifted again, to T-063.

**Scope:** `app/[locale]/page.tsx`, `components/SearchBar.tsx`, `components/CategoryGrid.tsx`, `components/AreaGrid.tsx`, and a one-value extension to `components/ui/Icon.tsx`'s `IconSize` enum (+28, for the category grid's larger visual anchor). Direction B tokens applied; emoji replaced with `lucide-react`; the known homepage `SearchBar.tsx` 320px overflow fixed (required defect fix per the ticket). Search-results page, `SalonCard` (global), salon-detail, and the T-060 shell are untouched. Full contract, imagery decision, and verification detail: `docs/06_ENGINEERING/VISUAL_BASELINE_V1.md`'s T-062 section.

**Key changes:**
- **SearchBar 320px overflow — root cause found and fixed:** the input was a `flex-1` item with no `min-width` override; flexbox's default `min-width: auto` refused to let it shrink, pushing the fixed-width submit button 13px past the 320px viewport. Fix: `min-w-0` on the input — the actual, minimal, one-class fix. Everything else in the file is presentation refresh (🔍 emoji → `lucide-react` `Search` icon, real `<label>`, `aria-label` on submit, Direction B tokens, both controls ≥44×44px). Verified 0px overflow at 320px across all 4 locales, down from 13px.
- **Category emoji → `lucide-react` icons** via the shared `Icon` component (a documented, one-time `IconSize` extension to 28, since the old emoji rendered larger than any existing Icon call site needed). Destinations, category count, and all 4 locale name maps unchanged. Some mappings are necessarily approximate (no literal "nail polish"/"razor" glyph exists in Lucide) but none are misleading — the visible label, not the icon, identifies the category.
- **Area discovery:** token-only refresh (no emoji existed here). `area_select` event shape/call-site/count unchanged — re-verified live via `gtag()`-call interception (fires exactly once per click).
- **Hero:** legacy `bg-gradient-to-br from-pink-50 to-purple-50` full-hero wash replaced with a restrained, non-photographic, zero-network-request composition (two blurred `brand-soft`/`accent-soft` circles, `aria-hidden`). **No licensed image asset exists** (`frontend/public/` has none beyond `robots.txt`/`sitemap.xml`) — using a real crawled salon photo would read as editorial endorsement of one business; recorded as a future, unscheduled content task rather than blocking the ticket. H1/subtitle copy kept unchanged (already states what Lookla is, its geographic scope, and implies breadth); typography switched to T-059's `.text-display`/`.text-body` tokens.
- **Found and fixed a real pre-existing false claim:** the "How it works" section's step 2 read "Book" / "Choose a time and book online" (and equivalent Greek/Russian/Ukrainian) — directly contradicting the fact that Lookla has no booking functionality (T-009/T-010 removed the last fake booking CTAs). Fixed narrowly to "Choose" / "Pick the salon or professional that suits you, then contact them directly" in all 4 locales (string values only, key names unchanged); step 3's copy was also adjusted to remove an now-orphaned "appointment" reference. How-it-works icons migrated off emoji too (🔍📅✨ → `Search`/`CheckCircle2`/`Sparkles`).
- Section containers now consume T-060's previously-unconsumed `max-w-shell-grid`/`max-w-shell-reading` tokens — the first page to actually adopt them.
- IA unchanged (hero → categories → areas → how-it-works) — already matched Direction B's preferred structure; nothing removed, nothing added.

**Verification:** 53 new tests + 1 pre-existing T-059 `Icon.test.tsx` assertion updated for the `IconSize` extension. Full suite: 905/905 passing (all T-042–T-060 regression suites green, unmodified). Lint/build clean. Isolated Playwright: 4 locales × 6 breakpoints (24 combinations) — 0px overflow everywhere (down from 13px at 320px), correct landmarks, ≥44×44 touch targets throughout, zero console/hydration errors; plus focus-state, reduced-motion, mobile-nav-over-homepage, category/area navigation, search-submission, and `area_select`-dedup checks. Accessibility: logical heading hierarchy (H1→H2×3→H3×3), no colour-only state, no duplicated/indistinguishable link names. Performance (isolated): CLS 0, LCP element is the H1 text (no image on the critical path — none exists on the page), homepage bundle +0.4kB (5.16kB→5.56kB), zero new network requests.

**Live production verification (`https://lookla.gr`, 2026-07-28, post-deploy):** all 4 locales × {320, 375, 390, 768, 1024, 1440}px — zero horizontal overflow at every combination (the 320px overflow fix confirmed live, not just isolated), search input never overlaps the submit button, zero console/hydration errors. Enter and the submit button each navigate to `/search?q=...` exactly once, confirmed separately. All 10 category tiles present with the expected slugs, icons `aria-hidden` (never contribute to accessible names), accessible names are clean text with no emoji. `area_select` fires exactly once per click, confirmed live via `gtag()`-call interception. No booking/appointment language and no unsupported verification/trust claim anywhere on the homepage; the "How it works" step-2 fix ("Choose" + "contact them directly") confirmed present live. T-060's mobile burger/panel confirmed still 44×44 and still opens cleanly over the refreshed homepage. Landmarks confirmed (1 h1/banner-header/main/footer); live CLS measured at 0.0025 (close to zero, consistent with the isolated 0 result — the small non-zero delta is expected on a real page with live analytics/consent scripts attaching, not a regression).

```text
T-062 regressions: 0
```

**Acceptance Criteria:**
- [x] Homepage SearchBar overflow fixed (320px, root cause documented, all 4 locales)
- [x] Homepage category emoji replaced with the Lucide icon system
- [x] No booking/verification/statistics claim beyond what the product truthfully supports (found and fixed a pre-existing false booking claim)
- [x] Search-results page, SalonCard (global), and salon-detail not redesigned
- [x] No backend/database/API/ranking/search-semantics change
- [x] No new or renamed GA4 event; `area_select` shape and dedup behaviour unchanged
- [x] T-060 shell preserved (Header/Footer/landmarks untouched, re-verified)
- [x] Four locales verified at 6 breakpoints
- [x] Accessibility: landmarks, heading hierarchy, keyboard operability, touch targets, no colour-only state
- [x] Performance impact measured (CLS/LCP/bundle/requests)
- [x] Live production verification — passed on `https://lookla.gr`
- [x] Independent review — **APPROVE**

---

### T-064 — Search Shell Visual Refresh
**Priority:** P0 (fourth ticket of the Visual Baseline v1 phase) | **Owner:** FE | **Epic:** EPIC-09
**Dependencies:** T-042 ✅, T-054 ✅, T-056 ✅, T-057 ✅, T-058 ✅, T-059 ✅, T-060 ✅, T-062 ✅
**Reserved separately:** T-063 — Map Accessibility (untouched by this ticket)
**Status:** ✅ Completed. Reviewed, **APPROVE**, merged via PR #59 (`9787fd8` on `main`), `beauty_web` rebuilt and restarted alone — API/DB/Redis/crawler/crawler_worker untouched — production smoke passed on `https://lookla.gr`.

**Ticket-identity note:** T-064 was confirmed genuinely unused before branching — no collision. T-063 remains reserved only for the future Map Accessibility ticket and was not modified.

**Scope:** `app/[locale]/search/page.tsx`'s render section (toolbar, search form, filter trigger/panel, results summary, List/Map selector, list/map async-state framing) and `components/ActiveFilterChips.tsx`. Direction B tokens applied; every emoji and inline SVG replaced with `lucide-react`; the known hardcoded Greek `Όλες οι αξιολογήσεις` rating-filter default fixed. Search-results page content — SalonCard internals, Leaflet markers/popups, ranking, pagination, the full T-042/T-054/T-056/T-057/T-058 functional contract — is untouched; map-marker accessibility is explicitly out of scope (reserved for T-063). Full contract and verification detail: `docs/06_ENGINEERING/VISUAL_BASELINE_V1.md`'s T-064 section.

**Key changes:**
- **Hardcoded Greek rating text — fixed:** `<option value="">Όλες οι αξιολογήσεις</option>` (rendered regardless of locale) replaced with `{t('all_ratings')}`, a new key added to all 4 locale files. EN/RU/UK now show their own translated text; EL correctly still shows the Greek original. Filter semantics/URL contract unchanged.
- **Additional hardcoded-string finding, fixed:** `search.list`/`search.map` had an emoji baked directly into the translated string (`"☰ List"`/`"🗺 Map"`) in all 4 locales — stripped, with a real Lucide `List`/`Map` icon now rendered alongside the clean text label instead.
- **Icon system:** the 🔍 search-submit emoji, ✕ clear-query emoji, inline `<svg>` filter-funnel icon, and `×` chip-remove glyph are all replaced by the shared `Icon` component (`Search`/`X`/`SlidersHorizontal`/`X`). Zero emoji remain in the search shell.
- **Direction B tokens** applied throughout the toolbar, filter panel, active-filter chips (`bg-brand-soft`/`text-brand` replacing `bg-pink-50`/`text-pink-700`, `rounded-pill`), results summary, and async-state (loading/empty/error) presentation.
- **Map shell:** only a `rounded-md overflow-hidden border` container and token-coloured loading/error framing added around the existing map — `MapView.tsx` (markers, popups, fetch, center/zoom) untouched; map dimensions confirmed unaffected.
- **List framing:** grid column/gap contract unchanged; only skeleton-tile and load-more-spinner colours updated. `SalonCard.tsx` not modified.
- Toolbar kept as its existing single sticky row (not restructured) — measurement showed it already wraps cleanly with no overflow; only tokens/icons changed.

**Verification:** 62 new/updated tests (33 net-new across `searchShellVisual.test.ts`/`ActiveFilterChips.test.tsx`; 6 pre-existing T-057-era assertions updated to locate their same guarantee inside the refreshed markup, not weakened). Full suite: 938/938 passing (all T-042–T-062 regression suites green). Lint/build clean (search-page bundle actually *shrank*, 13.4kB→9.46kB — the old inline SVG was replaced by a shared, already-loaded Lucide chunk). Isolated Playwright: 24 breakpoint×locale combinations — zero overflow, no control overlap, ≥44×44 touch targets, zero console/hydration errors; plus the Greek-hardcode fix re-verified per locale, filter-popover keyboard lifecycle (Escape/focus-return/no `aria-haspopup`), chip removal + clear-all, List↔Map toggle with live Leaflet render, a simulated API-500 → `role="alert"`, T-056 restoration (48/48 cards, toolbar intact after remount), and a `gtag()`-intercepted analytics check confirming filter open/close emits nothing and `search_results_view` still fires exactly once.

**Live production verification (`https://lookla.gr`, 2026-07-28, post-deploy):** all 4 locales × {320, 375, 390, 768, 1024, 1440}px — zero horizontal overflow, no search-input/submit overlap, filter trigger and both List/Map controls ≥44×44, zero console/hydration errors at every one of the 24 combinations. Rating-default localization re-confirmed per locale (EL correctly Greek, EN/RU/UK correctly translated); List/Map button text confirmed emoji-free with a real icon present, in all 4 locales. All toolbar icons confirmed `aria-hidden` (never contribute to accessible names). Filter popover: no `aria-haspopup`, opens/closes correctly, Escape returns focus to the trigger. Chip removal and clear-all both confirmed live; canonical total text present and correctly formatted. Simulated `/api/salons` 500 → `role="alert"`/`aria-live="assertive"` with a working Retry action. List↔Map toggle confirmed exactly one `aria-pressed="true"` before and after, with live Leaflet markers (2000) rendering unaffected. SalonCard confirmed still rendering its photo with a single outer link (no nested links) — visually and structurally unchanged. T-056 restoration confirmed live (48/48 cards); T-058 dedup confirmed live — exactly one `search_results_view` total across the full search→open→Back cycle via `gtag()`-call interception. CLS measured at 0.

```text
T-064 regressions: 0
```

**Acceptance Criteria:**
- [x] Hardcoded Greek `Όλες οι αξιολογήσεις` fixed (all 4 locales verified)
- [x] Search controls semantics preserved (form, clear, submit, filter trigger/panel, List/Map — all T-057 contracts byte-identical in logic)
- [x] Active-filter chip recovery preserved (T-054 contract unmodified)
- [x] T-056 restoration preserved (state/effects block untouched; re-verified live)
- [x] T-058 analytics dedup preserved; no new or renamed GA4 event
- [x] Four locales verified at 6 breakpoints
- [x] 320px overflow absent
- [x] SalonCard not redesigned internally; map markers/popups untouched (T-063 scope preserved)
- [x] No backend/database/API/ranking/default-ordering/filter-semantics change
- [x] Performance impact measured (CLS/LCP/bundle/requests) — bundle size decreased
- [x] Live production verification — passed on `https://lookla.gr`
- [x] Independent review — **APPROVE**

---

### T-065 — SalonCard Visual Refresh
**Priority:** P0 (fifth ticket of the Visual Baseline v1 phase) | **Owner:** FE | **Epic:** EPIC-09
**Dependencies:** T-055 ✅, T-056 ✅, T-058 ✅, T-059 ✅, T-060 ✅, T-062 ✅, T-064 ✅
**Reserved separately:** T-063 — Map Accessibility (untouched by this ticket)
**Status:** ✅ Completed. Reviewed, **APPROVE**, merged via PR #60 (`3eea3e5` on `main`), `beauty_web` rebuilt and restarted alone — API/DB/Redis/crawler/crawler_worker untouched — production smoke passed on `https://lookla.gr`.

**Ticket-identity note:** T-065 was confirmed genuinely unused before branching — no collision. T-063 remains reserved only for the future Map Accessibility ticket and was not modified.

**Scope:** `components/SalonCard.tsx` — the first ticket in this sequence allowed to change the card's *internal* visual presentation (T-059/T-060/T-062/T-064 all deliberately left it untouched). Plus the search page's loading-skeleton markup, updated to match the card's new geometry. Salon-detail, map markers/popups, ranking, and the entire T-055/T-056/T-058 functional/analytics contract are untouched. `SalonCard` has exactly one real consumer today (`search/page.tsx`) — the `'homepage'|'masters'` `source` values remain reserved/unused. Full contract and verification detail: `docs/06_ENGINEERING/VISUAL_BASELINE_V1.md`'s T-065 section.

**Key changes:**
- **Image:** fixed `h-44` (176px, a different crop ratio at every card width) replaced with a deliberate `aspect-[4/3]`, consistent at every breakpoint.
- **Fallback — a real gap found and fixed:** the old `onError` handler only hid the broken image, leaving a blank box on a *failed* request (the emoji fallback only ever covered a *missing* URL, not a failed one). Fixed with `useState` tracking load failure; both states now show the same honest fallback — a generic, decorative `Building2` icon (not category-specific, since `category` is a page-level filter, not verified per-salon data; not an emoji, not a stock photo, not AI-generated).
- **Rating:** the old 5-glyph Unicode star row (`★★★★☆`, redundant with the adjacent numeric value) replaced with **one** filled Lucide `Star` icon + the numeric value + review count — less visual noise, same information, coloured with T-059's text-safe `accent-strong` token instead of brand pink.
- **Open/closed:** `bg-green-500`/`bg-black/50` replaced with T-059's semantic `success`/`closed` tokens (defined but never consumed by an earlier ticket) — logic unchanged.
- **Verified badge:** documented what the field actually means first (`is_verified` gates presence; `is_owner_claimed` picks between the two already-restrained existing labels, "Owner verified"/"Information reviewed" — DEC-014). Restyled to a neutral (not brand/success-coloured) pill with a decorative `BadgeCheck` icon — the claim's strength is unchanged, only the surface.
- **Address:** a decorative `MapPin` icon added; address composition byte-identical.
- **Surface:** `rounded-md`/`shadow-resting`/`hover:shadow-elevated`/`focus-ring-token` — consolidates onto the same radius token already used elsewhere (was a 4th, one-off `rounded-xl`), and is the first component to actually use T-059's 2-level shadow system (resting default + elevated hover) as originally designed. Verified empirically (isolated HTML/CSS test, screenshotted) that `overflow-hidden` and the focus ring can safely live on the same element — an element's own outline is not clipped by its own overflow.
- **Skeleton:** updated to mirror the real card's new aspect-ratio-driven geometry (image placeholder + title/address/rating-price bars) instead of one fixed-height block that no longer matched.

**Verification:** 61 tests in the existing `SalonCard.test.tsx` (5 pre-existing T-055 assertions updated to locate their guarantee inside the refreshed markup) + 37 new tests in `SalonCardVisual.test.tsx` (image/fallback/failure states, tokens, all 6 metadata contracts, DOM integrity, no-new-data/no-new-analytics sweep). Full suite: 975/975 passing (all T-042–T-064 regression suites green — including one more pre-existing assertion in `lib/analytics.test.ts` fixed for the same reason). Lint/build clean (one real TypeScript catch: an icon size wasn't a valid enum member, fixed). Isolated Playwright: 24 breakpoint×locale combinations, DOM-integrity inspection, accessible names free of star glyphs with all decorative icons `aria-hidden`, focus-visible confirmed unclipped, 3 image states, reduced-motion, keyboard activation firing exactly one `salon_open`, zero events from hover/focus, T-056 restoration with the new design intact, and a List→Map→List transition.

**Live production verification (`https://lookla.gr`, 2026-07-29, post-deploy):** all 4 locales × {320, 375, 390, 768, 1024, 1440}px — zero horizontal overflow, real card dimensions, image aspect-ratio confirmed ~4:3 at every combination, zero console/hydration errors. Missing-URL and simulated-failed-request image states both confirmed to show the identical fallback (not broken-image UI), with no retry loop and stable card height. Accessible name confirmed to include the full salon name with no star glyph; all icons (including the Lucide star) confirmed `aria-hidden` and excluded from the accessible name. DOM integrity confirmed across 24 live cards: exactly one `<a>`, zero nested interactive elements, zero descendant `tabindex`. Focus ring confirmed rendered, unclipped. Hover confirmed to cause zero layout shift and zero analytics events. Pointer click and keyboard `Enter` each confirmed to produce exactly one `salon_open`. Ctrl-click confirmed to open a new tab (browser-default behaviour preserved, uninterfered with). T-056 restoration confirmed live: 48/48 cards and scroll position both restored, exactly one `search_results_view` across the full search→open→Back cycle (no duplicate), restored cards using the new design. List→Map→List confirmed with markers rendering (2000) and the list correctly restored afterward, no marker/popup behaviour change. Live CLS measured at 0.

```text
T-065 regressions: 0
```

**Acceptance Criteria:**
- [x] Exactly one outer Link; no nested interactive controls added
- [x] SalonCard accessible-name contract preserved (rating/status announced once, no star-glyph pollution)
- [x] Price conditional-rendering contract preserved (no reserved blank row)
- [x] Verification meaning not strengthened (documented first; restyled only)
- [x] No contact/booking/favourite/compare/share controls added
- [x] Map marker behaviour unchanged; map accessibility not implemented (T-063 scope preserved)
- [x] Salon-detail not redesigned
- [x] No new or changed GA4 event; `salon_open` unchanged
- [x] T-056 restoration preserved (re-verified live with the new design)
- [x] T-058 analytics dedup preserved
- [x] Four locales verified at 6 breakpoints
- [x] 320px overflow absent
- [x] Image performance measured (CLS/LCP/bundle/requests)
- [x] Live production verification — passed on `https://lookla.gr`
- [x] Independent review — **APPROVE**

---

### T-066 — Salon Detail Visual Refresh
**Priority:** P0 (sixth and final conversion-facing ticket of the Visual Baseline v1 phase) | **Owner:** FE | **Epic:** EPIC-09
**Dependencies:** T-009 ✅, T-042 ✅, T-055 ✅, T-058 ✅, T-059 ✅, T-060 ✅, T-062 ✅, T-064 ✅, T-065 ✅
**Reserved separately:** T-063 — Map Accessibility (untouched by this ticket; salon-detail has no embedded map today, only a text address + external Google Maps link)
**Status:** ✅ Completed. Reviewed, **APPROVE**, merged via PR #61 (`537981b` on `main`), `beauty_web` rebuilt and restarted alone — API/DB/Redis/crawler/crawler_worker untouched — production smoke passed on `https://lookla.gr`.

**Ticket-identity note:** T-066 was confirmed genuinely unused before branching — no collision.

**Scope:** `app/[locale]/salons/[slug]/SalonDetailClient.tsx` (full visual rewrite), `components/ContactButtons.tsx`, `components/SalonHours.tsx`, `components/ReportButton.tsx` (tokens/icons only in the latter three). `page.tsx` (metadata) untouched. Full contract and verification detail: `docs/06_ENGINEERING/VISUAL_BASELINE_V1.md`'s T-066 section.

**Key changes:**
- **Photo-count fix (the ticket's named bug):** the hardcoded Greek `+N φωτογραφίες` gallery overlay replaced with a proper ICU-pluralized `salon.more_photos` key, correct in all 4 locales.
- **A real gallery-layout bug found and fixed:** the pre-existing 3-tile gallery used CSS Grid (`grid-cols-3` + `col-span-2`) inside a fixed-height, `overflow-hidden` container — ordinary grid auto-placement pushed the 3rd tile (carrying the "+N photos" button) onto an implicit second row that the fixed height silently clipped, making the affordance invisible to sighted users despite being DOM-correct. Not a T-066 regression (classes were carried over unchanged), but directly defeated the ticket's own required fix, so repaired here: grid replaced with flexbox, which cannot produce a silent implicit-row wrap.
- **`is_open_now` now rendered** (previously fetched but never displayed anywhere on the page) — same `success`/`closed` semantic tokens as `SalonCard`.
- **Visual hierarchy:** the old flat stack of 7 near-identical `bg-white rounded-xl p-5` panels replaced with 3 tiers — prominent identity+contact card (only surface with a shadow), mid-tier Services/Reviews/Hours cards, quiet card-less Description/social/location/report sections.
- **Contact actions:** Call/WhatsApp/Website unified to one visual treatment (no invented channel priority), per the ticket's explicit instruction. `resolveContactActions`/`contact_action` tracking contract (T-010/T-015) unchanged.
- **Fallback:** reused and extended T-065's `PhotoFallback` pattern with genuine failed-image-request handling (a real gap the original code lacked).
- **Icons:** all emoji replaced with `lucide-react`; social-platform icons use generic stand-ins since the installed `lucide-react` version ships no brand/logo icons at all (`Instagram`/`Facebook`/`Youtube` confirmed absent from its exports).

**Verification:** 73 tests — the pre-existing `salonDetail.test.ts` (28, unchanged, all pass) + new `salonDetailVisual.test.ts` (45: photo-count fix, gallery fallback, no-emoji sweep, identity block, contact-action consistency, services/reviews/hours, map-shell boundary, analytics invariants, SEO/structured-data, Direction B tokens). Full suite: 1020/1020 passing. Lint/build clean (one real TypeScript catch: `Instagram`/`Facebook`/`Youtube` not exported by the installed `lucide-react`, fixed with generic icons). Isolated Playwright: responsive × 4-locale sweep, the gallery-clipping bug found/fixed/re-verified via DOM inspection and screenshot, accessibility (keyboard focus ring screenshotted, landmarks, alt text), analytics (`contact_action` × phone/whatsapp channels via `gtag()` interception, confirmed zero events fire from loading the detail page directly, confirmed `salon_open` fires exactly once from the search card and never re-fires on detail mount), T-056 restoration (search → open → interact → Back, no errors), SEO metadata (title/description/schema/og:image unchanged), CLS 0.0029.

**Live production verification (`https://lookla.gr`, 2026-07-29, post-deploy):** 23/24 breakpoint×locale combinations completed (24th interrupted mid-run by a harness timeout, with fully consistent results across the rest) — zero overflow, all 3 gallery tiles at the same vertical position (clipping fix confirmed live), `+N photos` correctly localized in all 4 locales, exactly one `<h1>`, zero console errors. `contact_action` (phone + whatsapp) and `salon_open` single-fire dedup re-verified live via `dataLayer.push` interception against production's real GA4 — correct shapes, no PII, no duplicates, zero events from a direct detail-page load. T-056 restoration re-confirmed live. CLS 0.0029, matching the isolated measurement.

```text
T-066 regressions: 0
```

**Acceptance Criteria:**
- [x] Hardcoded Greek `+N φωτογραφίες` fixed with proper ICU pluralization, all 4 locales
- [x] `is_open_now` now rendered (previously fetched, never shown)
- [x] Visual hierarchy replaces the 7-identical-panel layout with 3 deliberate surface tiers
- [x] Call/WhatsApp/Website share one visual treatment; no new channel priority invented
- [x] `contactActions`/`contact_action` contract preserved (T-010/T-015)
- [x] No booking functionality, no map-marker accessibility work (T-063 scope preserved), no backend/DB/API changes
- [x] No new or renamed GA4 events; `salon_open` still owned solely by the search card
- [x] T-056 restoration preserved (re-verified live)
- [x] Gallery layout bug (implicit-row clipping) found and fixed, re-verified via DOM inspection + screenshot
- [x] Four locales verified at 3 breakpoints (mobile/tablet/desktop)
- [x] Accessibility: single h1, landmark, alt text, aria-labels, visible focus ring
- [x] Performance measured (CLS/bundle)
- [x] Live production verification — passed on `https://lookla.gr`
- [x] Independent review — **APPROVE**

---

### T-067 — Visual Baseline Consistency & Beta Baseline Verification
**Priority:** P0 (seventh and final ticket of the Visual Baseline v1 phase) | **Owner:** FE | **Epic:** EPIC-09
**Dependencies:** T-059 ✅, T-060 ✅, T-062 ✅, T-064 ✅, T-065 ✅, T-066 ✅
**Reserved separately:** T-063 — Map Accessibility (explicitly untouched; a test asserts no keyboard/tabIndex work entered `MapView`)
**Status:** ✅ Completed. Reviewed, **APPROVE**, merged via PR #62 (`c3fc0fc` on `main`), `beauty_web` rebuilt and restarted alone — API/DB/Redis/crawler/crawler_worker untouched — production smoke passed on `https://lookla.gr`. **Beta Visual Baseline began `2026-07-30 11:39:31 Europe/Athens (EEST)`.** This ticket closes the Visual Baseline v1 phase.

**Ticket-identity note:** T-067 was confirmed genuinely unused before branching — no collision.

**Scope:** `components/CookieConsent.tsx`, `app/[locale]/privacy/page.tsx`, `app/[locale]/cookies/page.tsx`, `app/[locale]/not-found.tsx`, `components/MapView.tsx` (overlay chrome only), `package.json` test script. Full contract: `docs/06_ENGINEERING/VISUAL_BASELINE_V1.md`'s T-067 section.

**Key changes:**
- **CI test-coverage gap fixed (most consequential finding):** `npm test` enumerated 38 files by hand while 45 existed — **every visual regression suite from T-062/T-064/T-065/T-066 had never run in CI.** Replaced with filesystem discovery; suite count went 856 → 1071 on the same commit. A guard test blocks any return to a hardcoded list.
- **Cookie consent:** Direction B tokens, Lucide `X` for the `×` glyph, focus rings added (there were none). Accept/Reject moved onto one shared class constant — equal visual weight is a GDPR requirement, not a style choice; the constant is asserted to carry no brand fill.
- **Legal pages:** `max-w-shell-reading` (the token T-060 created for exactly this), typography scale, focus ring on the cross-link. Fixed a 320px overflow this ticket introduced by raising the h1 to 28px, which pushed the unbreakable Russian word "конфиденциальности" past the viewport — resolved with inherited `break-words` + `hyphens-auto`.
- **MapView overlay:** two more hardcoded Greek strings found and fixed (`Εντοπισμός τοποθεσίας`, `Η θέση σας`) — the third and fourth instances of this bug class in four consecutive tickets. The quick-dial link was emoji-only with **no accessible name at all**; now named. Marker/popup/zoom logic untouched.
- **Recorded, not silently fixed:** the real 404 users see is Next.js's built-in page (no root `app/not-found.tsx`); `SearchFilters.tsx` is dead code; `SalonCard`'s `♀`/`♂` glyphs need a product decision. Each is pinned by a test. Auth/dashboard/admin (~394 legacy utilities) confirmed out of phase scope.

**Verification:** 51 new tests + 1 pre-existing T-018 test updated (locator only, guarantee strengthened). **1071/1071 passing**, and for the first time that covers every test file in the repo. Lint/build clean; bundle flat. Isolated Playwright: 32 combinations (4 locales × 2 legal pages × 4 breakpoints) — zero overflow, one h1, landmark present, 768px reading measure, zero console errors. Consent gating re-verified: zero GA4/GTM requests and no `dataLayer`/`gtag` globals with consent absent.

**Live production verification (`https://lookla.gr`, 2026-07-30, post-deploy):** 96 breakpoint×locale combinations (legal pages and homepage/search, 4 locales × {320, 375, 390, 768, 1024, 1440}px) — zero overflow, reading measure exactly 768px, one `<h1>`, zero console errors. Consent denied → **zero** GA4/GTM requests; Reject → still zero, cookie `=0`; withdrawal mid-session → no further product events. Accept/Reject confirmed **byte-identical `className`** in the live DOM, both 44px with focus rings. Settings mode: `role="dialog"`, close control with `aria-label="Close"` + Lucide SVG + focus ring, Escape closes. `search_results_view` once on load and **zero** on Back; `salon_open` exactly once; one `contact_action` per click; PII scan clean. T-056: 48 cards **and scroll** restored exactly (9059 → 9059) — an earlier `scrollY=0` reading was a test artifact (clicking the first card makes Playwright scroll to top before dispatching), not a product defect; the same flaw affected T-066's script. MapView in all 4 locales: Leaflet + 2000 markers, no emoji, hardcoded Greek gone from en/ru/uk; marker `tabindex` is Leaflet's native default, unchanged. Salon detail: gallery fix holding (3 tiles, one row), localized `+N photos`, CLS 0.0029–0.0044. Async states: `role="alert"`/`role="status"` + localized Retry in all 4 locales. `npm test` on the deployed commit: **1071/1071**.

```text
T-067 regressions: 0
```

**Acceptance Criteria:**
- [x] Cookie consent UI on Direction B, with equal Accept/Reject weight preserved and enforced
- [x] Legal pages at reading width with shared typography
- [x] Shared `AsyncSection` states verified aligned (already tokenised — no change needed)
- [x] Full cross-page consistency audit, with out-of-scope surfaces explicitly recorded
- [x] All 4 locales × main breakpoints verified
- [x] Accessibility verified (landmarks, single h1, accessible names, focus rings)
- [x] Consent + GA4 invariants verified unchanged; no analytics taxonomy change
- [x] T-063 Map Accessibility not started (asserted by test)
- [x] No ranking experiments
- [x] Live production verification — passed on `https://lookla.gr`
- [x] Beta Visual Baseline timestamp recorded — `2026-07-30 11:39:31 Europe/Athens (EEST)`
- [x] Independent review — **APPROVE**

---

### T-063 — Map Accessibility
**Priority:** P1 | **Owner:** FE | **Epic:** EPIC-09
**Dependencies:** T-042 ✅, T-054 ✅, T-056 ✅, T-057 ✅, T-058 ✅, T-064 ✅, T-067 ✅ (Visual Baseline v1 complete, so marker/popup internals were still untouched when this started)
**Status:** ✅ Completed. Reviewed (one round of **REQUEST CHANGES** on the container tab stop, fixed and re-verified), **APPROVE**, merged via PR #63 (`089d4b8` on `main`), `beauty_web` rebuilt and restarted alone — API/DB/Redis/crawler/crawler_worker untouched — production smoke passed on `https://lookla.gr`.

**Ticket-identity note:** T-063 had been carried as an informal placeholder since the T-061→T-062 collision and was formally claimed here. No competing use existed.

**The defect, measured on production before any change:**

| Measure | Before | After |
|---|---|---|
| Markers rendered | 2000 | 2000 (unchanged) |
| Markers with `tabindex="0"` | **2000** | **1** |
| Markers with an accessible name | **0** | **2000** |
| Total focusable elements on the page | **2023** | **20** |
| Map container accessible name | none | localized |

Leaflet's `keyboard: true` default gives every marker `tabindex="0"` and `role="button"`. With 2000 markers that made the map ~99% of the page's tab stops, all of them unnamed — a keyboard user needed ~2000 presses to reach the footer, and a screen reader announced "button" 2000 times with no label.

**Approach — a true roving tabindex**, per the WAI-ARIA composite-widget convention (Tab moves between components, arrows move within one, only one element of the composite is in the tab sequence):
- `keyboard: false` on markers removes Leaflet's per-marker tabindex; focus is managed explicitly. Exactly one marker carries `tabindex="0"`, the remaining set members carry `-1`, and **Tab lands directly on the active marker** — not on a wrapper that needs a further keypress (that would be closer to `aria-activedescendant`, which is harder to verify in real screen readers on this DOM).
- **`keyboard: false` on the *map* as well — a review finding.** The first implementation left Leaflet's map-level keyboard handler enabled, which puts `tabindex="0"` on the *container*. That made the container an extra tab stop in front of the marker collection, so reaching the active marker took **two** Tab presses — not a roving tabindex, and directly contradicted the contract. Disabling it also removes Leaflet's container-level arrow-panning, which would otherwise bind the same keys as marker navigation. Panning is not needed to reach any navigable marker, because the keyboard set is viewport-bounded so every arrow target is already on screen; the zoom controls remain independently tabbable. The container keeps `role="group"` and a localized `aria-label` for browse-mode context, and its `tabindex` is additionally cleared defensively in case a future Leaflet version sets it regardless of the option. Verified live: container `tabindex` is `null`, and the tab order is `… → Map toggle → active marker → Zoom in → Zoom out → attribution links`.
- **Bounded set:** viewport markers, capped at 50 nearest the map centre, salon id as a stable tie-breaker so identical geometry yields an identical set. Recomputed on `moveend`/`zoomend` only, and **frozen** while a marker holds focus, a preview is open, or the user is arrowing; a pan that arrives while frozen is applied once the lock releases. If the active marker leaves the set, focus falls back to the nearest remaining member.
- **Spatial arrows** computed from projected container points, never raw lat/lng — under Web Mercator "north" is not a constant screen direction. Two-pass cone: a narrow pass first, then a wide fallback. The narrow pass exists because a single permissive cone let ArrowRight and ArrowUp resolve to the *same* diagonal marker (observed live), which reads as the direction keys being broken; the wide fallback keeps sparse scatters reachable rather than dead-ending. No wrapping — a dead end leaves focus put and stays silent. `Home`/`End` jump to the ends of the stable visual order.
- **Activation & preview lifecycle:** Enter and Space both open the existing preview, Space with `preventDefault` so the page does not scroll. Keyboard activation moves focus to the first interactive link in the card; **pointer activation deliberately does not move focus**. Escape closes and restores focus to the originating marker. The preview is *not* a modal — no `role="dialog"`, no `aria-modal`, no focus trap, and Tab continues through the page normally.
- **Pointer/keyboard sync:** a mouse click adopts the roving index, so a later Tab returns to the last marker used and the two input modes cannot diverge.
- **Accessible names:** `{name}, {area}, rating {rating}, {position} of {count} visible salons`. A missing area is omitted and a missing rating is omitted rather than announced as "rating 0". Coordinates, phone and street address are excluded to keep names short enough to arrow through. Markers *outside* the keyboard set are still named, so browse-mode users are not left with bare unnamed buttons.
- **Announcement:** one polite message on first entry, carrying the real set size ("50 of 2000"), never repeated per arrow — per-marker position already lives in each marker's own name, so arrowing is not announced twice.
- **Preserved:** the map container gained a name but no invented role; Leaflet's zoom and attribution controls remain exactly where they were in the tab order (verified: they follow the single marker stop).

**Explicitly out of scope and untouched:** clustering, ranking, marker data, map fetching, and the `salon_open` analytics contract from the map. The preview's plain-`<a href>` hard navigation was left open here and is **fixed by T-068** (see below).

**Verification:** 54 new tests in `lib/mapKeyboardNav.test.ts` — the pure geometry/selection module is unit-tested without Leaflet or a DOM, plus source-level assertions on the wiring. 1 pre-existing T-067 guard retired (it asserted *no* keyboard work existed in `MapView` specifically to stop a visual pass from starting T-063; that purpose is now fulfilled, and it was replaced with an assertion that still holds — that `MapView` owns no data/fetching/clustering concerns). Full suite **1125/1125**. Lint/build clean; search bundle unchanged at 9.58kB (`MapView` is dynamically imported). Isolated Playwright: tab-stop census (2023→20), a tab walk confirming the container is **not** a stop and Tab reaches the marker in one press before continuing through Leaflet's controls, four distinct arrow moves, single-`tabindex=0` invariant maintained after arrowing, no map panning during marker arrow navigation (the conflict `keyboard: false` removes), Space opening with `scrollDelta=0`, focus landing on the first preview link, Escape restoring marker focus, pointer sync without forced focus, the hint announced from marker focus and still exactly once after leaving and re-entering the collection, and all four locales confirmed localized (map label, rating word, position, hint).

**Acceptance Criteria:**
- [x] Exactly one marker in the tab sequence; Tab lands on it directly in one press
- [x] The map container is named but **not** tabbable — no extra stop before the markers
- [x] Container-level arrow panning does not compete with marker arrow navigation
- [x] Bounded, deterministically ordered keyboard set (≤50, viewport, nearest-to-centre, id tie-break)
- [x] Set frozen during focus/preview/arrow interaction; nearest-member fallback after pan/zoom
- [x] Spatial arrow navigation from projected points; no wrapping; silent dead ends
- [x] Enter and Space activate; Space does not scroll
- [x] Focus enters preview on keyboard activation only; Escape restores marker focus; no focus trap
- [x] Pointer clicks sync the roving index
- [x] Localized accessible names omitting missing area/rating; no coordinates/phone/address
- [x] One-time announcement with the real set size, in 4 locales
- [x] Leaflet zoom/attribution controls preserved in tab order
- [x] No clustering, ranking, marker-data or fetching changes; `salon_open` contract unchanged
- [x] Live production verification — passed on `https://lookla.gr`
- [x] Independent review — **APPROVE** (after one REQUEST CHANGES round)

**Live production verification (`https://lookla.gr`, 2026-07-30, post-deploy):** 2000 markers still rendered; container `tabindex: null` with `role="group"` and a localized name in every locale; exactly **1** marker at `tabindex="0"`, 49 at `-1`, 1950 with none, **2000/2000 named**; total focusable elements **23**. Tab order confirmed live: `Map toggle → active marker → Zoom in → Zoom out → attribution` — one press from the toggle to the marker, container never a stop. Hint announced once on first marker focus with the real counts, still exactly one entry after arrowing. Four arrows produced four distinct spatial moves; **map pane transform unchanged** during arrow navigation (no residual pan conflict); single-`tabindex=0` invariant held. Space opened the preview with `scrollDelta=0` and moved focus to the first link ("Call"); no `role="dialog"`. Enter also opened it. Escape closed it and restored focus to the originating marker. Pointer click adopted the roving index (clicked `8916` → roving `8916`, one `tabindex=0`) without forcing focus into the card. `salon_open` fired **exactly once** from the preview link with the unchanged shape (`{salon_id, source: "search_map", locale}`). All four locales verified: localized map name, rating word and position clause, localized hint with real counts, **zero** "rating 0" announcements, zero coordinate leaks. List view untouched (24 cards, no Leaflet markers present, `aria-pressed` intact). No horizontal overflow at 320/375/768/1280px. Zero console or page errors throughout.

*One name flagged by the empty-segment scan* — `"Фризерски Салон -,, Дијана\", Berovo, рейтинг 5.0"` — is **pre-existing dirty crawler data**: the `,,` is inside the salon's own stored name, and the composed segments (name, area, rating) are all correct. Data hygiene, not a T-063 defect, and deliberately not fixed here.

**Beta Visual Baseline unaffected:** the analytics baseline continues from `2026-07-30 11:39:31 Europe/Athens (EEST)`. T-063 changed no event taxonomy and no conversion-event contract, so there is nothing to re-anchor.

```text
T-063 regressions: 0
```

---

### T-068 — Map Preview Client Navigation & Search Return Preservation
**Priority:** P1 | **Owner:** FE | **Epic:** EPIC-09
**Dependencies:** T-056 ✅, T-058 ✅, T-063 ✅
**Status:** ✅ **Completed with documented follow-up.** Reviewed, **APPROVE**, merged via PR #64 (`749aa1e`), deployed to production **2026-07-30 15:52:12 Europe/Athens (EEST)** — `beauty_web` alone, API/DB/Redis/crawler/crawler_worker untouched.

```text
T-068 implementation goal: achieved
T-068 regressions introduced: 0
Known inherited analytics defect discovered: T-069
```

Deliberately **not** recorded as "the full checklist passed without exception": one smoke acceptance point (`search_results_view` must not fire after Back) is not met on the map path. That defect predates T-068, did not worsen, requires a separate analytics decision, and is unrelated to the client-navigation mechanism — it is owned by **T-069**. See "Open finding" below.

**Map-return-flow UX boundary marker:** `2026-07-30 15:52:12 Europe/Athens (EEST)` — from this deployment, returning from a map-opened salon preserves search state. Useful for segmenting map-path return behaviour in later analysis. This is **not** a baseline reset: the Beta Visual Baseline remains `2026-07-30 11:39:31 Europe/Athens`, since T-068 changed no GA4 taxonomy and no conversion-event shape.

**Ticket-identity note:** T-068 confirmed free before branching (highest number previously in use was T-067).

**The defect.** The map preview's "view salon" control was a plain `<a href>`, so activating it performed a full-document navigation. T-056 stores its search-return snapshot in a **module-scope Map** and writes it from a **save-on-unmount cleanup**. A hard navigation destroys the JS realm — the cleanup's write is lost along with the store — so returning from a salon opened via the map always remounted the search page at page 1 with scroll discarded. Registered as a known limitation in T-056 and carried unchanged through T-063.

**Root-cause detail worth keeping:** the search page's capture-phase scroll-freeze listener was *never* the problem. Its selector is `a[href*="/salons/"]`, which already matched the map preview link (and still matches what `next/link` renders). The only broken link in the chain was realm survival.

**The fix.** One element swap: `<a href>` → `next/link`'s `<Link href>`. Nothing else changed — the destination expression, the `salon_open` call, and the className are byte-identical, and the search page was not touched at all.

Deliberately **not** routed through `Link`: the adjacent `tel:` quick-dial. An external protocol is not a route, and handing it to the router would break it.

**Verification:** 16 new tests in `lib/mapPreviewNavigation.test.ts` (client-side mechanism, byte-identical destination/analytics/styling, `tel:` still a plain anchor, no `Link` carrying an external protocol, T-056 machinery untouched with exactly one `saveSnapshot` call site, T-063 keyboard model intact). One T-056 test **inverted**: it existed to document the limitation and explicitly said "if this ever changes to `<Link>`, the limitation (and this test) should be revisited" — the tripwire fired correctly and now asserts the fix, so a regression to a hard navigation fails in two suites. Full suite **1141/1141**. Lint/build clean; search bundle unchanged at 9.58kB.

Isolated Playwright, full `Map → preview → salon detail → Back` flow with the precondition actually established first (48 cards loaded via scroll before switching views):
- **Client-side navigation proven directly** via a realm probe (`window.__realmProbe`), which survives a client-side transition and dies on a document load. It read `alive` on the destination page. `framenavigated` counts were *not* used, because they fire for both kinds of navigation and cannot discriminate.
- **48 cards restored** after Back (the exact loss this ticket targets).
- **Scroll restored exactly.** Worth recording how this was measured: returning lands on **map** view, which is only ~181px scrollable, so an early run showing `scrollY=0` looked like a failure but was in fact correct restoration of a genuinely-zero position. Re-measuring with the map scrolled to its maximum first gave `181 → 181`, exact. This is the same measurement trap that produced false scroll "failures" in T-066 and T-067; the expected value must be captured before the navigation, never assumed.
- `salon_open` fires **exactly once** per activation with the unchanged shape (`{salon_id, source: "search_map", locale}`).
- **Ctrl+click still opens a new tab** with the correct destination and leaves the map page in place — `Link` preserves browser modifier defaults (verified on a clean element, after an initial run was invalidated by a `preventDefault` listener left over from the previous step).

**Acceptance Criteria:**
- [x] Preview navigation is client-side; the T-056 realm and snapshot survive
- [x] Destination unchanged (slug with numeric id fallback)
- [x] `salon_open` unchanged in name, shape and source; exactly one call site; fires once
- [x] Visual treatment unchanged — this is not a visual ticket
- [x] `tel:` remains a plain anchor; no `Link` carries an external protocol
- [x] Search page and T-056 snapshot machinery untouched (one `saveSnapshot` site)
- [x] T-063 keyboard model intact (Enter/Space, Escape, roving tabindex, focus-to-first-link)
- [x] 48 cards restored after `Map → preview → detail → Back`
- [x] Scroll restored exactly, against a measured expected value
- [x] Modifier-click browser defaults preserved
- [x] Live production verification — passed, except the one item below
- [x] Independent review — **APPROVE**
- [ ] `search_results_view` must not fire after Back — **NOT met on the map path** (fires 2×); inherited defect, owned by **T-069**, see below

**Live production verification (`https://lookla.gr`, 2026-07-30, post-deploy):** 48 cards established in List first (24 → 48, scrollY 2767), switched to Map, scroll set to its 181px maximum, preview opened by keyboard, navigated to salon detail, browser Back. Results: realm probe read `alive` on the detail page (**client-side, no new document**); returned to `view=map` with Leaflet rendered; **scrollY 181 → 181 exact** against the pre-measured value; **48 cards restored** (confirmed by switching back to List); **no page-1 flash** (card-count sampled 8× during restore, never showed 24); **no repeat initial search fetch** (`/api/salons?limit=24&page=1` did not reappear — only MapView's own `/api/salons/map?` refetch on remount, pre-existing); `salon_open` fired **exactly once** with the unchanged shape and **no second fire on detail mount**; destination, locale (`en`) and query context preserved; `tel:` still a plain `<a href="tel:...">`; Ctrl+click opened a new tab with the correct destination leaving the map page intact; T-063 keyboard model intact; no horizontal overflow; zero console or page errors.

### Open finding — `search_results_view` fires 2× on Back via the map path

**Measured, with a correct comparison baseline:**

| Path | `search_results_view` after `→ detail → Back` |
|---|---|
| List (card → detail → Back) | **0** — T-058 dedup works |
| Map (preview → detail → Back) | **2** |

**Root cause — a pre-existing T-058 design limitation, not caused by T-068.** `lib/searchResultsViewDedup.ts` stores **one** material key per history entry (`Map<entryId, string>`, written with `.set(entryId, key)` and checked with `.get(entryId) === key`). The map view legitimately reports **two different** material keys within a single history entry:

1. `all|0|map|en` — a transient state where `mapLoading` has already gone false but `mapSalons` is still empty
2. `all|51_plus|map|en` — once map data arrives

The second `.set` **overwrites** the first, so the store ends up holding only key 2. On Back, key 1 no longer matches (fires), then key 2 no longer matches because key 1 was just written (fires). The list path is unaffected because it only ever reports one key per entry. `entryId` was verified **preserved** across the whole cycle (`cddcade6…` before and after), so this is not an entry-identity problem.

**Not a regression.** Before T-068 the map path did a full-document navigation, so the dedup store was destroyed and both keys fired on Back anyway — the count was already 2. T-068 neither improved nor worsened it; it made the gap *visible and fixable* by preserving the realm. (Count-before is inference from the mechanism, not a live measurement, since production now carries T-068.)

**Secondary observation worth its own attention:** the transient `result_count_bucket: "0"` map event reports a "zero results" view that was never a real user-visible state — the map was simply still loading. That inflates the 0-bucket in analytics independently of the dedup issue.

**Resolution:** owned by **T-069 — Map Search Results View Stabilization**, with **variant (b) approved**: suppress the transient empty-map report so the map only reports a resolved, user-meaningful result state. This removes the double report at source and fixes the misleading 0-bucket. The `Map<entryId, string>` → `Map<entryId, Set<key>>` storage change is explicitly **not** bundled in: once the false zero is gone, a single correct key remains per entry and existing dedup should suffice. A regression test for an `A → B → A` material-state cycle will decide whether the Set is ever actually needed, rather than introducing it speculatively.

---

### T-069 — Map Search Results View Stabilization
**Priority:** P1 | **Owner:** FE | **Epic:** EPIC-09
**Dependencies:** T-015 ✅, T-042 ✅, T-056 ✅, T-058 ✅, T-068 ✅
**Status:** ✅ **Completed with documented follow-up.** Reviewed, **APPROVE**, merged via PR #65 (`2b5d5a6`), deployed to production **2026-07-30 18:26:17 Europe/Athens (EEST)** — `beauty_web` alone, API/DB/Redis/crawler/crawler_worker untouched.

```text
T-069 regressions: 0
```

T-069's own contract is fully verified live (see below). One smoke item — the stale-response race — **failed**, and is a **pre-existing unprotected defect that T-069 neither introduced nor claims to fix**. Owned by **T-070**, see "Open finding" below.

**Map `search_results_view` correction boundary:**

```text
Map search_results_view correction boundary:
2026-07-30 18:26:17 Europe/Athens (EEST)
```

From this timestamp the meaning and count of Map `search_results_view` change: transient pre-request states no longer emit a false `result_count_bucket: "0"`, and a restored map view no longer re-fires. For any KPI using `search_results_view` as a denominator, Map data either side of this boundary must be separated or explicitly annotated. This is **not** a conversion-baseline reset — the Beta Visual Baseline remains `2026-07-30 11:39:31 Europe/Athens`, and `salon_open` / `contact_action` are unaffected.

**Ticket-identity note:** T-069 confirmed free before branching.

**The defect (inherited, surfaced by T-068).** `mapLoading` is initialised `false`. The fetch effect is declared *before* the tracking effect, but the `setMapLoading(true)` it performs does not change the value already captured in the current render's closure — so on the very first map render the tracking effect saw `mapLoading === false` with `mapSalons === []` and reported `result_count_bucket: "0"`. That "zero results" view never existed: the request had simply not started.

Two consequences: the 0-bucket was inflated with states no user ever saw, and because T-058's dedup store holds one material key per history entry, the false `all|0|map|<locale>` was immediately overwritten by the real `all|51_plus|map|<locale>` — so on Back neither matched and **both fired again**.

**Approved approach — variant (b): report only resolved states.** "Not loading" is not "resolved": `!loading` is true both before a request starts and after it finishes, and an empty array looks identical in both. Resolution is now tracked explicitly (`mapResolved`), cleared when a request begins and set only when one settles successfully. The decision itself lives in a pure, Leaflet-free, DOM-free module (`lib/mapResultsResolution.ts`) so it is directly unit-testable.

`result_count_bucket: "0"` is still sent — but only when a completed request genuinely matched nothing. Verified live: a query matching no salons produces exactly one `"0"` map event.

**Deliberately NOT changed: the dedup storage model.** `Map<entryId, string>` stays as-is. An `A → B → A` cycle (List → Map → List → Map) *does* re-send the map key — but every List/Map toggle pushes a **new history entry with a distinct `entryId`** (measured: `99918f5e…` → `7e8347e8…` → `d810b731…` → `5dcd41f5…`), so the two reports live under different entries. A `Map<entryId, Set<key>>` would change nothing: the second lookup misses on the *entry* key, not on the material key within it. Semantically the re-send is also correct — `view` is part of the material key, and a deliberate toggle that creates a history entry is a genuinely new view of results. The dedup's job is suppressing re-reports of the *same* entry (Back restoration), which is verified and passes. Recorded with the reasoning so a `Set` is not introduced later on the strength of the bare "it fired twice" observation.

**Verification:** 25 new tests in `lib/mapResultsResolution.test.ts` (resolution semantics, genuine-vs-transient emptiness, full slow-API lifecycle, filter/locale/retry invalidation, page wiring, batching order, error path, unchanged payload, untouched event owners, and the A→B→A reasoning). Three pre-existing tripwires updated — they pinned the literal `if (mapLoading || mapError) return;` and the exact 9-dependency array, both of which T-069 intentionally changes; each now asserts the same underlying guarantee against the new structure (map branch still gates on raw `mapLoading`/`mapError` and never on AsyncSection-derived status; the gate still precedes computing the bucket; the dependency array is asserted as a *set* of required gating variables rather than a brittle literal). Full suite **1166/1166**. Lint clean (zero warnings on both touched files); build clean; search bundle unchanged at 9.64kB.

Isolated Playwright (map API artificially delayed 6s to reproduce the real production timing):

| Scenario | Result |
|---|---|
| Mid-flight, slow map API | **no** map event at all — the false `"0"` is gone |
| After resolution | exactly **1** map event, `51_plus` |
| Map → preview → detail → Back | `search_results_view` = **0** (was **2**), `salon_open` = 1 |
| List → detail → Back | **0** — no regression on the working path |
| Genuine empty completed request | exactly **1** event with `"0"` |
| Filter change (`area=glyfada`) | 1 new correct event, **no** transient `"0"` |
| Locale change (`ru`) | 1 correct event, `locale: "ru"`, no transient `"0"` |
| Consent denied | **0** events |

*Instrumentation note:* the isolated build carries no GA4 id, so `gtag.js` never loads and `trackEvent` bails on its `typeof window.gtag !== 'function'` guard. A first run therefore reported zeros everywhere — including states that should have fired — which would have read as a false pass. Stubbing `window.gtag` (rather than patching `dataLayer.push`, the approach production requires because the real `gtag.js` overwrites a stub) produced valid measurements.

**Acceptance Criteria:**
- [x] Slow map API creates no transient `"0"` event
- [x] Unresolved results are never treated as empty
- [x] A genuinely completed empty request sends exactly one `"0"`
- [x] A non-empty map result sends one correct bucket
- [x] The transient empty state no longer overwrites the dedup key
- [x] Map → detail → Back sends 0 new events
- [x] List → detail → Back unregressed
- [x] List/Map toggling follows the existing material-key contract
- [x] Filter change sends a new event after resolution
- [x] Locale change sends a correct new event
- [x] Snapshot restoration creates no intermediate `"0"`
- [x] Consent denied sends nothing
- [x] Event name and payload shape unchanged
- [x] `salon_open` / `contact_action` untouched
- [x] Production-like delayed response exercised in Playwright
- [x] Live production verification — passed for every T-069 item
- [x] `Map search_results_view correction boundary` recorded
- [x] Independent review — **APPROVE**
- [x] Stale-response race — **FAILED** here; pre-existing, not introduced by T-069, owned by **T-070** ✅ (fixed and verified live on `2026-07-31`)

**Live production verification (`https://lookla.gr`, 2026-07-30, post-deploy, real `gtag.js` intercepted via `dataLayer.push`):**

| # | Check | Result |
|---|---|---|
| 1 | Slow map API (6s) emits no transient `"0"` | **0 map events mid-flight** ✅ |
| 2 | After resolution, one correct bucket | 1 × `51_plus` ✅ |
| 3 | Genuine empty completed request | exactly 1 × `"0"` ✅ |
| 4 | Map → preview → detail → Back | **0** (was 2), `salon_open` = 1 ✅ |
| 5 | List → detail → Back | 0 ✅ |
| 6 | Filter change (`area=glyfada`) | 1 correct event, no transient `"0"` ✅ |
| 7 | Locale change (`ru`) | 1 correct event, `locale: "ru"` ✅ |
| 9 | Consent denied | 0 GA/GTM requests, 0 product events ✅ |
| 10 | Consent withdrawal | 0 further product events ✅ |

### Open finding — stale map response replaces current data (pre-existing, → T-070) — ✅ RESOLVED by T-070

There is **no** request-cancellation or latest-request guard in `search/page.tsx`: no `AbortController`, no request token, no `signal`. Confirmed by inspection and then by live measurement.

**Reproduced in production**, with the realm verified preserved (so this is a true in-realm race, not an artifact of a full navigation):

```text
request A (area=all)      delayed 16s   ─┐
  user changes filter in-page → glyfada  │  client-side router.push, realm survives
request B (area=glyfada)  400ms  ────────┘
B resolves   → 76 markers, 1 correct event (area=glyfada)
A lands late → 2000 markers   ← B's data REPLACED, URL still says area=glyfada
```

Against the four required properties of a stale response:

| Must not… | Observed |
|---|---|
| replace B's data | ❌ **violated** — 76 → 2000 markers while the filter reads Glyfada |
| re-mark the state as resolved | ❌ violated — the stale `.then` sets `mapResolved` true again |
| emit an extra bucket | ✅ none observed — **but coincidentally**: Glyfada (76) and all (2000) both bucket to `51_plus`, so the material key was unchanged. With a smaller area the stale count would produce a *different* bucket under the *current* area and would emit a wrong event |
| overwrite the dedup key | ✅ none — no event fired, so nothing was recorded |

**Not introduced by T-069.** The data-replacement half has existed for as long as the map fetch has had no cancellation. T-069 adds only the (harmless in isolation) re-assertion of `mapResolved`. T-069's mandate was the reporting semantics of resolved states, not the fetching contract, and the approval explicitly said fetching was not to be rewritten — so this is recorded rather than silently expanded into.

**Two earlier attempts at this test were invalid and are recorded so the result isn't over-trusted:** the first used `page.goto()` for the filter change, which is a full navigation that destroys the realm and the pending request, so no race existed; the second failed to open the filter popover (the page has two `aria-controls` buttons — the header burger renders first, per the T-064 note — so the selector matched the wrong one) and issued only one request. Only the third run, which used `div.relative button[aria-controls]` and an in-page `change` event, genuinely exercised the race.

**→ T-070 — Map Request Cancellation & Latest-Request Contract.** Should ensure a superseded map request cannot replace current data, re-assert resolution, or emit a bucket, via an `AbortController` or a request-token guard. Needs its own verification including the differing-bucket case that this run could not distinguish.

**Resolved:** T-070 shipped `2026-07-31 17:34:10 Europe/Athens`. The same scenario now leaves 76 markers at 76 in production. The differing-bucket concern was addressed by measuring **marker counts** directly rather than relying on analytics, since both counts share the `51_plus` bucket.

**Analytics data boundary (to be recorded after deploy):** T-069 changes both the meaning and the count of Map `search_results_view`, so its production deployment timestamp must be recorded as a `Map search_results_view correction boundary`. For KPIs using `search_results_view` as a denominator, Map data either side of that boundary must not be mixed without annotation. This does **not** reset the conversion baseline: the Beta Visual Baseline remains `2026-07-30 11:39:31 Europe/Athens`, and `salon_open` / `contact_action` are unaffected.

---

### T-070 — Map Request Cancellation & Latest-Request Contract
**Priority:** P1 | **Owner:** FE | **Epic:** EPIC-09 | **Phase:** Post-Baseline correctness
**Dependencies:** T-056 ✅, T-058 ✅, T-063 ✅, T-068 ✅, T-069 ✅
**Status:** ✅ Completed. Reviewed, **APPROVE**, merged via PR #66 (`47371ae` on `main`), `beauty_web` rebuilt and recreated alone — API/DB/Redis/crawler/crawler_worker untouched (`Up 2 weeks` / `Up 10 days` across the deploy) — production verification passed on `https://lookla.gr`, including a live reproduction of the original defect.

**The defect** (found during T-069 production verification, pre-existing): a slow `area=all` request landed *after* an in-page filter change to `area=glyfada` had already resolved, and replaced 76 Glyfada markers with 2000 all-area markers while the URL and the active filter still read Glyfada. A data/UI consistency violation, not merely an analytics inaccuracy.

#### Step 1 — Request-lifecycle inventory (before)

Every map-state write lived in one `useCallback` (`loadMapSalons`), started by `useEffect(() => { loadMapSalons(); }, [loadMapSalons])`, plus a Retry button reusing the same callback. Request inputs: `view, area, city, q, category, minRating` (the callback's own deps). There was **no** `AbortController`, no request token, no `signal`, and the effect had **no cleanup at all**.

| State write | Context | Stale request could reach it? |
|---|---|---|
| `setMapLoading(true)`, `setMapError(false)`, `setMapResolved(false)` | synchronous, at start | No |
| `setMapSalons(d)`, `setMapResolved(true)` | `.then` | **Yes** |
| `setMapSalons([])`, `setMapError(true)` | `.catch` | **Yes** |
| `setMapLoading(false)` | `.finally` | **Yes** |

All four asynchronous paths were unguarded — matching the observed behaviour exactly.

#### Steps 2–4 — Request identity, cancellation and ownership

`lib/latestRequest.ts` provides a `LatestRequestTracker` (plain class, no React, no DOM, no timers) held in a per-instance ref:

- `start()` aborts the previous controller, creates a new one, and increments a **monotonic generation**, returning a handle.
- `owns(handle)` is false if the handle's signal is aborted **or** its generation is no longer current.
- `invalidate()` aborts and bumps the generation without starting anything — used by the effect cleanup, so nothing can write after unmount or after a dependency change.

No new request key was invented: the existing callback dependencies already define the request completely, and a generation is minted whenever a real request starts (including Retry, which reuses the same callback).

**The generation token is the correctness guarantee; `AbortController` is cleanup and best-effort network cancellation.** Ownership is re-checked after *every* async boundary — response, parse, `catch`, and `finally` — and is assigned at start, never inferred by comparing a response against current state afterwards. That distinction is load-bearing: in the production case both counts fell in the same `51_plus` bucket, so a data-comparison or analytics-only check would have seen nothing wrong.

**The `finally` guard is explicit and deliberate:** a stale request settling last must not clear the loading state of a newer request that is still running.

#### Step 5 — Abort handling

`isAbortError(err, signal)` checks both `name === 'AbortError'` and `signal.aborted`, since runtimes differ. An abort renders no error, triggers no Retry UI, marks nothing resolved, clears nothing, and emits no analytics. Non-abort failures from the *latest* request keep their existing behaviour. Unrelated errors are not broadly swallowed — a bare `'AbortError'` string is explicitly rejected by a test.

#### Steps 6–7 — Loading UX and T-069 integration

The presentation decision is untouched — T-070 changes request ownership only. The T-069 resolved-state contract is preserved exactly: only the latest request may set `mapResolved` true, so a stale response can produce no false `"0"`, no bucket from old results, no second event, and no dedup-key overwrite. Event name, payload, bucket definitions, consent gating, `entryId` ownership and the dedup-store structure are all unchanged.

#### Verification — controlled settlement order

35 tests in `lib/latestRequest.test.ts`. Race tests use **deterministic deferred promises**, never timers, so the settlement order is exact (`resolve B; assert; resolve A; assert still B`): A-slow/B-fast, A-fast/B-slow, stale-failure-after-success, stale-success-after-failure, A→B→C, abort, unmount, retry, and an explicit "identical-looking payloads still respect ownership" case. One pre-existing T-056 tripwire updated — it pinned `loadMapSalons` and the one-line effect as byte-unmodified, both of which T-070 necessarily changes; it now asserts the guarantee it actually exists for (restoration never skips, gates or caches the map refetch).

Three scenarios from the test contract initially had no explicit assertion and were added before merge: the **locale-change race** (structurally the same guarantee as a filter change, but asserted separately because stale data rendering under the new locale's accessible names and analytics tagging is a distinct, worse failure); **a stale response emits no bucket, so it cannot overwrite T-058's per-entry dedup key** (asserted through the model's event log, not by reaching into the store); and **consent gating stays delegated to `trackEvent`** — exactly 3 `trackEvent(` call sites, none inside the fetch path.

Full suite **1201/1201** across 213 suites. Lint clean — including a legitimate warning this ticket surfaced and fixed properly rather than suppressed: reading `mapRequestsRef.current` inside the effect cleanup is the pattern that breaks when a ref stops being stable, so the tracker is captured in a local inside the effect. Build clean; search bundle 9.64 → 9.89kB.

#### Isolated Playwright — real filter UI, same realm throughout

| Scenario | Result |
|---|---|
| Slow A (`all`, 16s) vs fast B (`glyfada`) — the production defect | **76 markers stay 76** (was 76 → 2000), URL aligned, no extra event, realm confirmed preserved |
| Stale A settles while B still pending | B stays loading, 0 events; after B resolves, exactly 1 |
| A → B → C (`all` → `glyfada` → `piraeus`) | C resolves first; A and B land late; **still 1 event, `piraeus`, 90 markers** |
| Stale 500 after latest success | no error UI, markers kept, **no console errors** |
| Stale success after latest failure | latest error preserved, no map event |
| Unmount mid-request | no page errors, no post-unmount write |
| T-056 / T-068 / T-069 boundaries | Back → `view=map`, scroll **181 → 181**, 48 cards restored, `search_results_view` **0**, `salon_open` **1**, preview still a `Link` with realm alive |
| T-063 boundary | 2000 markers, 1 × `tabindex="0"`, 49 × `-1`, 2000 named, container `tabindex: null` |

**Verification traps recorded, because each one produced a misleading result before being corrected:**
- `page.goto()` between A and B **destroys the race** — a full navigation tears down the realm and the pending request. The filter change must go through the real in-page control.
- The page has **two** `aria-controls` buttons; the header burger renders first, so a naive selector opens the wrong one. Use `div.relative button[aria-controls]`.
- Clicking an **already-open** popover trigger closes it — an `ensureOpen` helper must check `aria-expanded` first. This silently turned an intended A→B→C into A→B on the first attempt.
- **"No extra analytics event" alone is not proof.** Glyfada (76) and all-areas (2000) both bucket to `51_plus`, so the original stale response was completely invisible to an analytics-only check. Marker counts had to be measured directly.

#### Production verification — `https://lookla.gr`, after deploy

The original defect was reproduced live against production with the real filter UI, holding request A at the network layer:

| Check | Result |
|---|---|
| Slow A (`area=all`, held 15s) vs B (`area=glyfada`) — **the production defect** | markers **76 → 76** after the stale A landed (was 76 → 2000); URL `?view=map&area=glyfada` aligned; realm probe `alive` |
| Analytics during the race | 3 events (`area_select`, `page_view`, `search_results_view` @ `area: glyfada`); stale A added **none** |
| Page errors during the race | none |
| Locale change mid-flight (`en` → `ru` via the real `router.replace()` switcher) | URL `/ru/search?view=map&area=glyfada`, markers **76 → 76**, events 3 → 3, single `search_results_view` tagged `locale: "ru"`, realm `alive` |
| T-069 boundary | exactly one `search_results_view`, bucket `51_plus` — **not** the false `"0"` |
| T-063 boundary | 2000 markers, keyboard set bounded at 50 (1 × `tabindex="0"`, 49 × `-1`), the other 1950 carry no `tabindex` and are **not focusable** (verified by `focus()` + `activeElement`); container `tabindex: null`, `role="group"` + label intact; 20 focusable elements page-wide |

**Two further verification traps, recorded because each produced a misleading reading first:**
- `gtag` pushes an **`arguments` object, not a real `Array`**. An `Array.isArray(a)` guard in a `dataLayer.push` capture helper silently drops every event of interest and yields a vacuous "0 events, so no extra event" pass. Test the array-like shape (`a.length >= 2 && a[0] === 'event'`) instead.
- The area filter is a native `<select>` inside the popover panel, not a list of option buttons; a `getByRole('option')` locator resolves to a hidden `<option>` and times out.

One smoke assertion of mine was **wrong, not the code**: it expected all 2000 markers to carry a `tabindex`. The bounded keyboard set is capped at `KEYBOARD_MARKER_LIMIT = 50` by T-063's approved design, so 1 + 49 is correct and the remaining markers are correctly left unfocusable.

#### Safety checklist

Backend changed: **No** · Database changed: **No** · API endpoint changed: **No** · Request parameters changed: **No** · Ranking changed: **No** · Clustering changed: **No** · Marker rendering changed: **No** · Map fetching semantics changed: **Only latest-request ownership** · Previous request aborted: **Yes** · Generation/token guard added: **Yes** · Stale success can update state: **No** · Stale failure can update state: **No** · Stale finally can update state: **No** · Abort shown as application error: **No** · T-069 resolved-state contract preserved: **Yes** · False `0` bucket reintroduced: **No** · Analytics taxonomy changed: **No** · Event payload changed: **No** · Consent changed: **No** · T-056 restoration preserved: **Yes** · T-063 keyboard contract preserved: **Yes** · T-068 client navigation preserved: **Yes** · Production touched before review: **No** · PM2 used: **No** · Other containers restarted: **No** · `crawler/celerybeat-schedule` intentionally changed: **No**

**Acceptance Criteria:**
- [x] Previous map request aborted when a new one starts
- [x] Monotonic generation token is the ownership guarantee, re-checked after every async boundary
- [x] Stale success / failure / finally cannot mutate any map state
- [x] Abort is never an application error and emits no analytics
- [x] Unmount aborts and invalidates; no post-unmount writes
- [x] Retry owns loading/error/resolved state
- [x] T-069 resolved-state contract, analytics taxonomy and consent gating unchanged
- [x] T-056, T-063, T-068 contracts verified intact
- [x] List fetching untouched; List view verified (48 cards, scroll, no duplicate event)
- [x] Live production verification — the original defect reproduced and **no longer reproduces** (76 stays 76)
- [x] `Map latest-request correctness boundary` recorded
- [x] Independent review — **APPROVE**
- [x] T-070 regressions: **0**

**Boundary recorded:**

```text
Map latest-request correctness boundary:
2026-07-31 17:34:10 Europe/Athens (EEST)
```

From this timestamp a superseded map request can no longer replace current map data, re-assert resolution, emit a bucket, or overwrite the per-entry dedup key. This is a **data/UI consistency** boundary, not an analytics-taxonomy one: no event name, payload or bucket definition changed, so no KPI needs re-anchoring to it.

T-070 does **not** redefine either existing boundary — the Beta Visual Baseline stays `2026-07-30 11:39:31 Europe/Athens (EEST)`, and the Map `search_results_view` correction boundary stays `2026-07-30 18:26:17 Europe/Athens`.

---

### T-071 — Backend test gate does not run (blocking)
**Priority:** P0 | **Owner:** OPS/BE | **Epic:** EPIC-09
**Dependencies:** None
**Status:** ✅ Completed. Reviewed, **APPROVE**, merged via PR #71 (`25b3bc2` on `main`). Both halves of the gate were demonstrated on real CI before merge. No production deploy — the change touches only the workflow, test configuration, the gate checker, tests and documentation; neither `beauty_api` nor `beauty_web` was rebuilt. Post-merge CI on `main` (run **30803524633**) reports `collected 180 items`, `180 passed`, `backend test gate: tests=180 failures=0 errors=0 skipped=0` — the first time the backend job has reported a real executed count.

**The defect** (found 2026-08-03 while preparing T-050): the backend CI job had never executed a single test.

`pytest` failed during **collection**, not during any test:

```text
collected 40 items / 3 errors
ERROR collecting tests/test_areas_endpoint.py
ERROR collecting tests/test_owner_claimed.py
ERROR collecting tests/test_salons_endpoint.py
E   pydantic_core._pydantic_core.ValidationError: 3 validation errors for Settings
!!!!!!!!!!!!!!!!!!! Interrupted: 3 errors during collection !!!!!!!!!!!!!!!!!!!!
```

Those modules import `app.main` → `Settings` → requires `SECRET_KEY`, `DB_USER`, `DB_PASSWORD`. CI set none. A collection error interrupts the whole session, so **zero tests ran**, and `continue-on-error: true` reported success regardless.

The two faults compound, which is why this survived so long: the collection error means nothing runs, and the flag means nothing is reported. Every backend ✅ from T-001 to T-070 is consistent with this state — the green tick reflected a job that exited early, not a suite that passed. The flag was added deliberately ("until T-030 (tests) is complete") and was reasonable when written; the interaction with a silent collection failure was not foreseen.

#### Fix

- **`backend/conftest.py`** — pytest imports the rootdir conftest before collecting any test module, so the required settings exist whichever module is imported first. Deliberately *not* an `os.environ.setdefault` inside a test file: that only helps modules sorting after it alphabetically, which is exactly why the T-050 branch saw the error count move `3 → 1` while still running zero tests. Values are set unconditionally rather than with `setdefault`, because `Settings` also reads the repo-root `.env` — on a deployment host that holds real credentials, and a test run must be identical everywhere.
- **`continue-on-error: true` removed** from the Tests step.
- **`backend/scripts/check_test_gate.py`** — a second, independent check that reads pytest's JUnit report and fails on zero tests, on failures, on errors (collection errors count here) or on a missing report. pytest's exit code remains the primary gate; this guards the one failure mode an exit code can no longer express once something swallows it. Runs with `if: always()`.
- **The checker has its own tests** (13), each asserting the *rejecting* path. A gate-checker that always returns 0 is indistinguishable from a working one while everything is healthy — the same blind spot being fixed.
- JUnit report uploaded as a build artifact.

#### Contract evidence

| # | Requirement | Evidence |
|---|---|---|
| 1 | Required settings present before collection | `backend/conftest.py`; suite runs with **no** env setup at all |
| 2 | Independent of test-file name/order | rootdir conftest, imported before all collection |
| 3 | No `continue-on-error` / `\|\| true` / `set +e` | removed; none remain in the workflow |
| 4 | Collection error → red | `errors` counter checked by the gate script |
| 5 | Test failure → red | run **30799128415**, below |
| 6 | Zero collected tests → red | `--min-tests 1`; unit-tested in `test_test_gate.py` |
| 7 | Job shows the real executed count | `backend test gate: tests=180 failures=0 errors=0 skipped=0` |
| 8 | Deliberate failure demonstrably reds CI | run **30799128415** |
| 9 | Green again once reverted | run **30799322609** |
| 10 | Both runs kept as evidence | recorded here |

**Run 30799128415 — deliberately red** (commit `f145d69` added `tests/test_t071_gate_proof.py` asserting `1 == 2`):

```text
collected 181 items
1 failed, 180 passed
##[error]Process completed with exit code 1.
FAIL: 1 test failure(s)
backend test gate: tests=181 failures=1 errors=0 skipped=0
```

Both mechanisms fired independently — pytest's exit code *and* the report check. Note `collected 181 items` with **no** collection errors: the conftest fixed collection completely.

**Run 30799322609 — green after removing the proof test:**

```text
collected 180 items
180 passed
backend test gate: tests=180 failures=0 errors=0 skipped=0
backend test gate: OK
```

#### Consequence for T-030

T-030 remains **open**: its four named test files (`test_is_bot`, `test_open_now`, `test_translate_query`, `test_auth_refresh`) still do not exist. The `continue-on-error` flag was tied to it, but the flag was never what broke the gate — the collection error was. Removing the flag is safe because the existing 180 tests pass; it does not close T-030, and T-030 should no longer be treated as blocking the gate.

**Relationship to T-050:** T-050 ships regression tests whose whole purpose is to stop a PII leak returning. Merged into the old CI they would never have executed. T-050 was rebased onto this ticket and its `os.environ.setdefault` stop-gap removed, the rootdir conftest having made it redundant.

**Ordering artefact, now resolved.** Before this ticket, T-050's test module set the three variables via `os.environ.setdefault` at import time so it could be collected on its own. Because pytest collects alphabetically that import landed after `test_areas_endpoint.py` and before `test_owner_claimed.py` and `test_salons_endpoint.py`, so CI on that branch reported `collected 181 items / 1 error` instead of `40 items / 3 errors` — the session was still `Interrupted` and still ran **zero** tests; only the error count moved. It was a filename-ordering-dependent side effect, not a partial fix. The rootdir conftest removes the dependency entirely, and the stop-gap was deleted when T-050 was rebased.

---

### T-072 — Audit and restrict unexpected public listeners
**Priority:** P1 | **Owner:** OPS | **Epic:** EPIC-09 | **Phase:** Pre-launch security hardening
**Dependencies:** T-049 ✅
**Status:** Open.

**Found during the T-049 inventory**, and deliberately not touched by it: services unrelated to Lookla are listening on public interfaces on this host.

| Listener | Bound to | Owner |
|---|---|---|
| `tinyproxy` | `0.0.0.0:8888` and `[::]:8888` | HTTP proxy, systemd |
| `next-server` ×3 | `*:3997`, `*:3998`, `*:3999` | unrelated Node projects |
| empty-SNI branch of the `:443` stream router | → `127.0.0.1:8888` | routes SNI-less TLS to tinyproxy |

T-049 preserved the empty-SNI → `:8888` route **only as an unchanged pre-existing contract**. That is not an endorsement: it was left alone because changing it was outside the reviewed scope, not because it was assessed as safe.

`tinyproxy` reachable from the whole internet is the sharpest item. An open HTTP proxy can be used to relay arbitrary traffic through this host, which is an abuse and attribution problem regardless of what else it protects. The `:443` no-SNI branch means it is reachable on **two** public ports.

**This ticket must inventory before it restricts** — these listeners may have consumers this project does not know about, and silently closing them is the same class of mistake T-049 avoided with the VPN.

For each listener establish: the owning process and unit; whether it is reachable externally (verified, not assumed); whether it requires authentication; whether access is logged; who actually consumes it; whether a source allowlist or a `127.0.0.1` bind would suffice; and whether it can simply be switched off.

**Acceptance Criteria:**
- [ ] Every public listener has a named owner and a documented consumer, or is switched off
- [ ] `tinyproxy` is authenticated, source-restricted, bound to loopback, or removed — with evidence it is not an open relay
- [ ] The `:443` empty-SNI route is re-decided explicitly rather than inherited
- [ ] The three `next-server` processes are bound to loopback or firewalled
- [ ] No restriction is applied before its consumers are identified

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
**Priority:** P2 | **Owner:** OPS | **Epic:** EPIC-09 | **Phase:** Pre-launch security hardening
**Dependencies:** T-050 ✅, T-071 ✅
**Status:** ✅ Completed. Reviewed, **APPROVE**, merged via PR #72 (`63cbab4`) and follow-up fix PR #73 (`5ded205`). Applied to production on the second attempt — the first failed safely at `nginx -t` before the firewall was touched, and the prepared rollback restored the tree exactly. No container was rebuilt or restarted; nginx was reloaded, never restarted.

**Risk being addressed:** the origin's ports 80/443 are reachable directly from the public internet, so anyone who learns the origin IP can bypass Cloudflare's WAF, rate limiting and bot controls entirely. Confirmed live: no packet filtering of any kind is active on this host.

#### Step 2 — Production network path inventory

| Layer | Current implementation | Relevant rule/path | T-049 implication |
|---|---|---|---|
| OS | Ubuntu 24.04.4 LTS, kernel 6.8 | — | — |
| Docker | Engine 29.4.2, **Firewall Backend: iptables** | `DOCKER-USER` exists and is **empty** | available if ever needed |
| iptables | v1.8.10 (**nf_tables** shim), `ip6tables` likewise | policies `INPUT/FORWARD/OUTPUT ACCEPT` | no backend migration required or permitted |
| Host firewall | **none active** — UFW `inactive`, firewalld `inactive`, nftables unit `inactive`, zero custom `INPUT` rules | — | the control would be new, not a modification |
| Public interface | `eth0`, single public IPv4 | default route via `eth0` | rule scope = `eth0` |
| IPv6 | **no global IPv6 address exists** (link-local only) | nginx binds `[::]:80/443` but nothing routes | see Step 10 |
| Ports 80/443 | **host nginx**, not a container | `0.0.0.0:80`, `0.0.0.0:443` | **`DOCKER-USER` is the wrong layer here** |
| Docker published ports | `127.0.0.1` only — web 3000, api 8001, redis 6379, db 5432 | loopback-bound | not publicly reachable at all; out of scope |

**The Docker premise in the ticket does not hold on this host.** The ticket assumed public ports are Docker-published and therefore bypass `INPUT`. They are not: nginx runs on the host and owns 80/443 directly, so ordinary `INPUT` filtering *is* the correct and sufficient layer, and `DOCKER-USER` must be left alone. Every Docker-published port is already bound to loopback and unreachable from outside.

#### Step 3/4 — Blocking conflict: port 443 is shared with a live VPN

`/etc/nginx/stream.d/port443.conf` makes port 443 an **SNI router**, not a web port:

```nginx
map $ssl_preread_server_name $upstream {
    lookla.gr       127.0.0.1:8443;   # web  → nginx HTTPS vhost
    www.lookla.gr   127.0.0.1:8443;
    ""              127.0.0.1:8888;   # no SNI → tinyproxy
    default         127.0.0.1:4443;   # everything else → Xray VLESS/REALITY
}
```

Lookla's HTTPS vhost does **not** listen on `0.0.0.0:443` at all — it listens on `127.0.0.1:8443` behind that router. The `default` branch carries a **Xray VLESS/REALITY VPN** (10 provisioned clients, REALITY `serverNames: amazon.com`), whose users connect to the origin IP on port 443 from ordinary residential addresses worldwide.

Evidence that this is live production traffic, not a dormant service:

```text
/var/log/xray/access.log, 7 days
  22 868 lines total
   6 052 local stats-API polls (the /opt/xray-traffic-collector.py cron)
  16 816 real proxied client requests
  active on every one of the last 7 days, including today
  most recent real request: 2026-08-03 05:01:44, identity user05@xray
```

**Consequence: a source-IP allowlist on TCP/443 would terminate the VPN.** The firewall sees only address and port; it cannot distinguish the `lookla.gr` SNI from the VPN's. This is the Step 3 stop condition in a form the ticket did not anticipate — not a DNS-only hostname, but a different service sharing the port. The rule would be technically correct and would break legitimate production traffic, so it has not been applied.

**Port 80 is not affected by this conflict.** It serves only the `lookla.gr` → HTTPS redirect and a default `localhost` vhost; nothing else on the host uses it.

#### Step 3 — DNS and proxy-status audit

| Hostname | A / AAAA target | Proxied | Served on this origin | Needs public 80/443 |
|---|---|---|---|---|
| `lookla.gr` | Cloudflare (`172.67.x`, `104.21.x`; AAAA `2606:4700:…`) | **proxied** | yes | via Cloudflare only |
| `www.lookla.gr` | same | **proxied** | yes | via Cloudflare only |
| `cdn.lookla.gr` | same | **proxied** | R2-backed, not this origin | no |
| `api.lookla.gr` | **does not resolve** | — | no | no |

No DNS-only A/AAAA record pointing at this origin was found for any web hostname. The VPN reaches the origin by **IP literal**, not by a DNS name, which is precisely why a DNS audit alone would have missed the conflict.

#### Step 4 — Direct origin consumers

| Consumer | Path | Needs direct origin access |
|---|---|---|
| Browsers / crawlers | proxied hostname | no |
| Xray VPN clients | **origin IP:443 directly** | **yes — the blocking conflict** |
| Tinyproxy (`:8888`, and the no-SNI 443 branch) | direct | separate service, outside T-049 scope |
| Certificate renewal | none — see Step 5 | no |
| Monitoring / webhooks / payments | none configured against the origin IP | no |

#### Step 5 — TLS renewal compatibility: **no conflict**

```text
issuer   CloudFlare Origin SSL Certificate Authority
notAfter Jun 20 15:07:00 2041 GMT
```

A **Cloudflare Origin Certificate**, valid for another ~15 years. No `certbot`, no `acme.sh`, no `/etc/letsencrypt`, no renewal timers. There is no HTTP-01 validation path to break, so the ticket's second mandatory precondition is satisfied outright.

#### Steps 6–7 — Official range source, validated fail-closed

`ops/cloudflare/cf_ranges.py` fetches only `https://www.cloudflare.com/ips-v4` and `/ips-v6`.

```text
retrieved_at_utc  2026-08-03T11:24:03Z
ipv4  count=15  sha256=f02c6d83bc01ab0ae8577160e036d700c7455359bce054df884e5d7d9e4e9e7b
ipv6  count=7   sha256=9e9d39e3e83bad00c4decafd53c63fa62029f3d95db68de937d2be28234ca0a9
```

Validation is a pure function, separated from I/O so it is testable without a network. It rejects: empty or whitespace-only bodies, HTML/JSON/XML error pages, wrong address family, invalid CIDRs, bare addresses without a prefix, networks with host bits set, truncated final lines, and counts outside plausible bounds. Duplicates are normalised deterministically so a snapshot diff reflects a real change rather than ordering noise. Any fetch or validation failure leaves the stored snapshot authoritative — the active list is never replaced by a partial one.

41 tests, and the guards were confirmed discriminating by mutation rather than assumed: disabling the minimum-count guard fails 1 test, the family check 2, the empty check 2.

`--check` mode is proven non-mutating (file hash unchanged across a run that detected a change) and exits `2` on change, so a third party editing their published list can never become an automatic firewall change.

#### Step 10 — IPv6

IPv6 is **not active** on this host, with proof rather than inference:

- `ip -6 addr show scope global` returns **zero** addresses (link-local `fe80::` only);
- there is no IPv6 default route;
- nginx binds `[::]:80` and `[::]:443`, but nothing routes to them from outside;
- Docker publishes no IPv6;
- `lookla.gr` AAAA records point at **Cloudflare**, not at this origin.

Direct IPv6 origin access is therefore not currently possible. The IPv6 allowlist is nonetheless fetched, validated and stored, so enabling IPv6 later does not silently ship an unprotected path.

#### Approved design — why the two layers differ

Port 80 is Lookla's alone, so it is filtered where filtering belongs: a dedicated `LOOKLA-CLOUDFLARE` chain entered only by `-i eth0 -p tcp --dport 80`. Port 443 is a shared SNI-multiplexed listener, and a packet filter cannot see SNI, so the gate for it has to live where SNI is visible — the nginx `stream` router that already routes it.

**A phase detail that decides the implementation:** nginx's stream *access* phase runs **before** the *preread* phase, so `allow`/`deny` cannot see `$ssl_preread_server_name`. The gate therefore cannot be an access rule; it is a routing decision in the content phase, built from a `geo` lookup on `$remote_addr` combined with the SNI class.

```nginx
geo $lookla_cf_source {          # default 0 lives HERE, in the reviewed file
    default 0;                   # a truncated generated include must mean
    include .../cloudflare-v4.conf;   # "nobody is Cloudflare", never everybody
    include .../cloudflare-v6.conf;
}
map $ssl_preread_server_name $lookla_sni_class { lookla.gr web; www.lookla.gr web; "" nosni; default vpn; }
map "$lookla_sni_class:$lookla_cf_source" $lookla_upstream { ... }
```

| SNI class | Source | Destination | Change |
|---|---|---|---|
| `lookla.gr`, `www.lookla.gr` | official Cloudflare range | `127.0.0.1:8443` web vhost | unchanged |
| `lookla.gr`, `www.lookla.gr` | anything else | `127.0.0.1:9443` **reject** | **new** |
| empty SNI | any | `127.0.0.1:8888` tinyproxy | unchanged |
| any other SNI | any | `127.0.0.1:4443` Xray | unchanged |

The Lookla hostname list is exactly the pre-existing one — no wildcard was introduced, and `cdn.lookla.gr` is deliberately absent because it was not in the previous map either; adding it would silently move it off the route it has today.

**The reject path is a real listener** (`listen 127.0.0.1:9443; return "";`), not a dead address. Pointing `proxy_pass` at an unreachable port makes the behaviour an accident of the kernel and fills the error log; `return ""` sends nothing and closes, so the client completes no handshake, sees no certificate, gets no application response, and reaches neither backend.

#### Isolated verification — a real nginx, full matrix

Static inspection is not evidence: `map` precedence and the phase in which `$ssl_preread_server_name` becomes available are nginx's decisions, not the reader's. `ops/cloudflare/verify_routing.py` starts a throwaway nginx with the production routing logic, points the upstreams at marker listeners, and varies the source address across `127.0.0.0/8` (already routed to loopback — no interface is created, the host firewall is never touched).

| case | expected | observed |
|---|---|---|
| Cloudflare source + `lookla.gr` | web | web ✅ |
| Cloudflare source + `www.lookla.gr` | web | web ✅ |
| ordinary source + `lookla.gr` | reject | reject ✅ |
| ordinary source + `www.lookla.gr` | reject | reject ✅ |
| ordinary source + VPN SNI | Xray | Xray ✅ |
| Cloudflare source + non-Lookla SNI | Xray | Xray ✅ |
| ordinary source + unknown SNI | Xray | Xray ✅ |
| ordinary source + empty SNI | tinyproxy | tinyproxy ✅ |

The harness was itself mutation-tested: routing `web:0` to the web upstream turns exactly the two reject rows red, so a passing run is a result rather than a formality.

#### Atomicity, rollback, persistence

`ipset` is not installed and `netfilter-persistent` is absent, so neither is used — adding a package to a production host is a larger change than this ticket warrants. Instead the chain is replaced by a single `iptables-restore --noflush` transaction (`:LOOKLA-CLOUDFLARE - [0:0]` creates-or-flushes inside the transaction), so there is no window in which the chain is empty, no momentary allow-all, and an interrupted run leaves the previous rules in force. `--noflush` leaves every other chain, Docker's included, untouched. The INPUT jump is inserted only after the chain is populated, and only when absent — so reapplying cannot stack duplicates.

`apply_t049.sh` orders the steps so the working state survives any failure: back up both layers → **arm a timed `systemd-run` rollback before the first mutation** → render includes from the stored snapshot → `nginx -t` *before* touching the firewall → apply the firewall atomically → `nginx -t` again → **reload, never restart** (a restart drops the established VPN connections a reload preserves) → verify → only then cancel the rollback. The generated `rollback.sh` needs no network and no repository: it removes only T-049's chain and jump, restores the saved stream directory, and reloads.

Persistence is a systemd oneshot that applies the **stored snapshot** and never fetches — a boot without connectivity restores the policy rather than leaving the origin open while a download times out.

#### IPv6

Public IPv6 remains proven inactive (zero global addresses, no v6 default route, AAAA records pointing at Cloudflare), so no IPv6 packet-filter policy is invented. The validated IPv6 snapshot and its generated `geo` include are still produced and wired into the stream config, so enabling IPv6 later cannot silently ship an ungated path.

#### Tests

**326 backend tests** (271 before + 55 for this layer), ruff clean, frontend unchanged. The scope guarantees are asserted against the bytes that would reach the kernel, not against intent: no rule references 443, 22, 8888, 3997–3999, 3000, 5432, 6379 or 8001; `build_jump_rule` refuses a forbidden port outright; no Docker chain is named; only T-049's own chain is populated; an empty allowlist cannot produce a chain; the deny is last and every Cloudflare range precedes it.

**Safety checklist:** Backend changed **No** · Frontend changed **No** · Database changed **No** · API contract changed **No** · Cloudflare DNS changed **No** · Proxy status changed **No** · TLS renewal verified **Yes — Origin Certificate to 2041, no ACME** · DNS-only consumers audited **Yes — none** · Direct integrations audited **Yes — VPN found** · Firewall backend preserved **Yes — nothing applied** · Docker firewall path handled **Yes — determined inapplicable, `DOCKER-USER` untouched** · UFW treated as sufficient **N/A — ports are host-owned, not Docker-published** · Docker chains modified **No** · Docker firewall management disabled **No** · IPv4 port 80 protected **Yes (implemented, not applied)** · IPv6 proven inactive **Yes** · VPN preserved **Yes — verified in isolation** · SSH rules changed **No** · Official endpoints used **Yes** · Lists validated **Yes** · Empty-list replacement possible **No** · Production firewall touched **No** · Full firewall dump published **No** · Origin IP published **No** · Containers restarted **No** · PM2 used **No**

#### Decision required

The origin IP cannot be protected on 443 without deciding what happens to the VPN. Options, with the trade-off stated honestly:

1. **Port 80 now, 443 deferred.** Immediate, zero risk to the VPN — but 443 is where the real bypass risk lives, so this alone buys little security.
2. **SNI-aware rejection in the nginx stream layer.** Combine `$ssl_preread_server_name` with a `geo` set of Cloudflare ranges: a `lookla.gr` SNI from a non-Cloudflare source is dropped, everything else routes as today. Keeps the VPN working and closes the WAF bypass. Enforcement is in nginx rather than the packet filter — it is still pre-HTTP and trusts no header, but the origin still accepts the TCP connection. Requires an nginx reload (no container restart).
3. **Move the VPN to another port**, then apply a clean firewall allowlist on 443. Strongest result; requires reconfiguring 10 VPN clients, and an uncommon port is more fingerprintable than 443.
4. **Cloudflare Tunnel for Lookla** — removes the public origin web ports entirely and makes the whole question moot. Largest change; the ticket lists it as an explicit follow-up, not as T-049.

Recommended: **2 combined with 1** — port 80 restricted at the packet filter, and 443 filtered by SNI + source in the stream layer — with 4 recorded as the durable fix.

#### Production rollout — two attempts, the first rolled back

**Attempt 1 (12:52) failed at `nginx -t`, before the firewall was touched.** `nginx.conf` carries `stream { include /etc/nginx/stream.d/*.conf; }`, so rendering the generated allowlist into `stream.d` made nginx parse `103.21.244.0/22 1;` as a stream-level directive:

```text
[emerg] unknown directive "103.21.244.0/22" in /etc/nginx/stream.d/cloudflare-v4.conf:4
[t049] FAIL: nginx -t failed — firewall untouched
```

The running nginx kept its configuration in memory, so production was never affected. The prepared `rollback.sh` was run immediately rather than waiting for the timer, and restored `port443.conf` byte for byte (md5 `af1c0d93…`), removed the rendered includes, and reloaded — with no chain created, no container touched and no VPN traffic lost.

**The test suite did not catch it.** The include-path test asserted the path against the same constant the config was written from — it proved the string matched itself and nothing about the environment. PR #73 replaced it with an assertion of the relationship that matters (the render directory is not one nginx globs into the stream block, which fails when the path is reverted) and made a failed `nginx -t` restore the previous file, so a broken config can no longer sit on disk waiting for the next reload, logrotate hook or reboot to turn it into an outage.

**Attempt 2 (16:14:29 Europe/Athens) succeeded.**

```text
Lookla origin restriction boundary:
2026-08-03 16:14:29 Europe/Athens (EEST)
```

#### Production smoke — results

| Check | Before | After |
|---|---|---|
| Direct TCP/80 from external non-Cloudflare nodes | **open** (bg1, hk1, se2) | **blocked, connection timed out** (ir6, it2, nl1, se1) |
| Direct :443 + SNI `lookla.gr` from a non-Cloudflare source | served the **Cloudflare Origin Certificate** | **`no peer certificate available`**; `curl --resolve` exits 35 |
| Direct :443 + SNI `www.lookla.gr` | — | **`no peer certificate available`** |
| Web access log for those rejected requests | — | **zero entries** (the successful Cloudflare-path requests did log, so the log itself was working) |
| :443 TCP reachability from outside | open | **still open** (ca1, nl1, tr1) — the VPN needs it |
| Non-Lookla SNI (`amazon.com`) | Xray | **Xray** — returns `CN = *.peg.a2z.com`, i.e. REALITY behaviour intact |
| Empty SNI | tinyproxy | **tinyproxy**, unchanged |
| Cloudflare path | 200 | **200** — `/`, `/en`, `/ru`, `/uk`, search, map, `/privacy`, `/cookies`, `/api/salons` |
| VPN access log | 22890 | **advancing** (22891) |
| Containers | — | **untouched**: api/web `Up 2 hours`, crawler `Up 13 days`, db/redis `Up 3 weeks` |
| `DOCKER-USER` and Docker chains | empty / 23 rules | **unchanged** |

**Firewall scope, verified against the live rules:** exactly one INPUT jump, `-i eth0 -p tcp --dport 80`; T-049's own chain contains 15 ACCEPT + 1 RETURN + 1 DROP and **no port match at all**; ports 443, 22, 8888 and 3997–3999 are absent. Rules that do mention 3000, 5432, 6379 and 8001 are pre-existing Docker DNAT entries in the `DOCKER` chain, not T-049's. A first pass at this check reported "2 rules on port 80" — a grep artefact, since `dport 80` also matches `dport 8001`; the precise count is one.

**Idempotence and persistence:** re-running the apply left the rule count unchanged at 46 with a single INPUT jump. The systemd unit is installed, enabled and active (`exit status 0`), and applies the stored snapshot without fetching, so a boot with no connectivity still restores the policy.

**Rollback:** armed before the first mutation both times, cancelled only after every check above passed. The artifact is retained at `/var/backups/t049/20260803T131429Z/` and needs neither network nor repository.

#### Follow-ups (deliberately not folded into T-049)

Authenticated Origin Pulls · Cloudflare Tunnel · origin IP rotation · automatic range-change monitoring · `tinyproxy` on `0.0.0.0:8888` and three `next-server` processes bound to `*:3997-3999` are publicly reachable and unrelated to Lookla — they deserve their own review.

---

### T-050 — Remove recipient-email logging from the Resend fallback path
**Priority:** P2 | **Owner:** BE | **Estimate:** 0.5h | **Epic:** EPIC-09
**Dependencies:** None

**Status:** ✅ Completed. Reviewed, **APPROVE**, merged via PR #70 (`a07b2e6` on `main`), `beauty_api` **and** `beauty_web` rebuilt and recreated together — `db`, `redis`, `crawler` and `crawler_worker` untouched (`Up 2 weeks` / `Up 12 days` across the deploy). Production smoke passed on `https://lookla.gr`.

**Description:** `backend/app/services/email.py`'s no-API-key fallback path (`send_email`) printed the intended recipient's email address to stdout instead of sending the email (`print(f"[email] No API key — skipping: {template} to {to}")`). Docker's json-file driver captures that with no size or rotation limit, so a transient delivery problem became durable PII storage that no retention policy covers.

#### Leak inventory — the documented path was one of three

| # | Location | What escaped |
|---|---|---|
| 1 | `email.py` no-API-key fallback | the recipient's full address (the known defect) |
| 2 | `email.py` Resend error branch | `r.text` — Resend **echoes the offending address back** in a 422 `Invalid \`to\` field` body |
| 3 | `email.py` exception branch | `str(e)` unbounded — an address in a URL query string surfaces here percent-encoded |

Paths 2 and 3 were not in the original ticket. Fixing only path 1 would have left the leak reachable through any provider rejection.

#### Design — HMAC pseudonym plus scrubbing

`app/core/log_redaction.py` (pure, no I/O, no framework):

- **`recipient_ref(address, key)`** — `HMAC-SHA256(LOG_PII_HMAC_KEY, normalised_address)`, first 12 hex chars. A plain or publicly-salted hash was rejected as insufficient: email addresses have a small, highly predictable structure, so anyone holding the log could hash a candidate dictionary and match. A key held only by the backend removes that offline attack. Stable output preserves the diagnostic value that omitting the recipient entirely would have cost — repeated failures for one person stay correlatable.
- **No unkeyed fallback.** With no key configured the log reads `recipient_ref=unavailable`. A fallback digest would look like protection while being trivially reversible.
- **`scrub()` / `scrub_and_limit()`** — HMAC only protects the field we author. Text we do not author (provider bodies, exception messages) is scrubbed of any address, including percent-encoded forms, then bounded to 500 chars.
- **Scrub runs before truncation.** Truncating first can cut an address mid-domain (`maria.papadopoulou@examp`), which no longer matches the pattern and so survives scrubbing while still exposing the whole local part.
- **`safe_field()`** — `lang` reaches `send_email` from an unvalidated request field, so control characters are stripped before it enters a log line; otherwise a newline in it could forge an additional, fully attacker-authored log record.
- Request headers and payload are never logged — they carry the API key, reset codes and claim tokens.

`LOG_PII_HMAC_KEY` is deliberately its own secret, not `SECRET_KEY` and not a provider credential: it is read on a logging path, and reusing an auth secret there would widen the blast radius of a logging mistake.

#### Verification

230 backend tests (180 on `main` after T-071 + 50 added here), frontend 1202/1202, ruff clean, eslint clean. Under the pre-T-071 CI none of the backend figures would have meant anything — the job exited during collection.

The new tests were checked by **mutation** rather than assumed correct — each leak was deliberately reintroduced to confirm the suite goes red:

| Mutation | Caught by |
|---|---|
| original `print(... {to})` restored | 5 tests, incl. the end-to-end capture |
| `r.text` logged unscrubbed | `test_provider_text_is_only_logged_through_the_scrubber` |
| unkeyed SHA-256 fallback when key missing | 3 tests |
| truncate-before-scrub | `test_scrub_runs_before_truncation` — **only after that test was fixed**, see below |

Two of the tests were wrong before the code was:

- `test_scrub_runs_before_truncation` originally chose a truncation limit that fell *before* the `@`, leaving a harmless `mari` fragment. It passed against a deliberately broken truncate-then-scrub implementation — it tested nothing. The cut point is now asserted (`text[:limit].endswith("@examp")`) rather than assumed.
- The locale-parity check matched the substring "we log the address", which also appears inside the *corrected* sentence "we do **not** write the address", producing a false failure on `ru` and `uk`. It now anchors on the affirmative marker of the old claim ("currently" / "προς το παρόν" / "в настоящее время" / "наразі").

Coverage added on rebase, at review request: `repr(exception)` (which embeds args and leaks an address as readily as `str()`), a wrapped exception chain, a percent-encoded local part, and the double-encoded `%2540` form that appears when a URL already containing an address is escaped a second time — in upper, lower and mixed case. Removing the encoded-address pattern makes 7 tests fail, so the cases discriminate rather than merely pass.

A negative control (`test_capture_helper_actually_sees_output`) guards the whole end-to-end group: every other assertion there is of the form "X is absent from the log", which passes vacuously if the helper captures nothing. It earned its place immediately — under the first mutation it failed, because `print()` bypasses logging and `caplog` saw nothing at all.

Observed output, all three paths, one shared `recipient_ref`:

```text
WARNING [email] no API key — skipped template=reset lang=ru recipient_ref=65482451984c
ERROR   [email] Resend rejected request status=422 recipient_ref=65482451984c detail={"statusCode":422,"name":"validation_error","message":"Invalid `to` field. [redacted-email] is not a valid address"}
ERROR   [email] request failed type=TimeoutError recipient_ref=65482451984c detail=timed out posting https://api.resend.com/emails?to=[redacted-email]
```

A log-injection attempt through `lang` (`"el\nERROR [email] forged line"`) produces one record, not two.

#### CI evidence — the suites actually ran

Run **30803977520** on the post-T-071 gate:

```text
backend:  collected 230 items → 230 passed
          backend test gate: tests=230 failures=0 errors=0 skipped=0
frontend: 1202/1202
```

Confirmed from the uploaded JUnit artifact rather than from the total, since a
larger number alone would not prove *these* tests ran:

| module | testcases in the CI report |
|---|---|
| `test_email_log_redaction` (T-050) | **50**, 0 failures / 0 errors / 0 skips |
| `test_salons_endpoint` | 77 |
| `test_salons_endpoint`, `test_areas_endpoint`, `test_owner_claimed` combined | 127 |
| `test_test_gate` (T-071) | 13 |

Those three modules are the ones whose import error used to abort collection: **127 tests that had never executed in CI before** now do.

#### Privacy Policy

T-017's disclosure was **corrected, not deleted**, in all four locales. The behaviour is improved but not eliminated: a keyed-HMAC reference is still written, and because we hold the key it remains personal data. The policy now says the address and its domain are not logged, describes the pseudonymous reference, and states plainly that it is not anonymous data. `lastUpdated` moves `2026-07-21` → `2026-08-03` in all four locales; **if the deploy date slips, this date must be corrected to match it.**

The T-017 tripwire that pinned the old disclosure fired correctly and was updated to assert the new truth, plus a new four-locale parity test.

**Acceptance Criteria:**
- [x] No fallback path logs the recipient's address — verified by mutation, not only by a passing test
- [x] Paths 2 and 3 (provider body, exception message) closed as well
- [x] Keyed HMAC, dedicated secret, no unkeyed fallback, no domain logged
- [x] Docker's `beauty_api` logging driver has `max-size: 10m` / `max-file: 3`
- [x] T-017 Privacy Policy corrected in all four locales
- [x] Regression tests actually execute in CI — T-071 merged (`25b3bc2`), gate proven red-then-green
- [x] Production deploy — `beauty_api` + `beauty_web` only; `LOG_PII_HMAC_KEY` installed in `.env` before the api container was recreated
- [x] Independent review — **APPROVE**
- [x] T-050 regressions: **0**

**Deploy note:** unlike every ticket since T-055, this one is not web-only. The fix lives in the backend and the policy text in the frontend, so both containers must be rebuilt; `db`, `redis`, `crawler` and `crawler_worker` stay untouched. `LOG_PII_HMAC_KEY` must exist in `.env` **before** the api container is recreated, or the first fallback log line will read `recipient_ref=unavailable`.

#### Production smoke — `https://lookla.gr`, after deploy

**Boundary recorded:**

```text
Email log-redaction boundary:
2026-08-03 13:54:58 Europe/Athens (EEST)   — beauty_api  (the security boundary)
2026-08-03 13:55:00 Europe/Athens (EEST)   — beauty_web  (Privacy Policy wording)
```

Deploy verified: `LOG_PII_HMAC_KEY` present in the api container (64 chars, distinct from `SECRET_KEY` and from the Resend key, single `.env` line), and the json-file driver now reports `max-file:3 max-size:10m` on `beauty_api`.

| Check | Result |
|---|---|
| Probe identifiers anywhere in `beauty_api` / `beauty_web` / nginx logs | **0 occurrences** of the address, the bare domain, `%40` or `%2540` forms, in any case |
| All three branches under the **live container's real settings** | one stable `recipient_ref` across all three; a second address produced a different ref; `[redacted-email]` substituted 3× |
| Secrets in log records | no Resend key, no `Authorization`, no `Bearer`, no reset code |
| Log forging | no embedded newlines; record count equals emission count |
| Privacy Policy, 4 locales | new wording present, pre-T-050 wording absent, `lastUpdated 2026-08-03`, no console or hydration errors |
| Pages | `/privacy` and `/cookies` 200 in all 4 locales; `/`, `/en/search`, `?view=map`, `/api/salons`, `/api/areas` all 200 |
| Backend errors since deploy | no tracebacks, nothing from `log_redaction` |

**What could not be proven live, stated plainly.** A *synchronous* provider rejection is not reachable from production without changing configuration, which the review explicitly prohibited. A real send to the synthetic recipient, and three concurrent password-reset sends, were all **accepted** by Resend, so no error branch fired. That run's only live assertion is a negative one — no address appears in the logs — and a negative assertion over an empty set proves nothing on its own. The branch behaviour was therefore exercised inside the running container against the real settings object, which proves the production key yields a valid 12-hex reference and that scrubbing works under production configuration, but does not re-prove the journey to `docker logs`; that path is covered by the CI end-to-end capture test, which asserts against a real `caplog` and fails when `print()` bypasses logging.

**Synthetic data removed.** `t050-probe@t050-probe.lookla.gr` — a subdomain of our own domain with no MX, chosen because the review's `example.invalid` is a reserved special-use name that Pydantic's `EmailStr` rejects before `send_email` is ever called. Cleanup deleted 3 `password_resets`, 1 `email_verifications` and 1 `users` row; 0 remain.

**No boundary redefined:** the Beta Visual Baseline stays `2026-07-30 11:39:31`, the Map `search_results_view` correction boundary stays `2026-07-30 18:26:17`, and the Map latest-request correctness boundary stays `2026-07-31 17:34:10` — all Europe/Athens.

#### Recorded, not fixed (out of this ticket's boundary)

- **`preferred_language` is unvalidated** — `RegisterIn.preferred_language: str = "el"` accepts any string and flows into `send_email(lang=...)` and into the `User` row (`String(2)`). T-050 defends its own log line via `safe_field()`, but the field should be constrained to `el|en|ru|uk` at the schema.
- **Every other service still has unbounded logging.** Only `api` was given a limit, per this ticket's scope — and because adding it to `db`/`redis`/`crawler` would require recreating those containers, which is outside any approved deploy.
- **`print()` remains in `moderation.py` and `payments.py`.** Neither currently interpolates PII, but both bypass logging configuration the same way this defect did.

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
