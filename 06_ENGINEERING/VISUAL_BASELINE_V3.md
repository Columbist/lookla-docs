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

V2 fixed the baseline at `2026-08-14 23:39:11 Europe/Athens` (P0's deploy). **V3 resets it again** (DEC-026, accepted, not accidental — under two weeks after the last reset). New inception point: **`2026-08-17 19:49:57 Europe/Athens`** (`beauty_web`'s Docker `State.StartedAt` at Phase 3A's production deploy, same methodology as V1/V2). Conversion data from before this point belongs to V2's baseline, not V3's.

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

## Phase 3A status: merged and deployed; visual verification still outstanding

T-105/T-106/T-107/T-108 are all on `main` (PRs #170–#172) and **deployed to production** as of 2026-08-17 19:49:57 Europe/Athens (see Conversion baseline above). Deploy used the established off-host build path (`build-artifact.yml` + `build-api-image.yml`, both against the exact merged commit `8083093`), preflight-tagged rollback (`ops/deploy-preflight.sh`, verified intact post-deploy), `docker compose up -d --no-deps api web` (no local build), and the full `ops/smoke.sh` (19/19 passed) plus a direct `min_reviews` API check post-deploy.

### Outstanding: RFC-0002's own screenshot-verification gate

RFC-0002 (§Phased approach) commits to "a screenshot-based visual verification pass (desktop 1440×900 + mobile 390×844 minimum) before the next phase starts." **Still not done** — deployed on the Product Owner's explicit decision to ship first and verify live (matching V1's own precedent of a live post-deploy check), specifically because this host has no browser/screenshot tooling and too little headroom (~225Mi free RAM at the time) to install one safely alongside the live site and database. CI's `next build`, full lint, the source-string test suite, and hand-computed CSS math for T-108's responsive columns all passed — real verification, just not the visual one the RFC promises.

**Still needed:** an actual look at `https://lookla.gr` (desktop + mobile) against the reference mockup, from a tool or session capable of it — this session still can't do that itself. **Phase 3B started anyway, on the Product Owner's explicit decision** — this gate remains open, not silently dropped.

---

## Phase 3B

### T-109 — Search results heading undersized

**✅ Done.** `/search`'s `<h1>` was `text-card-title` (16px) — the same scale a single `SalonCard`'s own name renders at, inside the very list this heading introduces. Now `text-section-title` (22px), matching the homepage's own list-introducing headings.

### T-110 — Map clusters restyled to the brand palette

**✅ Done.** `leaflet.markercluster`'s default green/yellow/orange tiers (RFC-0002's own cited evidence) overridden in `globals.css` with a single-hue `--brand`/`--brand-hover`/`--brand-active` ramp. White cluster-number text, contrast computed via the existing `colorContrast.ts` (T-059's own tool, not a new one): 4.96:1 / 6.54:1 / 8.87:1 — all clear WCAG AA. Plain marker dot and popup (T-059's boundary) untouched.

### T-111 — Professionals page: full Direction B migration + placeholder cleanup

**✅ Done.** This page predated Visual Baseline v1 entirely — untouched by T-060/T-062/T-064/T-065. Full legacy surface (gray/pink/purple palette, gradient hero, 3 emoji, 3 different border-radii) migrated to Direction B. **Real defect found and fixed, not just restyled:** the "specialties" row was 8 `<button>`s with no `onClick` at all — fake interactivity on a page that never has a professionals list to filter (always the empty state) — the same class of defect T-009 fixed for booking buttons. Converted to plain non-interactive badges; all 8 specialties × 4 locales kept. First-ever test coverage for this page (17 tests, `mastersPageVisual.test.ts`).

---

*Opened: 2026-08-17.*
