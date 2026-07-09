---
title: Wireframe Requirements
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 02_DESIGN/UX_FLOWS.md
  - 03_PAGES/HOME.md
  - 03_PAGES/SEARCH.md
  - 03_PAGES/SALON.md
  - 03_PAGES/ADMIN.md
  - 01_PRODUCT/MVP_SCOPE_LOCK.md
implementation_status: N/A — wireframe brief; no visual design produced yet
---

# Wireframe Requirements
**Lookla Beauty Marketplace**

> This document describes what wireframes are needed for MVP and what each wireframe must show.
>
> **No visual design decisions are made here.** Colours, fonts, and component styling are in DESIGN_SYSTEM.md.
>
> Wireframes are low-fidelity tools for aligning on layout, content priority, and interaction logic before visual design begins.
>
> Status: **Brief complete** — wireframes themselves are not yet produced.

---

## Purpose of Wireframes

Wireframes for MVP serve to:
1. Confirm content priority (what users see first vs after scrolling)
2. Expose layout conflicts before visual design
3. Give engineering a spatial reference alongside page specs
4. Document mobile vs desktop layout differences before development

---

## WF-01 — Homepage (Desktop)

**Corresponds to:** `03_PAGES/HOME.md`

**Required elements, in visual hierarchy order:**

```
┌──────────────────────────────────────────┐
│ HEADER                                   │
│ [Logo]          [Language: RU EL EN UK]  │
│                              [Login]     │
├──────────────────────────────────────────┤
│ HERO                                     │
│ [Headline — large, locale-specific]      │
│ [Subheadline — 1 sentence]               │
│ [Search bar: text input  ] [Search btn]  │
├──────────────────────────────────────────┤
│ POPULAR CATEGORIES                       │
│ [Section title: "Browse by service"]     │
│ [Icon] [Icon] [Icon] [Icon]              │
│ [Icon] [Icon] [Icon] [Icon]              │
├──────────────────────────────────────────┤
│ POPULAR AREAS                            │
│ [Section title: "Popular areas"]         │
│ [Area]  [Area]  [Area]                   │
│ [Area]  [Area]  [Area]                   │
├──────────────────────────────────────────┤
│ HOW IT WORKS                             │
│ [Step 1]    [Step 2]    [Step 3]         │
│ Search      Discover    Contact          │
├──────────────────────────────────────────┤
│ FOOTER                                   │
│ [About] [Contact] [Privacy]  [Logo]     │
│ [Language switcher — secondary]          │
└──────────────────────────────────────────┘
```

**Key constraints to show in wireframe:**
- Language switcher: in header (NOT only in footer — gap from current implementation)
- Hero: search bar must be the first interactive element
- No "Book now" or "Start free trial" CTA anywhere
- "Popular Cities" → "Popular Areas" label change visible

**Annotation notes:**
- Annotate: language switcher is visible on first viewport without scrolling
- Annotate: no payment or booking CTAs anywhere on this page

---

## WF-02 — Homepage (Mobile 375px)

**Same content as WF-01, mobile layout:**

```
┌───────────────────────┐
│ [Logo]    [RU EL EN]  │
├───────────────────────┤
│ HERO                  │
│ [Headline]            │
│ [Subheadline]         │
│ [Search input        ]│
│ [ SEARCH BUTTON      ]│
├───────────────────────┤
│ CATEGORIES            │
│ [Cat] [Cat]           │
│ [Cat] [Cat]           │
│ [Cat] [Cat]           │
├───────────────────────┤
│ POPULAR AREAS         │
│ [Area] [Area]         │
│ [Area] [Area]         │
├───────────────────────┤
│ HOW IT WORKS          │
│ [Step 1 card]         │
│ [Step 2 card]         │
│ [Step 3 card]         │
├───────────────────────┤
│ FOOTER                │
└───────────────────────┘
```

**Key constraints:**
- Search button is below input (not inline) on narrow screens
- Language switcher visible without scrolling (abbreviated: "RU / EL / EN")
- Touch targets ≥44px

---

## WF-03 — Search Page (Desktop, List View)

**Corresponds to:** `03_PAGES/SEARCH.md`

```
┌─────────────────────────────────────────────────┐
│ HEADER                                          │
│ [Logo] [Search bar: query text] [Lang] [Login]  │
├─────────────────────────────────────────────────┤
│ FILTER BAR                                      │
│ [Area ▼]  [Category ▼]  [Rating ▼]  [Map view]  │
├─────────────────────────────────────────────────┤
│ RESULTS COUNT: "47 salons in Glyfada"           │
├─────────────────────────────────────────────────┤
│ [SalonCard]  [SalonCard]  [SalonCard]           │
│ [SalonCard]  [SalonCard]  [SalonCard]           │
│ [SalonCard]  [SalonCard]  [SalonCard]           │
│ ...                                             │
│ [Scroll sentinel — triggers next 24]            │
├─────────────────────────────────────────────────┤
│ FOOTER                                          │
└─────────────────────────────────────────────────┘
```

**SalonCard anatomy (show in detail):**
```
┌──────────────────────────────────┐
│ [Photo 80px]  Salon Name         │
│               Glyfada · Nail     │
│               ★ 4.7 (128)        │
│               OPEN · closes 19:00│
│               from €15           │
│               [Reviewed ✓ label] │ ← text, not ✓ icon
└──────────────────────────────────┘
```

**Constraints to annotate:**
- Filter bar shows "Area" not "City"
- SalonCard shows "Reviewed" or "Owner verified" as text, not ✓ icon
- No booking button on card
- Results count updates as filters change

---

## WF-04 — Search Page (Desktop, Map View)

```
┌────────────────────────────────────────────────┐
│ HEADER                                         │
├────────────────────────────────────────────────┤
│ FILTER BAR (same as WF-03)         [List view] │
├────────────────────────────────────────────────┤
│                                                │
│  [Full-width Leaflet map]                      │
│                                                │
│  Pins visible, clustered if needed             │
│                                                │
│  Click pin → mini card:                        │
│  ┌─────────────────────┐                      │
│  │ Salon Name          │                      │
│  │ ★ 4.7  OPEN         │                      │
│  │ [View salon →]      │                      │
│  └─────────────────────┘                      │
│                                                │
└────────────────────────────────────────────────┘
```

---

## WF-05 — Search Page (Mobile)

```
┌───────────────────────┐
│ [Logo] [Lang] [Login] │
│ [Search bar          ]│
├───────────────────────┤
│ [Filters ▼]  [Map 🗺] │ ← collapsed filter button + map toggle
├───────────────────────┤
│ 47 salons in Glyfada  │
├───────────────────────┤
│ [SalonCard — full w.] │
│ [SalonCard — full w.] │
│ [SalonCard — full w.] │
│ ...                   │
└───────────────────────┘
```

**Filter bottom sheet (opens on tap of "Filters ▼"):**
```
┌───────────────────────┐
│ Filters          [✕]  │
│ ─────────────────     │
│ Area: [Glyfada   ▼]   │
│ Category: [Nail  ▼]   │
│ Rating: [4+      ▼]   │
│ ─────────────────     │
│ [Show 23 results]     │
└───────────────────────┘
```

---

## WF-06 — Salon Detail Page (Desktop)

**Corresponds to:** `03_PAGES/SALON.md`

```
┌─────────────────────────────────────────────────────┐
│ HEADER                                              │
├─────────────────────────────────────────────────────┤
│ [Hero photo — full width]                           │
│ [Thumb] [Thumb] [Thumb] [Thumb]                     │
├─────────────────────────────────────────────────────┤
│ [Salon Name                    ] [OPEN]             │
│ [Nail Salon · Glyfada          ] [★ 4.7 (128)]      │
│ [Information reviewed          ] ← text label only  │
├─────────────────────────────────────────────────────┤
│ [ Call salon ]  [ WhatsApp ]  [ Website ]           │ ← REQUIRED
├─────────────────────────────────────────────────────┤
│ DESCRIPTION / ABOUT                                 │
│ [Text description]                                  │
│ 12 Kyriazi Street, Glyfada · Mon–Sat 10:00–19:00   │
├─────────────────────────────────────────────────────┤
│ SERVICES (lazy-loaded)                              │
│ Nail Care                                           │
│ • Manicure — €15 – €25                             │
│ • Gel nails — from €30                             │
├─────────────────────────────────────────────────────┤
│ REVIEWS (lazy-loaded)                               │
│ Reviews                                             │
│ Source: Google Reviews │ Imported: Yes │ Original: No│ ← REQUIRED
│ ─────────────────────────────────────────────────── │
│ ★★★★★ "Great service!" — Maria, 3 weeks ago        │
│  🌐 Translated from Greek                           │
│ ★★★★☆ "Fast and professional." — Nikos, 2 months  │
├─────────────────────────────────────────────────────┤
│ LOCATION                                            │
│ [Map with pin — 300px height]                       │
│ [Open in Google Maps ↗]                             │
├─────────────────────────────────────────────────────┤
│ [Report incorrect information]                      │
├─────────────────────────────────────────────────────┤
│ FOOTER                                              │
└─────────────────────────────────────────────────────┘
```

**Critical annotations:**
1. Contact buttons: "Call salon", "WhatsApp", "Website" — no "Book now" button
2. Verified label: text only, no ✓ icon
3. Review section header: "Source: Google Reviews / Imported: Yes / Original: No" — always visible
4. 🌐 badge on translated content
5. Services and reviews load only when section enters viewport

**What must NOT appear:**
- Any "Book" / "Reserve" / "Schedule" button
- Any ✓ icon (replace with text)
- Review section without Google source disclosure

---

## WF-07 — Salon Detail Page (Mobile 375px)

```
┌───────────────────────────┐
│ HEADER [Logo] [Lang]      │
├───────────────────────────┤
│ [Hero photo — full width] │
│ [Thumb] [Thumb] [Thumb]   │
├───────────────────────────┤
│ Salon Name          [OPEN]│
│ Nail Salon · Glyfada      │
│ ★ 4.7 (128)               │
│ Information reviewed      │
├───────────────────────────┤
│ [   Call salon   ]        │ ← full-width buttons
│ [   WhatsApp     ]        │ ← full-width buttons
│ [   Website      ]        │ ← full-width buttons
├───────────────────────────┤
│ About                     │
│ [Description text...]     │
│ Mon–Sat 10:00–19:00        │
├───────────────────────────┤
│ Services [lazy]           │
│ • Manicure €15–€25        │
├───────────────────────────┤
│ Reviews [lazy]            │
│ Source: Google Reviews    │
│ Imported: Yes | Original:No│
│ [Review card]             │
│ [Review card]             │
├───────────────────────────┤
│ [Map — 200px]             │
│ [Open in Google Maps]     │
├───────────────────────────┤
│ [Report incorrect info]   │
└───────────────────────────┘
```

**Mobile-specific constraints:**
- Contact buttons are full-width, stacked vertically
- Contact buttons must be visible within 2 scrolls from top
- Review source label: must not be hidden on mobile (not a tooltip, not collapsed)

---

## WF-08 — Admin Panel (Desktop only)

**Corresponds to:** `03_PAGES/ADMIN.md`

```
┌──────────────────────────────────────────────────────┐
│ Lookla Admin            columb@europe.com  [Logout]  │
├─────────────┬────────────────────────────────────────┤
│ SIDEBAR     │ MAIN CONTENT                           │
│             │                                        │
│ Dashboard   │ [Stats cards]                          │
│ Salons      │ Total: 6320  Verified: 128             │
│   Needs     │ Open reports: 7  Needs review: 43      │
│   review    │                                        │
│   All       │ [Quick action buttons]                 │
│ Reports     │ "Review queue (43)" → opens Salons     │
│ Moderation  │                                        │
│ Users       │                                        │
│             │                                        │
└─────────────┴────────────────────────────────────────┘
```

**Salon list view (admin):**
```
┌──────────┬──────────┬────────┬────────┬────────────────┐
│ Name     │ Area     │ Active │ Reviewd│ Actions        │
├──────────┼──────────┼────────┼────────┼────────────────┤
│ Nails X  │ Glyfada  │ ✓      │ ─      │ [View] [Edit]  │
│ Hair Y   │ Kolonaki │ ✓      │ ✓      │ [View] [Edit]  │
└──────────┴──────────┴────────┴────────┴────────────────┘
```

**Annotation:** "Reviewed" column header — not "Verified"; reflects DEC-014 terminology

---

## Wireframe Priority for MVP

| Wireframe | Priority | Blocking |
|---|---|---|
| WF-06 (Salon Desktop) | P0 — critical | Contact buttons and review label changes |
| WF-07 (Salon Mobile) | P0 — critical | Same changes, mobile layout |
| WF-05 (Search Mobile) | P1 — important | Area filter change |
| WF-03 (Search Desktop) | P1 — important | Area filter change |
| WF-01 (Home Desktop) | P2 — important | Language switcher placement, area label |
| WF-02 (Home Mobile) | P2 — important | Same |
| WF-04 (Search Map) | P3 — can reuse existing | No structural changes needed |
| WF-08 (Admin) | P3 — internal | Not user-facing |

---

## What Wireframes Do NOT Need to Show

- Exact colours, fonts, or border radii (DESIGN_SYSTEM.md)
- Final icon designs
- Exact copy (page specs define approved copy)
- Animation or transition behaviour
- Loading states (described in page specs)

---

*Last updated: 2026-07-09*
