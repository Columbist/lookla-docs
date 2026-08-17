# Visual Baseline v3 — brand identity and homepage discovery

**Status: IN PROGRESS.** Opened by RFC-0002 (Approved, DEC-026, 2026-08-17). Ticket sequence: T-105 → T-106 → T-107 → T-108 (Phase 3A), then Phase 3B (T-109–T-111), then Phase 3C (T-112+).

This document is the living, ticket-by-ticket record for v3 — same role `VISUAL_BASELINE_V2.md` played for v2.

## Relationship to Visual Baseline v2

V2 (T-095–T-104, complete 2026-08-15) fixed desktop composition, gallery, reviews, map clustering, and contact-CTA layout, and gave the homepage hero its first image-led pass. **Every V2 change is kept, none reversed.** V3 is a further layer: a real logo where none existed, a homepage section that actually shows ranked salon listings, map cluster colours matched to the brand palette, and a professionals-page cleanup. Direction B's palette and type scale carry forward unchanged (RFC-0002, same as RFC-0001 before it: not a rebrand of the *system*, only of the *mark*).

## The three confirmations this phase depends on (DEC-026)

1. **Logo** — a real SVG (line-art lotus mark + wordmark) replaces the plain-text wordmark everywhere. Deliberate rebrand, confirmed 2026-08-17.
2. **Top salons ranking** — `rating_google` desc, `rating_count` desc (the same sort `salons.py`'s default listing already uses), floor of ≥4.5★ and ≥20 reviews. No manual curation, no paid placement.
3. **Conversion baseline** — resets again at Phase 3A's production deploy, same methodology as V1/V2.

## Conversion baseline

V2 fixed the baseline at `2026-08-14 23:39:11 Europe/Athens` (P0's deploy). **V3 will reset it again** (DEC-026, accepted, not accidental — under two weeks after the last reset). The new inception point is fixed at Phase 3A's production deployment completion, determined the same way (`beauty_web`'s Docker `State.StartedAt`). Not yet reset — recorded here once Phase 3A ships.

---

## Phase 3A

### T-105 — Logo: SVG lotus mark + wordmark, wired through Header

**✅ Done, PR #170.** New `Logo`/`LogoMark` component — inline SVG, five-petal lotus mark (`currentColor`, radially symmetric at 72°), `Header.tsx`'s bare-text wordmark replaced with `<Logo compact />`. Static deliverables `public/logo-mark.svg` / `public/logo-full.svg` (§29), `app/icon.svg` favicon reusing the same path. Verified via `cairosvg` rasterization at 400/64/32/16px — legible at every size, before commit. Not yet deployed.

### T-106 — Homepage hero: one composition, not text-plus-collage

**✅ Done, PR #171.** `HeroPhotoCollage` (3-photo mosaic) replaced by `HeroVisual`: one large real salon photo (`selectHeroSalons(pool, 1)`, was `3`) with `HeroSalonCard` — a floating info card (thumbnail, name, rating, review count, area, arrow CTA) that overlays the photo's corner on desktop and docks below it on mobile (no room to float on a narrow screen). Same empty-pool fallback discipline as T-104: renders nothing, never a broken slot. Not yet deployed.

### T-107 — Homepage: "Top salons" section

**✅ Done, PR #171.** New `TopSalons` component between Popular services and Explore by area. Ranking is entirely server-side — `GET /api/salons` gained a `min_reviews` param (the other half of DEC-026's floor; `min_rating` alone lets a 5.0-with-one-review listing through) — the component does no client-side sort/filter of its own. Desktop: real 4-column grid. Mobile: native scroll-snap, no carousel library. Renders nothing below the floor — no placeholder section. **Deliberately omits** the favourite-icon the original ticket text called for: re-checked and found `/account/favorites` doesn't exist and the whole account area sits behind the not-yet-launched accounts gate — a toggle there would point at nothing. Not yet deployed.

### T-108 — Popular services: compact row, brand line-icons

*(recorded once implemented)*

---

*Opened: 2026-08-17.*
