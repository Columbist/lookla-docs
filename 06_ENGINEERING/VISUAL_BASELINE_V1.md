# Visual Baseline v1 — foundation specification

**Status:** foundation laid by T-059 (tokens, typography, icon system), T-060 (global shell: header, footer, mobile navigation, language selector), and T-062 (homepage). Not yet the complete Visual Baseline — search shell, SalonCard, and salon-detail content are consumed by later, independently reviewable tickets. Do not treat this document as "Visual Baseline v1 complete."

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

Search (query submission, filter behaviour, List/Map URL state, result count, infinite scroll, T-056 restoration), SalonCard (single outer link, accessible name, all data fields, `salon_open`, conditional price/verified), Salon detail (contact destinations, `contact_action`, service/review loading, opening-hours logic), analytics/consent (GA4 event names and parameters, consent gating, cookie behaviour, T-058 deduplication), and accessibility (landmark structure, accessible names, `aria-expanded`/`aria-pressed`, keyboard interactions, 44px touch targets, async-state roles, focus restoration) — none of these were touched by any page-content file, across T-060's two rounds or T-062. The T-060 unification fix touched `search/page.tsx` and `SalonDetailClient.tsx` strictly at the chrome boundary (inline header/logo → `<Header variant="..." />`, `div`→`main` retag, no class changes below that boundary — confirmed via `git diff`). T-062 touched only `page.tsx`/`SearchBar.tsx`/`CategoryGrid.tsx`/`AreaGrid.tsx`/`Icon.tsx` — none of which any other protected surface imports or depends on; `area_select`'s call site lives in `AreaGrid.tsx`, re-verified byte-identical in shape and call count. Confirmed by: (1) the full pre-existing T-042/T-054–T-060 test suites passing unchanged (905/905 total after T-062's own new tests — the 320px `SearchBar.tsx` finding that used to be the sole non-pass is now genuinely fixed, not just documented), since none of their protected source files were modified; (2) isolated Playwright verification across all 6 unified-shell pages (T-060) and, for T-062, all 4 locales × 6 breakpoints of the homepage specifically, plus live-equivalent re-verification of search initial load, T-056 Back-restoration, the search map view's unchanged width, and `area_select` firing exactly once — all showing zero console/hydration errors and no regression beyond each ticket's own intended changes.
