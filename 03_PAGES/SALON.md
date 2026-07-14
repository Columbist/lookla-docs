---
title: Salon Detail Page Specification
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 01_PRODUCT/USER_JOURNEYS.md
  - 01_PRODUCT/PRODUCT_TERMINOLOGY.md
  - 00_GOVERNANCE/DECISION_LOG.md
  - 02_DESIGN/UX_FLOWS.md
  - 04_ARCHITECTURE/DATA_FLOW.md
implementation_status: Implemented — 4 changes required before MVP launch (DEC-013/014/015/017)
---

# Salon Detail Page (Listing)
**Lookla Beauty Marketplace**

---

## Purpose

The Salon Detail Page is the conversion page. This is where a Visitor decides whether to contact a salon. Every section on this page serves one goal: give the user enough confidence to make contact.

The page must provide:
- Immediate identification (is this the right salon?)
- Trust (is it real? is the information current?)
- Action (how do I contact them?)

**Primary conversion actions (DEC-015):**
1. "Call salon" → click-to-call on phone number
2. "Message on WhatsApp" → opens WhatsApp with salon number
3. "Visit website" → opens salon's own website in new tab

There is no booking flow. There is no registration requirement. There are no stubs.

---

## Target Persona

All personas converge here. Entry is from search results or from a direct URL.

- **P-02 (Russian/Ukrainian):** needs service names and reviews in Russian; WhatsApp is primary CTA
- **P-01 (Greek):** checks hours, calls to make appointment; phone is primary CTA
- **P-03 (Expat):** English content; may prefer website link to see more

---

## User Intent

| Intent | Signal | Page Response |
|---|---|---|
| "Is this salon what I need?" | Just arrived from search | Hero: name, photos, category, open/closed status |
| "Is it open right now?" | Looks at top section | Open/Closed badge + today's hours prominently displayed |
| "What services do they offer and at what price?" | Scrolls to services | Services section (lazy-loaded) with prices |
| "Are they any good?" | Scrolls to reviews | Reviews section with Google source label |
| "I want to contact them" | Looks for contact options | Contact CTAs (prominent, above fold or 1 scroll on mobile) |
| "Something looks wrong" | — | Report incorrect information link |

---

## Entry Points

| Source | URL |
|---|---|
| Search result click | `/[locale]/salons/[slug]` |
| Map pin click | Same |
| Direct URL / share | Same |
| Google SERP (via SSR metadata) | Same |

---

## Page Structure

### Above the fold (critical — user sees without scrolling)

```
[ Header: Logo | Search bar | Language switcher ]
─────────────────────────────────────────────────
[ Photo gallery (hero photo full-width, thumbnails row) ]
─────────────────────────────────────────────────
[ Salon name ]  [ OPEN / CLOSED badge ]
[ Category ]    [ Rating: 4.7 ★ (128 reviews) ]
[ Verified label — if applicable ]
─────────────────────────────────────────────────
[ CONTACT BUTTONS: Call | WhatsApp | Website ]
─────────────────────────────────────────────────
```

Everything above the fold must be visible on a typical mobile screen (375px width). The contact buttons must not require scrolling on mobile.

---

## Section 1 — Photo Gallery

**Content:**
- Primary photo displayed as large hero image
- Secondary photos as scrollable thumbnail row below

**Behaviour:**
- Click/tap photo → lightbox view (or full-screen overlay on mobile)
- On mobile: swipe through photos in full-screen

**Data source:** `GET /api/salons/{id}/photos`

**Empty state:** If no photos, show placeholder with salon name initial + brand colour

**Bot protection:** Photos are served from R2 CDN (or lazy-migrated from Google Places). Photo load is not behind IntersectionObserver — photos load eagerly. (Only services and reviews are bot-protected.)

---

## Section 2 — Salon Identity Block

**Content:**
- Salon name (large, H1 equivalent)
- Category badges (e.g., "Nail salon", "Hair salon")
- Open/Closed status badge:
  - OPEN — green, with today's closing time: "Open · Closes at 19:00"
  - CLOSED — red, with next opening: "Closed · Opens Tuesday at 10:00"
- Rating display: "4.7 ★ (128)" — where 128 is the review count from Google
- Verified label (DEC-014):
  - **"Information reviewed"** — if `is_verified = true` and salon is NOT claimed (admin-reviewed only)
  - **"Owner verified"** — if salon has been claimed by an owner AND completed verification
  - **No label** — default; most unclaimed salons

**Important:** Do NOT show the ✓ icon. Show text only. (DEC-014)

**Data source:** `GET /api/salons/{id}` (SSR)

---

## Section 3 — Contact Actions

**This is the most important section on the page.**

**Buttons (DEC-015):**

| Button | Condition | Behaviour |
|---|---|---|
| "Call salon" | `phone_primary` is present | Opens `tel:{phone}` on mobile; shows number on desktop |
| "Message on WhatsApp" | `phone_primary` is present | Opens `https://wa.me/{phone_e164}` in new tab |
| "Visit website" | `website` is present | Opens `{website}` in new tab |

**Not present:**
- "Book now" — prohibited (DEC-015)
- "Reserve" — prohibited
- "Schedule appointment" — prohibited
- Any stub or "Coming soon" button

**If no contact information:**
- Show: "Contact information not available."
- Show the Report link

**Registration requirement (DEC-016):**
- Phone number is shown directly — no login required
- WhatsApp link opens directly — no login required
- Website link opens directly — no login required

**Implementation status:** ✅ T-009 done (merged 2026-07-13, verified in production) — fake "Book now"/"Request appointment"/"Message" buttons removed. ✅ T-010 done (merged 2026-07-14, verified in production) — final 3-action contract live.

**T-010 final decisions:**
- **Viber removed.** DEC-015 and the backlog define exactly 3 approved actions (Call, WhatsApp, Website); Viber was a 4th undocumented action. The user-facing salon-detail Viber button is gone; backend fields and infrastructure are untouched.
- **Empty state implemented.** When none of the 3 actions have usable data, `ContactButtons` renders "Contact information not available" plus the existing `ReportButton` component (reused, not reimplemented) — no disabled buttons, no empty grid.
- **`components/ContactButtons.tsx` recreated properly** (T-009 had deleted the previous, fully-unreachable version) with a slim props contract (`phone`, `websiteUrl`, `salonName`, `salonId`, `locale`) and its logic backed by pure, unit-tested helpers in `lib/contactActions.ts`.
- **Phone normalization:** two small pure functions — `normalizePhoneForWhatsApp` (digits-only, for `wa.me`) and `normalizePhoneForCall` (keeps a leading `+` if present, for `tel:`). Neither invents a Greek country code for numbers stored without one.
- **Website normalization:** bare hostnames get `https://` added; existing `http://`/`https://` preserved as-is; `javascript:`/`data:`/`file:` and any other unrecognized scheme rejected (returns `null`, action hidden) rather than rendered unsafely. Embedded credentials (`https://user:pass@host`) are also rejected outright — review-round finding, fixed before merge.
- **Phone input is validated before normalization**, not just after: a value containing letters (e.g. a corrupted `+30 CALL-ME`) is rejected entirely rather than silently truncated to a short digit fragment that would still produce a formally-valid but meaningless `tel:`/`wa.me` link — review-round finding, fixed before merge.
- **Desktop shows the phone number** next to the "Call" label (`hidden sm:inline` — mobile stays label-only to avoid overflow on 375px).
- All 3 actions remain anonymous — no login/auth check.

**Analytics (DEC-017):**

| Action | GA4 Event | Parameters |
|---|---|---|
| Click "Call salon" | `contact_action` | `action_type: phone`, `salon_id`, `salon_name` |
| Click "Message on WhatsApp" | `contact_action` | `action_type: whatsapp`, `salon_id`, `salon_name` |
| Click "Visit website" | `contact_action` | `action_type: website`, `salon_id`, `salon_name` |

**These three events are the primary MVP success metric (DEC-008). They must be instrumented before launch.**

---

## Section 4 — About / Description

**Content:**
- Salon description text (if available)
- Address: street + district/area name
- Working hours table (full week, today's row highlighted)

**Data source:** `GET /api/salons/{id}` + `salon_hours` (SSR)

**Translation:** Description may be in Greek only. Translation to ru/uk on first real-user view (via GPT-4o-mini, cached in DB). If description is in Greek and locale is Russian, show translation with 🌐 badge.

**Empty state (no description):** Section is hidden; only address and hours are shown

---

## Section 5 — Services (Lazy-loaded)

**Loading trigger:** IntersectionObserver — loads when section enters viewport

**Behaviour:**
- Bot protection: `GET /api/salons/{id}/services?lang={locale}` returns `[]` for detected bots
- Real users: returns all services for the salon, with names translated to the current locale
- Translation badge: show 🌐 indicator on translated service names
- First view triggers translation (if not cached); cached result served on subsequent views

**Content per service:**
- Service name (in current locale)
- Price range: "€15 – €25" or "from €15"
- Duration (if available): "60 min"
- Category grouping (group by category if salon has multiple)

**Empty state:**
- No services in data: "Service information not available for this salon"
- Do not show skeleton indefinitely if API returns empty array

**Sort:** By category, then by price ascending within category

---

## Section 6 — Reviews (Lazy-loaded)

**This section implements DEC-013 and must be correct before MVP launch.**

**Loading trigger:** IntersectionObserver — loads when section enters viewport

**Behaviour:**
- Bot protection: returns `[]` for detected bots
- Real users: returns all reviews, translated to current locale on first view
- Translation badge: 🌐 on each translated review

**Section header (REQUIRED per DEC-013):**
```
Reviews
─────────────────────────────────────────
Source: Google Reviews  |  Imported: Yes  |  Original: No
─────────────────────────────────────────
```

This header must be visible. It cannot be hidden, collapsed, or shown in a tooltip. It is the honest disclosure required by DEC-013.

**Implementation status:** ✅ T-012 done (branch `feat/T-012-google-review-source-label`, pending independent review, merge, and production verification — do not mark Completed before all three). Exact required text per locale (`salon.googleReviewsSourceLabel`):

| Locale | Text |
|---|---|
| en | Source: Google Reviews / Imported: Yes / Original: No |
| el | Πηγή: Google Reviews / Εισήχθη: Ναι / Πρωτότυπο: Όχι |
| ru | Источник: Google Reviews / Импортировано: Да / Оригинал: Нет |
| uk | Джерело: Google Reviews / Імпортовано: Так / Оригінал: Ні |

Section-level disclosure (one `<p>` per page load, not per review) rendered directly above the review list, immediately after the "Reviews" `<h2>`. Shown only when reviews have loaded (`!loading && reviewCount > 0`) via the pure helper `shouldShowReviewSourceLabel` in `lib/reviewsSection.ts` — hidden while loading, hidden when there are zero reviews (whether genuinely empty or a failed fetch, since `useLazySection`'s error handling already collapses both to an empty array). Not a tooltip, not `title=`, not collapsible.

**Per-review content:**
- Author name
- Star rating
- Review text (translated if non-current-locale)
- Date of review
- Translation badge if translated (🌐 "Translated from Greek")

**Empty state:** Documented as "No reviews available for this salon", but **this text does not currently render** — when there are zero reviews (or the reviews fetch fails), the entire Reviews section (including the "Reviews" heading) renders nothing at all. Pre-existing gap, found during T-012, not fixed here (T-012 does not touch review fetching/empty-state UI by its own scope) — candidate for a follow-up ticket.

**Rating shown:** Average from `rating_google` (already shown in Section 2). Do not recalculate from individual reviews displayed.

---

## Section 7 — Location

**Content:**
- Full address: street number, district/area, city
- Embedded map with pin (Leaflet or static map image)
- "Open in Google Maps" link

**Data source:** `lat`, `lng` from salons table

**Empty state:** If no coordinates, show text address only; no map

**Mobile:** Map displayed below address; tap to open Google Maps

---

## Section 8 — Report Incorrect Information

**Content:**
- Small link/button: "Report incorrect information"
- Click → opens modal/form with fields:
  - What is incorrect: [Phone] [Hours] [Address] [Name] [Photos] [Other]
  - Optional: description text
  - Submit (requires auth per current implementation — `POST /api/reports`)

**Note on auth requirement:** Currently `/api/reports` requires authentication. This creates friction. Whether to remove auth requirement from reports is not a blocking MVP decision — document as a known friction point.

---

## Translation Behaviour Summary

| Content | Translation | Bot protection |
|---|---|---|
| Salon name | Pre-translated (name_el/name_en) | No |
| Description | On-demand, first real-user view | Yes (no translation) |
| Services | On-demand, first real-user view | Yes (returns []) |
| Reviews | On-demand, first real-user view | Yes (returns []) |
| Address | Not translated (proper noun) | No |
| Category names | Pre-translated (name_el/name_en/name_ru/name_uk in categories table) | No |

---

## Page Metadata (SSR)

For SEO and social sharing (SSR portion):
- `<title>`: "{salon_name} — {category} in {district} | Lookla"
- `<meta description>`: "{salon_name} in {district}. See working hours, services, and contact information."
- OG image: primary photo URL
- Canonical URL: `https://lookla.gr/{locale}/salons/{slug}`
- `X-Robots-Tag: noindex` NOT set on this page (this page should be indexable)

---

## Empty States

| Scenario | Behaviour |
|---|---|
| Salon not found | 404 page (custom) |
| No photos | Placeholder illustration |
| No description | Section hidden |
| No services | "Service information not available" |
| No reviews | "No reviews available" |
| No contact info | "Contact information not available" + Report link |
| No coordinates | Text address only; no map |

---

## Error States

| Scenario | Behaviour |
|---|---|
| Services API 500 | Show "Could not load services" with retry link |
| Reviews API 500 | Show "Could not load reviews" with retry link |
| Photo load fails | Show broken image placeholder; do not break layout |

---

## Mobile Considerations

- Contact buttons must be visible without scrolling (or at most 1 scroll on mobile 375px)
- Contact buttons must be full-width on mobile, tap-friendly (min 48px height)
- Photo gallery: swipeable carousel on mobile
- Services: collapsed by category, expandable on tap
- Map: smaller, tap to open Google Maps (not embedded full map on mobile)
- Review source label must be visible (cannot hide on mobile)

---

## Implementation Checklist (pre-MVP)

- [ ] Remove all booking stub buttons (DEC-015)
- [ ] Add "Call salon", "WhatsApp", "Visit website" CTAs if not already present
- [ ] Confirm CTAs require no login (DEC-016)
- [ ] Replace ✓ badge with text label "Information reviewed" / "Owner verified" (DEC-014)
- [ ] Add review section header with Google source label (DEC-013)
- [ ] Instrument contact click GA4 events (DEC-017)
- [ ] Confirm services and reviews are lazy-loaded (bot protection)
- [ ] Confirm translation badge (🌐) appears on translated content

---

*Last updated: 2026-07-09*
