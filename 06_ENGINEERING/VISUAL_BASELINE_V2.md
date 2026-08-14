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
*(pending)*

### T-097 — Salon detail: two-column desktop composition
*(pending)*

### T-098 — Reviews: compact, scannable, no technical metadata
*(pending)*

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
