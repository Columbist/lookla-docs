---
title: Home Page Specification
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 01_PRODUCT/PERSONAS.md
  - 01_PRODUCT/USER_JOURNEYS.md
  - 01_PRODUCT/MVP_DEFINITION.md
  - 02_DESIGN/UX_FLOWS.md
  - 03_PAGES/SEARCH.md
implementation_status: Implemented — update required (language switcher placement, area labels)
---

# Home Page
**Lookla Beauty Marketplace**

---

## Purpose

The Home Page is the primary trust-building and discovery entry point. Its job is:

1. Communicate what Lookla is within 3 seconds of landing
2. Let the user start a search immediately
3. Serve as an orientation surface for users arriving from organic search who don't already know the platform

The Home Page does not need to convert — that happens on the Search and Salon pages. Its goal is **confident initiation of a search**.

---

## Target Persona

All personas, weighted by DEC-009 priority:
- **P-02** (Russian/Ukrainian resident) — lands via community link or direct search
- **P-01** (Greek local) — lands via organic Google search
- **P-03** (Expat) — lands via English-language search or app store

The value proposition must be legible to P-02 within the first viewport without language knowledge: visuals and layout communicate before text does.

---

## User Intent

| Intent | Signal | Response |
|---|---|---|
| "I want to find a specific service" | Immediately types in search bar | Focus on search bar; category grid accelerates selection |
| "I'm not sure what I need yet" | Browses category grid | Category grid with icons drives exploration |
| "I heard about Lookla, I want to understand it" | Scrolls down | "How it works" section answers this |
| "I want to find something in my area" | Looks for city/area links | Popular Areas grid, below categories |

---

## Entry Points

| Source | How they arrive |
|---|---|
| Organic search (Google) | `/el`, `/en`, `/ru`, `/uk` — locale homepage |
| Community referral (WhatsApp, Telegram link) | Direct URL in Russian or Ukrainian |
| Direct type-in | `lookla.gr` → redirects to locale homepage |
| Social link | Any locale |
| Language switcher from another page | Stays on home with new locale |

---

## Page Sections

### Section 1 — Header / Navigation

**Content:**
- Logo (left)
- Language switcher (right, visible without scrolling — not buried in footer)
- Login / Register link (right, secondary)

**Constraints:**
- Language switcher must be visible on first load on all screen sizes (DEC-011 — ru/uk users must be able to switch before reading anything)
- No navigation links to `/pricing`, `/plans`, or any payment-related page (DEC-006)
- No "Book" or booking-related CTA anywhere in the header

**Mobile:** Language switcher visible as flag icon or "RU / EL / EN" text row; collapses to icon if space is tight

---

### Section 2 — Hero

**Purpose:** Communicate the product and capture immediate intent.

**Content:**
- Headline (by locale):
  - el: "Βρες το σαλόνι ομορφιάς που ψάχνεις"
  - en: "Find the beauty salon you're looking for"
  - ru: "Найдите салон красоты в Греции"
  - uk: "Знайдіть салон краси в Греції"
- Subheadline (by locale): 1 sentence reinforcing multilingual coverage and Greece focus
- **Search bar** (primary action, in focus on page load):
  - Text input: placeholder by locale ("nail salon in Glyfada...", "маникюр Афины...")
  - Submit button: "Search" / "Поиск" / "Αναζήτηση"
- Optional secondary hint text: "or browse by category ↓" (localized)

**Behaviour:**
- Search bar receives keyboard focus on desktop page load
- Submitting the form navigates to `/search?q={input}` with current locale preserved
- Empty submit → navigate to `/search` (shows full list)

**Visual:**
- Background: clean, light; beauty-relevant photography or illustration (no cheesy stock)
- High contrast for text (accessibility minimum AA)

**Mobile:** Hero is full-width with large touch target search bar; submit button below input (not inline)

---

### Section 3 — Popular Categories

**Purpose:** Accelerate discovery for users who know the service type but not the search term in the current language.

**Content:**
- Grid of 6–8 primary service categories with icon and name (in current locale)
- Example: Nail salon, Hair salon, Barbershop, Spa, Eyebrows & lashes, Massage, Makeup, Waxing

**Behaviour:**
- Each tile links to `/search?category={slug}` (locale-preserved)
- Icons should be visually distinct even without reading the label (cross-language recognition for P-02)

**Data:** From `/api/categories` — show top-level categories with `icon` field, ordered by salon count

**Empty state:** Not possible — categories are static. If API fails, show static fallback.

**Mobile:** 2-column grid; tiles are large enough for touch

---

### Section 4 — Popular Areas (formerly "Popular Cities")

**Purpose:** Let users who know their area jump directly to filtered results.

**Constraint per DEC-010:** These are not "Cities" — they are districts/areas of Athens (Glyfada, Athens Center, Kallithea, Marousi, etc.) plus city-level entries for Thessaloniki and other regions. The section label must say "Popular Areas" or "Αναζήτηση κατά περιοχή" — not "Cities."

**Content:**
- Top 8 active Attica areas by salon count (at least 6 shown when the API returns sufficient data)
- Athens districts take priority (DEC-012 — Athens focus)
- Each tile links to `/search?area={slug}` — the canonical, only location param for this section (T-008; `?district=` was never built, do not use it)

**Data:** From `GET /api/areas?region=attica` (T-004), ordered by `salon_count` descending with the stable slug as a deterministic tie-breaker. **Caching:** SSR, `revalidate: 86400` (24h) — see Data Requirements below. Localized area names come from `name_el`/`name_en`/`name_ru`/`name_uk` on each item; stable slug URLs, never localized names or raw `address_district` values, appear in the link.

**Empty state:** On `/api/areas` failure, an invalid/empty payload, or zero areas with `salon_count > 0`, silently render a static fallback of known Athens districts (Glyfada, Athens Center, Piraeus, Marousi, Kallithea, Nea Smyrni, Chalandri, Kifissia) — no invented salon counts, no error shown to the user.

**Mobile:** 2-column grid

---

### Section 5 — How It Works

**Purpose:** Build trust for first-time visitors, especially P-02 who may not understand what Lookla offers vs Google Maps.

**Content (3 steps):**
1. **Search** — "Type the service you need in your language" (icon: search/magnifier)
2. **Discover** — "Browse salons with real working hours, photos, and services in your language" (icon: list/cards)
3. **Contact** — "Call, WhatsApp, or visit the salon directly — no registration needed" (icon: phone/message)

**Language note:** Step 3 must explicitly mention that no registration is required (DEC-016). This is a trust signal for P-02 who may be worried about data/language barriers.

**Mobile:** Vertical stack of 3 cards

---

### Section 6 — Footer

**Content:**
- Language switcher (secondary placement; primary is in header)
- Links: About, Contact, Privacy Policy
- Copyright notice
- **Not linked:** `/pricing`, `/plans`, `/dashboard` (DEC-006)

---

## Data Requirements

| Data | Source | Caching |
|---|---|---|
| Category grid | `/api/categories` | SSR; can be cached aggressively |
| Popular areas | `/api/areas?region=attica` | SSR, `revalidate: 86400` |
| User locale | `next-intl` routing | URL-based |
| Auth state | `/api/auth/me` | Client-side hydration |

---

## User Actions and Analytics Events

| Action | GA4 Event | Parameters |
|---|---|---|
| Submit search from hero bar | `home_search_submitted` | `query`, `locale` |
| Click category tile | `home_category_clicked` | `category_slug`, `locale` |
| Click area tile | `home_area_clicked` | `area_name`, `locale` |
| Click language switcher | `locale_switched` | `from_locale`, `to_locale`, `page: home` |
| Click Login / Register | `auth_intent` | `action: login/register`, `page: home` |

---

## Empty States

| Scenario | Behaviour |
|---|---|
| Category API fails | Static fallback list of 8 known categories |
| Areas API fails | Static fallback list of Athens districts |
| User not logged in | Normal — anonymous access is standard (DEC-016) |
| Slow connection | Show skeleton placeholders for category and area grids |

---

## Error States

| Scenario | Behaviour |
|---|---|
| Full page fails to load | Browser default error (network issue — no special handling) |
| Category API 500 | Show static fallback silently; do not show error to user |
| Locale not supported | Redirect to `/el` (default locale) |

---

## Mobile Considerations

- Hero search bar must be large enough to tap without zooming (min 44px height)
- Language switcher must be visible without scrolling (top bar)
- Category grid: 2 columns
- Area grid: 2 columns
- "How it works": stacked cards, not horizontal
- No hover-only interactions
- All content must be usable without location permission (no geo prompts on homepage)

---

## Implementation Notes

**Changes from current implementation:**
1. Language switcher moved to header (currently footer-only — gap identified in J-02)
2. Implemented by T-008 (branch `feat/T-008-homepage-area-grid`, pending review/merge): "Popular Cities" section renamed to "Popular Areas" (`CityGrid` → `AreaGrid`), populated from `GET /api/areas?region=attica` (DEC-010). Completion is recorded here as `✅ Done (T-008)` only after merge and production verification.
3. "How it works" step 3 must mention no registration required (DEC-016 compliance)
4. Navigation: remove any link to `/pricing` if present (DEC-006 compliance check)

**Render mode:** SSR (current — correct). All above-fold content rendered server-side for performance and SEO.

---

*Last updated: 2026-07-09*
