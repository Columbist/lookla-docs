# Visual Baseline v1 — foundation specification

**Status: COMPLETE.** All seven tickets landed and verified in production — T-059 (tokens, typography, icon system), T-060 (global shell), T-062 (homepage), T-064 (search shell), T-065 (SalonCard), T-066 (salon detail), T-067 (consistency pass: cookie consent, legal pages, MapView overlay, 404, CI test-coverage fix).

**Official Beta Visual Baseline began: `2026-07-30 11:39:31 Europe/Athens (EEST)`** — T-067's production deployment completion, per Docker's `beauty_web` `State.StartedAt`; not the merge time. Conversion data from that moment onward is the primary post-refresh baseline. Anything earlier is instrumentation and preliminary observation only. Full evidence in the T-067 section below.

**Approved direction:** Direction B — Clean Marketplace, as recommended in the Visual Baseline Audit (2026-07-27) and confirmed by the user without reinterpretation.

## Source of truth

This document — not the audit artifact — is the living spec from this point forward. The audit's draft token proposal was the starting reference; every value below is either copied verbatim from that proposal or explicitly marked as extended/adjusted, with the reason stated inline.

## Token table

| Token | Value | Source | Role |
|---|---|---|---|
| `--bg` | `#FAF8F6` | Audit, verbatim | Page background |
| `--surface` | `#FFFFFF` | Audit, verbatim | Elevated surface / cards |
| `--surface-subtle` | `#F1ECE7` | New — audit didn't define a 3rd surface step | Subtle section backgrounds between bg and surface |
| `--surface-elevated` | `#FFFFFF` | New (= surface) | Elevation communicated via `--shadow-elevated`, not colour |
| `--text` | `#1E1A19` | Audit, verbatim | Primary text |
| `--text-secondary` | `#6B625C` | Audit, verbatim | Secondary text |
| `--text-muted` | `#7C7069` | **Adjusted** — audit's draft `#9C938C` was 3.01:1 on white (fails AA); darkened to 4.80:1 | Muted / caption text |
| `--text-inverse` | `#FFFFFF` | New — needed for text on `--brand` fills | Text on brand-filled buttons |
| `--brand` | `#A62E5C` | Audit's `--action`, renamed to the ticket's requested category | Primary brand/action colour |
| `--brand-hover` | `#8A2549` | Audit's `--action-hover`, verbatim | Primary hover |
| `--brand-active` | `#711D3C` | New — pressed-state step, same hue family | Primary active/pressed |
| `--brand-soft` | `#F3E4EA` | New | Light tint for selected/active backgrounds |
| `--accent` | `#C9A24B` | Audit, verbatim | Sparingly used second accent — **decorative-only**, see contrast note below |
| `--accent-strong` | `#8A6A2C` | New — darkened, text/icon-safe variant of `--accent` | Verified-badge text, any content-bearing gold use |
| `--accent-soft` | `#F7EFDC` | New | Light tint for accent chip backgrounds |
| `--border` | `#E7E1DB` | Audit, verbatim | Card / input borders |
| `--border-strong` | `#D3C9C0` | New | Stronger separators / hover borders |
| `--focus` | `#B84B7C` | **Adjusted** — audit's draft `#D98CAE` was 2.53:1/2.38:1 (fails the 3:1 non-text requirement); darkened to 4.84:1/4.57:1 | Focus ring |
| `--success` | `#3E7A52` | Audit, verbatim | Open-status colour (large fills) |
| `--success-text` | `#2F6140` | New — darkened for AA text-on-`success-soft` | Open-status pill text |
| `--success-soft` | `#E7F0E9` | New | Open-status pill background |
| `--warning` | `#B0742A` | Audit, verbatim ("reserved, not currently needed") | Reserved |
| `--warning-soft` | `#F5E9D8` | New | Reserved |
| `--danger` | `#A83232` | New — the audit deliberately did not define an error red | Error text |
| `--danger-soft` | `#F5E1DF` | New | Error background |
| `--closed` | `#57504B` | Audit, verbatim ("closed isn't an error") | Closed-status colour |
| `--closed-soft` | `#EDE9E5` | New | Closed-status pill background |
| `--radius-sm` | `6px` | Audit, verbatim | Inputs, badges |
| `--radius-md` | `10px` | Audit, verbatim | Cards, buttons |
| `--radius-pill` | `999px` | Audit, verbatim | Status pills, chips |
| `--shadow-resting` | `0 1px 2px rgba(30,26,25,.05), 0 2px 8px rgba(30,26,25,.04)` | Audit, verbatim | Card resting elevation |
| `--shadow-elevated` | `0 4px 16px rgba(30,26,25,.10)` | Audit, verbatim | Popovers/menus only |

Implemented as CSS custom properties in `frontend/app/globals.css`, aliased into `frontend/tailwind.config.ts`'s `theme.extend.colors/borderRadius/boxShadow` — a single source of truth, no value duplicated independently in CSS vs. Tailwind vs. TypeScript (per the ticket's explicit anti-pattern warning). No TypeScript token constants exist; nothing today needs runtime JS access to a token value.

## Token architecture decision

**Layering:** semantic CSS custom properties (`:root` in `globals.css`) → Tailwind theme aliases (`tailwind.config.ts`) → component classes consume the Tailwind aliases (`bg-brand`, `text-text-secondary`, etc.), never the raw CSS var or a literal hex. Explicitly rejected: a theme-switching framework, runtime theme provider, or dark mode (single theme, matching the ticket's "premature dark mode" prohibition and the audit's own scope).

## Contrast validation

All required pairs meet WCAG AA (4.5:1 normal text, 3:1 non-text/focus). Full computed table lives in `frontend/lib/visualBaselineTokens.test.ts`, which extracts the hex values live from `globals.css` (never a second hardcoded copy) and asserts each ratio via `frontend/lib/colorContrast.ts` — a real, reusable WCAG contrast function, not just a report table. If a future edit weakens any token's contrast, this test fails.

One deliberate exception: `--accent` (`#C9A24B`) alone is 2.40:1 on white and is documented as **decorative-only** — no token or component may use it for text or a meaningful icon; `--accent-strong` (5.03:1) is the variant for anything read as content. `frontend/lib/visualBaselineTokens.test.ts` asserts this constraint explicitly.

## Typography and font-loading contract

- **Family:** Inter, self-hosted via `next/font/google` in `frontend/app/[locale]/layout.tsx` — no runtime request to fonts.googleapis.com.
- **Subsets loaded:** `latin`, `latin-ext`, `greek`, `cyrillic`. Verified two ways: (1) Google Fonts' own metadata confirms Inter has full `greek`/`greek-ext`/`cyrillic`/`cyrillic-ext` coverage; (2) every actual non-ASCII character present across all four `messages/*.json` files was checked codepoint-by-codepoint against Inter's coverage ranges — the only 9 characters not covered are arrows/emoji/symbols (←→⏳☰⚠✅✓💡🗺), none of them Greek, Latin, or Cyrillic letters, and all of them candidates for the icon-system migration this ticket already starts. `greek-ext`/`cyrillic-ext`/`vietnamese` subsets are intentionally excluded — nothing in the product's real content needs them, and including them would download unused glyph ranges.
- **Weights loaded:** 400, 500, 600, 700 — exactly the four the type scale uses, requested as static weight files (not the full variable axis).
- **`display: 'swap'`** — avoids invisible-text layout shift.
- **Fallback:** the pre-existing `ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", ...` stack remains in `globals.css`'s `body` rule after `var(--font-inter)`, so a blocked font request still renders legible text immediately.
- **Applied globally** (`html`/`body`) — the one genuinely visible, uniform, sitewide change this ticket makes, confirmed via computed-style check on real production pages (homepage, search) post-build, not just the preview route.

### Typography scale

| Class | Size | Weight | Line-height | Role |
|---|---|---|---|---|
| `.text-display` | 36px | 700 | 1.2 | Largest display text |
| `.text-page-title` | 28px | 700 | 1.2 | Page-level heading |
| `.text-section-title` | 22px | 600 | 1.2 | Section heading |
| `.text-card-title` | 16px | 600 | 1.4 | Card/component title |
| `.text-body` | 16px | 400 | 1.4 | Body copy |
| `.text-body-sm` | 14px | 400 | 1.4 | Secondary body copy |
| `.text-label` | 13px | 500 | 1.4 | Form/UI labels |
| `.text-button` | 14px | 500 | 1.4 | Button labels |
| `.text-meta` / `.text-caption` | 12px | 400 | 1.4 | Metadata, captions |

Plain utility classes, not element selectors — no `<h1>`/`<h2>` global restyle, so document heading semantics are untouched wherever these classes are eventually applied.

## Shape and depth

Two radii + one pill (`--radius-sm` 6px, `--radius-md` 10px, `--radius-pill` 999px) and two shadow levels (`--shadow-resting`, `--shadow-elevated`) — matching Step 7's explicit cap. No component in production consumes these yet outside the internal preview route.

## Spacing guidance (documented, not enforced by new utilities)

Tailwind's existing 4px-based scale is kept as-is — no new spacing scale, no new container utilities added under T-059 (that's page-level work). Recommended standard values for later tickets to converge on: card padding 16px, section padding 24px (mobile) / 32px (desktop), a "content" container (~720px, salon detail/legal pages) and a "grid" container (~1200px, search/homepage) replacing today's three-way `max-w-3xl`/`4xl`/`6xl` split.

## Icon system

**Library:** `lucide-react` (^1.27.0). Zero runtime dependencies (only a `react` peer dependency), MIT-licensed, tree-shakeable (each icon is its own ES export), actively maintained, no runtime network calls. No existing icon dependency was already installed, so this is a new addition — justified because the product previously had three unrelated icon "families" simultaneously (platform emoji, two hand-authored inline SVGs, Unicode text symbols) and zero shared contract, per the audit's §10 finding.

**Contract (`frontend/components/ui/Icon.tsx`):**
- Sizes: 16 / 20 / 24px only.
- Stroke width: fixed at 1.75, not caller-configurable.
- `decorative` prop defaults to `true` → renders `aria-hidden="true"`; never invents an `aria-label` or relies on `title`.
- Not focusable (`focusable="false"`).
- Accessible names stay owned entirely by the surrounding control (button `aria-label`, real `<label>`, visible text) — matching every existing icon-adjacent control in the codebase, none of which was found to depend on an icon's own markup for its accessible name.

### Icon migration performed under T-059

| Current icon source | Location | Replacement | Status |
|---|---|---|---|
| Hand-authored inline `<svg>` (hamburger/close paths) | `components/Header.tsx` mobile menu toggle | `lucide-react`'s `Menu`/`X` via `Icon` | **Migrated** — same size (24px→24px), same colour (`text-gray-700`, unchanged), same accessible name (`aria-label="Menu"`, unchanged). Glyph-source swap only, no visual/behavioural change. |

### Icon migration deferred to later tickets

| Current icon source | Location | Replacement candidate | Future ticket |
|---|---|---|---|
| `🔍` in the search submit button | `app/[locale]/search/page.tsx` | `lucide-react`'s `Search` | Search shell visual refresh |
| Inline SVG funnel path, filter trigger | `app/[locale]/search/page.tsx` | `lucide-react`'s `SlidersHorizontal` | Search shell visual refresh |
| `☰`/`🗺` baked directly into the `search.list`/`search.map` **translated strings** (`messages/*.json`) | `app/[locale]/search/page.tsx` | Separate the emoji out of the localized string into a real `Icon`; requires a content edit across all 4 locale files | Search shell visual refresh — **not attempted under T-059** because it requires editing page-specific JSX and translated content, which the ticket's non-goals explicitly exclude ("do not begin page-level redesigns") |
| 10 category emoji (💇💅✨🪒👁️💄💆✂️🎨🧖) | `components/CategoryGrid.tsx` | `lucide-react` equivalents, or a lightweight custom icon per category | Homepage visual refresh — explicitly excluded by the ticket's non-goals ("do not replace all emoji categories") |
| `📞💬🌐` contact-channel icons | `components/ContactButtons.tsx` | `Phone`/`MessageCircle`/`Globe` | Salon detail visual refresh |
| `📷👥💬📲🎵▶️` social-platform icons | `app/[locale]/salons/[slug]/SalonDetailClient.tsx` | Brand-appropriate icon set | Salon detail visual refresh |
| `💈` image-fallback glyph (5+ locations) | `SalonCard.tsx`, `SalonDetailClient.tsx` | A designed placeholder tile (not an icon swap — a real fallback-image redesign) | SalonCard / Salon detail visual refresh |
| `📍⚠️🌐` misc (map pin, report, translated-badge) | Various | `MapPin`/`TriangleAlert`/`Globe` | Their respective page tickets |
| `←` back arrow | `SalonDetailClient.tsx` header | `ArrowLeft` | Salon detail visual refresh |
| `★ ✩ ☆` rating stars (3 inconsistent renderings — see audit §2) | `SalonCard.tsx`, `SalonDetailClient.tsx` (×2 sites) | A single shared `RatingStars` primitive, `Star`/`StarHalf` icons | SalonCard / Salon detail visual refresh (also fixes the inconsistency, not just the icon source) |
| `♂ ♀` gender-audience symbols | `SalonCard.tsx` | Kept as Unicode text symbols or dropped — not an icon-system concern | SalonCard visual refresh (product decision, not purely visual) |

**Leaflet markers are explicitly untouched** — no marker icon, popup, or map-shell change of any kind under T-059, matching the non-goal and the audit's own separate map-accessibility candidate.

## Interaction states

- **Hover/active:** defined per-component (Button's `hover:bg-brand-hover`/`active:bg-brand-active`); not swept sitewide.
- **Focus-visible:** `.focus-ring-token:focus-visible` in `globals.css` (2px solid `var(--focus)`, 2px offset) — defined and available via the `focus-ring-token` class, consumed today only by `Button`. Existing `focus:ring-pink-200` usages sitewide are **untouched** — swept only as each surface's own visual ticket lands (see migration map below), so nothing regresses today.
- **Disabled:** `disabled:opacity-50 disabled:pointer-events-none` on `Button` — stays legible (50% opacity, not hidden), non-interactive.
- **Reduced motion:** no entrance/large animations were added anywhere in this ticket (verified — the preview route has zero `animation-duration` > 1s on any element); the one `transition-colors` on `Button` is a short, non-intrusive hover/active transition consistent with `prefers-reduced-motion` best practice (colour transitions are conventionally exempted from reduced-motion concerns, unlike transform/opacity entrance animations).

## Shared primitive strategy

| Primitive | Decision |
|---|---|
| `Button` (primary/secondary) | **New**, minimal — created under T-059, consumed only by the internal preview route today |
| `Icon` | **New**, minimal — created under T-059, consumed by the preview route + Header's menu toggle |
| Input, Select | Not created under T-059 — no real page needs one yet; deferred to Search shell ticket |
| Chip | Already exists (`ActiveFilterChips.tsx`, T-054) — reusable as-is, not touched |
| Badge | Not created — status-pill pattern demonstrated on the preview route only; a real `Badge` primitive is deferred to whichever page-level ticket first needs to consolidate the 3 existing independent pill treatments (open/closed, verified, translated) |
| Card / Section container | Not created — deferred to Salon detail visual refresh, which is where the 7-duplicated-box finding actually needs solving |
| Container/max-width | Not created — deferred, see Spacing guidance above |

Deliberately not generalized further — no abstract component library, no premature primitives for content shapes (services/reviews/hours) that differ enough to resist a single rigid component, per the ticket's own explicit caution.

## Controlled proving surface

**Route:** `frontend/app/[locale]/design-system-preview/page.tsx` — server component, `robots: { index: false, follow: false }`, not linked from any navigation, not referenced by any other page or component. Renders every token, all 10 typography roles, both Button variants (+ disabled + a simulated focus-visible state), the Icon system at all 3 sizes, all 4 status-pill colours, and the shape/depth examples — using real localized strings pulled from the `home`/`search` next-intl namespaces (never lorem ipsum), so contrast and glyph rendering can be verified against actual product content in all 4 locales.

**Why a dedicated route instead of applying primitives directly to a real page:** the new `--brand` (`#A62E5C`) is deliberately different from the current `pink-600` (`#DB2777`) still present everywhere else in production. Any real page mixing both — e.g. a new-style `Button` sitting next to the still-pink-600 logo in `Header` — would be exactly the "visibly broken hybrid" the ticket warns against. The ticket's own Step 13 explicitly provides this fallback for exactly this situation; it was used deliberately, not as a shortcut.

**Real-page changes made instead:** only the two genuinely safe, uniform, non-patchwork changes — global font-family (visible everywhere at once, never inconsistent with itself) and the Header menu-icon glyph swap (no colour/token change, same size, same colour class, purely a cleaner glyph source).

## Migration ownership map — who converts each remaining surface

| Surface | Owner ticket | Notes |
|---|---|---|
| Header (full: logo colour, nav links, desktop CTA colours) | ~~Header/footer global-shell ticket~~ — **done, T-060** | — |
| Footer | ~~Header/footer global-shell ticket~~ — **done, T-060** | — |
| Homepage (hero, category/area tiles, "how it works") | ~~Homepage visual refresh~~ — **done, T-062** | Included the "Book" step copy fix and the SearchBar 320px overflow fix (see below) |
| Search shell (toolbar, filter popover, results heading, List/Map, active-filter chips) | ~~Search shell visual refresh~~ — **done, T-064** | Included fixing the hardcoded Greek `Όλες οι αξιολογήσεις` rating-filter placeholder |
| SalonCard | ~~SalonCard visual refresh~~ — **done, T-065** | First ticket in the sequence allowed to touch the card's internal appearance, not just surrounding chrome |
| Salon detail (7-box consolidation, CTA hierarchy, gallery) | ~~Salon detail visual refresh~~ — **done, T-066** | Fixed the hardcoded Greek `+N φωτογραφίες` overlay; also found and fixed a real gallery-layout bug (see T-066 below) |
| Cookie consent UI, legal pages, remaining AsyncSection states | ~~Shared async/legal/cookie alignment + final consistency pass~~ — **done, T-067** | `AsyncSection` needed no work (already tokenised). Also fixed two more hardcoded-Greek strings in `MapView`, the 320px legal-page overflow, and a CI gap where 7 test files never ran |
| Auth / dashboard / admin / account pages | **Not in Visual Baseline v1** — separate future phase | ~394 legacy colour utilities across 12 files; deliberately out of scope (see T-067) |

## T-060 — Global shell (header, footer, mobile navigation, language selector)

**Scope (revised after a REQUEST CHANGES round on PR #57):** the first T-060 pass only refreshed `Header.tsx`/`Footer.tsx`/`LanguageSwitcher.tsx` as used by the homepage, leaving search/salon-detail/legal pages on their own independent inline headers. The reviewer correctly rejected this as not actually satisfying "global shell" and required one of two remediations; **Option 1 (unify) was accepted**. This section documents the corrected, unified implementation. No homepage/search/SalonCard/salon-detail *content* (i.e. anything below the chrome) was touched — this remains a shell-only ticket.

### The fix: one shared `Header` contract, four variants

`components/Header.tsx` now takes a `variant?: 'default' | 'search' | 'detail' | 'legal'` prop (the exact names the reviewer suggested) plus optional `backHref` and `children`. All four variants share: the logo, `LanguageSwitcher`, the mobile burger + panel (identical markup, not four look-alikes), Direction B tokens, and touch-target rules. What differs is only what's shown *inline on desktop*:

| Variant | Used by | Desktop chrome | `backHref` |
|---|---|---|---|
| `default` | Homepage, `/masters` (bonus fix — see below) | Full nav (Salons/Professionals) + Login/Register + language switcher, burger only below `md` | — |
| `search` | `/search` | Logo + burger at every width; the search toolbar (T-057, untouched) renders as `children`, positioned as a sibling *after* `</header>` | — |
| `detail` | `/salons/[slug]` | Back arrow (→ `/search`) + logo + burger at every width | `${prefix}/search` |
| `legal` | `/privacy`, `/cookies` | Back arrow (→ home) + logo + burger at every width | `prefix \|\| '/'` |

`role="banner"` is now set **explicitly** on Header's own `<header>` element, rather than relied on implicitly — every variant can end up nested inside the page's own `<main>` (see below), which per HTML-AAM would otherwise silently suppress `<header>`'s implicit banner role. This is the direct fix for the reviewer's second blocking issue.

The `search` variant additionally suppresses Header's own `sticky top-0` (only `default`/`detail`/`legal` keep it) — the search toolbar rendered as its `children` already has its own pre-existing, T-057-protected `sticky top-0` behaviour; stacking two independently-sticky bars at the same `top: 0` would fight each other. Scrolling the search page now lets the slim brand bar scroll away while the toolbar (search input/filters/List-Map) sticks, which is normal, common sticky-bar-below-a-non-sticky-brand-bar behaviour, not a hack.

**Page-side diff is minimal and additive-only** for the three previously-independent inline headers: each page's own former `<header>...</header>` block is replaced with a single `<Header locale={locale} variant="..." ... />` call; nothing below it (search results, salon detail content, legal page copy) changed. `search/page.tsx` additionally lost its one inline `Lookla` logo `Link` (now owned by `Header`) and the now-unused `prefix` variable.

**Bonus, zero-new-code fix:** inventory also turned up a *fourth* independent inline header on `/masters` (`app/[locale]/masters/page.tsx`) — byte-similar to the homepage's pre-T-060 header, still on the old `pink-600`/`gray-*` palette. Since it needed nothing beyond `<Header locale={locale} variant="default" />` (the exact same variant the homepage already uses), it was folded in at no extra risk: leaving it on legacy styling while calling this ticket a "global shell" would have been the same inconsistency the reviewer flagged, just one page further out. `/login` and `/register` were inventoried too and currently have **no** page-specific header markup at all — left untouched, out of scope (not in the reviewer's named "at minimum" list).

### `<main>` landmark: one per page, owned by the page, not the layout

The reviewer's second blocking issue required a real `<main>` (or `role="main"` fallback), exactly one per page, with Header/Footer outside it. The layout-level wrapper (`[locale]/layout.tsx`'s `<div className="flex-1">{children}</div>`) stays a **plain `<div>`** — a layout-level `<main>` would either nest a second `<main>` inside pages that now own one, or need to exclude `Header` per-route, which a single shared layout can't do without deeper route-group restructuring. Instead, each of the 6 unified-shell pages (homepage, search, salon detail, privacy, cookies, masters) now wraps its **own** real content in its **own** `<main id="main-content">`, rendered as a true sibling immediately after its own `<Header ... />` call — verified by a new automated test (`globalShell.test.ts`) that every one of these 6 files renders `<Header` before `<main`, exactly one `<main id="main-content">`, and no nested `<main>`. Pages this ticket doesn't touch (dashboard/account/admin/login/register/pricing/etc.) still have no `<main>` landmark — an explicit, documented gap for their own future tickets, not a regression introduced here.

### Navigation route matrix (before = after — no route changed)

| Destination | Path | Locale-prefixed | Notes |
|---|---|---|---|
| Home | `/` (`el`), `/en`, `/ru`, `/uk` | Yes (as-needed) | Logo/home link, unchanged |
| Search | `/search` | Yes | Nav item, unchanged |
| Professionals | `/masters` | Yes | Nav item, unchanged |
| Login | `/login` | Yes | Unchanged |
| Register | `/register` | Yes | Unchanged |
| Privacy | `/privacy` | Yes | Footer + legal back-arrow, unchanged |
| Cookie Policy | `/cookies` | Yes | Footer + legal back-arrow, unchanged |
| Cookie settings | (in-page event, no route) | — | Footer button, unchanged |

Zero routes added, removed, or renamed. Greek `defaultLocale`/`localePrefix: 'as-needed'` behaviour is untouched (no change to `i18n/routing.ts`).

### Global container contract (Step 3)

Three named `maxWidth` aliases added to `tailwind.config.ts` — `shell-grid` (72rem/1152px, matches today's `max-w-6xl`: homepage sections, search grid), `shell-content` (56rem/896px, matches `max-w-4xl`: salon detail, footer link row), `shell-reading` (48rem/768px, matches `max-w-3xl`: legal pages). **Purely additive infrastructure** — no existing page was switched to consume these under T-060, matching T-059's own "tokens available, not yet consumed" precedent. Verified via production measurement that these three values are the actual widths already in use (1152px/896px/768px at a 1440px viewport).

### Desktop header visual contract

- Surface: `bg-surface` / `border-border` (was `bg-white`/`border-gray-100`).
- Brand: `text-brand` (was `text-pink-600`).
- Nav links: `text-text-secondary`, hover `text-brand`; each link's clickable box is the full header height (`h-full` inside a `h-14` header, ≈57px) via `inline-flex items-center`, not just its text line — clears 44px without any visible size change to the label.
- Auth buttons (Login/Register): `min-h-[44px]`, token colours, unchanged destinations/labels.
- Focus: every interactive element carries the shared `.focus-ring-token` class from T-059.

### Active navigation state (Step 5)

New `lib/activeRoute.ts` (`isActiveRoute(pathname, target)`): exact match or `target/`-prefixed nested match, using next-intl's own `usePathname()` (already locale- and query-stripped, so this needs no locale/query handling itself). Applied to both nav items (`/search`, `/masters`) with `aria-current="page"` **plus** a non-colour cue — a `border-b-2 border-brand` underline on desktop, a `bg-brand-soft` background on the mobile panel — satisfying "not colour-only." The logo/home link is never marked current. A salon-detail page (`/salons/[slug]`) is correctly never treated as "under" `/search`, since it's its own route, not nested.

### Mobile header and burger (Step 6)

**Fixed the known 40×40 finding:** `p-2` (8px) → `p-2.5` (10px) padding around the unchanged 24px icon = 44×44 total, no icon-size change. Verified via production measurement before (40×40, byte-identical to pre-T-059) and after (44×44) at 320/375px.

- `aria-label={t('menu')}` — now genuinely localized (previously a hardcoded English `"Menu"` string regardless of locale; new `nav.menu` key added to all 4 locale files).
- `aria-expanded={open}`, `aria-controls={mobileMenuId}` (stable `useId()`-generated id, matching the panel's own `id`).
- **Deliberately no `aria-haspopup`** — the T-057 lesson applied explicitly: `"true"` is spec-equivalent to `"menu"` and would misrepresent a plain navigation disclosure.
- The accessible name stays constant across open/closed state (`aria-expanded` alone communicates state), matching the T-057 precedent for the filter trigger.

### Mobile navigation panel semantics (Step 7)

**Inspected first, then classified:** the existing `{open && (...)}` conditional render is an **inline disclosure** — it renders in normal document flow directly below the header row, pushing page content down. It is not an overlay, drawer, or modal (no `position: fixed`/`absolute` anywhere in it). This is the simplest accurate model and was preserved as-is.

- **Open:** native `<button>` Enter/Space activation (no custom keydown handler needed for opening).
- **Escape:** closes the panel and returns focus to the burger trigger — the same pattern established in T-057 for the filter popover. Never mutates navigation state, never fires an analytics event, never propagates into unrelated global shortcuts.
- **Navigation:** activating any mobile link closes the panel (`onClick={() => setOpen(false)}`) before the route change completes.
- **Outside interaction:** **deliberately no outside-click handler**, and this is a documented decision, not an oversight — an inline disclosure has no "outside content" being visually obscured that would need an auto-dismiss affordance (unlike T-057's absolutely-positioned filter popover, where outside-click made obvious sense). If a future ticket converts this into an overlay/drawer, outside-click should be reconsidered at that point.
- **Body scroll:** never locked. The page simply grows taller while the menu is open — confirmed via inspection, no scroll-lock logic exists or was added.
- **Focus:** no focus trap (correctly not needed for a non-modal disclosure); no focus loss to `<body>` at any point in the open/Escape/navigate lifecycle.

### Language selector (Step 8)

**Classified as:** a group of direct `<button>` elements calling `router.replace()` — not a native `<select>`, not a custom combobox, not a disclosure. Preserved as-is; no pattern change.

**Found and fixed a real production bug:** switching locale previously dropped the entire query string — confirmed live before the fix (`/en/search?area=athens-center&view=map` → `/ru/search`, filters and view state silently lost) because next-intl's `usePathname()` is query-string-free by design and the old code passed it straight to `router.replace()` with nothing else attached. New `lib/localeSwitchHref.ts` (`buildLocaleSwitchPath`) re-attaches `useSearchParams().toString()` before the locale swap. Still the same `router.replace()` call (never `push`) — T-056's entry-id mechanism is unaffected either way, since this changes only the target *path string*, not the navigation *method*.

- Current locale: `aria-current="true"` (new) plus the existing colour/weight distinction — no longer colour-only.
- Touch target: `min-w-[44px] min-h-[44px]` (previously bare text, ~15-19px wide).
- Tokens: `text-brand`/`text-text-muted` (was `text-pink-600`/`text-gray-400`).
- Labels remain the existing plain 2-letter uppercase codes (`EL`/`EN`/`RU`/`UK`) — no flags, no full names, unchanged content decision.

### Footer visual contract (Step 9)

Tokens applied (`bg-surface`/`border-border`/`text-text-secondary`/`text-text-muted`), every link/button given `min-h-[44px]` (previously ~20px tall, confirmed via production measurement), shared focus-ring token added. All existing destinations preserved verbatim — Privacy, Cookie Policy, Cookie settings (still gated on `isAnalyticsConsentFeatureEnabled()`), copyright line, language switcher. No address, support channel, social link, or newsletter signup added — none existed before, none added now.

### Page transition / sticky footer (Step 10)

`[locale]/layout.tsx`'s `<body>` is `flex min-h-screen flex-col`, with a `flex-1` wrapper around `{children}` so `Footer` sits naturally at the bottom of short pages. This wrapper is (still) a plain `<div>`, not `<main>` — see "`<main>` landmark" above for why the `<main>` itself now lives per-page instead. `CookieConsent` (`position: fixed`) is entirely unaffected by this change, confirmed by inspection. Every current page still sets its own `min-h-screen` on its own root div (unchanged, page-level content) — so today's practical footer-position effect is limited until each page's future ticket drops that now-redundant class; documented as a known transitional state, not a bug.

### Icon migration (Step 11)

No new icons beyond what T-059 already migrated (`Menu`/`X`, both already in `Header.tsx`) — same 2-icon Lucide footprint, unchanged bundle impact. `Footer`/`LanguageSwitcher` have no icons. The mobile nav links' old decorative emoji (💇💅) were removed rather than replaced with new icons — this makes mobile nav text-only, matching the desktop nav's own existing (icon-free) treatment, rather than introducing a mobile-only iconography decision asymmetric with desktop.

### Performance (Step 17)

- Client/server boundary: `Header.tsx`/`Footer.tsx`/`LanguageSwitcher.tsx` were already `'use client'` before T-060 — no new client component type was introduced. However, unifying the shell means `privacy`/`cookies`/`masters` (previously near-static server components, 141B–1.72kB First Load JS) now also pull in `Header`'s client bundle: `privacy`/`cookies` 177B → 4.22kB, `masters` 1.72kB → 5.51kB. This is a direct, expected, and accepted consequence of genuinely sharing one interactive shell instead of three-plus static look-alikes — not a leak or regression.
- CSS bundle: ~48KB → ~52KB (+4KB, from the new token-class usage in Header/Footer/LanguageSwitcher plus the 3 new `maxWidth` aliases) — unchanged by the unification fix itself (same classes, more call sites).
- Zero new npm dependencies (the unification reuses `lucide-react`'s already-migrated `Menu`/`X`, plus one new glyph, `ArrowLeft`, for the back arrow on `detail`/`legal`).
- No runtime network request added (font/icon delivery unchanged from T-059).

### Isolated + live verification results

**Round 1 (pre-REQUEST CHANGES):** 4 locales × {320, 375, 390, 768, 1024, 1440}px — burger 44×44 at every mobile width, `aria-expanded`/`aria-controls`/no-`aria-haspopup` confirmed, mouse-open/keyboard-Enter-open/Escape-close/focus-return/link-navigation-closes-panel all confirmed at every locale, zero console/hydration errors, all 6 footer targets meet 44px at both 375px and 1440px, protected contracts (search initial load, T-056 restoration) unaffected.

**Round 2 (post-unification fix, re-verified against the corrected implementation):** every one of the 6 unified-shell pages (homepage, search, salon detail, privacy, cookies, masters) checked at 1280px and 375px for: exactly one `<header>` with `role="banner"`, exactly one `<main id="main-content">`, exactly one `<footer>`, no horizontal overflow, zero console/hydration errors — all pass. Mobile menu re-verified on all 4 variant surfaces (default via home/masters, search, legal via privacy): exactly one burger, 44×44, opens, reaches `/search`, no duplicated focusable nav DOM. `nav.back`/`nav.menu` accessible-name localization re-verified across all 4 locales on a `legal`-variant page. Locale-switch query preservation re-confirmed on `/search` post-refactor (`?area=athens-center&view=map` survives `en`→`ru`). Search's map view width re-confirmed unchanged (still fills its pre-existing, untouched `max-w-6xl` results container — 1120px at a 1280px viewport, exactly as before the `<div>`→`<main>` retag, confirmed via `git diff` that the retag touched no `className`). T-056 Back-restoration re-confirmed (48/48 cards) against the corrected build.

**Round 3 (live production, `https://lookla.gr`, post-merge/post-deploy, `beauty_web` rebuilt and restarted alone):** re-ran the same landmark/mobile-nav/aria-current/locale-switch/map-width/T-056 checks directly against production across all 6 unified-shell pages — all pass, matching Round 2 exactly. T-056 restoration additionally confirmed to restore both card count (48/48) *and* scroll position. Footer's Privacy/Cookie Policy links confirmed reachable.

```text
T-060 regressions: 0
Known pre-existing SearchBar 320px overflow: unchanged, deferred
```

**One finding, confirmed unrelated to T-060 (all three rounds):** a horizontal-overflow at 320px on the homepage, traced to `SearchBar.tsx`'s own search-submit button (`px-6 py-3 ... whitespace-nowrap`) extending 13px past the viewport. Verified byte-for-byte identical class list on current production both before and after this deploy, independent of any T-060 file — `SearchBar.tsx` is homepage content, out of scope. This is reported as confirmed non-regression, not as a passed visual check. Flagged for the homepage visual-refresh ticket.

## T-062 — Homepage Visual Refresh

**Scope:** `app/[locale]/page.tsx`, `components/SearchBar.tsx`, `components/CategoryGrid.tsx`, `components/AreaGrid.tsx`, and a one-value extension to `components/ui/Icon.tsx`'s `IconSize` enum (16|20|24 → +28, for the category grid's larger visual anchor). Direction B tokens applied throughout; emoji replaced with `lucide-react`; the known homepage `SearchBar.tsx` 320px overflow fixed. Search results page, `SalonCard` (global), salon-detail, and the T-060 shell (`Header`/`Footer`/`LanguageSwitcher`/layout) are untouched — this is the homepage-only ticket in the Visual Baseline v1 sequence (T-059 → T-060 → **T-062** → search-shell → SalonCard → salon-detail → final consistency pass).

**Ticket-identity note:** the ticket was requested as "T-061," but T-061 was already an informal, unreserved backlog placeholder for a future "map accessibility" candidate. Per the collision protocol, this ticket was assigned **T-062** instead (the next genuinely unused ID), preserving the requested title and scope verbatim; the map-accessibility placeholder's own informal working number shifted again, to T-063.

### Step 1–2 — Inventory & preserved interactions

| Section | Owner | Data source | Structure before | Visual role before | Interaction | Problem found |
|---|---|---|---|---|---|---|
| Hero | `page.tsx` | static copy (`messages/*.json`) | `bg-gradient-to-br from-pink-50 to-purple-50` full-hero wash | Brand identity + primary CTA | `<SearchBar>` | Large legacy gradient as the hero's entire identity; ad hoc `text-4xl md:text-5xl` typography, not T-059's scale |
| SearchBar | `components/SearchBar.tsx` | local `useState` | `flex` row, emoji 🔍 submit button | Primary action | `router.push('/search?q=...')` on submit | **320px horizontal overflow** (input had no `min-w-0`, so flexbox's default `min-width:auto` refused to shrink it, pushing the submit button 13px past the viewport) |
| Categories | `components/CategoryGrid.tsx` | `api.categories(locale)` | 2/3/5-col grid, `text-4xl` emoji per tile | Service discovery | `<Link href="/search?category=...">` | Emoji-driven category identity (10 emoji glyphs), legacy `pink-600`/`gray-100` palette |
| Areas | `components/AreaGrid.tsx` | `getHomepageAreas()` → `resolveHomepageAreas()` | 2/3/4/6-col grid, plain text tiles | Geographic discovery | `<Link href="/search?area=...">` + `trackEvent('area_select', ...)` | Legacy palette only — no emoji, already reasonably clean structurally |
| How it works | `page.tsx` | static copy | 3-column icon+text | Product explainer | none (no links) | Emoji icons (🔍📅✨); **step 2 falsely implied online booking** (`"Book"` / `"Choose a time and book online"` — the product has no booking functionality, per T-009/T-010's explicit removal of fake booking CTAs) |

Production measurements (`https://lookla.gr`, before implementation) at 320/375/390/768/1024/1440px: hero height 413px→346px across the range (3 H1 lines at 320px, 2 at ≥390px), search-form right edge at 320px measured 304px (within its own flex container) while the submit button's own right edge measured **333px — 13px past the 320px viewport**, confirming the overflow lived at the flex-item level, not the container level. 0px overflow at every other width. CLS unaffected by any pre-existing issue (T-059 had already measured 0.0028 on the live homepage).

**Interaction/route matrix — before = after, no destination changed:** search submit → `/search?q=<value>` (unchanged path logic, unchanged `encodeURIComponent`); category tile → `/search?category=<slug>` (unchanged); area tile → `/search?area=<slug>` + `area_select` (unchanged event shape/params); locale routing (unchanged, `Header`'s `LanguageSwitcher` untouched); no new history behavior, no ranking change, no API contract change, zero destinations removed.

### Step 3–4 — Information architecture & hero

Kept the existing 4-section order (hero → categories → areas → how-it-works) — it already matches Direction B's own preferred structure (hero/search → discovery shortcuts → existing content → footer), so no section was reordered, and nothing was removed (every section demonstrably serves a real, non-placeholder purpose already). Section containers now consume T-060's previously-unconsumed `max-w-shell-grid`/`max-w-shell-reading` tokens (1152px/768px) instead of bare `max-w-6xl`/`max-w-3xl` — the first page to actually adopt them.

Hero: H1/subtitle copy is **unchanged** (`hero_title`/`hero_subtitle` already state what Lookla is, the geographic scope — "across Greece" — and imply breadth — "Thousands of salons" — satisfying the ticket's own requirements 1–3 without a copy rewrite, which the ticket explicitly discourages). Typography switched to T-059's `.text-display`/`.text-body` tokens (36px/16px) — a deliberately restrained size versus the old responsive `text-4xl md:text-5xl` (up to 48px), matching Direction B's "restrained, not loud" brief. Background: `bg-surface-subtle` (Direction B neutral) replaces the pink/purple gradient. No autoplay video, no carousel, no full-height hero (search results discovery content stays visible above the fold on every measured breakpoint).

### Step 5 — Hero imagery decision

**No licensed image asset exists.** Inventory confirmed `frontend/public/` contains only `robots.txt`/`sitemap.xml` — zero photography, zero brand assets. Using a real crawled salon photo would read as editorial endorsement of that one business (explicitly forbidden); a multi-salon collage introduces real, unresolved licensing uncertainty for a prominent homepage marketing placement (crawled photos' existing, established use is scoped to that salon's own listing page, not homepage promotion). Per the ticket's own explicit fallback ("if no safe image asset exists, do not block the ticket"), the hero uses a **restrained, non-photographic, zero-network-request composition**: two large, softly blurred circles (`bg-brand-soft`/`bg-accent-soft`, `blur-3xl`, `opacity-70`, `aria-hidden="true"`, `pointer-events-none`) positioned behind the text. Real homepage photography is recorded here as a **future content task, not started under T-062**.

### Step 6 — SearchBar: overflow fix + refresh

**Root cause (confirmed via direct measurement, not guessed):** the input was a `flex-1` flex item with no `min-width` override. Flexbox's default `min-width: auto` on a flex item refuses to let it shrink below its content-based intrinsic width — combined with the submit button's own fixed width and the row's `gap-2`, the total exceeded the 288px available inside the hero's `px-4` padding at a 320px viewport, and since the *input* wouldn't shrink, the *button* got pushed 13px past the viewport edge instead.

**Fix:** `min-w-0` added to the input — the actual, minimal, one-class fix. Everything else in this file is presentation refresh, not a layout change: `role="search"` + a real `<label>` (previously placeholder-only), `aria-label` on the submit button (previously unlabeled beyond an emoji glyph — accessible-name behavior across screen readers for a bare emoji button is inconsistent), the 🔍 emoji replaced with `lucide-react`'s `Search` icon via the shared `Icon` component (plus a text label shown at `sm:` and above — a discoverability improvement over an icon-only button), Direction B tokens (`bg-brand`/`border-border`/`focus-ring-token`), and both controls now measure ≥44×44px (previously unconstrained height). T-057's search-page semantics are a separate file/toolbar — this component was never shared with it, so nothing there was touched. No autocomplete/suggestions added. No `trackEvent` call exists in this file, before or after — the raw query never reaches analytics (search-results-page-side tracking, unaffected, is out of scope here).

**Verified at 320px, all 4 locales, post-fix:** 0px overflow (down from 13px), submit button fully inside the viewport, no control overlap, focus ring not clipped.

### Step 7 — Category discovery

Emoji map replaced with `lucide-react` icons through the shared `Icon` component (`size={28}` — a deliberate, documented one-value extension to T-059's `IconSize` enum, since the old emoji were rendered at `text-4xl`, a genuinely larger visual anchor than any existing Icon call site needed before). Mapping: hair→`Scissors`, nails→`Hand`, skin→`Sparkles`, waxing→`Feather`, lashes_brows→`Eye`, makeup→`Palette`, massage→`Waves`, barbershop→`Wand2`, tattoo_piercing→`Gem`, spa→`Flower2`. `lucide-react` has no literal "nail polish" or "razor" glyph — two mappings (`Hand`, `Wand2`) are necessarily approximate, but none are misleading, and per the ticket's own framing the visible label — not the icon — identifies the category. Icons are decorative (`Icon`'s `aria-hidden` default, not overridden). Destinations, category count (`.slice(0, 10)`), and all 4 locale name maps are byte-identical to before. Tokens: `bg-surface`/`border-border`/`hover:border-brand/40`/`focus-ring-token` (was `bg-white`/`border-gray-100`/`hover:border-pink-200`). Touch target unchanged (`min-h-[96px]`). No new analytics event.

### Step 8 — Area discovery

Presentation-token refresh only (`bg-surface`/`border-border`/`text-text`/`text-text-muted`/`focus-ring-token`, was `bg-white`/`border-gray-100`/`text-gray-800`/`text-gray-400`) — no emoji existed here to begin with, so this section needed no icon migration. `area_select`'s call site, event name, and parameter shape (`{ area, source: 'homepage_grid', locale }`) are byte-identical; `trackEvent` still fires exactly once per click (verified live via `gtag()`-call interception — see verification below). No geolocation, no "near me," no map-based selection added — the existing text-only, salon-count-annotated tile grid was preserved as-is, just re-skinned.

### Step 9–11 — Trust presentation, section styling, and the booking-claim fix

No new trust claims were added (no "verified salons," no fabricated statistics, no testimonials, no partner logos, no guarantees) — the existing, already-true copy ("Thousands of salons ... across Greece") was kept unchanged rather than embellished.

**Found and fixed a real, pre-existing false claim while restyling the "How it works" section** (in scope: Step 10 explicitly forbids booking-availability claims in any section this ticket touches, and this section's step 2 was being restyled anyway): `home.step_book_title`/`step_book_desc` read **"Book" / "Choose a time and book online"** (Greek: "Κλείστε ραντεβού" / "Επιλέξτε ώρα και κλείστε online") in all 4 locales — directly contradicting the fact that Lookla has no booking functionality at all (T-009 removed the last fake booking CTAs; T-010 established Call/WhatsApp/Website as the only 3 contact actions). Fixed narrowly — only these two string *values* changed, key names kept, no broader copy rewrite: **"Choose" / "Pick the salon or professional that suits you, then contact them directly"** (and matching translations for el/ru/uk). `step_enjoy_desc` was also adjusted ("Go to your appointment and enjoy" → "Visit and enjoy the service") to remove the now-orphaned "appointment" reference and close the 3-step narrative honestly: Search → Choose (contact directly) → Visit/Enjoy. The three how-it-works icons were also migrated off emoji (🔍📅✨ → `Search`/`CheckCircle2`/`Sparkles`, each in a `bg-brand-soft` circular badge) — `CheckCircle2` was chosen over an initially-tried `MousePointerClick` after a visual check showed the two candidate glyphs (click+sparkle vs. plain sparkle) read as near-identical at this size next to the "Enjoy" step's own `Sparkles` icon; a plain checkmark is unambiguous.

Section rhythm: two surface levels only (`bg-surface` / `bg-surface-subtle`), alternating by section — avoids the "seven identical white panels" pattern the ticket warns against. Headings consistently use `.text-section-title` (categories/areas/how-it-works); card/tile text uses `.text-card-title`/`.text-body`/`.text-body-sm`. No new pill/border/shadow patterns invented beyond what T-059 already defined (`hover:shadow-resting`, `focus-ring-token`).

### Step 12–13 — Responsive & four-locale verification

Isolated standalone build, all 4 locales × {320, 375, 390, 768, 1024, 1440}px (24 combinations): 0px horizontal overflow at every one (the 320px SearchBar case now fixed, confirmed at all 4 locales, not just English); exactly 1 `<h1>`/banner-`<header>`/`<main id="main-content">`/`<footer>` at every combination; search submit + input both ≥44×44px at every width (submit narrows from icon+label to icon-only below `sm:`, which — as a side effect — also *helps* the overflow fix by freeing more room for the input); all 10 category tiles ≥44px tall at every combination; zero console/hydration errors. Greek and Russian/Ukrainian (longer average string length, Cyrillic) confirmed to wrap cleanly with no clipping at 320px — screenshots captured for all 24 combinations. Reduced-motion (`prefers-reduced-motion: reduce`) confirmed to render with no errors (the hero decoration is static CSS, not an animation, so there was nothing to disable). Mobile navigation (T-060's burger/panel) confirmed to open cleanly over the refreshed homepage with no overflow while open.

### Step 14 — Accessibility

Landmark structure: 1 banner (`role="banner"`, from T-060's `Header`), 1 `<main id="main-content">`, 1 `<footer>` — unchanged from T-060, re-verified. Heading hierarchy confirmed logical and matching visual order: H1 → H2 (Popular services) → H2 (Popular Areas) → H2 (How it works) → H3×3 (Search/Choose/Enjoy) — no skipped levels. Search: real `<label>` + `role="search"`, submit has an explicit `aria-label`. Category/area tiles: real `<Link>` elements (native keyboard focus/activation, no custom div+onClick), concise computed names (the visible label text — no icon glyph ever contributes to any accessible name, since every icon in this ticket stays `Icon`'s default `aria-hidden`). No colour-only state (hover/focus adds a border + shadow change, not colour alone; focus-visible uses the shared `.focus-ring-token` outline). Decorative hero shapes are `aria-hidden="true"`; no informative imagery exists to need `alt` text (no `<img>` anywhere on the homepage). No duplicated links to the same target with indistinguishable names within any single card (each category/area card is exactly one `<Link>`).

### Step 15 — Analytics invariants

`page.tsx` itself contains zero `trackEvent` calls (unchanged — the homepage was never a tracking call site for anything but `area_select`, which lives in `AreaGrid.tsx` and is untouched in shape). Verified live via `gtag()`-call interception (the T-056/T-057-established reliable pattern, since raw network sniffing under-counts GA4's batched delivery): clicking an area tile fires `area_select` exactly once, no duplicate. No new event name was introduced anywhere in this ticket's files. No raw query ever reaches analytics (`SearchBar.tsx` has no analytics import at all). No hero/image/category-label value is ever passed to `trackEvent`. Consent gating and T-058 deduplication are untouched (neither file this ticket touches participates in either mechanism).

### Step 16 — SEO & performance

Metadata/canonical/locale-alternates/robots/sitemap/heading-semantics: all untouched (no changes to `generateMetadata`, `notFound()` locale validation, or any `<head>`-affecting code). Homepage stays a server component (`HomePage` is still `async function`, no `'use client'` added at the page level). `CategoryGrid` remains a plain server-renderable component (no `'use client'` directive, no hooks — unchanged in this respect); `AreaGrid` was already `'use client'` before this ticket (needed for its `trackEvent` call) and stays that way; `SearchBar` was already `'use client'` before this ticket too. No component crossed the server/client boundary as part of this refresh.

Measured (isolated standalone, 1440px, `networkidle`): 42 total requests, CLS **0** (no layout shift — the hero decoration is `position: absolute` inside a `position: relative` parent, never affecting document flow), LCP element = the **H1 text** (not an image — confirmed via `PerformanceObserver`, size attribute empty/non-image), meaning no image payload sits on the critical rendering path at all, by construction (no `<img>` exists on the homepage). Homepage bundle: 5.16kB → 5.56kB First Load JS (+0.4kB, from the new icon imports and hero-decoration/token markup) — a bounded, expected cost for genuinely replacing 10+ emoji glyphs and a CSS gradient with a real icon system and composition, not a runaway increase. No new font/icon network request (`lucide-react` icons are inline SVG bundled into existing JS, not separate asset fetches — zero new requests). LCP's absolute isolated-host value (~3.3s) is not representative of production (this throwaway single-core, memory-constrained standalone server has no CDN, no production caching, and is shared with this session's own build/test load — the same caveat already recorded for every prior isolated-verification round in this document); it will be re-measured against `https://lookla.gr` directly during production verification.

### Verification summary

53 new focused tests (`SearchBar.test.tsx`, `CategoryGrid.test.tsx`, `AreaGrid.test.tsx`, `app/[locale]/homepage.test.ts`) plus 1 pre-existing T-059 `Icon.test.tsx` assertion updated for the `IconSize` extension. Full suite: 905/905 passing (all T-042/T-054–T-060 regression suites green, unmodified). Lint clean (only pre-existing, unrelated warnings). `next build` clean. Isolated Playwright: 24 breakpoint×locale combinations + focus-state, reduced-motion, mobile-nav-over-homepage, category/area navigation, search-submission, and `area_select`-dedup checks — all pass.

**Live production verification (`https://lookla.gr`, 2026-07-28, post-merge/post-deploy, `beauty_web` rebuilt and restarted alone):** re-ran the full breakpoint×locale matrix directly against production (24 combinations) — zero horizontal overflow everywhere, search input never overlaps the submit button, zero console/hydration errors. Enter and the submit-button click each independently confirmed to navigate to `/search?q=...` exactly once. All 10 category tiles present with the correct slugs; icons confirmed `aria-hidden` (never contribute to accessible names); accessible names confirmed clean (no emoji). `area_select` confirmed firing exactly once per click via `gtag()`-call interception. No booking/appointment language and no unsupported trust claim found anywhere on the live homepage; the "How it works" step-2 copy fix ("Choose" / "contact them directly") confirmed present. T-060's mobile burger/panel re-confirmed 44×44 and functional over the refreshed homepage. Landmarks re-confirmed (1 h1/banner-header/main/footer). Live CLS measured at 0.0025 (close to zero — the small non-zero delta versus the isolated build's exact 0 is expected on a real page with live analytics/consent scripts attaching, not a regression).

```text
T-062 regressions: 0
```

## T-064 — Search Shell Visual Refresh

**Scope:** `app/[locale]/search/page.tsx` (toolbar, search form, filter trigger/panel, active-filter chip container wiring, results summary, List/Map selector, list/map async-state framing) and `components/ActiveFilterChips.tsx`. Direction B tokens applied throughout; every emoji and inline SVG replaced with `lucide-react`; the known hardcoded Greek `Όλες οι αξιολογήσεις` rating-filter default fixed, plus one additional hardcoded-string finding (`search.list`/`search.map` had emoji baked directly into the translated string in all 4 locales). Search-results page **content** (SalonCard internals, Leaflet markers/popups, ranking, pagination, the entire T-042/T-054/T-056/T-057/T-058 functional contract) is untouched — this is a chrome-only ticket, same boundary discipline as T-060/T-062.

**Ticket identity:** T-064 was genuinely unused — no collision. T-063 (Map Accessibility) remains a separate, untouched, reserved placeholder; T-064 explicitly does not implement any marker-keyboard/popup-accessibility work.

### Step 1–2 — Inventory & preserved interactions

Production measurement (`https://lookla.gr/en/search`) before implementation, at 320/375/390/768/1024/1440px: zero horizontal overflow at every width (T-057 had already fixed the toolbar's own overflow risk); toolbar wraps to 2 rows below ~640px (search+filter on row 1, List/Map on row 2), a single row above; filter trigger/List/Map controls already 44×44 (T-057); results grid width matches the site's standard container at every breakpoint.

**Interaction/route matrix — before = after, no destination or contract changed:** query submit → `/search?q=...` (unchanged); area/rating/category change → same `update()`/`selectArea()` calls, same URL params; individual chip removal → same `removeActiveFilter`; clear-all → same `clearAllActiveFilters`; List↔Map → same `update('view', ...)`, same `aria-pressed` semantics; infinite scroll → same `IntersectionObserver`+`loadMore()`; API error → same `role="alert"` + `retry` callback; salon open → Back → same T-056 snapshot save/restore path; locale change with active params → untouched (Header's `LanguageSwitcher`, not this ticket). Zero lines of the state/effects/handlers block (roughly the first 505 lines of `page.tsx` — every `useState`/`useEffect`/`useCallback` governing search, filters, T-056 restoration, and T-058 dedup) were touched; only the render/JSX section below it changed.

### Step 3–4 — Visual hierarchy & toolbar

Kept the existing single sticky toolbar row (`sticky top-0 z-30`, unchanged — the ticket's own instruction was to not add/remove stickiness without a demonstrated need, and the current sticky behavior was already correct) rather than restructuring into two rows — production measurement confirmed the current flex-wrap composition already produces a clean, predictable 2-row mobile layout with no overflow, so no structural change was needed, only a token/icon refresh. Search input remains the widest, leftmost, visually dominant control; filter trigger and List/Map stay compact secondary controls; the results heading uses `.text-card-title` (16px/600) — deliberately smaller than a hero-style page title, per the ticket's own "no unnecessary large page title consuming mobile viewport" requirement.

### Step 5–7 — Search form, filter trigger, filter panel

**Search form:** `role="search"`, the real `<label>`, single `onSubmit` handler, and the canonical trimmed-query comparison are all byte-identical to T-057. Visual-only changes: the 🔍 emoji submit icon and ✕ emoji clear icon both replaced by the shared `Icon` component (`Search`/`X` from `lucide-react`), Direction B tokens (`bg-brand`/`border-border`/`focus-within:ring-focus`), both controls still exactly 44×44 (`w-11 h-11`, unchanged).

**Filter trigger:** `aria-expanded`/`aria-controls`/absence of `aria-haspopup` (the T-057 lesson) are all unchanged. The inline `<svg>` funnel path was replaced by `Icon`+`SlidersHorizontal`. The active-filter cue (a small count badge, already present pre-T-064) is unchanged in its derivation — still `[area || city, category, minRating].filter(Boolean).length`, never counting `view`, never double-counting legacy `city` (it's already OR'd with `area` in the same slot, exactly as before) — only its container now also flags "active" state via a `filterActive` boolean feeding both the badge and the button's own background, so the state is never colour-only.

**Filter panel:** `role="group"` + labelled region, non-modal (no dialog role, no focus trap — confirmed absent, matching the existing implementation), Escape-closes-without-applying and outside-click-without-forcing-focus are both unchanged (separate listeners, cannot race — same T-057 architecture). Visual-only: `bg-surface`/`shadow-elevated`/`border-border` replace `bg-white`/`shadow-lg`/`border-gray-100`; labels use `.text-label`; selects get `focus-ring-token`.

### Step 8 — Hardcoded string fixes

**Primary fix:** `<option value="">Όλες οι αξιολογήσεις</option>` (a literal Greek string, unconditionally rendered regardless of locale) replaced with `<option value="">{t('all_ratings')}</option>` — a new `search.all_ratings` key added to all 4 locale files (`el`: "Όλες οι αξιολογήσεις" — the correct value for that locale, unchanged in meaning; `en`: "All ratings"; `ru`: "Все рейтинги"; `uk`: "Всі рейтинги"). Verified live: the EN/RU/UK builds now show their own translated text instead of the Greek placeholder; the EL build correctly still shows the Greek text (it's the right language for that locale). Filter semantics, selected/default value, and the URL/API `min_rating` param are all byte-identical — only the *label text* changed.

**Additional finding, in scope (owned by the search shell), fixed:** `search.list`/`search.map` had an emoji glyph baked directly into the translated string itself (`"☰ List"` / `"🗺 Map"` in en, and the equivalent in el/ru/uk) — not a Greek-specific bug, but the same class of problem (a decorative glyph welded into translatable text, which the site's Direction B icon system is meant to replace with a real, separately-controllable icon). Fixed by stripping the glyph from all 4 locale values and rendering a real `lucide-react` `List`/`Map` icon component alongside the now-clean text label instead.

The star-rating option text (`★ 3+`/`★ 4+`/`★ 4.5+`) was deliberately left as-is — locale-independent (a number plus a universal star symbol), not a translation bug.

### Step 9–11 — Active-filter chips, results summary, List/Map selector

**Chips:** the entire T-054 contract (canonical effective-filter derivation, individual removal, clear-all, `useFilterChipFocus` recovery, legacy-`city` handling) is untouched — `ActiveFilterChips.tsx`'s props/logic are unmodified. Visual-only: `bg-pink-50`/`text-pink-700` → `bg-brand-soft`/`text-brand`; `rounded-full` → the shared `rounded-pill` token; the `×` text glyph → `Icon`+`X` (16px, decorative); `focus-ring-token` added to the remove button. Accessible names (`removeLabel(filter)`), focus sequence, and the one-`<li>`-per-chip/one-`<button>`-per-chip structure are all unchanged.

**Results summary:** still derives its count exclusively from the canonical list-fetch `total` (never `salons.length`/`mapSalons.length`), still `aria-live="polite"`, still shows nothing during loading beyond the existing skeleton placeholder, still shows nothing on error. Visual-only: `.text-card-title` heading, `.text-body-sm text-text-secondary` count text, token-coloured skeleton placeholder.

**List/Map:** `aria-pressed`, the "re-selecting the active view is a no-op" behaviour, and the URL `view` param contract are all unchanged (still plain toggle buttons, not a tabs pattern). Visual-only: wrapped in a shared `bg-surface-subtle` segmented-control container, active state now `bg-brand text-text-inverse` with a `List`/`Map` icon alongside the (now emoji-free) text label — text labels are never dropped, satisfying the ticket's explicit "no icon-only control" requirement.

### Step 12–13 — List/map framing

**List:** grid column/gap contract (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4`) is unchanged — verified byte-identical. Only the loading-skeleton tiles' own colours (`bg-white`/`border-gray-100` → `bg-surface`/`border-border`) and the load-more bounce-dot colour (`bg-pink-400` → `bg-brand`) changed. `SalonCard.tsx` itself was not modified (confirmed: it contains no reference to any T-064-introduced import).

**Map:** `MapView.tsx` (markers, popups, clustering, fetch, center/zoom) is completely untouched — the dynamic `import('@/components/MapView')` call site is byte-identical. T-064 only added a `rounded-md overflow-hidden border border-border` shell around the existing `AsyncSection`-wrapped map, plus token colours on the loading/error framing around it (never on the map itself). Verified the wrapper adds no height/width-constraining class, so map dimensions are unaffected — confirmed live (Leaflet still renders at its existing size, `.leaflet-container` present and functional after the visual refresh).

### Step 14 — Async states

T-042's functional/accessibility contract (`role="alert"`/`aria-live="assertive"` for errors, `role="status"`/`aria-live="polite"` for empty, `aria-hidden` skeletons, `useFocusOnStatusRecovery`-driven focus-on-retry) is entirely unchanged — only colours/tokens on the skeleton, empty, and error presentations were touched (`text-gray-400`→`text-text-muted`, `text-red-400`→`text-danger`, retry links `text-pink-600`→`text-brand`). Verified live: simulating a `500` on `/api/salons` still surfaces a `role="alert"` region.

### Step 15–16 — Responsive & four-locale verification

Isolated standalone build, all 4 locales × {320, 375, 390, 768, 1024, 1440}px (24 combinations): zero horizontal overflow at every one; search input never overlaps the submit button; filter trigger and List/Map controls both ≥44×44 at every combination; zero console/hydration errors. The Greek-hardcode fix specifically re-verified per-locale: EN/RU/UK show their own translated "All ratings" text, EL correctly still shows the Greek original.

### Step 17 — Accessibility

T-060's landmarks (banner/main/footer) are unaffected (this ticket doesn't touch `Header`/`Footer`/layout). Filter-trigger `aria-expanded`/`aria-controls`/no-`aria-haspopup`, Escape-close-with-focus-return, List/Map `aria-pressed`, chip focus recovery, and async-state roles are all re-verified live and unchanged. No icon glyph contributes to any accessible name anywhere in the touched files (every `Icon` call stays at its `decorative`-by-default, `aria-hidden` setting). Map-marker accessibility remains entirely out of scope, reserved for T-063.

### Step 18–19 — Analytics & T-056 restoration

Re-verified live via `gtag()`-call interception: opening and closing the filter popover (click, then Escape) emits no event at all; only `search_results_view` fires, exactly once, matching the pre-existing contract. `trackEvent` call-site sweep confirms only the 5 pre-existing T-015 event names appear anywhere in `page.tsx`, and none of the T-064-authored code paths (chip remove, clear-all, List/Map toggle, filter open/close) call it. T-056 regression re-run live: load 48 cards → open a salon → Back — cards restored (48/48) and the refreshed toolbar renders correctly intact after the remount, with no visual flash back to a page-1 state and no duplicate fetch.

### Step 20 — SEO & performance

Metadata/canonical/locale-alternates/indexability: untouched (no changes to any `<head>`-affecting code — this ticket only touches `SearchContent`'s render output). Measured (isolated standalone, 1440px, `en/search`, `networkidle`): CLS **0**; LCP element is a **`<img>` salon photo served from `cdn.lookla.gr`** (`SalonCard`'s own existing photo, not anything this ticket added or could have added — LCP was already photo-bound before T-064 and remains so, since `SalonCard.tsx` itself is untouched). Search-page bundle: 13.4kB → 9.46kB First Load JS — a **decrease**, not an increase: the old inline `<svg>` funnel path string was replaced by a shared `lucide-react` icon reference that reuses chunks already loaded elsewhere on the site (`Icon`/lucide icons were already part of the shared bundle since T-059/T-060/T-062). No new npm dependency, no new font/icon network request.

### Verification summary

62 new/updated focused tests (`searchShellVisual.test.ts` — 29 new; `ActiveFilterChips.test.tsx` — 4 new; 5 pre-existing T-057 assertions in `searchControlsA11y.test.ts` and 1 in `searchPage.test.ts` updated to match the new markup while preserving the exact same underlying guarantee, after their original literal-string/fixed-offset markers stopped matching the refreshed source — not a weakening of what they check, only how they locate it). Full suite: 938/938 passing (all T-042/T-054/T-055/T-056/T-057/T-058/T-059/T-060/T-062 regression suites green). Lint clean. `next build` clean. Isolated Playwright: 24 breakpoint×locale combinations, the Greek-hardcode fix per-locale, filter-popover keyboard lifecycle, chip removal + clear-all, List↔Map toggle with live Leaflet render, a simulated API-500 → `role="alert"`, T-056 restoration, and the `gtag()`-intercepted analytics-invariant check — all pass.

**Live production verification (`https://lookla.gr`, post-merge/post-deploy, `beauty_web` rebuilt and restarted alone):** re-ran the full breakpoint×locale matrix directly against production (24 combinations) — zero overflow, no input/submit overlap, filter trigger and both List/Map controls ≥44×44, zero console/hydration errors throughout. Rating-default localization and the List/Map emoji-removal fix both re-confirmed per locale live. All toolbar icons confirmed `aria-hidden`. Filter-popover lifecycle (no `aria-haspopup`, Escape-close-with-focus-return), chip removal + clear-all + canonical-total presence, a simulated API-500 → `role="alert"` + Retry, and the List↔Map toggle (exactly one `aria-pressed="true"`, 2000 live Leaflet markers rendering) all re-confirmed live. `SalonCard` re-confirmed structurally unchanged (single outer link, photo present). T-056 restoration (48/48 cards) and T-058 dedup (exactly one `search_results_view` across the full search→open→Back cycle) both re-confirmed live via `gtag()`-call interception. Live CLS measured at 0.

```text
T-064 regressions: 0
```

## T-065 — SalonCard Visual Refresh

**Scope:** `components/SalonCard.tsx` only, plus the search page's loading-skeleton markup (`app/[locale]/search/page.tsx`) updated to match the card's new geometry. First ticket in the Visual Baseline v1 sequence permitted to change the card's *internal* appearance — T-059/T-060/T-062/T-064 all deliberately left `SalonCard.tsx` untouched. Salon-detail, map markers/popups, ranking, and the entire T-055/T-056/T-058 functional/analytics contract are untouched.

**Consumer map:** `SalonCard` has exactly **one real consumer** today — `app/[locale]/search/page.tsx`. The `source` prop's `'homepage' | 'masters'` values exist in the type but are not currently exercised by any call site (homepage has no salon previews per T-062; `/masters` is a specialties/CTA page per T-060, not a card grid) — reserved, unused, unchanged by this ticket.

### Step 2 — Data-state matrix

Every state below is possible with real production data and was verified live: photo present / absent (both occur — not every salon has `primary_photo`) / request fails (simulated via route interception); long salon names (line-clamp-2 already handles this per T-055); rating + reviews present / rating absent (`rating_google` is optional); address present (near-universal) / partial (missing `address_number` collapses cleanly via the existing `.filter(Boolean)` join); open / closed / status-unknown (`is_open_now` undefined/null — the existing gate gap gates it correctly); verified / unverified (`is_verified` is `false` on effectively all ~6320 salons today, per the T-055 audit — the conditional branch exists and was exercised via a forced-true test fixture, not live production data, since no real verified salon currently exists to screenshot); price present / absent (`min_price` is null for most salons). No impossible state was designed for.

### Step 3 — Visual hierarchy (final)

1. Photo (or honest fallback) — full-width, `aspect-[4/3]`, dominant.
2. Salon name — `.text-card-title`, line-clamp-2.
3. Address — one line, decorative `MapPin` icon, secondary tone.
4. Rating + review count — one filled star, numeric value, count in parens.
5. Price (conditional) — right-aligned alongside rating, subordinate to identity.
6. Open/closed + verified — overlaid on the photo (unchanged position from before this ticket; this is a deliberate, high-scannability placement matching common marketplace-card conventions, not a literal DOM-order restatement of the numbered list above).

This matches the ticket's recommended hierarchy; the only interpretation applied was keeping status/verification as photo overlays (already the pre-existing pattern, and more scannable there than inline text) rather than moving them into the text block.

### Step 4 — Surface & shape

`bg-surface rounded-md border border-border overflow-hidden shadow-resting hover:shadow-elevated hover:border-border-strong transition-shadow focus-ring-token` — was `bg-white rounded-xl border-gray-100 hover:shadow-md hover:border-pink-100`. `rounded-md` (10px) replaces the old `rounded-xl` (12px) to align with the radius token already standardized on Header/Footer/search-toolbar/filter-panel — not a fourth radius value. `shadow-resting` is now the card's *default* surface treatment (not hover-only), with `hover:shadow-elevated` for the lift — the actual intended use of T-059's 2-level shadow system, which no earlier ticket had consumed yet. `overflow-hidden` and `focus-ring-token` deliberately live on the *same* outer `<Link>` element — verified empirically (an isolated HTML/CSS test, screenshotted) that an element's own `overflow: hidden` does **not** clip that same element's own `outline` (only descendant content is clipped); the focus ring renders fully, unclipped, confirmed both in the isolated test and live on the search page.

### Step 5–6 — Image & fallback

**Aspect ratio:** `aspect-[4/3]` replaces the old fixed `h-44` (176px). The old fixed-height approach produced a *different* visual crop ratio at every card width (since height was constant but width was responsive); `aspect-[4/3]` keeps a single, deliberate ratio at every breakpoint. `object-cover` unchanged (crops rather than stretches). `loading="lazy"` preserved unchanged — priority/eager loading for above-the-fold cards was considered (Step 5 explicitly allows it) but not implemented: it would require threading an index/priority prop through the search page's call site, expanding this ticket's file boundary for a marginal, unmeasured LCP gain: deferred, not started, noted here as a real future option rather than silently dropped.

**Fallback — a real gap found and fixed:** the old `onError` handler only set `style.display = 'none'`, leaving a blank pink-gradient box with *nothing* in it on a failed image request (the `💈` emoji fallback only ever rendered for a *missing URL*, never for a *failed* one — two different states the old code didn't actually distinguish correctly). Fixed with `useState<boolean>` (`imageFailed`) set in `onError`; `showPhoto = salon.primary_photo && !imageFailed` now covers both "no URL" and "URL present but failed" with the identical, honest fallback UI — a generic `Building2` (storefront) icon on `bg-surface-subtle`, decorative/`aria-hidden`. Deliberately *not* category-specific (e.g. `Scissors` for a hair salon): the `category` prop reflects the page's current search filter, not verified per-salon data, so a specific service icon risked misrepresenting a salon that doesn't actually offer it. Verified live: simulating a blocked image request shows the fallback icon, not broken-image browser UI, with the card height unchanged (392px, matching a normal photo card at the same breakpoint).

### Step 7 — Salon name

`.text-card-title` (T-059's 16px/600/1.4 token — literally named for this use case) replaces the ad hoc `font-semibold text-gray-900 text-sm leading-tight`. `line-clamp-2` and `title={salon.name}` both preserved unchanged from T-055 — full name remains in `aria-label` regardless of visual truncation (unchanged T-055 guarantee). No uppercase transform, no tooltip-as-accessibility-substitute.

### Step 8 — Rating

**Real visual change, explicitly invited by the ticket:** the old `STARS()` helper rendered a 5-glyph Unicode row (`★★★★☆`, decorative/`aria-hidden`) alongside the *same* numeric value directly next to it — redundant information (both convey the identical rating), adding visual noise without adding meaning. Replaced with **one** filled Lucide `Star` icon (`fill-accent-strong text-accent-strong`, decorative) + the numeric value + review count in parens — the numeric value alone already fully conveys the rating; one icon anchors it visually without competing for attention. Colour: `accent-strong` (T-059's text-safe gold/amber variant, explicitly designed for exactly this "text-adjacent decorative gold" case) — not brand pink, matching the ticket's explicit "not universal brand pink" requirement. Missing rating still shows a neutral `—`, never a fabricated `0.0`. Accessible name: unchanged — rating is announced exactly once, via `buildCardAriaLabel`'s `rating` clause; the star icon, numeric span, and review-count span all stay outside or correctly excluded from double-announcing (verified via the updated T-055 test suite plus a new live check).

### Step 9 — Address

A decorative `MapPin` icon (16px, `text-text-muted`, `aria-hidden`) added before the address text — a restrained scan-aid, per the ticket's "only if it improves scanning" allowance. Address *composition* (`[street, number].filter(Boolean).join(' ')` + conditional `, city`) is byte-identical to before — no new fallback rule, no city/area inference, no coordinates exposed, no map deep-link added. Still `line-clamp-1`, still only reachable via the single outer Link (no nested link).

### Step 10 — Open/closed status

Logic completely unchanged (`is_open_now !== undefined && !== null` gate, same two-value label lookup). Visual-only: `bg-green-500`/`bg-black/50` replaced with the semantic `bg-success`/`bg-closed` tokens — tokens T-059 defined with (in retrospect) exactly this use case in mind, never consumed by an earlier ticket. Status text remains visible alongside the colour (never colour-only). No new "closing soon" state, no assumed-open default.

### Step 11 — Verified state

**Documented meaning (first, as the ticket requires):** `is_verified` is a boolean *gate* — when `false` (currently true for effectively 0 of ~6320 salons, per the T-055 audit), no badge renders at all. When `true`, `is_owner_claimed` picks between exactly two existing, already-restrained strings: "Owner verified" or "Information reviewed" (`lib/verificationLabel.ts`, `DEC-014`) — neither implies quality, safety, or a recommendation; both were already this restrained before T-065. Visual-only: badge moved from a blue (`text-blue-600`) pill to a neutral `bg-surface/95 text-text-secondary` pill — deliberately *not* brand or success-coloured, since a verified badge is informational, not a positive-status or primary-action signal. A decorative `BadgeCheck` icon was added (a modest checkmark, not `ShieldCheck`, which reads closer to "safety-certified" — too strong for what this field actually means). Unverified cards render no negative/warning element (unchanged — the conditional stays a pure show/hide, no else-branch).

### Step 12 — Price

Conditional gate (`min_price != null && > 0`), rounding (`Math.round`), currency (`€`, hardcoded — the product is Greece-only, not a formatting change without evidence), and the `fromLabel` prefix are all byte-identical to before. Visual-only: token colours. Price remains plain text with no border/background/padding that could read as a button, staying subordinate to the salon identity above it.

### Step 13 — Metadata composition examples

- **Minimal-data card** (no photo, no rating, no address components, no price): fallback icon fills the photo frame; name; a bare address line if *any* address fragment exists (city alone still renders); a lone `—` where rating would be; no price row content (the flex container itself still renders, empty on the price side — unchanged from T-055's "no reserved blank row" guarantee, since the price `<div>` itself is conditionally absent, not present-but-empty).
- **Typical card** (photo, rating+reviews, address, open/closed, no verification, no price): the common real-data shape, screenshotted extensively above.
- **Full-data card** (photo, rating, address, status, verified, price): every element present — visually confirmed no collision between the verified badge and status badge (opposite corners of the photo) and no crowding in the bottom metadata row.

### Step 14–15 — Interaction states & DOM integrity

**Hover:** `shadow-resting`→`shadow-elevated` and `border-border`→`border-border-strong` on the card; the photo scales `1.05×` *inside its own `overflow-hidden` frame* — text and layout never move; the scale is on the `<img>` only, not the outer Link (verified: the outer Link's own className carries no `hover:scale-*`). **Focus-visible:** `focus-ring-token`'s standard 2px `--focus`-coloured outline, confirmed rendered and unclipped (see Step 4). **Active:** no scale/persistent-selected state was ever added by any prior ticket; T-065 introduces none. **Reduced motion:** `motion-reduce:transition-none motion-reduce:transform-none` on the image disables the hover-zoom transition under `prefers-reduced-motion: reduce`, confirmed live (page renders cleanly, zero errors, under a reduced-motion browser context).

**DOM integrity, verified live via direct DOM inspection across 24 rendered cards:** exactly one `<a>` per card (the outer Link), zero nested `<a>`/`<button>`/`<input>`/`<select>`, zero descendant `tabindex`, zero click handlers outside the single outer `onClick={handleOpen}`.

### Step 16 — Analytics invariants

`salon_open`'s ownership, parameter shape (`salon_id: String(salon.id)`, never `salon.slug`), and single call site are byte-identical to T-055. Verified live: keyboard `Enter` on a focused card activates navigation and fires exactly one `salon_open`; hovering and focusing a card (without activating) fires **zero** analytics events of any kind (a `gtag()`-call-interception check, with the page's own normal load-time `search_results_view` call explicitly excluded from the measurement window so it isn't mistaken for a hover/focus side effect). No new event names, no new payload parameters, no PII.

### Step 17 — T-056 restoration

Live regression: load 48 cards → open a salon → Back — 48/48 cards restored, and the restored cards render with the *new* visual design immediately (icons present, zero legacy Unicode star glyphs) — no flash back to an old/fallback structure, confirmed by inspecting the first restored card's rendered markup right after restoration.

### Step 18–19 — Search-grid compatibility & skeleton alignment

Grid column/gap contract (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4`) in `search/page.tsx` is untouched. The loading skeleton *was* updated — it previously used a single fixed `h-64` block, which no longer approximates the real card's height now that the image uses a responsive `aspect-[4/3]` instead of a fixed pixel height (the real card's total height now genuinely varies by breakpoint, tracking the image's aspect-ratio math). The new skeleton mirrors the real structure directly (an `aspect-[4/3]` placeholder + title/address/rating-price placeholder bars in the same `p-3` padding), so it tracks the same height automatically at every breakpoint rather than needing a hand-tuned fixed value per width. Skeleton stays `aria-hidden`, no fake readable text, `animate-pulse` given `motion-reduce:animate-none`. Skeleton count (6) and the overall async-state contract from T-042/T-064 are untouched.

### Step 20–21 — Responsive & four-locale verification

Isolated standalone build, all 4 locales × {320, 375, 390, 768, 1024, 1440}px (24 combinations): zero horizontal overflow at every one; card renders with real, non-zero dimensions at every combination; zero console/hydration errors. Russian (longest average string length of the 4 locales) confirmed clean at 375px — status badge, truncated address, and 2-line title all render without overflow or clipping.

### Step 22 — Accessibility

Exactly one focusable element per card (the outer Link — re-confirmed via live DOM inspection). Accessible name confirmed free of star glyphs, confirmed present, confirmed correctly built from `buildCardAriaLabel` (unchanged T-055 function). All decorative icons (star, map pin, badge-check, photo-fallback) confirmed `aria-hidden` live, across every rendered card on the page, not just a single sample. Rating and status are each announced exactly once (T-055's original invariant, re-verified against the new markup). No ARIA was added beyond what already existed (`aria-label` on the Link) — no per-row ARIA was introduced for the individual metadata lines, per the ticket's own "do not add ARIA to every internal visual row" instruction.

### Step 23 — Performance

Isolated standalone measurement (`en/search`, 1440px, `networkidle`, two separate runs): CLS **0** in both runs (the `aspect-[4/3]` container reserves its own space before the image loads, same as the old fixed-height approach — no regression). LCP element unchanged in nature — still a `SalonCard` photo (`<img>` from `cdn.lookla.gr`) — LCP timing itself ranged 5.2–6.6s across two runs on this same isolated host, overlapping with T-064's own 5.6s baseline measurement; given CLS stayed perfectly 0 and total transferred bytes (~3.83MB) and image-request count (19, no duplicates) were essentially unchanged from the T-064 baseline, this range reads as this shared, memory-constrained host's known measurement noise (documented repeatedly across this project's prior tickets), not a real regression introduced by this ticket. Search-page bundle: 9.46kB → 9.98kB First Load JS (+0.52kB, from the new icon imports) — a small, expected cost for genuinely removing a 5-glyph Unicode star row and adding 4 real Lucide icons per card.

### Verification summary

61 tests in the existing `SalonCard.test.tsx` (updated: 5 pre-existing T-055 assertions rewritten to locate their same literal-string-pinned guarantee inside the refreshed markup — including fixing two comment-vs-code false positives introduced by my own new JSDoc prose, the same recurring class of bug this project has hit and fixed repeatedly) + 37 new tests in `SalonCardVisual.test.tsx` (image/fallback/failure handling, surface tokens, rating/address/status/verified/price contracts, DOM integrity, and a no-new-data/no-new-analytics regression sweep). Full suite: 975/975 passing (all T-042–T-064 regression suites green, unmodified — including one more comment-false-positive fix in the *pre-existing* `lib/analytics.test.ts`'s own SalonCard-related assertion, found and fixed the same way). Lint/`next build` clean (one real TypeScript catch during the build: an icon `size={14}` isn't a member of the fixed `IconSize` enum — corrected to `16`, the nearest valid value). Isolated Playwright: 24 breakpoint×locale combinations, DOM-integrity inspection across 24 live cards, accessible-name + decorative-icon verification, focus-visible (screenshotted, confirmed unclipped), 3 image states (valid/missing/failed — including a route-interception-simulated failed request), reduced-motion, keyboard activation + single `salon_open`, zero hover/focus events, T-056 restoration with the new design, and a List→Map→List transition — all pass.

**Live production verification (`https://lookla.gr`, post-merge/post-deploy, `beauty_web` rebuilt and restarted alone):** re-ran the full breakpoint×locale matrix directly against production (24 combinations) — zero overflow, image aspect-ratio confirmed ~4:3 at every combination, zero console/hydration errors. Missing-URL and a simulated-failed-request image state both re-confirmed to converge on the identical fallback, with no retry loop and a stable card height. Accessible name and decorative-icon exclusion re-confirmed live. DOM integrity re-confirmed across 24 live cards. Focus ring re-confirmed rendered and unclipped. Hover re-confirmed to cause zero layout shift and zero analytics events. Pointer click and keyboard `Enter` both re-confirmed to produce exactly one `salon_open`; Ctrl-click re-confirmed to open a new tab, browser-default behaviour uninterfered with. T-056 restoration (48/48 cards + scroll) and T-058 dedup (exactly one `search_results_view` across the full cycle) both re-confirmed live. List→Map→List re-confirmed with markers rendering and the list correctly restored. Live CLS measured at 0.

```text
T-065 regressions: 0
```

## T-066 — Salon Detail Visual Refresh

**Scope:** `app/[locale]/salons/[slug]/SalonDetailClient.tsx` (full visual rewrite), `components/ContactButtons.tsx`, `components/SalonHours.tsx`, `components/ReportButton.tsx` (tokens/icons only in the latter three — no logic changes). `app/[locale]/salons/[slug]/page.tsx` (server component, metadata) untouched. T-063 (Map Accessibility) remains a separate, untouched, reserved placeholder — this ticket confirmed during inventory that salon-detail has no embedded map/Leaflet widget at all today (only a text address + an external Google Maps link), so T-063 has nothing to own here yet. This is the last conversion-facing screen in the Visual Baseline v1 sequence (T-059 → T-060 → T-062 → T-064 → T-065 → **T-066**).

**Ticket identity:** no collision — T-066 was genuinely unused.

### Inventory findings (Steps 1–2)

Two real, pre-existing gaps found during inventory, both addressed by this ticket:
- **The hardcoded Greek `+N φωτογραφίες` overlay** — the exact bug named in the ticket. The gallery's "show more photos" affordance always rendered this literal Greek string regardless of locale. Fixed with a proper ICU-pluralized `salon.more_photos` key across all 4 locales (`el`/`en` use `=0/one/other`; `ru`/`uk` use the full Slavic `=0/one/few/many/other` set, matching the existing `search.results_summary` precedent even though all Russian/Ukrainian categories render identically for "фото").
- **`is_open_now` was fetched but never rendered anywhere on the page**, despite being available data (and already driving `SalonCard`'s open/closed badge on the search results page). Added a matching open/closed badge here too, using the same `bg-success`/`bg-closed` semantic tokens T-065 introduced.

Every visible surface used the identical `bg-white rounded-xl p-5` panel treatment (7 near-identical white boxes stacked down the page), giving photo gallery, identity, description, services, reviews, hours, and social links all equal visual weight — no hierarchy, no indication of which action (Call/WhatsApp/Website) mattered most.

### Visual hierarchy & surface levels (Steps 3–4)

Three tiers, replacing the flat 7-box stack:
1. **Prominent** — the identity+contact card (name, address, rating, status, verified badge, Call/WhatsApp/Website buttons): `bg-surface rounded-md border border-border shadow-resting p-5`. The only card carrying a shadow — deliberately the page's single loudest surface, since it's the primary conversion point.
2. **Mid-tier** — Services/Reviews/Hours: `bg-surface rounded-md border border-border p-5`, no shadow. Real content sections, but subordinate to identity+contact.
3. **Quiet, card-less** — Description, social links, location/map-link, data-freshness note, report link: no surface at all, just typography and spacing. These are supporting information, not decision points.

### Gallery, fallback, and a layout bug found during implementation (Steps 5–7)

**Photo-count fix:** see Inventory findings above.

**Fallback:** reused T-065's `PhotoFallback` contract (decorative `Building2` icon on `bg-surface-subtle`, non-category-specific) and extended it with genuine per-image failed-request handling — a new `GalleryImage` component tracks `onError` via `useState` so a photo that fails to load converges on the identical fallback UI as a missing URL, rather than leaving a blank/broken tile. The original code had no such handling at all (a real gap, not a regression).

**A real bug found and fixed during implementation, not introduced by this ticket but exposed by it:** the gallery's 3-tile layout used CSS Grid (`grid-cols-3`, first tile `col-span-2`) inside a fixed-height (`h-56 md:h-72`), `overflow-hidden` container. With tile 1 spanning 2 of 3 columns and tile 2 filling the remaining column, row 1 is completely full (2+1=3 units) — ordinary CSS Grid auto-placement therefore pushes tile 3 (the one carrying the "+N photos" button) onto an *implicit second row*, which the fixed-height, overflow-hidden container then silently clips out of view. Confirmed via direct DOM inspection of a real 10-photo salon: 3 grid children genuinely existed, with tile 3 positioned at `y: 464.4` — a full row below tiles 1–2 at `y: 81` — and confirmed via screenshot that the "+7 photos" affordance was completely invisible to sighted users despite being correct, present, and keyboard-reachable in the DOM. Since this container's classes were carried over unchanged from the pre-T-066 implementation, this was a **pre-existing, previously-unnoticed bug**, not a regression — but it directly defeated the very feature (the photo-count fix) this ticket was required to deliver, so it was in-scope to fix here. Replaced the grid with flexbox (`flex` + `flex-[2]`/`flex-1` + `min-w-0` per tile) — a single flex row cannot silently wrap to an implicit second row the way grid auto-placement can, so it cannot reproduce this clipping. Re-verified via DOM inspection (all 3 tiles now at the same `y`) and screenshot (the "+7 photos" tile clearly visible and clickable) after the fix. Zero CLS impact measured (0.0029, isolated standalone).

### Identity block, contact actions, sections (Steps 8–18)

**Identity:** name (`.text-page-title`), address with decorative `MapPin`, rating as one filled Lucide `Star` + numeric value + count (replacing any prior star-glyph pattern, matching T-065's SalonCard precedent), open/closed badge (semantic tokens, newly rendered — see Inventory findings), verified badge (`BadgeCheck`, neutral `bg-surface-subtle` pill, same restrained treatment as T-065's SalonCard verified badge, using the existing `getVerificationLabelKey` two-string contract unchanged).

**Contact actions:** Call/WhatsApp/Website deliberately share one identical visual treatment (`bg-brand-soft text-brand hover:bg-brand hover:text-text-inverse`, `min-h-[48px]` touch target) — per the ticket's explicit instruction not to invent a new channel priority among the three. `resolveContactActions`/`hasAnyContactAction` (T-010) and the `contact_action` tracking contract (T-015, single owner in `ContactButtons.tsx`'s `trackContact`) are byte-for-byte unchanged. The no-contact-info state (`contactInfoUnavailable` message + `ReportButton`) is unchanged.

**Services/Reviews:** unchanged lazy-load (`IntersectionObserver` + `AsyncSection`) architecture; only surface tokens and the per-review star treatment changed (single `Star` icon + numeric rating, replacing a repeat()-based Unicode star row).

**Hours:** `SalonHours.tsx` — tokens only; the today-detection (`(new Date().getDay()+6)%7`) and sort logic are byte-identical.

**Social links & location:** social-platform icons use generic `lucide-react` stand-ins (`Camera`/`Users`/`Send`/`MessageCircle`/`Music`/`Video`) — the installed `lucide-react` version ships **zero brand/logo icons** (`Instagram`/`Facebook`/`Youtube` all confirmed absent from the package's exports), a real upstream constraint, not a design choice made carelessly. Location section is a quiet text address + external Google Maps link — no embedded map exists on this page (see Scope note on T-063).

### Verification (Steps 20–26, 28)

**Responsive:** mobile (375px), tablet (768px), desktop (1280px) all render cleanly, isolated standalone build, real 10-photo salon.

**Four locales:** `more_photos` and the new `location` heading both confirmed correctly localized and non-overflowing in all 4 locales (`el`: `+7 φωτογραφίες`, `en`: `+7 photos`, `ru`/`uk`: `+7 фото`); Greek's longer plural form wraps to two lines within the gallery tile without clipping or overflow.

**Accessibility:** exactly one `<h1>`, `#main-content` landmark present, all `<img>` have `alt`, gallery button and contact links carry descriptive `aria-label`s, visible focus ring confirmed via real keyboard `Tab` + screenshot (not a `:focus-visible` computed-style query, which doesn't work as a pseudo-class probe — verified with an actual keyboard-driven focus + screenshot instead).

**Analytics:** `contact_action` re-verified live via `gtag()`-call interception (with the `lookla_consent` cookie set to `'1'`, the real granted-value the consent module writes — not the string `'granted'`) — fires exactly the T-015 shape (`salon_id`, `channel`, `page: 'salon_detail'`, `locale`) for both `phone` and `whatsapp` clicks, with no salon name, phone number, or URL in the payload. Confirmed loading the detail page directly fires **zero** events (no `salon_open` — that event remains solely owned by the originating search-card link, per T-015/T-058). Confirmed the full search→detail cycle: `search_results_view` fires once on the search page, `salon_open` fires exactly once on the card click, and does not re-fire when the detail page mounts.

**T-056 restoration:** search → open a salon → interact with the gallery → browser Back — search results correctly restored with no console errors.

**SEO:** title/description/`BeautySalon` structured data (`aggregateRating`, address, telephone)/`og:image` all confirmed unchanged (server-component `page.tsx` metadata untouched; the `SalonDetailClient` schema.org block preserved as-is).

**Performance:** isolated standalone measurement — CLS **0.0029**, confirming the gallery's grid→flexbox rewrite introduced no layout shift. Bundle: salon-detail route stayed essentially flat (6.83kB First Load JS).

### Verification summary

73 tests: the pre-existing `salonDetail.test.ts` (28 tests, all pass unchanged — every structural marker it slices on, e.g. `{/* CTA buttons */}`/`{/* Description */}`, preserved verbatim) + a new `salonDetailVisual.test.ts` (45 tests: photo-count fix, gallery fallback, no-emoji sweep, identity block, contact-action consistency, services/reviews/hours, map-shell boundary, analytics invariants, SEO/structured-data, Direction B tokens). Full regression suite green throughout (1020/1020, then re-confirmed green again after the lucide-react brand-icon build fix). Lint clean. `next build` clean (one real TypeScript catch: `Instagram`/`Facebook`/`Youtube` aren't exported by the installed `lucide-react` — corrected to generic icons, see Social links above). Isolated Playwright: responsive × locale sweep, the gallery-clipping bug found/fixed/re-verified, accessibility (focus ring, landmarks, alt text), analytics (`contact_action` × 2 channels, `salon_open` single-fire dedup), T-056 restoration, SEO metadata, and CLS/LCP measurement — all pass.

**Live production verification (`https://lookla.gr`, 2026-07-29, post-deploy):** all 4 locales × {320, 375, 390, 768, 1024, 1440}px (24 combinations, one interrupted mid-run by a harness timeout but with an identical, fully consistent result across the other 23) — zero horizontal overflow, all 3 gallery tiles rendered at the same vertical position (the grid→flexbox clipping fix confirmed live), `+N photos` correctly localized and visible/clickable in every locale (`+7 φωτογραφίες`/`+7 photos`/`+7 фото`), exactly one `<h1>` at every combination, zero console/page errors. Analytics re-verified live via `dataLayer.push` interception (production runs a real, configured GA4 — unlike the isolated local build — so verification here intercepts the actual `gtag.js` transport rather than a stub): `contact_action` fires the exact T-015 shape for both `phone` and `whatsapp` clicks, no PII in the payload; loading the detail page directly fires zero `salon_open`/`contact_action` events; the full search→click→detail cycle fires `salon_open` exactly once (correct shape, `source: "search_list"`), with no duplicate on detail-page mount. T-056 restoration re-confirmed live: search → open a salon → Back — cards restored, zero errors. Live CLS measured at 0.0029, matching the isolated measurement exactly.

```text
T-066 regressions: 0
```

## T-067 — Visual Baseline Consistency & Beta Baseline Verification

**Scope:** `components/CookieConsent.tsx`, `app/[locale]/privacy/page.tsx`, `app/[locale]/cookies/page.tsx`, `app/[locale]/not-found.tsx`, `components/MapView.tsx` (overlay chrome only), plus `package.json`'s test script. The final consistency pass of Visual Baseline v1 — no new surfaces, no product behaviour, no analytics changes.

**Ticket identity:** T-067 was confirmed genuinely unused before branching — no collision. T-063 (Map Accessibility) remains reserved and untouched; see the explicit boundary note below.

### Cookie consent UI

Direction B tokens applied. The `×` glyph became a Lucide `X` with its existing accessible name preserved, and every control gained `focus-ring-token` (previously there was no visible focus state at all).

**The one deliberate non-change, now enforced:** Accept and Reject share a *single* class constant rather than two matching literals. Equal visual weight between the two choices is a legal requirement, not a style preference — a more prominent "Accept" is the consent dark pattern that EDPB guidance and GDPR Art. 4(11) ("freely given") treat as invalidating consent. The constant carries a neutral surface, never a brand fill, since brand-filling either side tilts the pair. A pre-existing T-018 test already asserted this; it located the buttons by matching two inline `className="…"` literals, so the refactor to a shared constant broke its *locator* while strengthening the *guarantee*. The test was updated to accept either form and additionally assert the shared constant contains no `bg-brand` — the same "update how it locates, never what it checks" discipline used in T-064/T-065.

Consent logic is untouched: `getAnalyticsConsent`/`setAnalyticsConsent`/`isAnalyticsConsentFeatureEnabled` wiring, the Escape-closes-settings-only rule, and the initial `'hidden'` state are byte-identical. `lib/consent.ts` and `lib/analytics.ts` were not modified at all.

### Legal pages

Both pages moved to `max-w-shell-reading` — T-060 defined that 768px token with legal pages as its stated use case, so this is the swap it was created for. Tokens and the typography scale applied throughout; the cookie→privacy cross-link gained a focus ring.

**A regression found and fixed by this ticket's own sweep:** raising the `h1` from `text-2xl` (24px) to `text-page-title` (28px) pushed the Russian title "конфиденциальности" — a single 19-character unbreakable token — past the 320px viewport. Caught by the isolated breakpoint sweep, not by any test, and precisely located by comparing `scrollWidth` against `clientWidth` per element (the element *boxes* all measured within the viewport; only the text content overflowed, so a bounding-rect check alone reported nothing). Fixed with `break-words` on `<main>`: `overflow-wrap` is an inherited property, so one declaration covers the headings and every paragraph, including body literals like `_ga/_ga_<container-id>` and `«/account/messages»` that would overflow the same way. `hyphens-auto` was added alongside it for cleaner break points — `<html lang>` is correctly set per locale, so hyphenation dictionaries apply, with `break-words` remaining the guaranteed fallback. A regression test now pins the class.

### MapView overlay — and the T-063 boundary

Overlay chrome only: the status pill, the selected-salon preview card, and its two action links. Leaflet marker creation, popup binding, clustering, centre/zoom, and the preview link's navigation semantics (including the plain-`<a href>` behaviour T-056 documented as a known limitation) are all untouched. **No keyboard handlers and no `tabIndex` were added to any map internal** — that is T-063's scope and was deliberately not started; a test asserts their continued absence so this boundary cannot erode silently.

**Two more hardcoded-locale bugs found, the third and fourth of this class:** after T-064's `Όλες οι αξιολογήσεις` and T-066's `+7 φωτογραφίες`, the sweep found `📍 Εντοπισμός τοποθεσίας...` (the geolocation status pill) and `📍 Η θέση σας` (the user-location marker tooltip, bound through Leaflet's `bindTooltip`) — both hardcoded Greek rendered in all four locales. Fixed with new `locating_position` / `your_location` keys across all four locales. This makes four instances of the same bug found in four consecutive tickets, in four different files, which is the strongest argument yet that the pattern is systemic rather than incidental.

The quick-dial link was an **emoji-only control (`📞`) with no text and no `aria-label` — no accessible name whatsoever**. Swapping the emoji for a Lucide icon forced the fix: it now reuses the existing `callSalon` string rather than adding a key. The preview close button likewise had no accessible name (bare `×`) and gained `close_preview`.

The user-location marker's blue (`#2563eb`/`#3b82f6`) was deliberately **not** tokenised to brand pink: blue is the cross-product convention for "your location" and must stay visually distinct from the pink salon markers. It is recorded below as an intentional exception, not outstanding debt.

### Test coverage gap — the most consequential finding

`npm test` enumerated **38 test files by hand while 45 existed on disk.** The seven omitted files were `homepage.test.ts`, `searchShellVisual.test.ts`, `SalonCardVisual.test.tsx`, `salonDetailVisual.test.ts`, `CategoryGrid.test.tsx`, `AreaGrid.test.tsx`, and `SearchBar.test.tsx` — that is, **every visual regression suite created by T-062, T-064, T-065 and T-066 had never run in CI.** Each of those tickets ran its suite manually via an explicit path list and correctly reported it green, and each PR's CI was also genuinely green — but CI was green on a subset, and nothing in the process would have revealed the divergence. Declaring a Beta Visual Baseline on top of that would have meant declaring it on unverified regression coverage.

Fixed by replacing the hardcoded list with filesystem discovery (`find … -print0 | xargs -0 node --import tsx --test`; Node 18 does not support globs in `--test`, and npm runs scripts under `sh`, so shell globstar is unavailable). `xargs` propagates a non-zero exit, so a failing suite still fails CI — verified explicitly. Suite count went **856 → 1020** on the same commit, purely from files that were always there. A guard test now fails if the script ever returns to enumerating individual files.

### Findings recorded, deliberately not "fixed"

Three items were surfaced by the audit and left alone on purpose, each pinned by a test so it cannot spread unnoticed:

- **The 404 page is not what users actually see.** `app/[locale]/not-found.tsx` was restyled and is correct if reached, but there is no root `app/not-found.tsx`, so unmatched paths (`/zz`, `/zz/search`) render Next.js's built-in unstyled error page — verified live. Adding a root 404 requires an i18n decision (which locale for a prefix-less URL?) that belongs in its own ticket. Separately, `/en/salons/<nonexistent>` returns **HTTP 200** with an in-page "not found" state — a pre-existing soft-404 with SEO implications, out of scope here. A test asserts the root file's continued absence so the note stays truthful.
- **`components/SearchFilters.tsx` is dead code** (zero imports, first noted in T-007). Left on legacy tokens deliberately — restyling dead code implies it ships. A test fails if anything starts importing it.
- **`SalonCard`'s `♀`/`♂` category glyphs** render as text. Replacing them is a product decision (what the marker means, how to name it for screen readers), not a token swap. A test pins them to the `CATEGORY_GENDER` map so they cannot spread.

The rating filter's `★` inside `<option>` is **not** a missed migration: `<option>` may contain text only, so an SVG icon cannot be nested there. A test asserts `★` appears only on `<option>` lines.

### Scope boundary — what this pass did not sweep

Auth, dashboard, admin and account pages (~394 legacy colour utilities across 12 files) were **not** migrated. Visual Baseline v1 was scoped to the conversion funnel plus shared chrome and legal/consent surfaces; those pages are a separate, larger surface with their own flows and were never in this phase. They are listed under known remaining patterns below.

### Verification

51 new tests in `lib/visualBaselineConsistency.test.ts`; 1 pre-existing T-018 test updated (locator only). Full suite **1071/1071 passing** — and, for the first time, that number reflects every test file in the repository. Lint clean (the two remaining warnings, an `<img>` hint and an `exhaustive-deps` note in `reset-password/page.tsx`, are both pre-existing and in files this ticket did not touch). `next build` clean; bundle flat (`/privacy` 4.21kB, `/cookies` 4.22kB, `/search` 9.58kB).

Isolated Playwright: 32 combinations (4 locales × {privacy, cookies} × {320, 375, 768, 1440}px) — zero horizontal overflow, exactly one `<h1>`, `#main-content` landmark present, reading measure confirmed at 768px, zero console/page errors. Consent gating re-verified with consent absent: **zero** requests to `google-analytics.com`/`googletagmanager.com`, and neither `window.dataLayer` nor `window.gtag` defined.

**Live production verification (`https://lookla.gr`, 2026-07-30, post-deploy):**

- **Legal pages — 48 combinations** (4 locales × {privacy, cookies} × {320, 375, 390, 768, 1024, 1440}px): zero horizontal overflow, reading measure confirmed at exactly 768px, exactly one `<h1>`, `#main-content` present, zero console/page errors. The Russian/Ukrainian long-compound case that overflowed pre-fix now wraps correctly at 320px.
- **Homepage + search — 48 combinations**: zero overflow, zero console errors, in all four locales.
- **Consent, denied path:** with no choice made, **zero** requests to `google-analytics.com`/`googletagmanager.com`. After clicking Reject: still zero, cookie written as `lookla_consent=0`.
- **Equal-weight requirement, verified in the live DOM:** Reject and Accept render **byte-identical `className` strings**, both 44px tall with `focus-ring-token`; the only difference is intrinsic text width (146px vs 150px).
- **Consent, settings mode:** `role="dialog"` with `aria-label="Cookie settings"`; the close control carries `aria-label="Close"`, renders an inline SVG (Lucide, no glyph), and has a focus ring; Escape closes it.
- **Consent withdrawal:** after switching the cookie to rejected mid-session, a subsequent card activation fired **no product events at all**.
- **Analytics dedup and payloads:** `search_results_view` fires exactly once on load and **zero** times on Back-restoration (T-058 holding). `salon_open` fires exactly once (`{salon_id:"12608", source:"search_list", locale:"en"}`). One phone click → exactly one `contact_action`; one WhatsApp click → exactly one. PII scan across every captured payload (phone digits, `wa.me`, external URLs, salon name, Greek address): **clean**.
- **T-056 restoration:** 48 cards loaded via scroll, then Back → cards restored and **scroll restored exactly** (9059 → 9059). *Methodology note worth keeping:* an earlier run reported `scrollY=0` and looked like a regression. It was the test's fault — clicking the *first* card makes Playwright scroll the element into view (to the top) before dispatching, so the snapshot legitimately captured 0. Clicking a card already in view restores correctly. The same flaw was present in T-066's script, which is why that ticket's smoke also recorded 0; scroll restoration was never actually broken.
- **MapView, all four locales:** Leaflet renders with 2000 markers; no `📍`/`📞` emoji anywhere; the previously hardcoded Greek strings appear **only** on the Greek locale (where they are the correct translation) and are absent on en/ru/uk. Marker `tabindex` is present on all 2000 markers — that is **Leaflet's own native default, not added by T-067** (a source test asserts `MapView.tsx` adds no `tabIndex`), so marker keyboard behaviour is unchanged and T-063's scope remains untouched.
- **Salon detail, all four locales:** the T-066 gallery fix holds — 3 tiles on one row, `+N photos` correctly localized (`+7 φωτογραφίες` / `+7 photos` / `+7 фото`), one `<h1>`, no overflow. CLS 0.0029–0.0044.
- **Shared async states:** with `/api/salons` forced to 500, `role="alert"` and `role="status"` both present, the Retry control renders correctly localized in all four locales, and no legacy palette classes appear.
- **Legal metadata:** titles unchanged and locale-correct.
- **Deployed commit's test command:** `npm test` on `c3fc0fc` runs **1071/1071 passing across 192 suites** — the full suite, not the former 856-test subset.

### Beta Visual Baseline — status

**Started.** Taken from Docker's own `beauty_web` `State.StartedAt` (a verifiable record rather than a hand-entered time), following the successful smoke above:

```text
Beta Visual Baseline began:
2026-07-30 11:39:31 Europe/Athens (EEST)
```

Deliberately **not** the merge time (`c3fc0fc`, 08:09 UTC) and **not** the build-start time. From this timestamp onward:

> Post-refresh conversion data is part of the official Beta Visual Baseline.

Everything recorded before it:

> Analytics are valid for instrumentation and preliminary observations only.

```text
T-067 regressions: 0
```

**Visual Baseline v1 is officially complete.**

## Known remaining legacy patterns (unchanged by T-059, listed for later tickets)

- 641 literal Tailwind colour-utility occurrences across `app`/`components` (e.g. `text-pink-600` ×47, `bg-gray-50` ×41) — none swept; each surface's own ticket migrates its own occurrences.
- 4 border-radius patterns in simultaneous use (`rounded`, `rounded-lg`, `rounded-xl`, `rounded-2xl`) plus `rounded-full` — not consolidated.
- 5 shadow patterns (`shadow-sm` ×13, `shadow` ×2, `shadow-md` ×1, `shadow-lg` ×3, `shadow-xl` ×1) — not consolidated.
- 32 `focus:ring-2` / 36 `focus:ring-pink-*` occurrences — not migrated to `.focus-ring-token`.
- 3 unique literal hex colours outside the token system (`#2563eb`, `#3b82f6`, `#db2777`) — not removed.
- ~118 raw emoji/symbol-range character occurrences across 21 files — Header's original 2 removed by T-059, plus 2 more (mobile nav 💇💅) removed by T-060; see the icon migration table above for full disposition.
- ~~Header mobile-menu touch target is 40×40px~~ — **fixed by T-060** (now 44×44).
- ~~`/search` has zero `<header>`/banner landmark~~ — **fixed by T-060's unification pass**: `/search` now renders the shared `Header` (`variant="search"`) with `role="banner"`.
- ~~No sitewide `<main>` landmark~~ — **fixed by T-060's unification pass** on the 6 pages it unified (homepage, search, salon detail, privacy, cookies, masters); each now owns exactly one `<main id="main-content">`. Dashboard/account/admin/login/register/pricing/etc. still have none — deferred to their own future tickets (unchanged status, just no longer conflated with the shell pages above).
- ~~Homepage `SearchBar.tsx` overflows horizontally at 320px~~ — **fixed by T-062** (root cause: missing `min-w-0` on the flex-item input; see the T-062 section above).
- ~~Homepage emoji-driven category identity and false "Book online" claim~~ — **fixed by T-062**.
- 10 category icon mappings are necessarily approximate (`lucide-react` has no literal "nail polish"/"razor" glyph — see the T-062 section above) — decorative-only, not misleading, not planned for further iteration unless a better-fitting icon set is adopted product-wide.
- No homepage photography exists — the T-062 hero uses a non-photographic composition by design (no licensed asset was available; see the T-062 imagery-decision writeup). Real homepage photography is an open, unscheduled future content task.

## Protected contracts — explicitly verified unaffected

Search (query submission, filter behaviour, List/Map URL state, result count, infinite scroll, T-056 restoration), SalonCard (single outer link, accessible name, all data fields, `salon_open`, conditional price/verified — as of T-065, these are contracts *preserved through a visual refresh*, not an untouched file — see below), Salon detail (contact destinations, `contact_action`, service/review loading, opening-hours logic), analytics/consent (GA4 event names and parameters, consent gating, cookie behaviour, T-058 deduplication), and accessibility (landmark structure, accessible names, `aria-expanded`/`aria-pressed`, keyboard interactions, 44px touch targets, async-state roles, focus restoration) — none of these contracts were broken by any page-content file, across T-060's two rounds, T-062, T-064, or T-065. The T-060 unification fix touched `search/page.tsx` and `SalonDetailClient.tsx` strictly at the chrome boundary. T-062 touched only `page.tsx`/`SearchBar.tsx`/`CategoryGrid.tsx`/`AreaGrid.tsx`/`Icon.tsx`. T-064 touched `search/page.tsx`'s render section and `ActiveFilterChips.tsx`'s presentation only (state/effects/handlers block byte-for-byte unmodified) — `MapView.tsx` and `SalonCard.tsx` were not touched at all under T-064. **T-065 is the first ticket to modify `SalonCard.tsx` itself** — its own `handleOpen`/`buildCardAriaLabel` logic, the `salon_open` call site and parameter shape, the accessible-name-building strategy, and every conditional-rendering gate (price, verified, status) are all byte-for-byte unchanged; only surrounding JSX/className (tokens, icons, image-fallback state) changed. `MapView.tsx` and `SalonDetailClient.tsx` remain untouched by T-065. Confirmed by: (1) the full pre-existing T-042/T-054–T-064 test suites passing unchanged (975/975 total after T-065's own new/updated tests — several T-055-era and one T-015-era assertion needed their literal-string/fixed-offset markers updated to locate the same guarantee inside the refreshed markup, including fixing comment-vs-code false positives introduced by T-065's own new JSDoc prose, not a weakening of what they check), since no protected source file's logic was modified; (2) isolated Playwright verification across all 6 unified-shell pages (T-060), the homepage (T-062), the search page (T-064), and now SalonCard specifically across 24 breakpoint×locale combinations plus DOM-integrity/accessible-name/focus/image-state/reduced-motion/keyboard/analytics/T-056-restoration checks (T-065) — all showing zero console/hydration errors and no regression beyond each ticket's own intended changes.
