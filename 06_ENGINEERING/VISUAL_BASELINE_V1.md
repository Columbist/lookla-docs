# Visual Baseline v1 — foundation specification

**Status:** foundation laid by T-059 (tokens, typography, icon system) and T-060 (global shell: header, footer, mobile navigation, language selector). Not yet the complete Visual Baseline — homepage, search shell, SalonCard, and salon-detail content are consumed by later, independently reviewable tickets. Do not treat this document as "Visual Baseline v1 complete."

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
| Homepage (hero, category/area tiles, "how it works") | Homepage visual refresh | Untouched by T-059/T-060; includes the "Book" step copy fix flagged by the audit, and the SearchBar 320px overflow found during T-060 verification (see below) |
| Search shell (toolbar, filter popover, results heading, List/Map, active-filter chips) | Search shell visual refresh | Untouched by T-059; includes fixing the hardcoded Greek `Όλες οι αξιολογήσεις` rating-filter placeholder (known bug, bundled here per the user's own direction) |
| SalonCard | SalonCard visual refresh | Untouched by T-059 |
| Salon detail (7-box consolidation, CTA hierarchy, gallery) | Salon detail visual refresh | Untouched by T-059; includes fixing the hardcoded Greek `+N φωτογραφίες` overlay (known bug, bundled here per the user's own direction) |
| Cookie consent UI, legal pages, remaining AsyncSection states | Shared async/legal/cookie alignment + final consistency pass | Untouched by T-059 |

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
- **Homepage `SearchBar.tsx` overflows horizontally at 320px** (found during T-060's live verification, 2026-07-28; re-confirmed still present and still unrelated after the unification fix) — confirmed pre-existing, byte-identical class list on current production. Flagged for the homepage visual-refresh ticket.

## Protected contracts — explicitly verified unaffected

Search (query submission, filter behaviour, List/Map URL state, result count, infinite scroll, T-056 restoration), SalonCard (single outer link, accessible name, all data fields, `salon_open`, conditional price/verified), Salon detail (contact destinations, `contact_action`, service/review loading, opening-hours logic), analytics/consent (GA4 event names and parameters, consent gating, cookie behaviour, T-058 deduplication), and accessibility (landmark structure, accessible names, `aria-expanded`/`aria-pressed`, keyboard interactions, 44px touch targets, async-state roles, focus restoration) — none of these were touched by any page-content file, in either T-060 round. The unification fix additionally touched `search/page.tsx` and `SalonDetailClient.tsx`, but strictly at the chrome boundary: one inline `<header>`/logo block replaced by a `<Header variant="..." />` call, and the results/content container's tag renamed `div`→`main` (id added, no class changes) — confirmed via `git diff` that nothing below that boundary changed. Confirmed by: (1) the full pre-existing T-042/T-054/T-055/T-056/T-057/T-058/T-059 test suites passing unchanged (851/852 total after both T-060 rounds' own new tests — the one non-pass is the pre-existing, documented, unrelated 320px `SearchBar.tsx` overflow, not a test failure), since none of their protected source files were modified beyond the chrome boundary; (2) isolated Playwright verification across all 6 unified-shell pages × multiple breakpoints plus all 4 locales, and live-equivalent re-verification of search initial load, T-056 Back-restoration, and the search map view's unchanged width, all showing zero console/hydration errors and no regression beyond the intended shell changes.
