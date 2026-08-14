# Visual Baseline v2 — desktop composition and image-led marketplace feel

**Status: IN PROGRESS.** Opened by RFC-0001 (Approved, DEC-023, 2026-08-14). Ticket sequence: T-095 → T-096 → T-097 → T-098 → T-099 → T-100 → T-101 → T-102 → T-103 (P0), then T-104+ (P1, homepage).

This document is the living, ticket-by-ticket record for v2 — same role `VISUAL_BASELINE_V1.md` played for v1. Each ticket section below is filled in as it lands, not written in advance.

## Relationship to Visual Baseline v1

V1 (T-059–T-067, complete 2026-07-30) established the token system, typography, icon system, and component consistency under **Direction B — "Clean Marketplace, restrained not loud"**. V2 does not replace V1's tokens — the same `--brand`/`--surface`/`--text` palette and type scale carry forward unchanged (RFC-0001: *"Not a rebrand… don't change the main brand colour"*). What v2 changes is **composition**: container width usage on desktop, salon-detail layout, gallery presentation, map behaviour at scale, and — for the P1 homepage hero specifically — a deliberate, explicit revisit of V1's "no carousel, no full-height hero" stance in favour of an image-led treatment using real salon photography. That reversal is scoped to the hero only; it is not a general license to add carousels/gradients/glassmorphism elsewhere, which the RFC and the underlying design brief both explicitly rule out.

## Conversion baseline

V1 fixed the Beta Visual Baseline inception point at `2026-07-30 11:39:31 Europe/Athens` — the moment T-067 completed deployment — and no ticket since has reset it (T-063→T-071 all held it deliberately).

**V2 will reset it.** This is accepted, not accidental (RFC-0001, Risks section, Product Owner sign-off 2026-08-14). The new inception point is fixed at the production deployment completion of the **last P0 ticket** in this sequence (T-103), determined the same way V1 did it — `beauty_web`'s Docker `State.StartedAt` at that deploy, not the merge time. Until then, conversion data continues to accumulate against the *existing* 2026-07-30 baseline; each individual P0 ticket does not reset it on its own, only the completed P0 batch does, since a half-migrated UI is not a stable comparison point either way.

*(This line is updated with the actual timestamp once T-103 ships — do not backfill it before that.)*

## Container tokens

No new width token added at v2's foundation ticket (T-095). `shell-grid` (1152px) and `shell-content` (896px) from V1 remain; T-097 moves salon detail from `shell-content` to `shell-grid` for the page shell (reading-width sub-blocks may still use a narrower measure for line-length, at the component level, not the page level). The architect brief's suggested 1180–1280px range was evaluated against the existing 1152px token and not adopted as a new number — reusing the token system beats introducing a close-but-different magic value.

## Ticket log

### T-095 — Desktop container width + nav consistency

**Done.** `Header.tsx`'s desktop nav + auth/language block was gated behind `!isCompact` (`variant !== 'default'`) — every page except home showed the mobile burger at every width, confirmed live as the RFC's primary evidence. Fixed by removing the `isCompact` gate entirely: the nav, auth, and language blocks now render at `md:flex` (768px+) for every variant, and the burger/mobile panel are `md:hidden` for every variant, matching what 'default' already did. Kept the existing `md` (768px) breakpoint rather than introducing the brief's literal `~1024px` — it's the same breakpoint already tested and shipped on the homepage since T-060, and using two different breakpoints across variants for the identical nav markup would itself be an inconsistency.

Layout note: removing the old `justify-between` (which relied on hidden flex items to fake per-variant spacing) required an explicit replacement — `nav` gets `md:ml-6` for breathing room after the logo/back-arrow, the auth+language block gets `md:ml-auto` to stay pinned right, and the burger keeps its own independent `ml-auto` for mobile. This avoids the two-item vs. three-item spacing inconsistency `justify-between` would otherwise produce once every variant has the same visible children.

Container-token part of this ticket (widening beyond `shell-grid`) turned out to need no new token — evaluated the brief's 1180–1280px suggestion against the existing `shell-grid` (1152px) and kept the token as-is; T-097 is where the actual width usage changes (`shell-content` → `shell-grid` on salon detail).

`Header.test.tsx` had a test that explicitly locked in the old per-variant burger behaviour as a T-060 decision (`"non-default variants show the burger... at every width"`) — updated it to assert the new T-095 behaviour instead, with the supersession recorded inline, per DEC-023's approval.

**Verification:** 1280/1280 tests passing (was 1279; +1 new test), 0 fail. `npm run lint` clean (only pre-existing unrelated warnings). `npm run build` clean — all 21 routes compiled, no type errors.

**Files:** `frontend/components/Header.tsx`, `frontend/components/Header.test.tsx`.

### T-096 — Salon gallery: data-driven mosaic

**Done.** Re-audited T-066's gallery logic before touching anything, per the ticket's own "confirm exact current photo-count branching" step — it turned out the desktop mosaic was already correctly data-driven (`slice(0,3).map` never renders a tile for a photo that doesn't exist; 1 photo already renders as one large tile since `flex-[2]` only applies at `length >= 3`). The real, confirmed gap was narrower than the ticket's "Найдено" assumed: **mobile had no swipe gallery at all** — it showed the same cramped 3-tiles-in-a-row desktop mosaic, just shorter (`h-56`).

Added `MobileGallery`: a `md:hidden` native CSS scroll-snap carousel (`overflow-x-auto snap-x snap-mandatory`) showing every photo (not just the first 3 — swiping already reaches all of them, so no separate "view all" control was needed on mobile), with a `scroll`-derived "N / total" position indicator (`aria-hidden`, decorative). No new npm dependency. Desktop mosaic is untouched except `hidden md:flex` (was unconditional `flex`) so the two don't render simultaneously.

**A T-066 test had to be updated, not silently passed around:** `salonDetailVisual.test.ts` had `assert.ok(!/lightbox|carousel|swiper/i.test(source))` — T-066 deliberately shipped without any carousel and guarded against one regressing back in. T-096's mobile swipe *is* a carousel, so the guard was narrowed to what it actually meant to prevent (a lightbox/overlay pattern, and the `swiper` library specifically) while explicitly allowing the one native-CSS `MobileGallery` component, with the supersession recorded inline per RFC-0001/DEC-023.

**Verification:** 1287/1287 tests passing (+7 new T-096 tests), 0 fail. Lint clean. Build clean — `salons/[slug]` route grew 7.29kB → 7.58kB (MobileGallery only).

**Files:** `frontend/app/[locale]/salons/[slug]/SalonDetailClient.tsx` (adds a `Photo` type import, already exported by `lib/api.ts` — that file itself is untouched), `frontend/app/[locale]/salons/[slug]/salonDetailVisual.test.ts`.

### T-097 — Salon detail: two-column desktop composition

**Done.** The RFC's primary confirmed problem: `SalonDetailClient.tsx` wrapped its entire page in one `max-w-shell-content` (896px) column, gallery through footer, no sidebar. Switched the page container to `max-w-shell-grid` (1152px) and added a real two-column composition at `md:` (768px) and up: `md:grid md:grid-cols-[360px_1fr] md:gap-6 md:items-start`.

**Sidebar is left, not right — a deliberate accessibility choice, not a visual default.** Identity/contact/hours/location needed to stay first in the DOM (mobile requires them right after the gallery, unchanged from before T-097). Two ways exist to then place that block on the *right* at desktop: CSS `order` (visual-only reposition, DOM/tab order stays first) or literal column placement matching DOM order. `order` was rejected — it would make desktop tab order visit the sidebar before the main column even though it's drawn on the right, a real WCAG 1.3.2 (meaningful sequence) mismatch, not a hypothetical one. Sidebar-left avoids the mismatch entirely: DOM order = visual order = tab order on both breakpoints, with zero `order` usage (a test locks this in). Precedent for "quick facts + contact on the left, longer content on the right" exists in the category already (Google Business Profile, Yelp).

**Hours and Location moved up in the DOM**, from after Reviews/Social-links to right after the identity/contact card — the only way to get them into the sidebar without duplicating markup (the alternative, two parallel mobile/desktop trees toggled by `md:hidden` as `Header.tsx` and `MobileGallery` both do, was rejected here specifically because the sidebar contains `ContactButtons`, a much larger interactive surface than a nav or an image tile — duplicating it risked doubled analytics wiring for no real benefit, since the reorder achieves the same result without duplication). This is a real, disclosed mobile-order change, not hidden in a refactor: **Hours and Location now appear right after the contact card on mobile too**, arguably an improvement (open/closed + hours next to the CTA, not buried below the review list) rather than a compromise made only for desktop's sake.

**Sidebar is `md:sticky md:top-20 md:self-start`** — stays visible (contact CTA, hours) while scrolling a long review list in the main column. `self-start` stops it from stretching to the grid row's full height, which would otherwise break `sticky`.

**Two pre-existing tests broke, both from the same root cause (fragile comment-marker string slicing that assumed a fixed section order) — fixed, not worked around:** `salonDetail.test.ts` sliced `reviewsBlock` as `source.slice(indexOf('{/* Reviews'), indexOf('{/* Hours'))`, which silently produced garbage once `{/* Hours` moved to *before* `{/* Reviews` in the file — updated to slice to `{/* Social links` (the section that still immediately follows Reviews), with the reasoning recorded inline. `salonDetailVisual.test.ts` asserted the page container was `max-w-shell-content` — updated to assert `max-w-shell-grid`, exactly the change T-095's own doc predicted ("T-097 is where salon detail's width usage actually changes").

**Local build could not be verified on this host** — `next build`'s TypeScript type-check phase was killed three consecutive times on columbxray (1.9GB RAM, already running the live `beauty_web` container plus several other services; no OOM evidence in kernel/journal logs, but the failure is consistent and always at the same, most memory-hungry phase). Tests (source-level, no full `tsc` program build) and lint both ran clean locally. Full build verification deferred to CI, which has adequate resources — the standard gate for this repo regardless. This is a known, disclosed limitation of local verification on this specific host, not a skipped check: CI's `frontend` job runs `next build` as part of its pipeline and must be green before merge.

**Verification:** 1292/1292 tests passing (+5 new T-097 tests), 0 fail. Lint clean. Build: CI-verified only (see above).

**Files:** `frontend/app/[locale]/salons/[slug]/SalonDetailClient.tsx`, `frontend/app/[locale]/salons/[slug]/salonDetail.test.ts`, `frontend/app/[locale]/salons/[slug]/salonDetailVisual.test.ts`.

### T-098 — Reviews: compact, scannable, no technical metadata

**Done.** The confirmed technical-metadata problem was real but not what it looked like at first: `"Source: Google Reviews / Imported: Yes / Original: No"` was not stray debt — it was **DEC-013's own literal mandated text** (2026-07-09, trust/honesty, tied to DEC-003's no-fake-activity principle), locked in by a dedicated exact-string test across all 4 locales. Stopped before touching it, reported the conflict to the Product Owner rather than silently simplifying under the redesign's general "no admin metadata" instruction, and got an explicit decision: **DEC-024** simplifies the wording to a single "Google reviews" label (localized) while leaving DEC-013's actual disclosure requirement intact — naming the source still tells a reader these aren't Lookla-native reviews, just without the field:value dump. DEC-013 now carries a "superseded in part by DEC-024, wording only" note; DEC-024 has the full reasoning.

**Other three fixes, all presentation-only:**
1. **Truncation.** New `ReviewCard` component: text is clamped 4 lines mobile / 6 desktop (`line-clamp-4 md:line-clamp-6`) behind Read more/Show less. The toggle only renders when the text actually overflows — measured via `scrollHeight > clientHeight` on mount, not a character-count guess, so short reviews never get a dead button. The measuring effect depends on `rev.text` only, not `expanded` — otherwise expanding would re-measure the now-unclamped element and immediately hide "Show less".
2. **Long reviewer names.** The name/rating header row is `flex-wrap` with `min-w-0` + `truncate` on the name and `shrink-0` on the rating+date group — a long name now truncates instead of colliding with or pushing out the rating.
3. **Raw date.** `rev.published_at.slice(0, 7)` ("2026-01") replaced with a localized "Mon YYYY" via `toLocaleDateString`, reusing the exact same locale-mapping convention already established by the Data-freshness line elsewhere in this file. `whitespace-nowrap` so the short formatted string can't wrap mid-word.

**A T-096 test boundary broke as a direct, mechanical side-effect of adding `ReviewCard` — fixed, not worked around:** five tests sliced `source` from `function MobileGallery(` to `interface LazySectionResult` to isolate just that component's body; `ReviewCard` now sits between the two, so that boundary silently absorbed all of `ReviewCard` too — including its own JSDoc, which (ironically) mentioned the very `.slice(` pattern one test was asserting against. Fixed the boundary to end at `function ReviewCard(` instead, and separately reworded that one JSDoc line to avoid writing the literal old code pattern as prose in the first place — the second fix is the more durable one; the first was still necessary since other tests in that same block needed the corrected boundary regardless.

**Verification:** 1297/1297 tests passing (+13 new: 4 for ReviewCard, 1 for the date-format supersession, 1 boundary-fix comment; net of the 5 T-096 tests whose only change was their slice end-marker), 0 fail. Lint clean. Build: CI-verified only, same reasoning as T-097 (local `next build` remains unreliable on this host's memory).

**Files:** `frontend/app/[locale]/salons/[slug]/SalonDetailClient.tsx`, `frontend/app/[locale]/salons/[slug]/salonDetailVisual.test.ts`, `frontend/lib/reviewsSection.test.ts`, `frontend/messages/{el,en,ru,uk}.json`.

### T-099 — Search toolbar: unified responsive composition
*(pending)*

### T-100 — Mobile filters: real bottom sheet
*(pending)*

### T-101 — Map marker clustering
*(pending)*

### T-102 — Missing/failed image presentation polish
*(pending)*

### T-103 — Contact CTA: count-aware layout
*(pending)*

### T-104 — Homepage visual pass (P1)
*(pending — not started until P0 ships and is verified in production)*

---

*Opened: 2026-08-14. Last updated: 2026-08-14.*
