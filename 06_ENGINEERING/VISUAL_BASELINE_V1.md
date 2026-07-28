# Visual Baseline v1 — foundation specification

**Status:** foundation laid by T-059 (tokens, typography, icon system). Not yet the complete Visual Baseline — page-level surfaces are consumed by later, independently reviewable tickets. Do not treat this document as "Visual Baseline v1 complete."

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
| Header (full: logo colour, nav links, desktop CTA colours) | Header/footer global-shell ticket | T-059 only touched the menu icon glyph |
| Footer | Header/footer global-shell ticket | Untouched by T-059 |
| Homepage (hero, category/area tiles, "how it works") | Homepage visual refresh | Untouched by T-059; includes the "Book" step copy fix flagged by the audit |
| Search shell (toolbar, filter popover, results heading, List/Map, active-filter chips) | Search shell visual refresh | Untouched by T-059; includes fixing the hardcoded Greek `Όλες οι αξιολογήσεις` rating-filter placeholder (known bug, bundled here per the user's own direction) |
| SalonCard | SalonCard visual refresh | Untouched by T-059 |
| Salon detail (7-box consolidation, CTA hierarchy, gallery) | Salon detail visual refresh | Untouched by T-059; includes fixing the hardcoded Greek `+N φωτογραφίες` overlay (known bug, bundled here per the user's own direction) |
| Cookie consent UI, legal pages, remaining AsyncSection states | Shared async/legal/cookie alignment + final consistency pass | Untouched by T-059 |

## Known remaining legacy patterns (unchanged by T-059, listed for later tickets)

- 641 literal Tailwind colour-utility occurrences across `app`/`components` (e.g. `text-pink-600` ×47, `bg-gray-50` ×41) — none swept; each surface's own ticket migrates its own occurrences.
- 4 border-radius patterns in simultaneous use (`rounded`, `rounded-lg`, `rounded-xl`, `rounded-2xl`) plus `rounded-full` — not consolidated.
- 5 shadow patterns (`shadow-sm` ×13, `shadow` ×2, `shadow-md` ×1, `shadow-lg` ×3, `shadow-xl` ×1) — not consolidated.
- 32 `focus:ring-2` / 36 `focus:ring-pink-*` occurrences — not migrated to `.focus-ring-token`.
- 3 unique literal hex colours outside the token system (`#2563eb`, `#3b82f6`, `#db2777`) — not removed.
- ~118 raw emoji/symbol-range character occurrences across 21 files — only the Header's 2 removed; see the icon migration table above for full disposition.
- **Header mobile-menu touch target is 40×40px, short of 44×44** (found during T-059's live production verification, 2026-07-28). Confirmed pre-existing and byte-identical before/after T-059's icon migration (`git show` comparison: the old inline `w-6 h-6` SVG inside `p-2` padding produces the same 40px math as the new `Icon size={24}` swap) — not a regression, out of T-059's scope (a glyph-source swap, deliberately not a sizing change). Concrete input for the Header/Footer & Global Shell ticket.

## Protected contracts — explicitly verified unaffected

Search (query submission, filter behaviour, List/Map URL state, result count, infinite scroll, T-056 restoration), SalonCard (single outer link, accessible name, all data fields, `salon_open`, conditional price/verified), Salon detail (contact destinations, `contact_action`, service/review loading, opening-hours logic), analytics/consent (GA4 event names and parameters, consent gating, cookie behaviour, T-058 deduplication), and accessibility (landmark structure, accessible names, `aria-expanded`/`aria-pressed`, keyboard interactions, 44px touch targets, async-state roles, focus restoration) — none of these were touched by any file this ticket changed. Confirmed by: (1) the full pre-existing T-042/T-054/T-055/T-056/T-057/T-058 test suites passing unchanged (775/775 total after T-059's own 96 new tests), since none of their source files were modified; (2) isolated Playwright verification against real production pages (homepage, search) showing zero console/hydration errors and no visual regression beyond the intended font change.
