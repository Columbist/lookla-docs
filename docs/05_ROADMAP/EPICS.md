---
title: Engineering Epics
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 05_ROADMAP/IMPLEMENTATION_BACKLOG.md
  - 05_ROADMAP/MILESTONE_M01.md
  - 01_PRODUCT/MVP_SCOPE_LOCK.md
  - 04_ARCHITECTURE/BACKEND_ARCHITECTURE.md
  - 04_ARCHITECTURE/FRONTEND_ARCHITECTURE.md
  - 08_REVIEWS/ARCHITECTURE_REVIEW.md
implementation_status: N/A — planning document; decomposed into IMPLEMENTATION_BACKLOG.md
---

# Engineering Epics
**Lookla Beauty Marketplace — M-01 MVP Athens Launch**

> An Epic is a logical group of related tasks that delivers a coherent piece of user or system value.
>
> Each Epic maps to one or more approved decisions (DEC-NNN) or architecture documents.
>
> Epic complexity is estimated in **developer-days** (1 dev-day = 1 focused developer working day, no interruptions assumed).

---

## EPIC-01 — Database Foundations

**Goal:** Make the database schema evolution safe and implement DEC-010 location hierarchy at the data layer.

**Why this is Epic 1:** Everything else depends on having a correct, migration-tracked schema. This must be done before any other backend change.

**Decisions:** DEC-010 | Architecture finding: UNDER-01, CONTRADICTION-03

**Features:**
- Alembic setup and baseline migration capturing current schema
- `address_district` and `address_region` columns added to `salons` table
- Backfill migration: populate `address_district` for all existing salons from `address_city` values
- GIN full-text search index verification (create if missing)
- `idx_salons_address_district` BTREE index

**Dependencies:** None. This is the first Epic.

**Estimated complexity:** 2 developer-days

**Acceptance Criteria:**
- [ ] `alembic upgrade head` runs cleanly on a fresh DB from `db/init.sql`
- [ ] `alembic downgrade -1` reverts the `address_district` column without data loss
- [ ] All 6300 existing salons have a non-null `address_district` value for Athens metro salons
- [ ] `SELECT * FROM salons WHERE address_district = 'Glyfada' LIMIT 5` returns expected results
- [ ] GIN index exists: `SELECT indexname FROM pg_indexes WHERE tablename = 'salons' AND indexdef LIKE '%GIN%'`
- [ ] `idx_salons_address_district` index exists in `pg_indexes`

**Tasks:** T-001, T-002, T-003 (see IMPLEMENTATION_BACKLOG.md)

---

## EPIC-02 — Location Hierarchy (Area Filter)

**Goal:** Replace the flat "City" filter with the approved district/area hierarchy so users can search by Glyfada, Kolonaki, Marousi, etc.

**Decisions:** DEC-010

**Features:**
- Backend: `GET /api/areas` new endpoint returning Athens district list with salon counts
- Backend: `GET /api/salons` updated to accept `area` param (mapping to `address_district`)
- Backend: CITY_SYNONYMS dict updated to include district-level synonyms for Russian/Ukrainian input
- Frontend: `SearchFilters.tsx` area dropdown populated from `/api/areas`
- Frontend: Filter label changed from "City" to "Area" / "Περιοχή" / "Район" in all 4 message files
- Frontend: `CityGrid.tsx` → `AreaGrid.tsx` on homepage, populated with Athens districts
- Frontend: Homepage area section label renamed from "Popular Cities" to "Popular Areas"
- Frontend: URL state: `?area=glyfada` replaces `?city=Glyfada`

**Dependencies:** EPIC-01 (address_district column must exist before area filter works)

**Estimated complexity:** 2 developer-days

**Acceptance Criteria:**
- [ ] `GET /api/areas` returns ≥8 Athens districts with `salon_count > 0`
- [ ] `GET /api/salons?area=glyfada` returns only salons where `address_district = 'Glyfada'`
- [ ] `GET /api/salons?city=Glyfada` still works (backwards compat during transition)
- [ ] Search page filter label shows "Area" (en), "Περιοχή" (el), "Район" (ru), "Район" (uk)
- [ ] Homepage area grid shows ≥6 Athens districts with click links to `/search?area=`
- [ ] Empty state: `GET /api/salons?area=unknown-place` returns `{"items": [], "total": 0}`
- [ ] Filtering by area shows correct result count in "N salons in [Area]" header

**Tasks:** T-004, T-005, T-006, T-007, T-008

---

## EPIC-03 — Honest Salon Detail

**Goal:** Bring the salon detail page into compliance with DEC-013, DEC-014, and DEC-015 — the three decisions that define honest UX for the most important page.

**Decisions:** DEC-013 (review labels), DEC-014 (verified badge), DEC-015 (no booking stubs)

**Features:**
- Remove all booking stub buttons from `SalonDetailClient.tsx`
- Verify "Call salon", "WhatsApp", "Visit website" CTAs present and functional
- Confirm all CTAs work without registration (DEC-016 compliance)
- Replace ✓ badge/icon with text label: "Information reviewed" or "Owner verified" (see ARCHITECTURE_REVIEW CONTRADICTION-01 for resolution)
- Add review section header: "Source: Google Reviews / Imported: Yes / Original: No"
- Apply badge and review changes to `SalonCard.tsx` as well (card-level verified label)

**Dependencies:** EPIC-01 (requires is_verified/owner-verified distinction to be resolved first — CONTRADICTION-01)

**Estimated complexity:** 1 developer-day

**Acceptance Criteria:**
- [ ] No "Book", "Reserve", "Schedule" text visible on salon detail page at any screen size
- [ ] "Call salon" button fires `tel:` link on mobile; shows phone number on desktop
- [ ] "Message on WhatsApp" opens `https://wa.me/{phone}` in new tab
- [ ] "Visit website" opens salon's website URL in new tab with `rel="noopener noreferrer"`
- [ ] All 3 CTAs are accessible without being logged in
- [ ] `is_verified = true` AND no `salon_owners` row → shows "Information reviewed" text
- [ ] `is_verified = true` AND `salon_owners` row exists → shows "Owner verified" text
- [ ] `is_verified = false` → no badge shown
- [ ] Review section header: "Source: Google Reviews / Imported: Yes / Original: No" visible on desktop AND mobile
- [ ] Review label is NOT in a tooltip, NOT collapsed, NOT behind a "show more" click

**Tasks:** T-009, T-010, T-011, T-012

---

## EPIC-04 — Analytics Integration

**Goal:** Install GA4 before MVP launch so DEC-008 success metrics (500 contact actions in 90 days) can be measured.

**Decisions:** DEC-017, DEC-008

**Features:**
- GA4 property created in Google Analytics account
- GA4 tracking script added to Next.js root layout (`strategy="afterInteractive"`)
- Custom event `contact_action` fired on every contact button click (phone, whatsapp, website)
- `useAnalytics()` hook implemented and used in `ContactButtons.tsx`
- Admin email excluded from GA4 tracking (filter in GA4 dashboard)
- Google Search Console property created and verified via DNS TXT record
- `NEXT_PUBLIC_GA4_ID` env var defined in `.env` and `.env.example`

**Dependencies:** None (frontend-only; can run in parallel with EPICs 01-03)

**Estimated complexity:** 1 developer-day

**Acceptance Criteria:**
- [ ] GA4 Realtime report shows pageview events when browsing the site
- [ ] Tapping "Call salon" fires `contact_action` event with `action_type: phone` in GA4 Realtime
- [ ] Tapping "WhatsApp" fires `contact_action` event with `action_type: whatsapp`
- [ ] Tapping "Visit website" fires `contact_action` event with `action_type: website`
- [ ] Events include `salon_id` and `salon_name` parameters
- [ ] Admin user (`columb@europe.com` session) is excluded from GA4 counts
- [ ] Search Console: property verified, `lookla.gr` URL inspection shows indexing status
- [ ] GA4 script does NOT block page render (uses `strategy="afterInteractive"`)
- [ ] LCP on salon detail is not degraded by GA4 script (verify with PageSpeed Insights)

**Tasks:** T-013, T-014, T-015, T-016

---

## EPIC-05 — Legal and Compliance

**Goal:** Satisfy GDPR requirements before GA4 is activated and before any user data is collected.

**Context:** This epic MUST be completed before EPIC-04 is deployed. GA4 without a Privacy Policy and cookie consent is a GDPR violation (see ARCHITECTURE_REVIEW UNDER-04).

**Decisions:** DEC-017 (analytics requires disclosure), SECURITY.md §6

**Features:**
- Create `/[locale]/privacy` page with Privacy Policy text
- Create cookie consent banner component (minimal: one click Accept)
- Add GA4 IP anonymization (dashboard setting, no code change)
- Configure GA4 data retention to 14 months (dashboard setting)

**Dependencies:** None for page creation. Must be complete BEFORE EPIC-04 is deployed.

**Estimated complexity:** 0.5 developer-days (code) + time to write Privacy Policy copy

**Privacy Policy must cover:**
- What data is collected (GA4 sessions, contact events, registration data)
- Why it is collected (service improvement, analytics)
- Third parties: Google (GA4), Cloudflare (CDN, security)
- User rights: access, deletion, portability (email hello@lookla.gr)
- Cookie types: session cookies (auth), analytics cookies (GA4)
- Data retention periods

**Acceptance Criteria:**
- [ ] `/el/privacy`, `/en/privacy`, `/ru/privacy`, `/uk/privacy` pages are accessible (same content, localized)
- [ ] Privacy page is linked from footer on all pages
- [ ] Cookie consent banner appears on first visit; sets a cookie `lookla_consent=1` on Accept
- [ ] GA4 script only loads if `lookla_consent=1` cookie is present
- [ ] GA4 property has IP anonymization enabled (verify in GA4 admin)
- [ ] Privacy Policy mentions Google Analytics by name

**Tasks:** T-017, T-018, T-019

---

## EPIC-06 — New Static Pages

**Goal:** Create the About and Contact pages specified in the product spec.

**Decisions:** ABOUT.md spec, CONTACT.md spec

**Features:**
- `/[locale]/about` page (SSR, static content)
- `/[locale]/contact` page (SSR, static content)
- Footer links to both pages added on all layouts

**Dependencies:** None. Fully independent.

**Estimated complexity:** 0.5 developer-days

**Acceptance Criteria:**
- [ ] `/el/about`, `/en/about`, `/ru/about`, `/uk/about` return 200
- [ ] `/el/contact`, `/en/contact`, `/ru/contact`, `/uk/contact` return 200
- [ ] Both pages appear in footer navigation
- [ ] About page does not claim features that don't exist (no "Book online" language)
- [ ] About page mentions "no account required to search" (DEC-016)
- [ ] Contact page directs users to use the Report button on salon pages (not a duplicate form)
- [ ] Contact page mentions hello@lookla.gr for salon owners
- [ ] Neither page links to /pricing or /plans

**Tasks:** T-020, T-021

---

## EPIC-07 — Homepage Updates

**Goal:** Move language switcher to header (HOME.md spec gap) and update homepage to reflect area-based navigation.

**Decisions:** HOME.md spec, DEC-010

**Features:**
- Language switcher added to `Header.tsx` (visible on all pages, not just footer)
- Header language switcher is visible without scrolling on mobile 375px
- "Popular Cities" section label → "Popular Areas" in all 4 locales
- Area grid linked to `?area=` params (after EPIC-02 deploys)
- Step 3 of "How it works" section mentions no registration required

**Dependencies:** EPIC-02 (area grid links need area params)

**Estimated complexity:** 0.5 developer-days

**Acceptance Criteria:**
- [ ] Language switcher visible in header on desktop and mobile without scrolling
- [ ] Footer language switcher remains as secondary option
- [ ] Homepage section label shows "Popular Areas" (en) / "Δημοφιλείς Περιοχές" (el) / "Популярные районы" (ru)
- [ ] Clicking a language in the header preserves the current page path
- [ ] "How it works" step 3 text mentions no registration required (at least in en/ru locales)
- [ ] `/pricing` is NOT in the header navigation (DEC-006 verification)

**Tasks:** T-022, T-023

---

## EPIC-08 — Admin Enhancement

**Goal:** Give the admin an inline edit form for salon data — the missing piece identified in ADMIN.md spec and ARCHITECTURE_REVIEW.

**Decisions:** ADMIN.md spec, DEC-012 (data quality), DEC-014 (admin sets verified status)

**Features:**
- Inline edit form in admin salon list: phone_primary, address_street, address_city, address_district
- Admin can set `is_verified = true` ("Information reviewed") with a confirmation click
- Admin salon list displays "Reviewed" text (not ✓) per DEC-014
- Admin dashboard shows "Claimed salons" count (from salon_owners table)
- Daily pg_dump backup cron configured on server (UNDER-05)

**Dependencies:** EPIC-01 (address_district must exist before admin can set it), EPIC-03 (is_verified semantics resolved)

**Estimated complexity:** 1 developer-day

**Acceptance Criteria:**
- [ ] Admin can edit phone_primary on any salon and save; change is reflected immediately on public salon page
- [ ] Admin can set is_verified=true; public salon page shows "Information reviewed" label
- [ ] Admin "Reviewed" column shows text label (not ✓ icon)
- [ ] Admin dashboard stats include "Claimed: N" count
- [ ] `docker logs` shows no SQL errors after admin saves a salon
- [ ] Daily backup cron: `crontab -l` shows the pg_dump job on the server

**Tasks:** T-024, T-025, T-026

---

## EPIC-09 — Code Quality Foundations

**Goal:** Extract critical shared code, add error boundaries, and ensure the codebase is maintainable before development velocity increases.

**Documents:** FRONTEND_ARCHITECTURE.md §7, AUDIT.md §21, ARCHITECTURE_REVIEW UNDER-02, UNDER-03

**Features:**
- Extract `useMe()` hook from 4 pages into `hooks/useMe.ts`
- Extract `localePrefix()` utility from 8 components into `lib/locale.ts`
- Add React error boundary around `SalonDetailClient` with graceful fallback
- Write tests for 4 critical backend functions: `is_bot()`, `_batch_open_now()`, `_translate_query()`, auth refresh
- Add `try/except` in `translate.py` OpenAI call (SPOF-02 mitigation)
- Create `public/robots.txt`

**Dependencies:** None for utilities. Tests should be written before any change to the tested functions.

**Estimated complexity:** 1.5 developer-days

**Acceptance Criteria:**
- [ ] `hooks/useMe.ts` exists; all 4 pages import from it; inline fetch code removed from those pages
- [ ] `lib/locale.ts` `localePrefix()` exists; 8 components import from it; no inline `locale === 'el' ? '' : ...` patterns remain
- [ ] Error boundary wraps `SalonDetailClient`; if a runtime error occurs, fallback shows salon name and contact buttons (from SSR data), not a blank page
- [ ] `pytest tests/test_is_bot.py` passes with ≥5 test cases (known bots + known browsers)
- [ ] `pytest tests/test_open_now.py` passes with DST edge case (last Sunday of October/March)
- [ ] `pytest tests/test_translate_query.py` passes with Russian and Ukrainian input cases
- [ ] `translate.py` catches `openai.APIError` and returns original text as fallback
- [ ] `public/robots.txt` exists with correct Disallow rules (see FRONTEND_ARCHITECTURE.md §14)

**Tasks:** T-027, T-028, T-029, T-030

---

## EPIC-10 — Translation QA

**Goal:** Verify Russian translation quality meets the standard for the primary MVP persona (P-02, DEC-009/DEC-011).

**Decisions:** DEC-011 (el/en/ru mandatory quality)

**Features:**
- Manual review of 20 Athens salon service name translations (Russian)
- Manual review of 10 review translations (Russian)
- Spot check UI strings in `messages/ru.json` — no missing keys, no machine-literal phrases
- Verify translation badge (🌐) appears correctly on translated content
- Spot check English translations (en) for expat persona

**Dependencies:** EPIC-01, EPIC-02 (services must be accessible to trigger translations)

**Estimated complexity:** 0.5 developer-days (manual review, not code)

**Acceptance Criteria:**
- [ ] 20 service names in Russian sound natural (not machine-literal)
- [ ] No "manicure" transliterated as "маникюр" where context suggests a better term
- [ ] All UI strings in ru.json have values (no missing keys returning raw key strings)
- [ ] 🌐 badge visible on at least one translated service name when locale=ru
- [ ] `messages/en.json` has no missing keys (compared to el.json)

**Tasks:** T-031

---

## Epic Summary

| Epic | Complexity | DEC(s) | Blocker? | Parallel with |
|---|---|---|---|---|
| EPIC-01 Database Foundations | 2 days | DEC-010 | Yes (for all DB) | Nothing — must be first |
| EPIC-02 Location Hierarchy | 2 days | DEC-010 | Yes (area filter) | EPIC-04, EPIC-05, EPIC-06 |
| EPIC-03 Honest Salon Detail | 1 day | DEC-013/014/015 | Yes (DEC violations) | EPIC-04, EPIC-05, EPIC-06 |
| EPIC-04 Analytics | 1 day | DEC-017/008 | Yes (after EPIC-05) | EPIC-02, EPIC-03 |
| EPIC-05 Legal/Compliance | 0.5 day | DEC-017 | Yes (before EPIC-04) | All |
| EPIC-06 New Pages | 0.5 day | ABOUT/CONTACT spec | No | All |
| EPIC-07 Homepage | 0.5 day | HOME.md spec | No | EPIC-02 (partial) |
| EPIC-08 Admin Enhancement | 1 day | ADMIN.md spec | No | EPIC-01, EPIC-03 |
| EPIC-09 Code Quality | 1.5 days | AUDIT.md | No | All |
| EPIC-10 Translation QA | 0.5 day | DEC-011 | No | After EPIC-02 |
| **Total** | **~10.5 days** | | | |

---

*Last updated: 2026-07-09*
