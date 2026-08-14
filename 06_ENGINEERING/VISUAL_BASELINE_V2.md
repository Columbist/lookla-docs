# Visual Baseline v2 — desktop composition and image-led marketplace feel

**Status: IN PROGRESS.** Opened by RFC-0001 (Approved, DEC-023, 2026-08-14). Ticket sequence: T-095 → T-096 → T-097 → T-098 → T-099 → T-100 → T-101 → T-102 → T-103 (P0), then T-104+ (P1, homepage).

This document is the living, ticket-by-ticket record for v2 — same role `VISUAL_BASELINE_V1.md` played for v1. Each ticket section below is filled in as it lands, not written in advance.

## Relationship to Visual Baseline v1

V1 (T-059–T-067, complete 2026-07-30) established the token system, typography, icon system, and component consistency under **Direction B — "Clean Marketplace, restrained not loud"**. V2 does not replace V1's tokens — the same `--brand`/`--surface`/`--text` palette and type scale carry forward unchanged (RFC-0001: *"Not a rebrand… don't change the main brand colour"*). What v2 changes is **composition**: container width usage on desktop, salon-detail layout, gallery presentation, map behaviour at scale, and — for the P1 homepage hero specifically — a deliberate, explicit revisit of V1's "no carousel, no full-height hero" stance in favour of an image-led treatment using real salon photography. That reversal is scoped to the hero only; it is not a general license to add carousels/gradients/glassmorphism elsewhere, which the RFC and the underlying design brief both explicitly rule out.

## Conversion baseline

V1 fixed the Beta Visual Baseline inception point at `2026-07-30 11:39:31 Europe/Athens` — the moment T-067 completed deployment — and no ticket since has reset it (T-063→T-071 all held it deliberately).

**V2 will reset it.** This is accepted, not accidental (RFC-0001, Risks section, Product Owner sign-off 2026-08-14). The new inception point is fixed at the production deployment completion of the **last P0 ticket** in this sequence (T-103), determined the same way V1 did it — `beauty_web`'s Docker `State.StartedAt` at that deploy, not the merge time. Until then, conversion data continues to accumulate against the *existing* 2026-07-30 baseline; each individual P0 ticket does not reset it on its own, only the completed P0 batch does, since a half-migrated UI is not a stable comparison point either way.

**Reset complete: `2026-08-14 23:39:11 Europe/Athens (EEST)`** — `beauty_web`'s Docker `State.StartedAt` at the deploy that shipped P0 (T-095–T-103) to production, same methodology as V1. Conversion data from this moment onward is the new baseline; everything before it, including the entire 2026-07-30→2026-08-14 window, is now historical/pre-refresh data, same status the pre-2026-07-30 data got when V1 shipped.

Deploy note: production build could not complete locally on columbxray (2GB RAM — `npm ci` inside the Docker build was killed repeatedly, root-caused to genuine memory pressure, not a fluke: disk-cache pruning, `--maxsockets=1`, and a BuildKit npm cache mount were all tried and didn't fully resolve it). Shipped instead by building the identical, fully-verified output (`npm ci` + `npm run build`, same lockfile, no shortcut) on a GitHub Actions runner and assembling the final runtime image locally from that output — a copy-only step with no install/compile, trivial even on this host. One real mistake happened and was caught within ~90 seconds: the first artifact upload silently dropped `.next/standalone/.next` (`actions/upload-artifact`'s own `include-hidden-files: false` default), which crashed the container on start; rolled back immediately, root-caused, fixed, and the corrected build was verified in a throwaway local container *before* touching the production one a second time.

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

**Done — turned out narrower than the ticket assumed, same pattern as T-096.** Re-audited the toolbar (`search/page.tsx`) before writing any layout change, per the ticket's own "confirm current composition" step. It was already what the brief asked for: search + filter trigger + List/Map segmented control share one bordered/background sticky surface; the row is `flex flex-wrap` so the List/Map group drops to its own line at narrow widths instead of overflowing (`ml-auto` still pins it right on whichever row it lands on); the search input already has `min-w-0` — the same fix T-062 applied to the homepage SearchBar, already present here too (likely from T-064's own pass); the filter popover is viewport-capped (`max-w-[calc(100vw-1rem)]`); the page container is already `max-w-shell-grid`, full desktop width.

**The real, confirmed gap:** unlike the homepage SearchBar (T-062, tested and verified at 320px, "0px overflow (down from 13px)"), this toolbar had **zero** overflow-safety regression coverage of its own — nothing would catch a future edit that silently dropped `min-w-0` or `flex-wrap` until it showed up as a pixel bug in production. Added 6 tests locking in the properties that already prevent overflow, closing that specific coverage gap rather than changing markup that didn't need changing.

**Verification:** 1303/1303 tests passing (+6 new), 0 fail. Lint clean. Build: CI-verified only (same reasoning as T-097/T-098).

**Files:** `frontend/app/[locale]/search/searchShellVisual.test.ts` only — no production code changed.

### T-100 — Mobile filters: real bottom sheet

**Done.** First correction before implementation: RFC-0001's evidence cited `components/SearchFilters.tsx` as the buggy file — that file is confirmed **dead code** (T-067 already documented it as unreferenced, "recorded for deletion, not migration," locked in by `lib/visualBaselineConsistency.test.ts`'s dead-code guard). The real, live filter UI is the inline popover in `search/page.tsx` — same underlying bug the RFC described (one `absolute` popover, `role="group"`, no separate mobile branch, no `role="dialog"`, no scroll-lock), just a different file than originally cited. Corrected in this record rather than left silently wrong.

**Implementation:** one shared `filterFields` JSX value (area/category/rating `<select>`s), rendered in two presentational wrappers — the desktop popover (unchanged, `hidden md:block`) and a new mobile bottom sheet (`md:hidden`). State and handlers (`area`/`category`/`minRating`, `selectArea`, `update`) are not duplicated; both wrappers close over the same values, so there is exactly one filter state regardless of presentation — matches the ticket's explicit "don't duplicate filter logic" requirement.

**Mobile sheet:** `role="dialog"` + `aria-modal="true"` + `aria-labelledby`, backdrop-click-to-close, explicit close button, `Escape` (via the existing shared T-057 effect — unmodified), body scroll lock, and a focus trap — the last two **scoped to when the sheet is actually the visible presentation** via `sheet.offsetParent === null` (true exactly when `md:hidden` makes it `display:none`) rather than a duplicated width check in JS, so they can never drift out of sync with the CSS breakpoint that actually decides which presentation shows. The desktop popover deliberately keeps T-057's original behaviour (no trap, no scroll lock — "compact popover pattern is appropriate there," per the brief itself).

**"Show N salons" footer button:** reuses the page's existing, already-live `total` state directly — no staged/preview count, no new fetch. Filters apply immediately on select change today (both before and after this ticket), so the button's only job is to close the sheet; it was never going to need its own "apply" step to duplicate.

**A T-057 test asserted the popover "stays a non-modal disclosure" file-wide** (`!source.includes('role="dialog"')`, no `aria-modal`) — that was correct when there was only one shared popover; T-100 makes it correct only for the *desktop* presentation. Split into two tests: one re-confirms the desktop popover is still non-modal (sliced to just that block), one confirms the mobile sheet is deliberately, scopedly modal — not a silent weakening of the original guarantee.

**Local build could not be verified** (host memory, same as T-097/T-098/T-099) — CI is the gate.

**Verification:** 1312/1312 tests passing (+15 net new across `searchControlsA11y.test.ts`), 0 fail. Lint clean.

**Files:** `frontend/app/[locale]/search/page.tsx`, `frontend/app/[locale]/search/searchControlsA11y.test.ts`, `frontend/messages/{el,en,ru,uk}.json` (`close_filters`, `show_results`).

### T-101 — Map marker clustering

**Done.** `leaflet.markercluster@1.5.3` + `@types/leaflet.markercluster` — evaluated against the ticket's "actively-maintained" preference honestly: last published 2022, but authored by Volodymyr Agafonkin (`mourner`), Leaflet's own creator, MIT, zero relevant CVEs in `npm audit` (the 8 pre-existing high-severity findings are all unrelated tooling — Next.js/eslint/postcss), peer-compatible with the project's `leaflet@^1.9.4`, and still the de facto standard the Leaflet ecosystem itself points to. Staleness here reads as feature-complete, not abandoned — proceeded, documented rather than silently picked.

**Integration:** `layerGroupRef.current = L.layerGroup()` → `L.markerClusterGroup({ showCoverageOnHover: false })` — the only line that changes to get clustering, since `MarkerClusterGroup` is API-compatible with `LayerGroup` for everything this file already does (`clearLayers()`/`addTo()`). `showCoverageOnHover` is the one option overridden (unnecessary visual noise); `zoomToBoundsOnClick`/`spiderfyOnMaxZoom`/`maxClusterRadius` stay at the plugin's own defaults. `refreshMarkers` switched from adding each marker one at a time (`.addTo(layerGroupRef.current)` inside the loop) to a single bulk `addLayers(markers)` call — the plugin's own documented recommendation for large sets, relevant here at ~2000 salons.

**The plugin itself needed a documented workaround, not a silent one:** `leaflet.markercluster` is an older UMD-only package (no ESM build) that expects a global `L` — the classic `<script>`-load-order pattern. `(window as any).L = L;` is set before `await import('leaflet.markercluster')`, the standard fix for using this plugin with a bundler's dynamic import.

**Types needed the same treatment.** This project's `tsconfig.json` sets `"types": []`, disabling automatic `@types/*` inclusion. That restriction only blocks *implicit* global inclusion — explicit, import-driven resolution still works — so a type-only `import type {} from 'leaflet.markercluster';` was added specifically to force `@types/leaflet.markercluster`'s `declare module "leaflet"` augmentation into the program (a side-effect-only dynamic `import()` deeper in the file wasn't a reliable way to guarantee that on its own). Local `next build`/`tsc --noEmit` both remain unrunnable on this host (memory) — **this ticket in particular needed CI's TypeScript check as the real verification**, more than any other in this sequence, given the type-augmentation risk was reasoned through but not locally provable.

**The one real correctness risk, found and fixed:** the pre-existing T-063 roving-tabindex system (`applyKeyboardSet`) computed its keyboard-navigable marker set from *every* marker's lat/lng, regardless of whether that marker currently has a DOM element. With clustering, a marker absorbed into a cluster bubble has no DOM element (`marker.getElement()` returns `undefined`) until the cluster expands. Unfixed, `selectKeyboardSet` could pick a currently-clustered marker as the "active" one, and the tabindex-assignment loop's own `if (!el) continue` would silently skip it — leaving **zero** markers with `tabindex="0"`, at exactly the low-zoom levels where clustering matters most. Fixed by filtering the point list to markers with a live DOM element *before* `selectKeyboardSet` runs, so it degrades correctly to "no individual markers visible right now" instead of pointing at nothing.

**Explicitly not attempted:** the cluster bubbles themselves are not yet keyboard-focusable (Tab-reachable, with an accessible name) — a new UI surface, not a regression of the existing system, and the ticket's own text allows deferring this to T-063 proper ("that's still T-063's proper scope if it needs deeper work"). Mouse/touch cluster interaction (click-to-zoom, spiderfy) works via the plugin's own defaults, no code needed.

**Two pre-existing tests explicitly forbade the string `markercluster`/`MarkerCluster`** in `MapView.tsx` — `lib/mapKeyboardNav.test.ts` (T-063) and `lib/visualBaselineConsistency.test.ts` (T-067) — both written when clustering was legitimately future/out-of-scope (`VISUAL_BASELINE_V1.md` itself calls T-063 "a reserved, untouched placeholder"). Narrowed both to keep guarding against real regressions (`fetch(`, `useSWR`, `axios` — no new data-fetching) while removing the now-obsolete clustering prohibition, with the reasoning recorded inline.

**Verification:** 1322/1322 tests passing (+10 new in a new `components/MapView.test.ts`, net of 2 pre-existing tests narrowed), 0 fail. Lint clean. Build: CI-verified only — see above for why this ticket needed it more than most.

**Files:** `frontend/components/MapView.tsx`, `frontend/components/MapView.test.ts` (new), `frontend/lib/mapKeyboardNav.test.ts`, `frontend/lib/visualBaselineConsistency.test.ts`, `frontend/app/globals.css`, `frontend/package.json` (+`leaflet.markercluster`, +`@types/leaflet.markercluster`).

### T-102 — Missing/failed image presentation polish

**Done — small, one real gap found.** Audited every `<img>` in the app first: `SalonCard.tsx` (T-065) and `SalonDetailClient.tsx`'s `GalleryImage` (T-066/T-096) already have the honest `imageFailed`-state + fallback contract. The map popup's thumbnail (`MapView.tsx`) did not — no `onError` handler at all, so a present-but-broken `primary_photo` URL fell through to the browser's own broken-image icon, exactly what the brief calls out.

**Fixed:** `selectedImageFailed` state, reset via a `useEffect` keyed to `selected?.id` (not paired manually into each of the several `setSelected()` call sites — correct regardless of how selection changes, now or later). On failure, swaps to the same `Building2`/`bg-surface-subtle`/decorative fallback tokens `PhotoFallback` already established elsewhere — one honest fallback contract, not a second one invented for this component — sized to 16px instead of `PhotoFallback`'s 28px, since a 28px icon in a 64px popup thumbnail would dominate it (SalonCard's icon sits in a much larger photo area, where 28px reads as small).

**Explicitly unchanged:** a salon with no `primary_photo` at all still renders no image slot in the popup (unchanged) — this ticket only fixes the failed-*after*-a-URL-existed case, not the already-correct no-URL case.

**Verification:** 1327/1327 tests passing (+5 new), 0 fail. Lint clean. Build: CI-verified only.

**Files:** `frontend/components/MapView.tsx`, `frontend/components/MapView.test.ts`.

### T-103 — Contact CTA: count-aware layout

**Done — last P0 ticket.** Confirmed the exact bug: `ContactButtons.tsx`'s container was an unconditional `grid grid-cols-2 gap-2` regardless of how many of the 4 possible actions (Call/WhatsApp/Viber/Website, DEC-021) actually render. At 3 actions: row 1 fills two cells, row 2 has one button and one empty cell. At 1 action: a half-width button next to an empty cell. 2 and 4 actions were already correct (`grid-cols-2` fills exactly).

**One rule covers both gaps:** the container stays a constant `grid-cols-2`; only the *last* active action's own grid item gets `col-span-2`, and only when the active count is odd (1 or 3) — `activeCount % 2 === 1`. `activeKeys` is derived once, filtering the fixed `phone`/`whatsapp`/`viber`/`website` order down to whichever are actually present; `spanFull(key)` is just `key === lastActiveKey && activeCount % 2 === 1`. Website's span lives on its wrapping `<div>` (which also carries the optional warning line), not its inner `<a>` — spanning has to include the warning text, not just the button.

**Shared, not duplicated:** `ContactButtons` is one component, called exactly once from `SalonDetailClient.tsx` (in the T-097 sidebar, which mobile and desktop both render — no separate mobile/desktop CTA logic exists to keep in sync).

**One pre-existing test needed updating, not working around:** a T-066 test counted literal `className={BUTTON_CLASS}` occurrences (expected 4, enforcing "every channel uses the same class, no per-channel importance"). Three of four actions now build their className via a template literal (`` `${BUTTON_CLASS}${spanFull ? ' col-span-2' : ''}` ``) to add the span conditionally — the *invariant* still holds (every action still references the same `BUTTON_CLASS`, `col-span-2` is a layout addition not a new class), only the exact-literal detection method was outdated. Rewritten to count occurrences of the `BUTTON_CLASS` identifier itself (any syntactic form) instead.

**Verification:** 1335/1335 tests passing (+8 new in a new `ContactButtons.test.ts`, simulating the count/order logic against fixtures for 1/2/3/4-action cases, not just checking that `col-span-2` appears somewhere), 0 fail. Lint clean. Build: CI-verified only.

**Files:** `frontend/components/ContactButtons.tsx`, `frontend/components/ContactButtons.test.ts` (new), `frontend/app/[locale]/salons/[slug]/salonDetailVisual.test.ts`.

---

**P0 complete.** T-095 through T-103, nine tickets, all merged to `main`, all CI-green. P1 (T-104, homepage) does not start until P0 is verified in production, per RFC-0001/`VISUAL_BASELINE_V2.md`'s own conditions.

### T-104 — Homepage visual pass (P1)
*(pending — not started until P0 ships and is verified in production)*

---

*Opened: 2026-08-14. Last updated: 2026-08-14.*
