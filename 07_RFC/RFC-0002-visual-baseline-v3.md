---
title: RFC — Visual Baseline v3: brand identity and homepage discovery
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-08-17
related_documents:
  - 07_RFC/RFC-0001-visual-baseline-v2.md
  - 06_ENGINEERING/VISUAL_BASELINE_V2.md
  - 06_ENGINEERING/VISUAL_BASELINE_V3.md
  - 00_GOVERNANCE/DECISION_LOG.md
implementation_status: Approved — implementation starting with T-105
---

# RFC-0002 — Visual Baseline v3: brand identity and homepage discovery

Date: 2026-08-17
Requested by: Product Owner, acting on a design review conducted with an external design-architect pass (GPT-based) over the already-shipped Visual Baseline v2, plus attached reference mockups (desktop + mobile homepage, logo concept sheet)
Status: Approved

---

## Problem

Visual Baseline v2 (T-095→T-104, complete 2026-08-15) fixed desktop composition, gallery, reviews, map clustering, and contact-CTA layout, and gave the homepage hero a first image-led pass (rotating real salon photo collage). The Product Owner's follow-up review, against attached reference mockups, is that the result reads as **the same Lookla with tidier spacing and a few added photos** rather than a visually distinct new version — specifically: the homepage hero is still a text block with a small photo collage bolted on, there is no dedicated section actually showcasing real salon listings above the fold, the site has no logo asset at all (the wordmark is plain bold text, confirmed at `Header.tsx:96`), and map cluster colours use a generic traffic-light palette unrelated to the brand.

This is explicitly **not** a reversal of V2 — every V2 change (desktop two-column layout, gallery, compact reviews, responsive contact actions, marker clustering, desktop nav, mobile filters, image-fallback handling) is kept unmodified. This is a further pass, one layer up: brand identity (a real logo) and homepage discovery density (a section that actually shows salons, not just a hero photo).

## Evidence

- Code-confirmed: `Header.tsx:96` renders the logo as `<Link className="text-xl font-bold text-brand">Lookla</Link>` — plain text, no SVG/image asset exists anywhere in the repo to "replace"; this is new-asset creation, not a swap.
- Code-confirmed: the homepage (`page.tsx`) has no salon-listing section at all between the hero and "How it works" — `CategoryGrid` and `AreaGrid` show categories/areas, never actual salons, until a visitor leaves the homepage entirely.
- Code-confirmed: `salons.py`'s default listing query already sorts `rating_google.desc().nullslast(), rating_count.desc()` — the exact criterion this RFC proposes for a "Top salons" homepage section already exists and is already the site's own definition of "best first," not a new invented ranking.
- Code-confirmed: `MapView.tsx`'s cluster styling (T-101, this session) uses `leaflet.markercluster`'s default size-tier palette, never restyled to the brand's burgundy/blush tokens.
- Design-review reference: one attached image (`ChatGPT Image Aug 17, 2026, 06_45_17 PM.png`) — desktop hero (two-part composition: headline+search left, single large salon photo + floating salon-card right), mobile hero (same composition, stacked), Popular services row, a new "Top salons in Athens" card row, "Explore by area," and a logo concept sheet (line-art lotus mark + wordmark, horizontal/symbol-only/compact variants).

## Goal

The homepage hero becomes one cohesive composition (headline + search + one large real salon photo + a floating real-salon info card), not text-plus-collage; a new "Top salons" section surfaces real, ranked salon listings above "Explore by area," so discovery content appears before the homepage fully commits to just categories/areas; a real SVG logo (line-art lotus mark + wordmark) replaces the plain-text wordmark everywhere (header, favicon); map clusters are restyled to the brand palette; the professionals page's placeholder feel (emoji feature icons, an empty "coming soon" screen) is cleaned up — all **without** fake data, fake bookings, fake promotions, paid placement, or any change to routing, search/filter behaviour, legal pages, cookie consent, API contracts, or auth/business logic.

## Proposed Solution

Full text of the accepted design-architect brief is kept alongside this RFC as the working spec input; the living, ticket-by-ticket implementation record is `06_ENGINEERING/VISUAL_BASELINE_V3.md` (opened by this RFC, structured like V1/V2's). The brief's own three-phase split is kept, renamed to avoid colliding with V2's P0/P1 terminology:

- **Phase 3A** — logo asset, homepage hero recomposition, Top salons section (T-105–T-108)
- **Phase 3B** — search/list visual harmonisation, map cluster brand styling, professionals page cleanup (T-109–T-111)
- **Phase 3C** — salon-detail visual harmonisation, footer, final responsive polish (T-112+)

Each phase ends in a screenshot-based visual verification pass (desktop 1440×900 + mobile 390×844 minimum, per the brief's own §26) before the next phase starts — build/tests passing is necessary, not sufficient, per the brief's own explicit failure criterion (§27).

## Alternatives Considered

**Scope the logo to a CSS/typography treatment instead of a real SVG mark** — rejected: the reference mockup's own visual-direction test ("user should immediately notice this is a new Lookla") depends on a real mark, not a font change, and the brief explicitly asks for a designed SVG asset (§4), not a font substitution.

**"Top salons" ranked by something other than the existing rating/review-count sort** (manual curation, paid placement, newest-first) — rejected by Product Owner: no manual curation, no payment for placement — real data, the same criterion the site already uses elsewhere as its definition of "best," with a minimum bar (≥4.5★, ≥20 reviews) so a single 5.0-with-one-review listing can't appear as a false "top" result.

## User Value

A homepage that reads as a real marketplace with real, browsable inventory above the fold, not a search box with categories underneath; a real brand mark instead of plain text, which is the single most-cited "still looks like the old site" signal in the design review.

## Implementation Complexity

Large — comparable to or larger than V2's P0. Phase 3A alone touches `Header.tsx` (new logo everywhere, including favicon), `page.tsx` (hero recomposition, new Top salons section), a new `TopSalons` component, plus their tests. No backend/API changes anticipated — Top salons reuses the existing sort; no new endpoint.

## Maintenance Impact

One new runtime asset class (SVG logo, `logo-full.svg`/`logo-mark.svg`) with no new dependency. Token-driven, component-level changes throughout, same discipline as V1/V2.

## Architecture Impact

No data model, API contract, or component-boundary changes anticipated. Presentation-layer only, with one exception to confirm per-ticket: the "Top salons" section's data source (existing `/api/salons` listing endpoint, filtered/limited client- or server-side — decided at T-107, not pre-committed here).

## Mobile Impact

Explicitly in scope, and explicitly **not** a scaled-down desktop composition — the brief (§6) requires a separate mobile hero composition, and reference mockups give both breakpoints directly.

## AI Impact

None. No AI feature involved.

## Estimated Cost

| Item | Estimate |
|---|---|
| Implementation time | Phase 3A: 4 tickets; full v3 sequence budgeted ticket-by-ticket like V1/V2, not fixed upfront |
| Infrastructure cost (monthly) | None |
| AI/API cost (per request or monthly) | None |
| Maintenance burden | Comparable to V1/V2 |

## Dependencies

None blocking start. T-105 (logo asset) has no dependency and is sequenced first, matching the brief's own phase ordering.

## Risks

- **A second conversion-baseline discontinuity in close succession.** V2's baseline reset on 2026-08-14 23:39 is under two weeks old at RFC time. Product Owner explicitly chose to reset again at v3's completion rather than treat this as a continuation of the same baseline — see Decision below.
- **Rebrand risk.** A real logo, once shipped, is the kind of change that is expensive to reverse gracefully (favicon caching, brand recognition). Confirmed explicitly with Product Owner as a deliberate rebrand, not proceeding on the reviewer's say-so alone.
- **"Top salons" ranking drift.** If the rating/review-count criterion is ever changed, it changes which real businesses appear on the homepage — noted so a future ticket doesn't casually adjust the threshold without recognising it as a visible product decision, not a tuning parameter.
- Rollback plan: same as V1/V2 — revert the specific ticket's commit(s); nothing in this RFC is a single irreversible cutover.

---

## Decision

Decision: **APPROVED**
Reason: Product Owner reviewed the three real open questions this RFC's implementing session raised before writing code — (1) whether the new logo is a deliberate rebrand, (2) the Top-salons ranking criterion, (3) whether to reset the conversion baseline again — and confirmed all three directly (2026-08-17), each with the recommended default.
Conditions: (1) `06_ENGINEERING/VISUAL_BASELINE_V3.md` records the new conversion-baseline inception point at the moment Phase 3A's homepage changes reach production, mirroring V1/V2's own methodology. (2) Ships as a ticket sequence, each verified (lint/typecheck/tests/build + responsive + screenshot check) before the next starts. (3) No product-model change (booking, fake listings, discounts, paid placement) — unchanged from V2's own non-goals.
Decision ID: DEC-026
Date: 2026-08-17
