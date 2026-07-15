---
title: Frontend Architecture
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 04_ARCHITECTURE/API_SPECIFICATION.md
  - 03_PAGES/HOME.md
  - 03_PAGES/SEARCH.md
  - 03_PAGES/SALON.md
  - 02_DESIGN/UX_FLOWS.md
  - 06_ENGINEERING/AUDIT.md
implementation_status: Describes current implementation + MVP-required changes
---

# Frontend Architecture
**Lookla Beauty Marketplace**

> **Approved.** Describes the current Next.js 14 frontend as deployed, plus required changes for MVP launch.

---

## 1. Technology Stack

| Component | Technology | Notes |
|---|---|---|
| Framework | Next.js 14 (App Router) | No Pages Router; App Router throughout |
| Styling | Tailwind CSS 3 | Utility-first; no CSS modules |
| i18n | next-intl | 4 locales: el, en, ru, uk |
| Map | Leaflet + react-leaflet | Dynamic import (no SSR) |
| Icons | — | Tailwind + SVG inline; no icon library confirmed |
| UI primitives | Custom (shadcn-style) | `components/ui/` — buttons, inputs, etc. |
| TypeScript | Yes | Strict mode not enforced; `as any` casts present |
| Analytics | GA4 (to be added) | DEC-017 — required before MVP launch |

---

## 2. App Router Structure

**All routes are under the `[locale]` dynamic segment.** The locale prefix determines language.

```
frontend/
├── app/
│   ├── layout.tsx                    # Root layout: HTML, body, fonts
│   └── [locale]/
│       ├── layout.tsx                # Locale layout: next-intl provider, Header, Footer
│       ├── page.tsx                  # Homepage (SSR)
│       ├── search/
│       │   └── page.tsx              # Search (CSR via client component)
│       ├── salons/
│       │   └── [slug]/
│       │       └── page.tsx          # Salon detail (SSR metadata + CSR body)
│       ├── about/
│       │   └── page.tsx              # About (SSR static) — NEW, required for MVP
│       ├── contact/
│       │   └── page.tsx              # Contact (SSR static) — NEW, required for MVP
│       ├── admin/
│       │   └── page.tsx              # Admin panel (CSR, role-gated)
│       ├── account/
│       │   └── page.tsx              # User profile (CSR, auth-gated)
│       ├── dashboard/
│       │   ├── salon/
│       │   │   └── page.tsx          # Owner salon management (CSR, role-gated)
│       │   └── master/
│       │       └── page.tsx          # Professional profile (CSR, role-gated)
│       ├── login/
│       │   └── page.tsx              # Login (CSR)
│       ├── register/
│       │   └── page.tsx              # Register (CSR)
│       ├── pricing/
│       │   └── page.tsx              # EXISTS — must not be linked per DEC-006
│       └── masters/
│           └── page.tsx              # Professional listing (CSR)
├── components/
│   ├── Header.tsx
│   ├── SalonCard.tsx
│   ├── SalonHours.tsx
│   ├── SearchBar.tsx
│   ├── SearchFilters.tsx
│   ├── CategoryGrid.tsx
│   ├── CityGrid.tsx                  # → to be renamed AreaGrid.tsx (DEC-010)
│   ├── MapView.tsx
│   ├── ContactButtons.tsx
│   ├── ReportButton.tsx
│   ├── LanguageSwitcher.tsx
│   └── ui/                           # UI primitives (Button, Input, Modal, etc.)
├── lib/
│   ├── api.ts                        # API client + TypeScript interfaces
│   └── locale.ts                     # NEW: localePrefix() utility (replaces 8× inline pattern)
├── hooks/
│   ├── useMe.ts                      # NEW: extract from 4 pages; GET /api/auth/me
│   └── useAnalytics.ts               # NEW: GA4 event helpers (DEC-017)
├── messages/
│   ├── el.json                       # Greek translations
│   ├── en.json                       # English translations
│   ├── ru.json                       # Russian translations
│   └── uk.json                       # Ukrainian translations
└── i18n/
    └── routing.ts                    # next-intl config: locales, defaultLocale='el'
```

---

## 3. Routing

**Locale prefix pattern:**
- Default locale (Greek): `lookla.gr/` or `lookla.gr/el/` — both work
- Non-default locales: `lookla.gr/ru/search`, `lookla.gr/en/salons/[slug]`

**Current code pattern (to be replaced by utility):**
```typescript
// Repeated verbatim in 8+ files — replace with localePrefix()
const prefix = locale === 'el' ? '' : `/${locale}`;
```

**After extraction:**
```typescript
// lib/locale.ts
export function localePrefix(locale: string): string {
  return locale === 'el' ? '' : `/${locale}`;
}
```

**Dynamic segments:**
- `[locale]` — language prefix; validated by next-intl against `['el', 'en', 'ru', 'uk']`
- `[slug]` — salon URL slug; fetched from `/api/salons/{slug}`

**Route protection:**
- `/admin` — check `role === 'admin'` in component; redirect to `/login` if not
- `/dashboard` — check authenticated; redirect to `/login` if not
- `/account` — check authenticated; redirect to `/login` if not
- All other routes — fully public (DEC-016)

---

## 4. Layouts

**Root layout** (`app/layout.tsx`):
- Sets `<html lang>` attribute based on locale
- Loads root CSS (Tailwind globals)
- GA4 script tag (DEC-017 — add here before MVP launch)

**Locale layout** (`app/[locale]/layout.tsx`):
- Wraps content in `next-intl` `NextIntlClientProvider`
- Renders `<Header>` and `<Footer>` around `{children}`
- `Header` contains: Logo, LanguageSwitcher, Login/Register links
- `Footer` contains: About, Contact, Privacy links + secondary LanguageSwitcher

**Render mode:** Both layouts are Server Components. They do not fetch user data. Auth state is loaded client-side via `useMe()` hook inside components that need it.

---

## 5. Render Strategy per Page

| Route | Strategy | Reason |
|---|---|---|
| `/` (homepage) | SSR | Category + area data fetched server-side; SEO critical |
| `/search` | CSR | Highly interactive (filters, infinite scroll, map toggle) |
| `/salons/[slug]` | SSR (metadata) + CSR (body) | SSR for OG tags and title; CSR for services/reviews lazy load |
| `/about` | SSR | Static content; SEO |
| `/contact` | SSR | Static content |
| `/admin` | CSR | Internal tool; no SEO needed |
| `/account` | CSR | Auth-gated; no SEO |
| `/dashboard/*` | CSR | Auth-gated; no SEO |
| `/login`, `/register` | CSR | No SEO needed |

**SSR data fetching pattern:**
```typescript
// app/[locale]/salons/[slug]/page.tsx
export async function generateMetadata({ params }) {
  const salon = await fetch(`/api/salons/${params.slug}`).then(r => r.json());
  return { title: `${salon.name} | Lookla`, description: ... };
}

export default async function SalonPage({ params }) {
  const salon = await fetch(`/api/salons/${params.slug}`).then(r => r.json());
  return <SalonDetailClient initialData={salon} />;
}
```

---

## 6. Component Architecture

### Shared Components

**Server Components** (can be): layouts, static sections, metadata generators

**Client Components** (must be): anything with `useState`, `useEffect`, `IntersectionObserver`, event handlers, `useTranslations` (client-side)

**Current god component to split (Audit §21, Priority 4):**

`SalonDetailClient.tsx` contains:
- Lazy loading hook (IntersectionObserver)
- Photo carousel
- Services section + translation badge
- Reviews section + translation badge + Google source label
- Hours display
- Contact buttons
- Map embed
- Social links
- Report button

**Target split (MVP-compatible, not required for launch):**
```
SalonDetailClient.tsx (coordinator)
├── <SalonPhotos />          photos carousel
├── <SalonIdentity />        name, category, open/closed, badge
├── <ContactButtons />       already extracted — ensure DEC-015 compliant
├── <SalonAbout />           description, address, hours
├── <SalonServices />        lazy-loaded, translated
├── <SalonReviews />         lazy-loaded, translated, Google source label
├── <SalonMap />             Leaflet embed
└── <ReportButton />         already extracted
```

Splitting is recommended for maintainability; not a launch blocker.

---

## 7. Hooks

### Existing (inline, to be extracted)

**`useMe`** — Appears inline in 4 pages as:
```typescript
const [user, setUser] = useState(null);
useEffect(() => {
  fetch('/api/auth/me').then(r => r.ok ? r.json() : null).then(setUser);
}, []);
```

Extract to `hooks/useMe.ts`:
```typescript
export function useMe() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    fetch('/api/auth/me')
      .then(r => r.ok ? r.json() : null)
      .then(u => { setUser(u); setLoading(false); });
  }, []);
  return { user, loading };
}
```

### New (required for MVP)

**`useAnalytics`** — GA4 event helpers (DEC-017):
```typescript
// hooks/useAnalytics.ts
export function useAnalytics() {
  const trackContactAction = (type: 'phone' | 'whatsapp' | 'website', salonId: number, salonName: string) => {
    window.gtag?.('event', 'contact_action', {
      action_type: type,
      salon_id: salonId,
      salon_name: salonName,
    });
  };
  return { trackContactAction };
}
```

Used inside `<ContactButtons>` for DEC-008 success metric tracking.

### Existing (already correct)

**IntersectionObserver hook pattern** — used in:
- `search/page.tsx` (infinite scroll sentinel)
- `SalonDetailClient.tsx` (lazy section loader)

Both use `useRef` correctly to avoid stale closures. Do not refactor without testing.

---

## 8. API Layer

**`lib/api.ts`** — central API client:

```typescript
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '';

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    cache: 'no-store',           // Disables Next.js ISR — intentional for dynamic data
    credentials: 'include',      // Sends httpOnly auth cookies
    ...options,
  });
  if (!res.ok) throw new ApiError(res.status, await res.text());
  return res.json();
}
```

**TypeScript interfaces** for API responses are defined in `lib/api.ts`. These are the client-side contract with the backend.

**Caching strategy:**
- Currently: `cache: 'no-store'` on all requests — correct for auth-sensitive and real-time data
- For static data (categories, areas): change to `cache: 'force-cache'` or `next: { revalidate: 3600 }` in SSR fetches

---

## 9. Caching Strategy

| Data | Current | Recommended |
|---|---|---|
| Salon detail (SSR) | `no-store` | Keep `no-store` — hours/open-closed changes |
| Search results | `no-store` (CSR) | Keep — filters change per request |
| Categories list | `no-store` | `revalidate: 86400` — changes rarely |
| Areas list (new) | — | `revalidate: 86400` — static for MVP |
| Photos | — | Served from R2 CDN via Cloudflare; Cloudflare caches at edge |
| Translation results | — | Cached in DB (not at HTTP layer) |

**No Redis caching in API layer.** Future: add Redis for expensive repeated queries (search with common params). Not needed for MVP traffic levels.

---

## 10. Loading States

**Pattern:** Skeleton placeholders using `animate-pulse` Tailwind class.

**Current state:** Inline in each page — not extracted to a shared component.

**MVP minimum:** Skeletons must exist on:
- Search page (card grid placeholder while first load completes)
- Salon detail services section (lazy load pending)
- Salon detail reviews section (lazy load pending)

**Recommended extraction (not a launch blocker):**
```typescript
// components/ui/Skeleton.tsx
export function Skeleton({ className }: { className?: string }) {
  return <div className={`animate-pulse bg-gray-200 rounded ${className}`} />;
}
```

---

## 11. Error Boundaries

**Current state:** No React error boundaries implemented. A runtime error in a client component crashes the visible page.

**Minimum for MVP:** Add error boundary around the main content area of search and salon detail pages:

```typescript
// Must be a class component or use 'react-error-boundary' package
<ErrorBoundary fallback={<div>Something went wrong. <a href="/">Go back</a></div>}>
  <SalonDetailClient ... />
</ErrorBoundary>
```

**Pattern for API errors in components:**
```typescript
const [error, setError] = useState<string | null>(null);
// ... in fetch:
.catch(() => setError('Could not load services. Try refreshing.'));
// ... in render:
if (error) return <p className="text-red-500">{error}</p>;
```

---

## 12. Responsive Strategy

**Approach:** Mobile-first with Tailwind breakpoints.

| Breakpoint | Screen | Usage |
|---|---|---|
| (none) | Mobile < 640px | Default styles; full-width layout |
| `sm:` | 640px+ | 2-column grids |
| `md:` | 768px+ | Sidebar layouts; horizontal filters |
| `lg:` | 1024px+ | 3-column card grids; max-w-6xl container |

**Components requiring mobile verification before MVP:**
- Salon detail: contact buttons must be full-width and above-fold on 375px
- Search filters: must collapse into bottom sheet on mobile
- Language switcher: must be visible in header on mobile without scrolling
- Review source label: must be visible on mobile (not hidden/collapsed)

**Not targeted for MVP:** `xl:` and `2xl:` breakpoints. Desktop cap at `max-w-6xl`.

---

## 13. Internationalisation (i18n)

**Library:** `next-intl`

**Supported locales:** `el` (default), `en`, `ru`, `uk`

**Message files:** `messages/{locale}.json` — flat key structure.

**Usage in Server Components:**
```typescript
import { getTranslations } from 'next-intl/server';
const t = await getTranslations('HomePage');
```

**Usage in Client Components:**
```typescript
import { useTranslations } from 'next-intl';
const t = useTranslations('SearchPage');
```

**Locale detection:** URL prefix is the source of truth. `next-intl` middleware reads `[locale]` segment and sets context. No cookie-based detection.

**Missing translations handling:** If a key is missing in a non-Greek locale, `next-intl` falls back to the key string (not the Greek value). Ensure all keys are present in all 4 message files before MVP launch.

**DEC-011 reminder:** el/en/ru are mandatory quality. uk ships but is lower QA priority — verify all uk keys exist even if copy is imperfect.

---

## 14. SEO

**SSR metadata (current, correct):**
```typescript
export async function generateMetadata({ params }) {
  return {
    title: `${salon.name} — ${category} in ${district} | Lookla`,
    description: `...`,
    openGraph: { images: [primaryPhoto] },
    alternates: { canonical: `https://lookla.gr/${locale}/salons/${slug}` },
  };
}
```

**Canonical URLs:** Must include locale prefix. All 4 locale versions should have `<link rel="alternate" hreflang="...">` pointing to each other.

**Robots:** Homepage, search, and salon pages should be indexable. Auth pages (`/login`, `/register`, `/dashboard`, `/admin`) should be `noindex`.

**`robots.txt`** — does not exist currently; must be created before MVP launch:
```
User-agent: *
Disallow: /admin
Disallow: /dashboard
Disallow: /account
Disallow: /login
Disallow: /register
Disallow: /pricing
Allow: /
Sitemap: https://lookla.gr/sitemap.xml
```

**`sitemap.xml`** — **correction (T-036, 2026-07-15):** this file already exists (`frontend/public/sitemap.xml`, tracked in git since the initial commit) and is live, serving ~21,900 real URLs. The "explicitly deferred" note below was stale. Note the robots.txt content above (with `Disallow: /login`, `/register`, `/pricing`) has not been implemented as-is — see T-036 in `IMPLEMENTATION_BACKLOG.md` for the canonical content actually shipped and the open SEO question this discrepancy raises.

**GA4 script placement** (DEC-017):
```typescript
// app/layout.tsx
import Script from 'next/script';

<Script
  src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"
  strategy="afterInteractive"
/>
<Script id="ga4-init" strategy="afterInteractive">
  {`window.dataLayer=window.dataLayer||[];
    function gtag(){dataLayer.push(arguments);}
    gtag('js',new Date());
    gtag('config','G-XXXXXXXXXX');`}
</Script>
```

---

## 15. Required Changes for MVP Launch

| Change | Decision | File | Complexity |
|---|---|---|---|
| Move LanguageSwitcher to Header | HOME.md spec | `Header.tsx` | Low |
| Rename CityGrid → AreaGrid; populate with Athens districts | DEC-010 | `CityGrid.tsx` | Low |
| Update area filter label (City → Area) in all 4 locales | DEC-010 | `messages/*.json`, `SearchFilters.tsx` | Low |
| Remove booking stubs from SalonDetailClient | DEC-015 | `SalonDetailClient.tsx` | Low |
| Add "Call salon" / "WhatsApp" / "Website" CTAs | DEC-015 | `ContactButtons.tsx` | Low |
| Replace ✓ badge with text label | DEC-014 | `SalonCard.tsx`, `SalonDetailClient.tsx` | Low |
| Add Google source label to reviews section | DEC-013 | `SalonDetailClient.tsx` | Low |
| Wire GA4 contact click events | DEC-017 | `ContactButtons.tsx` | Low |
| Add GA4 script to root layout | DEC-017 | `app/layout.tsx` | Low |
| Create `/about` page | ABOUT.md spec | `app/[locale]/about/page.tsx` | Low |
| Create `/contact` page | CONTACT.md spec | `app/[locale]/contact/page.tsx` | Low |
| Add About + Contact to Footer | HOME.md spec | `Footer.tsx` (or inline in locale layout) | Low |
| Extract `localePrefix()` utility | Audit §21 | `lib/locale.ts` | Trivial |
| Extract `useMe()` hook | Audit §21 | `hooks/useMe.ts` | Low |
| Add `robots.txt` | SEO spec | `public/robots.txt` | Trivial |
| Verify `/pricing` is not in navigation | DEC-006 | `Header.tsx` | Verify only |

---

*Last updated: 2026-07-09*
