# Visual Baseline v3 — brand identity and homepage discovery

**Status: IN PROGRESS.** Opened by RFC-0002 (Approved, DEC-026, 2026-08-17). Ticket sequence: T-105 → T-106 → T-107 → T-108 (Phase 3A), then Phase 3B (T-109–T-111), then Phase 3C (T-112+). Phase 3A is fully implemented and merged to `main` as of 2026-08-17 — **not yet deployed**, pending the screenshot-verification gate below.

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

**✅ Done, PR #172.** Density pass only, no new layout system: `CategoryGrid` keeps the same 10 tiles, same Lucide icons, same `active:` pressed state from T-104. Mobile adaptive 3-then-2 via `min-[360px]:grid-cols-3` (a real Tailwind arbitrary variant, not the undefined bare "extra-small" name — the same mistake T-104's TopSalons work almost repeated, caught before commit). Desktop reaches one row at `lg:grid-cols-10`, matching the existing `.slice(0, 10)` cap. Tiles shrank `p-5`→`p-3`, `min-h-[96px]`→`min-h-[76px]`, icon `28`→`24`, all hand-computed against this project's own spacing tokens rather than guessed. Not yet deployed.

---

## Phase 3A status: fully merged, not yet deployed

T-105/T-106/T-107/T-108 are all on `main` (PRs #170–#172). **Not deployed to production.**

### Outstanding: RFC-0002's own screenshot-verification gate

RFC-0002 (§Phased approach) commits to "a screenshot-based visual verification pass (desktop 1440×900 + mobile 390×844 minimum) before the next phase starts." **This has not happened for Phase 3A.** Every ticket above was verified by source-level tests (lint/typecheck/`next build` via CI, plus the project's usual source-string test convention) and hand-computed CSS math for the responsive column math on T-108 — real verification, but not the visual screenshot pass the RFC itself promises.

**Why it was skipped rather than attempted and faked:** this host (`columbxray`) runs the live site, Postgres for ~6320 salons, and Xray VPN alongside this work, with ~225Mi free RAM and 4.2G disk free at the time T-108 was implemented. Installing a browser engine (Playwright/Chromium, no lighter tool exists on this host) to self-verify would risk the exact class of incident `feedback_disk_preflight` already recorded once (2026-07-13, a build dropping disk to ~400M and touching the live DB) — except with live production traffic and a live database now also on the line, not just a build. The CI `next build` job (a separate, disposable runner) already confirms the build itself is sound; what it can't confirm is that the layout actually *looks* like the reference mockup.

**Before calling Phase 3A done and resetting the conversion baseline (DEC-026 point 3):** deploy via the established off-host build workflow, then run the same live-production verification V1 used post-deploy (`https://lookla.gr`, real breakpoint matrix) — this needs either a tool capable of visual screenshotting from this session, or a session/host with more headroom. Flagging this explicitly rather than deploying and marking the RFC's own gate satisfied when it wasn't checked.

---

*Opened: 2026-08-17.*
