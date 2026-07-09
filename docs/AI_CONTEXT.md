# AI_CONTEXT.md — Lookla Project Context
**Entry point for AI assistants (Claude, GPT, Copilot, etc.)**

> Read this file first. It gives you the current state of the project in under 3 minutes.
> After reading this file, consult the documents listed in "Where to start."

---

## Project

**Name:** Lookla
**Type:** Beauty discovery marketplace for Greece
**URL:** lookla.gr
**Owner:** Andrey (columb@europe.com)
**Documentation repo:** github.com/Columbist/lookla-docs (public)
**Full monorepo:** github.com/Columbist/lookla-platform (private)

---

## What Lookla is

A multilingual directory of beauty salons, barbershops, spas, and independent professionals in Greece. Clients search by area, category, and language. The platform serves users in Greek, English, Russian, and Ukrainian.

Current data: ~6300 salons, aggregated from public sources (crawlers). No fake data. No paid listings.

---

## Current Phase

**Technical Architecture.** M-01 (MVP Athens Launch) is in progress.

Product decisions are fully approved (DEC-001 through DEC-017). UX specifications are approved (page specs, UX flows, wireframe requirements). Technical architecture is now approved (backend, frontend, DB schema, API spec, security, performance).

**Next:** Development begins. A developer can open `04_ARCHITECTURE/` and write code without asking product questions.

---

## What is Approved (source of truth)

### Governance
| Document | What it defines |
|---|---|
| `00_GOVERNANCE/PROJECT_CHARTER.md` | **Highest authority.** All rules. Read first. |
| `00_GOVERNANCE/DECISION_LOG.md` | All official decisions (DEC-001 to DEC-017) |

### Product
| Document | What it defines |
|---|---|
| `01_PRODUCT/PRODUCT_SCOPE.md` | What Lookla IS and IS NOT |
| `01_PRODUCT/PRODUCT_VISION.md` | Why Lookla exists, differentiators |
| `01_PRODUCT/PRODUCT_TERMINOLOGY.md` | Official dictionary |
| `01_PRODUCT/MVP_DEFINITION.md` | Approved MVP scope + all Q decisions |
| `01_PRODUCT/MVP_SCOPE_LOCK.md` | **Locked boundary — WILL HAVE / WILL NOT HAVE** |

### UX / Design
| Document | What it defines |
|---|---|
| `03_PAGES/HOME.md` | Homepage spec (language switcher placement, area grid) |
| `03_PAGES/SEARCH.md` | Search page spec (area filter, verified label) |
| `03_PAGES/SALON.md` | Salon detail spec (contact CTAs, review labels, badge) |
| `03_PAGES/ADMIN.md` | Admin panel spec |
| `03_PAGES/CONTACT.md` | Contact page spec (new page) |
| `03_PAGES/ABOUT.md` | About page spec (new page) |
| `02_DESIGN/UX_FLOWS.md` | 4 MVP user flows with edge cases |
| `02_DESIGN/WIREFRAME_REQUIREMENTS.md` | 8 wireframe layouts (ASCII) with annotations |

### Technical Architecture
| Document | What it defines |
|---|---|
| `04_ARCHITECTURE/BACKEND_ARCHITECTURE.md` | Service boundaries, layers, modules, job scheduling |
| `04_ARCHITECTURE/FRONTEND_ARCHITECTURE.md` | Next.js structure, routing, components, hooks, i18n, SEO |
| `04_ARCHITECTURE/DATABASE_SCHEMA.md` | All entities, attributes, relationships, indexes |
| `04_ARCHITECTURE/API_SPECIFICATION.md` | Every endpoint: method, route, request, response, errors |
| `04_ARCHITECTURE/SECURITY.md` | Auth, CSRF, rate limits, bot protection, GDPR |
| `04_ARCHITECTURE/PERFORMANCE.md` | Core Web Vitals targets, caching, image pipeline |
| `04_ARCHITECTURE/DATA_FLOW.md` | How data moves: read, write, analytics, translation flows |
| `04_ARCHITECTURE/AI_STRATEGY.md` | AI features postponed; translation is infrastructure only |
| `04_ARCHITECTURE/FEATURE_FLAGS.md` | Features in code but hidden from users |

### Engineering
| Document | What it defines |
|---|---|
| `06_ENGINEERING/AUDIT.md` | Full technical audit (§27: implementation readiness) |
| `06_ENGINEERING/DEVELOPMENT_STANDARDS.md` | Commit format, branching, naming, testing, DoD |

---

## All Decisions (DEC-001 to DEC-017)

| ID | Decision |
|---|---|
| DEC-001 | Private project, no monetization, no advertising |
| DEC-002 | Documentation-first: no implementation without approved docs |
| DEC-003 | No fake data, reviews, ratings, or activity |
| DEC-004 | Every feature requires evidence of user need |
| DEC-005 | AI product features postponed |
| DEC-006 | Stripe exists in code; must not be user-facing |
| DEC-007 | Monorepo: docs live with code |
| DEC-008 | MVP success = 500 contact interactions in 90 days |
| DEC-009 | Primary persona: P-02 (ru/uk) → P-01 (el) → P-03 (expat); tourists last |
| DEC-010 | Location hierarchy: Country→Region→City→District; replace "City" filter |
| DEC-011 | el/en/ru mandatory for MVP; uk ships at lower QA priority |
| DEC-012 | Athens metropolitan area first |
| DEC-013 | Google reviews: label "Source: Google Reviews / Imported: Yes / Original: No" |
| DEC-014 | Replace ✓ with text: "Information reviewed" (admin) or "Owner verified" (claimed) |
| DEC-015 | No booking stubs; only real CTAs: "Call salon" / "WhatsApp" / "Visit website" |
| DEC-016 | View/call/WhatsApp = anonymous; Favorites = registration required |
| DEC-017 | GA4 + Search Console required before launch |

---

## Current Phase: Technical Architecture

All 6 technical architecture documents were approved 2026-07-09. A developer can now write code from these documents without product decisions.

### What's been specified

| Layer | Document | Key content |
|---|---|---|
| Backend | BACKEND_ARCHITECTURE.md | 13 routers, 4 services, layered architecture, 12 must-not-change items |
| Frontend | FRONTEND_ARCHITECTURE.md | App Router structure, 15 MVP changes enumerated |
| Database | DATABASE_SCHEMA.md | 9 entities, indexes, 2 new columns required (DEC-010) |
| API | API_SPECIFICATION.md | All endpoints: request/response/errors; 1 new endpoint (`GET /api/areas`) |
| Security | SECURITY.md | Auth flow, bot protection layers, GDPR requirements |
| Performance | PERFORMANCE.md | Core Web Vitals targets, image pipeline, caching strategy |

### Engineering assumptions made during architecture

1. `address_district` and `address_region` columns must be added to `salons` table (DEC-010)
2. `GET /api/areas` endpoint does not exist yet — must be created for area filter
3. Athens district → `address_city` mapping is needed as a backend dict during DEC-010 transition
4. slowapi rate limits must be connected to Redis (one-line config fix)
5. `useMe()` hook should be extracted to `hooks/useMe.ts` (replaces 4× inline duplication)
6. `localePrefix()` utility should be extracted to `lib/locale.ts` (replaces 8× inline duplication)
7. GA4 tracking ID must be added to `NEXT_PUBLIC_GA4_ID` env var
8. Privacy Policy page (`/privacy`) must be created before MVP launch (GDPR)
9. Cookie consent banner required for GDPR when GA4 is active
10. Hero photo on salon detail must use `next/image` with `priority={true}` for LCP

---

## Pre-Launch Implementation Checklist

**Ordered by dependency (from AUDIT.md §27.5):**

### Step 1 — Data
- [ ] Define Athens district → `address_city` mapping (backend)
- [ ] Add `address_district` column to salons table
- [ ] Update `/api/salons` area filter to use district mapping

### Step 2 — Backend
- [ ] Add `GET /api/areas` endpoint (district list with salon counts)
- [ ] Connect slowapi to Redis
- [ ] Add admin inline salon edit (phone, address) to `PATCH /api/admin/salons/{id}`

### Step 3 — Salon Detail (highest user impact)
- [ ] Remove booking stubs (DEC-015)
- [ ] Add contact CTAs: "Call salon", "WhatsApp", "Visit website" (DEC-015)
- [ ] Replace ✓ badge with text label (DEC-014)
- [ ] Add review section header: "Source: Google Reviews / Imported: Yes / Original: No" (DEC-013)
- [ ] Wire GA4 contact click events (DEC-017)

### Step 4 — Search
- [ ] Update area filter label City → Area in all 4 locales (DEC-010)
- [ ] Populate area filter with Athens districts
- [ ] Update verified label on SalonCard

### Step 5 — Homepage
- [ ] Move LanguageSwitcher to header
- [ ] Rename CityGrid → AreaGrid with Athens districts (DEC-010)

### Step 6 — Analytics
- [ ] Create GA4 property; obtain tracking ID
- [ ] Add GA4 script to root layout
- [ ] Verify `contact_action` events fire
- [ ] Verify Google Search Console
- [ ] Add cookie consent banner
- [ ] Create `/privacy` page with GA4 disclosure

### Step 7 — New pages
- [ ] Create `/[locale]/about`
- [ ] Create `/[locale]/contact`
- [ ] Add About + Contact links to footer

### Step 8 — Admin
- [ ] Admin inline edit form for phone/address
- [ ] Verify admin email excluded from GA4

### Step 9 — Pre-launch gate
- [ ] `/pricing` not in navigation (DEC-006 compliance)
- [ ] Manual QA of J-01 and J-02 journeys in production
- [ ] PageSpeed Insights on salon detail page: LCP < 2.5s
- [ ] Verify GIN index on salons FTS tsvector

---

## Known Mismatches (implementation ≠ documentation)

| Mismatch | Decision | Status |
|---|---|---|
| ✓ badge means "admin reviewed" not "owner verified" | DEC-014 | ⬜ Fix pending |
| Reviews show without "Source: Google" label | DEC-013 | ⬜ Fix pending |
| City filter says "City" but returns districts | DEC-010 | ⬜ Fix pending |
| Booking stub buttons visible on salon page | DEC-015 | ⬜ Fix pending |
| `/pricing` page may be linked in navigation | DEC-006 | ⬜ Verify pending |
| Language switcher in footer only (not header) | HOME.md spec | ⬜ Fix pending |

---

## Technical Risks

| Risk | Severity | Mitigation |
|---|---|---|
| No database migrations (Alembic) | High | Every schema change is ad-hoc; add before `address_district` column |
| 10 SQL-only tables without ORM models | Medium | Limits type safety; add ORM models for `reports`, `salon_owners`, `claiming_tokens` |
| Zero test coverage | High | Add tests for `is_bot()`, `_batch_open_now()`, auth flow before changing them |
| `SalonDetailClient.tsx` god component | Medium | Split for MVP is recommended; required for future maintainability |
| slowapi in-process (resets on restart) | Low | Connect to Redis (one-line fix) |
| Translation call blocks request thread 1–3s | Low | Acceptable for MVP; Celery async for post-MVP |
| No Privacy Policy page | High (pre-launch) | Required for GDPR + GA4; must be created |

---

## What NOT to do

- Do not implement features without an approved RFC in `07_RFC/`
- Do not mark any document `Approved` without Product Owner confirmation
- Do not resolve mismatches by silently changing code or docs — report them
- Do not expose Stripe, subscriptions, or monetization to users (DEC-006)
- Do not add fake data or fake activity signals (DEC-003)
- Do not add geo search "near me" UI (tourists deprioritized per DEC-009)
- Do not add AI-generated content or AI ranking (DEC-005)
- Do not change the `is_bot()` regex without a test proving the change doesn't break it
- Do not change JWT auth mechanism (httpOnly cookies) without a security review
- Do not commit `.env` files to git

---

## Next Milestone

**M-01 — MVP Athens Launch**
Status: **In Progress — Technical Architecture approved; Development starting**
Reference: `05_ROADMAP/ROADMAP.md`
Launch gate: `01_PRODUCT/MVP_SCOPE_LOCK.md`
Pre-launch checklist: See above (9 steps, 25+ items)

After M-01 launches (500 contact interactions measured in 90 days): plan M-02 based on GA4 evidence.

---

## Where to Start

**For a developer starting implementation:**
1. `04_ARCHITECTURE/BACKEND_ARCHITECTURE.md` — understand the backend structure
2. `04_ARCHITECTURE/API_SPECIFICATION.md` — understand every endpoint
3. `04_ARCHITECTURE/DATABASE_SCHEMA.md` — understand the data model
4. `06_ENGINEERING/DEVELOPMENT_STANDARDS.md` — how to write code and commits
5. `06_ENGINEERING/AUDIT.md §27.5` — ordered implementation checklist

**For a product/UX designer:**
1. `01_PRODUCT/MVP_SCOPE_LOCK.md` — what's in scope
2. `02_DESIGN/WIREFRAME_REQUIREMENTS.md` — wireframe briefs
3. `03_PAGES/SALON.md` — the conversion page (most important)

**For any AI assistant entering this project:**
1. Read this file (done)
2. Read `00_GOVERNANCE/PROJECT_CHARTER.md` — the rules
3. Read `01_PRODUCT/MVP_SCOPE_LOCK.md` — the boundary
4. Read `04_ARCHITECTURE/API_SPECIFICATION.md` — what the API does

---

## Tech Stack (brief)

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), Tailwind CSS, next-intl |
| Backend | FastAPI (Python 3.12), SQLAlchemy (sync), PostgreSQL 16 |
| Infrastructure | Docker Compose, Nginx, Cloudflare, R2 CDN |
| Task queue | Celery + Redis (crawlers only) |
| AI | OpenAI gpt-4o-mini (translation infrastructure; DEC-005) |
| Payments | Stripe (configured; not user-facing per DEC-006) |
| Auth | Cookie-based JWT (HS256) + Google OAuth (RS256) |
| Analytics | GA4 + Google Search Console (DEC-017; not yet installed) |

---

*Last updated: 2026-07-09*
*Update this file whenever phase changes or a major decision affects project state.*
