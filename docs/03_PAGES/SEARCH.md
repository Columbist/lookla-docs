---
title: Search Page Specification
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 01_PRODUCT/USER_JOURNEYS.md
  - 01_PRODUCT/MVP_DEFINITION.md
  - 00_GOVERNANCE/DECISION_LOG.md
  - 02_DESIGN/UX_FLOWS.md
  - 03_PAGES/SALON.md
  - 04_ARCHITECTURE/DATA_FLOW.md
implementation_status: Implemented — filter label update required (DEC-010)
---

# Search Page
**Lookla Beauty Marketplace**

---

## Purpose

The Search Page is the primary discovery surface. Its job is to let users find a specific salon from the catalog using a combination of text query, area filter, category filter, and rating filter.

The Search Page must handle:
- Users who know exactly what they want ("маникюр Глифада")
- Users who are browsing a category in an area ("nail salons in Kolonaki")
- Users who arrived from a category tile on the homepage
- Users who arrived from an area tile on the homepage

**Critical constraint (DEC-010):** The location filter must reflect the area/district hierarchy — not a flat "City" list. Users search for Glyfada, Kolonaki, Marousi — not "Athens."

---

## Target Persona

All personas:
- **P-02** (Russian/Ukrainian) — searches in Cyrillic; expects multilingual results
- **P-01** (Greek) — searches in Greek; expects local relevance
- **P-03** (Expat) — searches in English; needs English-labeled results

---

## User Intent

| Intent | Entry | Filter state |
|---|---|---|
| "Find nail salons near me in Glyfada" | Typed "маникюр" or "nail" + area | q=маникюр, area=glyfada |
| "See all hairdressers in Kolonaki" | Clicked Hair salon category → then area | category=hair, area=kolonaki |
| "Browse everything in my area" | Clicked area tile on homepage | area=marousi |
| "Find something with ≥4 stars" | Used rating filter | min_rating=4 |
| "I need something open now" | Sees open/closed badges on cards | (filter does not exist; visual only) |

---

## Entry Points

| Source | URL State |
|---|---|
| Hero search bar (home) | `/search?q={query}` |
| Category tile (home) | `/search?category={slug}` |
| Area tile (home) | `/search?area={slug}` |
| Direct URL / bookmark | Any combination of params |
| Browser back from salon detail | Returns to same filter state (URL-preserved) |

---

## Page Layout

```
[ Header: Logo | Search bar | Language switcher | Login ]
─────────────────────────────────────────────────────────
[ Filter bar: Area ▼ | Category ▼ | Rating ▼ | Map toggle ]
─────────────────────────────────────────────────────────
[ Results count: "47 salons in Glyfada" ]
─────────────────────────────────────────────────────────
[ SalonCard ] [ SalonCard ] [ SalonCard ]
[ SalonCard ] [ SalonCard ] [ SalonCard ]
   ... (infinite scroll, 24 per load) ...
[ Scroll sentinel → loads next 24 ]
─────────────────────────────────────────────────────────
[ Footer ]
```

**Map view (toggle):** Full-width map replaces card grid; pins show salons; click pin → mini card; click mini card → salon detail

---

## Filter Behaviour

### Area Filter (DEC-010 — replaces "City" filter)

**Label:** "Area" / "Περιοχή" / "Район" / "Район"

**Structure:** Uses the location hierarchy (Country → Region → City → District). For MVP (Athens focus), the filter shows Athens districts as primary options:
- Glyfada, Kolonaki, Kallithea, Marousi, Piraeus, Nea Smyrni, Chalandri, Kifissia, Psirri, Exarchia, Pagkrati, etc.

**Behaviour:**
- Selection sets `area={slug}` in URL
- API call: filters by `address_district ILIKE` (or by mapped `address_city` values until full hierarchy is implemented)
- Selecting "Athens" returns all Athens metro area salons (not just central)
- Clear filter → remove `area` param, show all results

**Placeholder text:** "All areas" / "Όλες οι περιοχές" / "Все районы"

**Implementation note:** Until the full location hierarchy migration is complete (DEC-010), the area filter maps user-visible district names to the corresponding `address_city` values in the database. This mapping must be defined in the backend before MVP launch.

---

### Category Filter

**Label:** "Category" / "Κατηγορία" / "Категория"

**Options:** Top-level categories from `/api/categories`, labeled in current locale

**Behaviour:**
- Selection sets `category={slug}` in URL
- API translates slug to keyword list (`CATEGORY_KEYWORDS`) and runs subquery on services
- Multiple selection: not in MVP (single category only)
- Clear filter → remove `category` param

---

### Rating Filter

**Label:** "Rating" / "Αξιολόγηση" / "Рейтинг"

**Options:**
- Any (default)
- 3+ stars
- 4+ stars
- 4.5+ stars

**Behaviour:** Sets `min_rating={value}` in URL

---

### Search Bar (in-page)

The header search bar persists on the Search page and reflects `?q=` param. Editing and submitting updates the results in-place (no full navigation — just URL update).

---

## Results

### SalonCard content:

Each card shows:
- Primary photo (thumbnail)
- Salon name (in locale: translated where available)
- Area/district (from `address_city` until hierarchy is implemented)
- Category badge(s)
- Open / Closed badge (computed from working hours + current Athens time)
- Rating (stars + count): "4.7 ★ (128)"
- Minimum price indicator: "from €15" (when available)
- Verified label (if applicable per DEC-014):
  - "Information reviewed" (if admin-reviewed, is_verified = true without claim)
  - "Owner verified" (if claimed by salon owner)
  - No label = default

**Not on card:** Booking button, "Book now", price range (only min price)

### Sort order:

Default: `rating_google DESC, rating_count DESC`

No other sort options in MVP. "Nearest" sort is a future feature (geo search deprioritized per DEC-009).

### Pagination:

Infinite scroll with IntersectionObserver sentinel. 24 salons per load. Loads next page when sentinel enters viewport.

---

## Map View

**Toggle:** Button in filter bar "Map / List" (or icon)

**Map content:**
- Leaflet map, Athens center as default viewport
- Pins at `(lat, lng)` for each matching salon
- Viewport set to encompass all result pins on first load
- Click pin → mini card popup: name, rating, open/closed, link to detail page

**Loading:** Map is `dynamic(() => import(...), { ssr: false })` (client-only per current implementation)

**Mobile:** Map and list cannot both be visible; toggling replaces one with the other

**Edge case:** Salon has no coordinates → not shown on map but shown in list

---

## Results Count

Show: "47 salons found" / "Βρέθηκαν 47 σαλόνια" / "Найдено 47 салонов"

Update dynamically as filters change.

---

## Empty State

**When:** No salons match the current filter combination.

**Display:**
- Headline: "No salons found in this area"
- Subtext: "Try searching a different area or removing a filter"
- Actions: "Clear filters" button (removes all filters, returns to default)
- Optionally: suggest 3 nearby areas with salon counts

**Do not show:** "Be the first to add a salon" or any user-generated content CTA (DEC-003 — no fake activity)

---

## Error States

| Scenario | Behaviour |
|---|---|
| API 500 | Show "Something went wrong" with retry button |
| Network timeout | Same as above |
| Empty category filter returns results | Normal — shows all salons |
| Area not found in data | Return empty state (not 404) |

---

## Mobile Considerations

- Filter bar: collapsible into a "Filters" button that opens a bottom sheet
- Bottom sheet filters: Area, Category, Rating — applied on "Show results"
- Map toggle: visible above fold on mobile
- SalonCard: full-width card (not grid) on narrow screens
- Infinite scroll works on touch-scroll
- No hover states relied upon for core interactions

---

## URL State

All filter state lives in the URL query string:
- `q` — text search query
- `area` — district/area slug
- `category` — category slug
- `min_rating` — minimum rating (1–5)
- `view` — `list` (default) or `map`
- `page` — not needed with infinite scroll; omit

**Behaviour:** Browser back/forward navigates between filter states. Sharing a URL reproduces the same results.

---

## Analytics Events

**MVP Critical (implemented in M-01):**

| Action | GA4 Event | Parameters | Task |
|---|---|---|---|
| Search submitted | `search_submitted` | `query`, `locale`, `source: header/hero` | T-034 |
| SalonCard clicked | `salon_card_clicked` | `salon_id`, `salon_name`, `position_in_results` | T-034 |
| Contact button clicked | `contact_action` | `action_type`, `salon_id`, `salon_name` | T-015 |

**Post-MVP (tracked in FUTURE_FEATURES.md — not in M-01 scope):**

| Action | GA4 Event |
|---|---|
| Area filter applied | `filter_applied` |
| Category filter applied | `filter_applied` |
| Map view toggled | `map_toggled` |
| Infinite scroll load | `results_page_loaded` |
| Empty state shown | `search_empty_state` |

---

## Data Requirements

| Data | Source | Notes |
|---|---|---|
| Salon list | `GET /api/salons?q=&area=&category=&min_rating=&page=` | Paginated, 24/page |
| Map data | `GET /api/salons/map?q=&area=&category=` | All results, lat/lng only |
| Categories | `GET /api/categories` | For filter dropdown; cached |
| Areas | `GET /api/areas` (T-004) | Cached with `revalidate: 86400`; returns districts with salon counts |
| Open/closed status | Computed per salon via salon_hours + current Athens time | In API response |
| Translation | Service name/description translation is not needed on cards | Only on detail page |

---

## Implementation Notes

**Changes from current implementation:**
1. Filter label: "City" → "Area" (copy change in all 4 languages)
2. Area filter values: must include Athens districts (Glyfada, Kolonaki, etc.) not just "Athens"
3. Backend: add district-to-city mapping for `address_city` filter until full hierarchy is implemented
4. Verified label on SalonCard: replace ✓ icon with text label per DEC-014
5. No booking buttons on cards (current state is correct — confirm no stubs present)

**Existing implementation (correct, no change needed):**
- Infinite scroll with IntersectionObserver ✓
- URL-based filter state ✓
- Multilingual query translation (SERVICE_SYNONYMS) ✓
- 24-per-page pagination ✓
- Map/list toggle ✓

---

*Last updated: 2026-07-09*
