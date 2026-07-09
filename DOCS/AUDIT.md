# Lookla — Architecture Audit
**Date:** 2026-07-09  
**Role:** Lead Software Architect (read-only analysis — zero code changes)  
**Scope:** Full-stack review of `/root/beauty-gr` as deployed on `columbxray` (10.10.0.1)

---

## 1. Technology Stack

| Layer | Technology | Version | Notes |
|---|---|---|---|
| Frontend | Next.js (App Router) | 14 | SSR + CSR hybrid |
| Styling | Tailwind CSS | 3 | Utility-first, no component library |
| i18n | next-intl | — | 4 locales: el, en, ru, uk |
| Backend API | FastAPI | — | Python 3.12 |
| ORM | SQLAlchemy | — | Synchronous (psycopg2) |
| Database | PostgreSQL | 16 | Alpine Docker image |
| Cache / Queue broker | Redis | 7 | Used by Celery crawler only |
| Crawler | Celery | — | 2-worker concurrency, 500 MB RAM cap |
| Object Storage | Cloudflare R2 | — | CDN at cdn.lookla.gr |
| Reverse Proxy | Nginx | — | SSL termination, rate limiting |
| CDN / DDoS | Cloudflare | — | Full SSL mode, Origin Certificate |
| Email | Resend | — | Transactional (verify, reset, claim) |
| Payments | Stripe | — | Subscriptions via abstract PaymentProvider |
| Error Monitoring | Sentry | — | traces_sample_rate=0.1 |
| OAuth | Google | — | RS256 JWKS verification |
| CAPTCHA | Cloudflare Turnstile | — | Key configured, frontend integration unverified |
| AI translation | OpenAI gpt-4o-mini | — | On-demand, bot-protected, DB-cached |
| Container runtime | Docker Compose | 3.9 | 6 services, host-network via 127.0.0.1 ports |

**Notable absences:** No PostGIS (Haversine in SQL), no Alembic (raw ALTER TABLE), no Redis usage in API layer (only crawler), no TypeScript strict mode enforced, no test suite of any kind.

---

## 2. Frameworks

### Backend (FastAPI)
- `slowapi` for global + per-endpoint rate limiting (`200/minute` default, `5/minute;20/hour` on register)
- `python-jose` for JWT RS256 decoding of Google tokens and HS256 for internal JWTs
- `pydantic-settings` for env-based config (`Settings` class, `lru_cache` singleton)
- `openai` (1.86.0) for translation
- Synchronous SQLAlchemy session (`get_db` dependency) — no async ORM, no connection pooling beyond SQLAlchemy defaults

### Frontend (Next.js 14)
- App Router with `[locale]` dynamic segment as the outermost route group
- `next-intl` for server and client translations (`getTranslations`, `useTranslations`)
- `dynamic(() => import(...), { ssr: false })` for Leaflet map (client-only)
- `IntersectionObserver` used in two places: infinite scroll sentinel (search) and lazy section loader (salon detail)
- Tailwind for all styling — no CSS modules, no styled-components
- No state management library; all state is local `useState` + URL search params

---

## 3. Current Project Structure

```
/root/beauty-gr/
├── backend/
│   └── app/
│       ├── core/         # config, database, deps, security
│       ├── models/       # SQLAlchemy ORM models
│       ├── routers/      # 13 FastAPI routers
│       ├── schemas/      # Pydantic schemas
│       ├── services/     # translate.py, email.py, moderation.py, media.py
│       └── main.py
├── crawler/              # Celery tasks, scrapers (vrisko, xo, beauty_project, treatwell)
│   └── (volume-mounted — live edits apply immediately)
├── db/
│   └── init.sql          # Initial schema (PostgreSQL DDL)
├── frontend/
│   ├── app/[locale]/     # All pages under locale prefix
│   ├── components/       # 11 shared components
│   ├── lib/api.ts        # API client + TypeScript interfaces
│   ├── i18n/             # Routing config (locales, defaultLocale)
│   └── messages/         # el.json, en.json, ru.json, uk.json
├── DOCS/                 # ROADMAP.md, TROUBLESHOOTING.md, AUDIT.md (this file)
├── docker-compose.yml
└── .env                  # Single shared env file for all services
```

**Critical deployment note:** `api` and `web` Docker images bake code at build time — there are no volume mounts. Every source code change requires `docker buildx build` + `docker compose up -d`. The `crawler` container IS volume-mounted, so its code is live-editable.

---

## 4. Existing Pages

| Route | Render | Description |
|---|---|---|
| `/` or `/el` | SSR | Homepage: hero search, CategoryGrid, CityGrid, "How it works" |
| `/search` | CSR | Salon list with infinite scroll + map toggle; filter panel (city, category, rating) |
| `/salons/[slug]` | SSR + CSR | Salon detail: metadata SSR, services+reviews lazy-loaded client-side |
| `/masters` | CSR | Professional listing (similar to search, separate data) |
| `/account` | CSR | User profile, role badge, logout; redirects to login if unauthenticated |
| `/dashboard` → redirects to `/dashboard/salon` | CSR | Owner panel: my salons list, claim flow (form → verify code) |
| `/dashboard/salon` | CSR | Salon management: edit profile, hours, services, photos |
| `/dashboard/master` | CSR | Professional profile management: portfolio, availability, social links |
| `/admin` | CSR | Admin panel: stats dashboard, salon moderation queue, user management |
| `/account/messages` | CSR | In-app chat (conversations list + thread) |
| `/login` | CSR | Email+password login, Google OAuth button |
| `/register` | CSR | Registration form with honeypot field |
| `/forgot-password` | CSR | Email-based password reset request |
| `/reset-password` | CSR | Token-based password reset |
| `/verify-email` | CSR | Email verification via token in query param |
| `/pricing` | CSR | Subscription plan display (Stripe checkout integration) |
| Not-found | SSR | Custom 404 page |

**Total:** 17 distinct routes (several are locale-prefixed variants of the same page).

---

## 5. Existing Components

| Component | Type | Purpose |
|---|---|---|
| `Header` | Client | Top navigation: logo, locale-aware links, auth state |
| `SalonCard` | Client | Salon list card: photo, name, address, rating, open/closed badge, min price with gender icon |
| `SalonHours` | Client | Weekly hours table with current-day highlight |
| `SearchBar` | Client | Unified search input with autocomplete-style behavior, navigates to /search |
| `SearchFilters` | Client | Filter dropdowns (city, category, rating) — used inside search page |
| `CategoryGrid` | Client | Grid of category icons/cards linking to search?category=slug |
| `CityGrid` | Client | Grid of city cards linking to search?city=name |
| `MapView` | Client | Leaflet map with salon pins; dynamically imported (no SSR) |
| `ContactButtons` | Client | Phone / WhatsApp / website action buttons on salon detail |
| `ReportButton` | Client | "Report a problem" trigger; posts to /api/reports |
| `LanguageSwitcher` | Client | Locale selector, preserves current path |
| `ui/` | Mixed | Internal UI primitives (shadcn-like buttons, inputs, etc.) |

**Inline components (not extracted):**
- `TranslatedBadge` — locale-aware "🌐 Переведено" badge, defined inside SalonDetailClient.tsx
- Skeleton loaders — `animate-pulse` divs, scattered inline in search and detail pages

---

## 6. Existing API Endpoints

### Salons (`/api/salons`)
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/salons` | No | Paginated list (24/page), filters: city, q, category, min_rating; includes open_now + min_price |
| GET | `/api/salons/map` | No | All matching salons for map view (no pagination, lat/lng only) |
| GET | `/api/salons/{id}` | No | Full salon detail; services=[], reviews=[] (lazy-loaded) |
| GET | `/api/salons/{id}/services?lang=` | No | Services with on-demand translation; returns [] for bots |
| GET | `/api/salons/{id}/reviews?lang=` | No | Reviews with on-demand translation; returns [] for bots |
| GET | `/api/salons/{id}/photos` | No | All photos for a salon |

### Search (`/api/search`)
| Method | Path | Description |
|---|---|---|
| GET | `/api/search` | Unified search: salons + (future) professionals; supports q, city, lat/lng/radius |

### Auth (`/api/auth`)
| Method | Path | Rate Limit |
|---|---|---|
| POST | `/api/auth/register` | 5/min, 20/hr |
| POST | `/api/auth/login` | — |
| POST | `/api/auth/logout` | — |
| POST | `/api/auth/refresh` | — |
| GET | `/api/auth/me` | — |
| POST | `/api/auth/forgot-password` | 3/min, 10/hr |
| POST | `/api/auth/reset-password` | — |
| POST | `/api/auth/verify-email` | — |
| GET | `/api/auth/google/start` | — |
| GET | `/api/auth/google/callback` | — |
| POST | `/api/auth/generate-password` | — |
| POST | `/api/auth/change-password` | — |

### Owner (`/api/owner`)
| Method | Path | Description |
|---|---|---|
| POST | `/api/owner/claim/request` | Send 6-char code to salon's contact |
| POST | `/api/owner/claim/verify` | Verify code, link owner, set is_verified=true |
| GET | `/api/owner/salons` | List my claimed salons |
| GET/PATCH | `/api/owner/salons/{id}` | Get/update salon profile |
| PUT | `/api/owner/salons/{id}/hours` | Replace full week schedule |
| POST/DELETE | `/api/owner/salons/{id}/services` | Add/remove services |
| POST | `/api/owner/salons/{id}/photos` | Upload photo (R2) |

### Professionals (`/api/professionals`)
| Method | Path | Description |
|---|---|---|
| GET | `/api/professionals` | Paginated list with geo filter |
| GET | `/api/professionals/{slug}` | Full detail |

### Masters (`/api/masters`)
| Method | Path | Description |
|---|---|---|
| GET/PATCH | `/api/masters/me` | Get/update professional profile |
| POST/DELETE | `/api/masters/portfolio` | Portfolio photos (R2) |
| PUT | `/api/masters/availability` | Weekly availability schedule |

### Bookings (`/api/bookings`)
| Method | Path | Description |
|---|---|---|
| GET | `/api/bookings/slots` | Available time slots for a date |
| POST | `/api/bookings` | Create appointment |
| GET | `/api/bookings` | List my bookings |
| PATCH | `/api/bookings/{id}` | Update status (confirm/cancel) |

### Chat (`/api/chat`)
| Method | Path | Description |
|---|---|---|
| POST | `/api/chat/conversations` | Start or get conversation |
| GET | `/api/chat/conversations` | List conversations |
| GET | `/api/chat/conversations/{id}/messages` | Thread messages |
| POST | `/api/chat/conversations/{id}/messages` | Send message |
| POST | `/api/chat/availability-requests` | Soft booking inquiry |
| GET | `/api/chat/availability-requests` | List requests (for salon owner) |
| POST | `/api/chat/availability-requests/{id}/propose` | Propose slot (owner response) |

### Payments (`/api/payments`)
| Method | Path | Description |
|---|---|---|
| GET | `/api/payments/plans` | List subscription plans |
| POST | `/api/payments/checkout` | Create Stripe checkout session |
| POST | `/api/payments/portal` | Create Stripe customer portal link |
| POST | `/api/payments/webhook` | Stripe webhook handler |
| GET | `/api/payments/subscription` | My current subscription |
| DELETE | `/api/payments/subscription` | Cancel subscription |

### Admin (`/api/admin`)
| Method | Path | Description |
|---|---|---|
| GET | `/api/admin/stats` | Platform stats (salons, users, bookings, reports) |
| GET/PATCH | `/api/admin/salons` | List + update salon flags (is_verified, needs_review) |
| GET | `/api/admin/professionals` | List professionals |
| GET | `/api/admin/users` | List users |
| GET/PATCH | `/api/admin/reports` | List + resolve user reports |
| GET | `/api/admin/moderation` | Moderation queue |

### Other
| Prefix | Description |
|---|---|
| `/api/categories` | Category tree with i18n names |
| `/api/cities` | City list with salon counts |
| `/api/media/photo/{id}` | Photo proxy: lazy R2 migration from Google Places URLs |
| `/api/reports` | Submit user report (requires auth) |
| `/api/health` | Health check: db connectivity |

---

## 7. Existing Database Entities

### SQLAlchemy ORM Models (code-defined)

**users** — Core auth entity  
`id, email, password_hash, name, google_id, role (user/salon_owner/professional/admin), preferred_language, is_email_verified, is_active, avatar_url, created_at`

**email_verifications** — `id, user_id, token, expires_at, used_at`

**password_resets** — `id, user_id, token, channel, expires_at, used_at`

**refresh_tokens** — `id, user_id, token_hash (SHA-256), expires_at, revoked_at`

**salons** — Primary catalog entity  
`id, name, name_el, slug, description, description_el, description_ru, description_uk, address_street/number/city/region/postal, lat, lng, phone_primary/secondary, email, website, rating_google, rating_count, price_level, is_verified, is_active, needs_review, data_verified_at, google_place_id, created_at, updated_at`

**salon_hours** — `id, salon_id, day_of_week (0=Mon), open_time, close_time, is_closed`

**photos** — `id, salon_id, url (Google Places or R2), r2_key, is_primary, width, height, caption, created_at`

**services** — Price catalog  
`id, salon_id, category_id, name, name_el, name_en, name_ru, name_uk, description, duration_min, price_from, price_to, currency, is_active`

**service_categories** — `id, name, name_el, name_en, name_ru, name_uk, slug, parent_id, icon`

**salon_categories** — Junction table: `salon_id, category_id`

**reviews** — `id, salon_id, source (google/internal), author_name, rating, text, text_el, text_en, text_ru, text_uk, published_at, is_verified`

**social_links** (salons) — `id, salon_id, platform, url`

**staff** — `id, salon_id, name, role, bio, photo_url`

**professionals** — Independent from salons  
`id, user_id, name, slug, specialty, base_city, base_lat, base_lng, service_radius_km, does_home_visits, has_home_studio, phone, email, bio, bio_el, bio_ru, bio_uk, rating_avg, review_count, price_level, is_verified, is_active, featured_photo, instagram, created_at`

**professional_portfolio** — `id, professional_id, url_after, url_before, r2_key_after, r2_key_before, caption, service_tag, is_featured`

**professional_availability** — `id, professional_id, day_of_week, start_time, end_time, is_available`

**professional_social_links** — `id, professional_id, platform, url`

### SQL-Only Tables (no ORM model — raw SQL in routers)

These tables exist in the database but have no SQLAlchemy model class. All access is via `db.execute(text(...))`:

- **salon_owners** — `user_id, salon_id` (many-to-many: claimed salons)
- **claiming_tokens** — `user_id, salon_id, token, expires_at, used_at`
- **appointments** — booking records (referenced in bookings.py)
- **conversations** — chat thread headers (referenced in chat.py)
- **messages** — individual chat messages
- **availability_requests** — soft booking inquiries via chat
- **moderation_queue** — content moderation items
- **reports** — user abuse reports
- **subscription_plans** — Stripe plan definitions
- **subscriptions** — active user subscriptions

---

## 8. Existing Search Logic

There are **two independent search systems:**

### System A: `GET /api/salons` (main list)
Used by the Search page. Multi-filter SQL query on the `salons` table:
1. **Multilingual query translation** — `_translate_query(q)` maps RU/UK/EN service terms to English keywords (SERVICE_SYNONYMS dict), and city names to Greek (CITY_SYNONYMS dict). ~150 synonym entries.
2. **Full-text search** — PostgreSQL `to_tsvector('simple', unaccent(...))` on `(name || name_el || address_city)`, queried with `plainto_tsquery`. Requires `unaccent` extension.
3. **City filter** — `address_city ILIKE :city` after CITY_SYNONYMS translation.
4. **Category filter** — `CATEGORY_KEYWORDS[slug]` mapped to a list of name-match keywords, applied as `services.name ILIKE %keyword%` subquery or `name ILIKE` on salon name.
5. **Rating filter** — `rating_google >= :min_rating`
6. **Sorting** — by `rating_google DESC, rating_count DESC` (no relevance score weighting)
7. **Open/Now enrichment** — batch `SELECT` from `salon_hours` for current Athens weekday
8. **Min-price enrichment** — batch `MIN(price_from ≥ 5€)` from services, optionally filtered by category keywords

### System B: `GET /api/search` (unified)
Separate endpoint, intended for future unified results (salons + professionals). Uses Haversine distance (pure SQL, no PostGIS). Currently returns salons only. Category filter here is a crude `name ILIKE %cat%` on salon name — does not use the keyword system from System A.

**Gap:** The two systems are not aligned. System B's category filter is weaker than System A's. The header `SearchBar` likely routes to System A via the `/search` page.

---

## 9. Authentication Flow

Cookie-based JWT with rotation:

```
Register/Login → set httpOnly cookies:
  access_token  (JWT, 15 min, HS256)
  refresh_token (JWT, 30 days, HS256, SHA-256 hash stored in refresh_tokens table)

Every request → FastAPI reads access_token cookie → decode_token() → get user
  If 401 → frontend calls POST /api/auth/refresh → new token pair issued, old refresh revoked
  (Token rotation: old refresh_token hash invalidated, new pair set)

Logout → revoke refresh_token in DB, delete both cookies

Google OAuth flow:
  GET /api/auth/google/start → redirect to Google with CSRF token in oauth_csrf cookie
  GET /api/auth/google/callback → verify CSRF, exchange code for id_token
    → _verify_google_id_token() validates RS256 with live Google JWKS
    → upsert user (by google_id or email) → set auth cookies → redirect to /account
```

**Bot protection layers (on top of auth):**
1. Honeypot field `website_url` in registration form (bots fill it → 400)
2. `is_bot(user_agent)` regex in `/api/salons/{id}/services` and `/reviews` endpoints
3. Lazy loading via IntersectionObserver — bots without JS never trigger lazy endpoints
4. nginx `X-Robots-Tag: noindex, nofollow` on `/api/salons/*/services` and `/reviews`
5. `slowapi` rate limits on sensitive endpoints

**Security notes:** Access token is short-lived (15 min) which is correct. Refresh token rotation is implemented. Google id_token verification fetches live JWKS and caches by `kid`. CSRF protection uses `secrets.compare_digest`.

---

## 10. Partner (Salon Owner) Functionality

The "partner" flow covers salon owners claiming and managing their listings:

**Claiming flow:**
1. Owner registers → `role='user'`
2. Enters salon ID in `/dashboard/salon`, clicks "Claim"
3. `POST /api/owner/claim/request` → generates 6-char hex token → stores in `claiming_tokens` (1hr TTL) → sends to salon's email via Resend
4. Owner enters code → `POST /api/owner/claim/verify` → inserts into `salon_owners`, sets `salons.is_verified=true`, upgrades `users.role='salon_owner'`

**Management capabilities (implemented in backend):**
- View owned salons list
- Edit salon name, description, address, phone, email, website
- Replace full weekly schedule (PUT /api/owner/salons/{id}/hours)
- Add/remove services with pricing
- Upload photos to R2

**Frontend coverage:** The dashboard UI (`/dashboard/salon`) shows the claim flow and owned salons list. Editing individual salon details (`/dashboard/salon/[id]`) appears to be partially implemented. The service management and photo upload UIs were not fully reviewed but backend endpoints exist.

**Gap:** SMS/WhatsApp claiming (channel='sms' or 'whatsapp') sends nothing — only email is wired. The code has the channel parameter but no Twilio/Meta API key is configured.

---

## 11. Admin Functionality

All admin routes require `require_admin` dependency which checks `user.role == 'admin'`. The admin email is hardcoded in config as `columb@europe.com`.

**Available admin capabilities:**
- **Stats dashboard** — total/verified salons, pending moderation, total users, bookings today/total, open reports
- **Salon management** — paginated list with filters (needs_review, verified, search), bulk-update `is_active/is_verified/needs_review`
- **Professional management** — paginated list, active filter
- **User management** — list users (admin endpoint)
- **Reports** — list open reports, mark resolved
- **Moderation queue** — view pending content items

**Frontend:** `/admin` page exists as a CSR page. Extent of admin UI coverage not fully reviewed.

**Gap:** No admin interface to edit salon content directly (merge duplicates, fix crawled data errors). No bulk import or data correction tools. Moderation queue exists in DB but its population mechanism (what triggers adding to moderation_queue) is not clearly documented in reviewed code.

---

## 12. Missing Pages

Pages that are implied by the product or mentioned in roadmap but do not currently exist:

| Missing Page | Rationale |
|---|---|
| `/salons/[slug]/book` | Booking flow is backend-complete but has no dedicated page; booking buttons on salon detail are stubs |
| `/booking/confirm/[id]` | Post-booking confirmation page |
| `/booking/cancel/[id]` | Cancellation with token (for guests) |
| `/professionals/[slug]` | Professional detail page (API endpoint exists, page does not) |
| `/account/bookings` | Client's booking history |
| `/account/messages` | Exists as route but Chat UI completeness unverified |
| `/sitemap.xml` | SEO (explicitly deferred) |
| `/robots.txt` | SEO |
| `/terms` | Legal |
| `/privacy` | Legal |
| `/about` | Marketing |
| `/blog` or `/tips` | SEO content (future) |
| `/partners` | Marketing landing for salon owners |
| `/admin/salons/[id]` | Admin detail page for editing a specific salon |
| `/dashboard/salon/[id]` | Owner detail management — exists as directory but content unverified |

---

## 13. Missing Functionality

Backend infrastructure exists but is not connected end-to-end:

| Feature | Backend Status | Frontend Status |
|---|---|---|
| Online booking | Complete (slots, appointments, cancellation) | Stub buttons only |
| Booking email notifications | `send_email` exists, likely not called on booking | Not wired |
| SMS/WhatsApp messages | Code has channel param, no API keys | N/A |
| Real-time chat notifications | No WebSocket, no push | N/A |
| Booking calendar for owners | Endpoint exists | Not built |
| Subscription + paywall | Stripe checkout exists | /pricing shows plans, no gate enforcement |
| Content moderation | moderation_queue table exists | Not built |
| Photo moderation | Google Vision key configured, usage unclear | N/A |
| Admin salon edit | Partial (is_verified flag) | No inline edit UI |
| Sitemap.xml | Not implemented | Deferred |
| Review verification | `is_verified` column in reviews | Not surfaced |
| Duplicate salon detection | `needs_review` flag set by crawler | No merge UI |
| Staff profiles | `staff` table populated by crawler | Not shown on salon detail page |
| Price range display on detail | min_price on list cards only | Not on detail page |
| Search relevance ranking | Currently rating DESC | No TF-IDF or ML ranking |
| Geo-IP default city | Not implemented | User must manually filter |
| Favorite/bookmark salons | Not implemented | Not designed |
| Email notifications (booking, reminder) | Infrastructure exists (Resend) | Not connected |
| WhatsApp notifications | No Twilio/Meta key | N/A |
| Analytics events | No tracking layer | No GTM/GA4 |

---

## 14. Technical Debt

**Critical (blocks reliability or future work):**

1. **No database migrations (Alembic)** — Schema changes are applied as ad-hoc `ALTER TABLE` statements. There is no migration history, no rollback mechanism, no reproducibility guarantee. The `db/init.sql` is the initial schema but diverges from current state.

2. **~10 SQL-only tables with no ORM models** — `salon_owners`, `claiming_tokens`, `appointments`, `conversations`, `messages`, `availability_requests`, `moderation_queue`, `reports`, `subscription_plans`, `subscriptions`. All access via raw `text()` SQL in routers. This makes schema changes invisible to the ORM, makes queries untyped, and means `db.query(SomeModel)` is impossible for half the business entities.

3. **DeepL API key configured but unused** — `deepl_api_key` is in Settings and `.env`, but translation was replaced by OpenAI. Dead configuration creates confusion about which service is active.

4. **Redis unused in API** — Redis is provisioned and `REDIS_URL` is passed to the API container, but no Redis client is used in any API code. Rate limiting (slowapi) works via in-process memory, not Redis. This means rate limits reset on container restart and don't work across hypothetical future API replicas.

5. **No test suite** — Zero unit, integration, or end-to-end tests across all layers. Every deployment is a manual smoke test. The bot-detection regex, translation caching, open/closed logic, and auth flows have no test coverage.

**Medium (degrades maintainability):**

6. **CITY_SYNONYMS and SERVICE_SYNONYMS as hardcoded dicts** — 150+ entries in the router file. Should be in a data file or DB table. Adding a new city synonym requires a code change + Docker rebuild.

7. **Static CATEGORY_KEYWORDS dict** — Category-to-service-keyword mapping is duplicated conceptually: once in `salons.py` (CATEGORY_KEYWORDS for price filtering) and once in `SalonCard.tsx` (CATEGORY_GENDER for icon display). Adding a new category requires updating both independently.

8. **`SalonDetailClient.tsx` is a god component** — Contains: lazy loading hook, translated badge component, services section, reviews section, photos carousel, hours display, contact buttons, map embed, social links, report button. All in one file. Single-responsibility principle is not applied.

9. **No API versioning** — All endpoints are under `/api/` with no version prefix. Breaking changes require coordinated frontend+backend deploys with no rollback path.

10. **Docker images bake code** — No volume mounts for `api` and `web`. A one-line bug fix requires a full multi-minute Docker rebuild. Development cycle is slow; there is no hot-reload in production-equivalent environment.

**Low (quality/hygiene):**

11. **Inconsistent locale prefix handling** — `const prefix = locale === 'el' ? '' : '/${locale}'` is repeated verbatim in 8+ components. Should be a shared utility.

12. **`(params as any).locale`** — Type cast workaround in every page component, indicating Next.js 14 `params` typing is not properly resolved. Suggests missing `generateStaticParams` or incorrect async params handling.

13. **`apiFetch` always `cache: 'no-store'`** — Disables Next.js ISR/SSG caching for all API calls. Fine for dynamic content, but prevents any static optimization for public pages like category lists.

14. **Memory limits may be tight** — `api: 200m`, `web: 300m`. Next.js production builds are memory-hungry; under load or after a hot path warms all pages, the 300m limit may cause OOM restarts.

---

## 15. Duplicate Code

| Pattern | Locations | Impact |
|---|---|---|
| `const prefix = locale === 'el' ? '' : '/${locale}'` | 8+ page/component files | Repeated string logic |
| `fetch('/api/auth/me').then(r => r.ok ? r.json() : null)` | account, dashboard/salon, dashboard/master, admin pages | Should be a shared `useMe()` hook |
| `IntersectionObserver` setup | search/page.tsx (infinite scroll) + SalonDetailClient.tsx (lazy sections) | Different use cases, but setup boilerplate is similar |
| Skeleton loader `animate-pulse` divs | search, salon detail, account pages | No shared `<Skeleton>` component |
| `add_header X-Robots-Tag` nginx block | Written once (correct) but pattern applies to other bot-sensitive endpoints | Low risk currently |
| `_require_ownership` check in owner router | Likely repeated across multiple owner endpoints | Needs audit |
| Bot-detection + translation pattern | services endpoint + reviews endpoint in salons.py | Extracted to `translate.py` (correct) but endpoint code is still ~80 lines each |

---

## 16. Current UI Architecture

The UI is **server-component-first at the route level, client-component-first inside the route.** Specifically:

- `page.tsx` files are async Server Components: they fetch data, generate metadata, pass serialized props to the client component
- The actual rendered UI is a single large Client Component per page (e.g., `SalonDetailClient`, `SearchContent`)
- This means hydration bundles are large per page — no streaming, no Suspense at component level except the Search page wrapper

**Design system:** No formal design system. The visual language is consistent (pink-600 accent, gray-50 backgrounds, rounded-xl cards, tailwind utilities) but is maintained by convention, not by a component library or Storybook.

**Typography:** System fonts inherited from body, no explicit font-face definitions reviewed. All sizes via Tailwind text-sm/text-base/text-xl/text-2xl etc.

**Color palette (de facto):**
- Primary: `pink-600` (#db2777)
- Background: `gray-50`, `white`
- Text: `gray-900` (headings), `gray-500` (secondary), `gray-400` (meta)
- Success: `green-500`
- Danger: `red-500`

---

## 17. CSS Architecture

**100% Tailwind CSS utility classes.** No external CSS files except `globals.css` (base resets). No CSS variables for design tokens. No CSS modules.

**Consequences:**
- Good: Zero specificity conflicts, all styles co-located with markup
- Bad: Long className strings in JSX (30–60 chars per element common); no semantic CSS hooks for theming; changing the primary color (pink-600) requires a global search-replace or Tailwind config change
- Bad: No `@layer components` abstractions defined — repetitive patterns like `rounded-xl border border-gray-100 overflow-hidden` appear in many places without a shared class

**Responsive breakpoints used:**
- `sm:` — tablet portrait (640px+)
- `md:` — tablet landscape (768px+)  
- `lg:` — desktop (1024px+)
- No `xl:` or `2xl:` breakpoints observed — max content width capped at `max-w-6xl`

---

## 18. JS Architecture

**Frontend:**
- No global state management (Redux, Zustand, Jotai). All state in component `useState`.
- URL search params as the only persistent client state: filters (`city`, `category`, `q`, `min_rating`, `view`) survive page refresh via `useSearchParams`.
- No data fetching library (React Query, SWR). Manual `fetch()` in `useEffect`.
- No request deduplication, no stale-while-revalidate, no optimistic updates.
- `useRef` used correctly to avoid stale closures in `IntersectionObserver` callbacks.

**Backend:**
- Synchronous FastAPI with psycopg2 — correct for the current load, but blocks the event loop on slow queries.
- All rate limiting in-process (slowapi). Not distributed.
- `gpt-4o-mini` calls are synchronous and block the request thread for the duration of the API call (~1–3 seconds for a batch of 20 items). Under concurrent load this creates a thread-pool bottleneck.
- `is_bot()` regex is compiled once at module import (correct).
- OpenAI client is a lazy singleton (correct — avoids reconnection overhead).

---

## 19. Responsive Implementation

The search page and salon cards are designed mobile-first:
- Card grid: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`
- Search bar in header: `flex-1 min-w-[160px] max-w-xs` with overflow wrapping
- Filter panel: absolute-positioned dropdown, `max-w-[calc(100vw-1rem)]` prevents overflow on mobile
- Map view: full-width via Leaflet's responsive container

**Gaps identified:**
- Salon detail page not fully audited for mobile layout (single-column vs. multi-column split)
- MapView on mobile: Leaflet defaults work but no touch-friendly marker clustering
- No `viewport` meta in `layout.tsx` (inherited from Next.js defaults, but worth verifying)
- Dashboard pages (owner, admin) are not explicitly mobile-responsive — likely functional but not polished on small screens
- No PWA manifest, no service worker, no offline capability

---

## 20. What Should NEVER Be Changed

These components are stable, correct, and critical — changes are high risk:

1. **Cookie-based JWT auth** — The httpOnly cookie flow with CSRF validation, refresh token rotation, and token hash storage is correctly implemented. Changing to localStorage or header-based auth would introduce XSS attack surface.

2. **`is_bot()` regex pattern** — The current pattern correctly avoids matching `Mozilla/5.0` (the `moz` bug was fixed). Any modification risks re-breaking bot detection or blocking legitimate users. Test before any change.

3. **`X-Robots-Tag` on `/api/salons/*/services` and `/reviews`** — Nginx config that prevents Google from indexing lazy-loaded translation endpoints. Removing this would cause Google to index translated content that isn't stable (changes with each translation pass), harming SEO.

4. **`_batch_open_now()` with `ZoneInfo("Europe/Athens")`** — Correct timezone-aware open/closed computation. Any change to timezone handling will produce wrong results for half the year (DST).

5. **Photo proxy `/api/media/photo/{id}`** — The lazy R2 migration pattern is the bridge between old Google Places URLs and CDN URLs. Breaking this would show broken images for all non-migrated photos.

6. **`docker-compose.yml` healthchecks** — `api` depends on `db` being healthy before starting. Removing health checks causes race conditions on restart.

7. **`unaccent` PostgreSQL extension** — Full-text search uses `unaccent()` in queries. If the extension is dropped from the DB, all search queries fail.

8. **`db/init.sql`** — The canonical initial schema. This should never be edited in-place; new DDL must go to migration scripts.

---

## 21. What Should Be Redesigned First

Ranked by impact-to-effort ratio:

**Priority 1 — Alembic migrations** (2 days effort, eliminates a class of production risk)  
The absence of migration tooling is the highest structural risk. One accidental `docker compose down -v` or a need to restore from backup puts the current schema state in question. Set up Alembic with `autogenerate` from current SQLAlchemy models, then write manual migrations for the 10 SQL-only tables.

**Priority 2 — ORM models for SQL-only tables** (1 day)  
`appointments`, `conversations`, `messages`, `salon_owners`, `subscriptions` etc. Adding SQLAlchemy models enables type safety, IDE support, and Alembic tracking. The raw SQL in routers can stay for now; models just need to exist.

**Priority 3 — Extract `useMe()` auth hook** (2 hours)  
Four pages duplicate the "fetch /api/auth/me → redirect if null" pattern. A single `useMe()` hook cleans this up and makes adding auth state (e.g., avatar, role checks) a single change.

**Priority 4 — Split `SalonDetailClient.tsx`** (half-day)  
Extract: `<SalonPhotos>`, `<SalonServices>`, `<SalonReviews>`, `<SalonHoursSection>`. Each becomes independently lazy-loadable and independently testable.

**Priority 5 — Redis for rate limiting** (2 hours config)  
Connect `slowapi` to the already-running Redis instance. Zero code changes — just pass `storage_uri` to the Limiter. Ensures rate limits survive API restarts and work across replicas.

**Priority 6 — locale prefix utility** (30 min)  
Extract `const prefix = locale === 'el' ? '' : '/${locale}'` to `lib/locale.ts → localePrefix(locale)`. Replaces ~8 occurrences.

---

## 22. What Can Be Postponed

The following have low current impact and can wait without accruing significant debt:

- **SEO** (sitemap.xml, canonical URLs, meta descriptions) — Already explicitly deferred. Low urgency while content is still being structured.
- **PostGIS** — Haversine in SQL handles current geo queries adequately. PostGIS is worth adding when professional geo-search becomes primary traffic.
- **TypeScript strict mode** — The `as any` casts in page params are a nuisance, not a bug. Address when Next.js 15 upgrade is planned.
- **Design system / Storybook** — The Tailwind approach is workable at current component count. Extract a design system when the component library grows above ~30 components.
- **Cache layer (Redis for API responses)** — Not needed until traffic shows DB bottlenecks. Monitor query times first.
- **Admin content editing** — Full CMS-like admin for editing salon data has low ROI until there are active verified salon owners requesting corrections.
- **WhatsApp/SMS notifications** — The channel parameter exists; wiring Twilio is a few hours of work but low value until booking volume exists.
- **PWA / service worker** — Mobile web experience is adequate. Add after a dedicated mobile design pass.
- **Analytics (GA4/GTM)** — Useful but not urgent; add when marketing needs funnel data.
- **Clustering on map** — Leaflet.markercluster is a one-package add; add when map view is a primary used feature.

---

## 23. Future Features Already Partially Supported

The codebase has infrastructure for features not yet exposed to users:

| Future Feature | What's Already There |
|---|---|
| **Full booking flow** | `appointments` table, `GET /slots`, `POST /bookings`, `PATCH /bookings/{id}` — complete backend |
| **In-app messaging** | `conversations`, `messages`, `availability_requests` tables + full chat router |
| **Slot proposals** (soft booking) | `availability_requests` + `POST .../propose` endpoint |
| **Stripe subscriptions** | `subscription_plans`, `subscriptions` tables, checkout/portal/webhook endpoints, abstract PaymentProvider |
| **Google OAuth mobile** | `google_id` column in users, full JWKS verification — just needs a mobile redirect_uri |
| **Professional geo-search** | `base_lat/lng`, `service_radius_km`, `does_home_visits` — data model ready, `/api/professionals` supports geo filter |
| **Multi-language service names** | `name_en/ru/uk` columns in services, on-demand translation wired |
| **Multi-language reviews** | `text_en/ru/uk` columns in reviews, on-demand translation wired |
| **Multi-language salon descriptions** | `description_el/ru/uk` in salons — populated by crawler |
| **Content moderation** | `moderation_queue`, `reports` tables, admin endpoints, `google_vision_api_key` configured |
| **Staff profiles** | `staff` table populated by crawler, not yet shown on frontend |
| **Salon photo management** | R2 upload endpoint in owner router — UI not built |
| **Role-based access control** | `user/salon_owner/professional/admin` roles, `require_admin`, `get_current_user` — extensible |
| **Disposable email blocking** | `is_disposable_email()` in moderation.py — already called on register |

---

## 24. Risks for Future Mobile Applications

If a native iOS/Android app is built against the current API:

**Favorable:**
- REST API is JSON over HTTPS — works natively on mobile
- Cookie auth can work on mobile webviews; native apps can use the same endpoints with `Authorization: Bearer` header if access tokens are exposed (minor endpoint change)
- Google OAuth is already wired server-side; adding a mobile redirect_uri is trivial

**Risks:**
1. **httpOnly cookie auth** — Native HTTP clients (URLSession, OkHttp) don't naturally persist httpOnly cookies. The API would need an additional `Authorization: Bearer` path or a dedicated `/api/auth/token` endpoint returning JSON tokens for mobile clients.

2. **No push notification infrastructure** — There is no FCM/APNs token storage, no notification service. Building real-time booking/chat notifications for mobile requires a new infrastructure layer.

3. **No API versioning** — Current API has no `/api/v1/` prefix. Breaking changes for mobile clients are harder to manage without versioning, since mobile users don't update apps instantly.

4. **Large response payloads** — Some list endpoints return full objects. Mobile bandwidth is constrained; a dedicated compact list schema per entity would be valuable.

5. **Synchronous translation calls** — If mobile users trigger service/review translation, the API blocks for 1–3 seconds. Mobile apps expect <500ms responses. This path needs an async queue (Celery task → webhook callback) for mobile.

6. **No rate limit per client app** — Current rate limits are IP-based. A mobile app client share one IP (from proxy) or many IPs (direct). Neither is ideal for per-user rate limiting.

---

## 25. Risks for Future Scalability

Current architecture is single-server vertical scaling. Key bottlenecks as traffic grows:

| Bottleneck | Current Limit | Mitigation Path |
|---|---|---|
| **API thread pool** | Synchronous psycopg2; FastAPI workers × threads | Switch to `asyncpg` + SQLAlchemy async; or add more `uvicorn` workers |
| **OpenAI translation** | Blocks request thread for 1–3s per translation batch | Move to background Celery task; return `pending` status, poll or webhook |
| **PostgreSQL single instance** | No read replicas; all reads hit the primary | Add PgBouncer + read replica for list/search queries |
| **Full-text search on salons** | `to_tsvector` computed inline (no GIN index confirmed) | Add GIN index on `tsvector` column; consider Elasticsearch for more advanced search |
| **Redis in-process rate limiting** | Not shared across processes; resets on restart | Already mitigated by connecting slowapi to Redis (see Priority 5 above) |
| **API memory limit (200m)** | Under load with multiple concurrent translations, may OOM | Increase limit or offload translation to worker queue |
| **Docker images rebuilt on every change** | No CD pipeline; manual build takes 2–5 min per service | Set up GitHub Actions + registry; separate build from deploy |
| **No horizontal scaling** | Single Docker Compose on single host | Migrate to Kubernetes or Docker Swarm if multi-node needed; currently not needed |
| **Crawler writes directly to primary DB** | Two Celery workers write concurrently with API reads | Low risk at current volume; add connection pooling if contention observed |
| **R2 photo migration in request path** | First-view of Google Photos URL triggers R2 upload synchronously | Move to background task; return placeholder while R2 migration runs |

---

## 26. Estimated Complexity of Redesign

Assuming a full frontend visual redesign (new design system, new layout, new component structure) with no backend changes:

| Scope | Effort Estimate | Risk |
|---|---|---|
| Design system extraction (Tailwind config + base components) | 3–5 days | Low — Tailwind makes token extraction mechanical |
| Homepage redesign | 1–2 days | Low |
| Search page redesign + new filter UX | 3–5 days | Medium — infinite scroll logic must be preserved |
| Salon detail page redesign + split into sub-components | 3–4 days | Medium — lazy loading hooks must survive |
| Dashboard pages (owner + master) | 4–6 days | Medium — form validation, file uploads |
| Admin panel | 3–5 days | Low — data tables, no complex interactions |
| Auth pages | 1–2 days | Low |
| Mobile-responsive pass across all pages | 3–5 days | Medium — requires device testing |
| i18n strings audit (missing translations, new keys) | 1–2 days | Low |
| **Total frontend redesign** | **~3–5 weeks** | **Medium** |

Redesign complexity depends heavily on whether the component boundary changes:
- **Preserve current component boundaries** → cosmetic CSS changes → 2 weeks
- **Split SalonDetailClient + introduce shared design system** → 4–5 weeks
- **Full redesign with new routing patterns or framework upgrade** → 8+ weeks (out of scope without strong justification)

**Backend redesign is not recommended** at this stage. The FastAPI API is clean, well-structured, and decoupled enough from the frontend. Priority should be Alembic + ORM models (see Section 21), not a rewrite.

---

## Summary

Lookla is a **working, deployed, multi-language beauty marketplace** with solid foundational architecture: clean REST API, correct auth flow, good bot protection layering, and a visually consistent frontend. The platform's primary structural risk is the absence of database migration tooling and the split between ORM models and raw-SQL tables — this needs to be addressed before the schema evolves further. The booking, chat, and payment systems are backend-complete but frontend-incomplete, offering a clear near-term roadmap for feature completion without architectural change.

The codebase is well-positioned for a frontend redesign: Tailwind CSS and React component boundaries make visual changes low-risk. The highest-value investment is closing the gaps between backend infrastructure and frontend surfaces (booking flow, messaging, subscriptions) rather than redesigning what already works.
