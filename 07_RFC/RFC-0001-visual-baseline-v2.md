---
title: RFC — Visual Baseline v2: desktop composition and image-led marketplace feel
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-08-14
related_documents:
  - 06_ENGINEERING/VISUAL_BASELINE_V1.md
  - 06_ENGINEERING/VISUAL_BASELINE_V2.md
  - 00_GOVERNANCE/DECISION_LOG.md
implementation_status: Approved — implementation starting with T-095
---

# RFC-0001 — Visual Baseline v2: desktop composition and image-led marketplace feel

Date: 2026-08-14
Requested by: Product Owner, acting on a design review conducted with an external design-architect pass (GPT-based) over current production screenshots
Status: Approved

---

## Problem

Visual Baseline v1 (T-059→T-067, complete 2026-07-30) fixed the token system, component consistency, and emoji/hardcoded-string cleanup under an explicit **Direction B — "Clean Marketplace, restrained not loud"**: no hero collage, no carousel, no full-height hero (see V1 doc, T-062 section).

A follow-up design review of current production screenshots — desktop specifically — surfaced a problem V1 didn't set out to fix: **desktop pages are laid out as a narrow mobile column centered in a wide viewport**, most visibly on salon detail (`max-w-shell-content` = 896px, single column, no sidebar — confirmed at `SalonDetailClient.tsx:169`) and on non-home pages where `Header`'s `variant="compact"` forces the mobile hamburger even above the `md` breakpoint (confirmed at `Header.tsx:91,98,138`). Beyond layout, the review's broader conclusion is that the restrained Direction B reads as closer to an MVP catalog than a consumer marketplace (Fresha/Treatwell/Airbnb-tier), specifically on the homepage hero, salon gallery, and map.

## Evidence

- Code-confirmed: `Header.tsx` renders the horizontal nav only when `!isCompact` (`variant !== 'default'`); every non-home page (search, salon detail, professionals, legal) gets the hamburger regardless of viewport width.
- Code-confirmed: `SalonDetailClient.tsx` wraps its entire content in one `max-w-shell-content mx-auto` div; no two-column/sidebar structure exists.
- Code-confirmed: `SearchFilters.tsx`'s filter UI is a single `absolute` popover (`w-72`) with no separate mobile presentation — no bottom-sheet, no `role="dialog"`, no body-scroll-lock.
- Doc-confirmed: `VISUAL_BASELINE_V1.md` — T-063 ("Map Accessibility"/clustering) was left an untouched, reserved placeholder; marker clustering genuinely does not exist yet.
- Design-review screenshots (external, GPT-based architect pass) of current production desktop pages at 1440×900 and 1920×1080, provided by Product Owner.

## Goal

Desktop no longer reads as a stretched mobile column; salon detail gets a real two-column composition; navigation is consistent (real nav ≥1024px, hamburger below); map remains usable at hundreds/thousands of salons via clustering; mobile filters become a real bottom sheet; homepage/gallery/reviews feel image-led and consumer-oriented rather than a settings-panel catalog — **without** a rebrand, a new framework, fake content, or product-model changes (booking, discounts, fake listings are explicitly out of scope, per the review's own non-goals).

## Proposed Solution

Full text of the accepted design-architect brief is kept alongside this RFC as the working spec input; the living, ticket-by-ticket implementation record is `06_ENGINEERING/VISUAL_BASELINE_V2.md` (opened by this RFC, structured like V1's). Priority order (P0 → P1 → P2) and the file/component-level technical plan are recorded there per ticket, starting with T-095.

## Alternatives Considered

**Scope down to layout bugs only, keep Direction B's restrained hero/no-collage stance verbatim** — rejected by Product Owner: the desktop-narrow-column problem and the "feels like MVP catalog" problem share root causes (container tokens, image presentation discipline) and splitting them into two initiatives would mean re-touching the same files twice. Product Owner explicitly chose to treat this as a full, intentional v2 direction rather than a bugfix-only pass.

## User Value

Desktop users (real traffic share not yet segmented in this RFC — to be pulled by the Analytics owner before/alongside T-095) currently see ~25–40% of viewport width used on salon detail and search pages; this directly affects perceived product quality and, per the design review's premise, conversion. Mobile users get a real bottom-sheet filter UI and a less empty hamburger drawer.

## Implementation Complexity

Large, multi-ticket sequence — mirrors V1's T-059→T-067 shape. P0 alone is 10 tickets (T-095–T-104) touching `Header.tsx`, `SalonDetailClient.tsx`, `SearchFilters.tsx`, `MapView.tsx`, `SalonCard.tsx`, `ContactButtons.tsx`, `tailwind.config.ts`, `globals.css`, plus their tests. No backend/API changes anticipated for P0.

## Maintenance Impact

Same as V1: token-driven, component-level changes are cheaper to maintain than page-specific CSS. Map clustering (T-063 revival) adds one dependency (clustering plugin for the existing Leaflet stack) — the only new runtime dependency anticipated in P0.

## Architecture Impact

No data model, API contract, or component-boundary changes anticipated. Presentation-layer only. Does not conflict with `PROJECT_CHARTER.md` to the extent already checked; full compliance check happens per-ticket as each lands, same discipline as V1.

## Mobile Impact

Explicitly in scope — this RFC treats mobile and desktop as one adaptive system per ticket (P0 items 5, 6, 8, 9 are mobile-primary). No web-only dependency anticipated.

## AI Impact

None. No AI feature involved.

## Estimated Cost

| Item | Estimate |
|---|---|
| Implementation time | P0: ~10 tickets, V1's comparable sequence (T-059–T-067, 7 tickets) took ~5 weeks; P0 is larger — budget accordingly, ticket-by-ticket, not fixed upfront |
| Infrastructure cost (monthly) | None |
| AI/API cost (per request or monthly) | None |
| Maintenance burden | Comparable to V1 — token/component-driven, not page-specific overrides |

## Dependencies

None blocking start. T-095 (desktop nav consistency) has no dependency and is the cheapest, most-confirmed item — sequenced first.

## Risks

- **Conversion-baseline discontinuity.** The Beta Visual Baseline established 2026-07-30 (per V1) has not been reset by any ticket since. Shipping V2's P0 to production **will** reset it — this is accepted, not accidental, and is the primary reason this needed an RFC rather than proceeding as an ordinary ticket. See Decision below.
- **Direction B reversal.** V1's "no carousel, no full-height hero" stance is being revisited for the homepage hero (P1, not P0) — flagged explicitly so it isn't read later as scope creep on a "restrained" ticket.
- Rollback plan: same as any Visual Baseline v1 ticket — revert the specific ticket's commit(s); tokens/components are additive/replaceable per ticket, not a single irreversible cutover.

---

## Decision

Decision: **APPROVED**
Reason: Product Owner reviewed the conflict with V1's Direction B and the conversion-baseline discontinuity directly (raised by the implementing session before work began, per this RFC's Evidence section) and chose to proceed as a deliberate, named Visual Baseline v2 rather than scope the work down to bugfixes only.
Conditions: (1) `06_ENGINEERING/VISUAL_BASELINE_V2.md` records the new conversion-baseline inception point at the moment P0's last ticket reaches production, mirroring V1's own methodology. (2) P0 ships as a ticket sequence, each verified (lint/typecheck/tests/build + responsive check) before the next starts — no single giant diff. (3) No product-model change (booking, fake listings, discounts) — unchanged from the design review's own non-goals.
Decision ID: DEC-023
Date: 2026-08-14
