---
title: Release Checklist
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 05_ROADMAP/MILESTONE_M01.md
  - 06_ENGINEERING/RISK_REGISTER.md
  - 06_ENGINEERING/TESTING_STRATEGY.md
  - 01_PRODUCT/MVP_SCOPE_LOCK.md
  - 04_ARCHITECTURE/SECURITY.md
implementation_status: N/A — gate document; must be fully checked before production deployment
---

# Release Checklist — M-01 MVP Launch
**Lookla Beauty Marketplace**

> **This checklist is a gate, not a guide.** Every item with `[BLOCKER]` must be checked before deployment.
>
> Items without [BLOCKER] are strongly recommended but can be deferred to the first post-launch patch (within 7 days).
>
> **Completion sign-off:** Product Owner signs off after manual QA passes (J-01, J-02, J-03).

---

## Section 1 — Infrastructure & Operations

### 1.1 Database
- [ ] [BLOCKER] Alembic is configured and `alembic upgrade head` runs cleanly on production DB
- [ ] [BLOCKER] `address_district` and `address_region` columns exist in `salons` table
- [ ] [BLOCKER] Daily pg_dump backup cron is active: `crontab -l | grep pg_dump`
- [ ] [BLOCKER] Manual backup taken immediately before deployment: `lookla_pre_m01_YYYYMMDD.sql.gz` exists in `/opt/backups/`
- [ ] [BLOCKER] GIN index on `salons` FTS tsvector exists: `SELECT indexname FROM pg_indexes WHERE tablename='salons' AND indexdef LIKE '%GIN%'`
- [ ] [BLOCKER] `idx_salons_address_district` BTREE index exists
- [ ] ≥80% of Athens salons have non-null `address_district`
- [ ] ≥300 salons have non-null, correct-format `phone_primary`

### 1.2 Environment
- [ ] [BLOCKER] `.env` file is NOT committed to git: `git ls-files | grep "\.env"` returns only `.env.example`
- [ ] [BLOCKER] `NEXT_PUBLIC_GA4_ID` is set to a real tracking ID (not "G-XXXXXXXXXX")
- [ ] [BLOCKER] `NEXT_PUBLIC_GA4_ID` is present in `.env.example` as placeholder
- [ ] All other required env vars are set (check against DEVELOPMENT_STANDARDS.md §8 list)
- [ ] `DATABASE_URL` points to production DB (not local)

### 1.3 Docker
- [ ] `docker compose ps` shows all services Up: api, web, db, redis
- [ ] `docker logs beauty_api --tail=50` shows no ERROR or CRITICAL messages
- [ ] `docker logs beauty_web --tail=50` shows no NEXT_JS_BUILD_ERROR messages
- [ ] `docker stats` — no service is exceeding memory limits

### 1.4 Nginx / DNS
- [ ] `https://lookla.gr` returns 200
- [ ] `https://lookla.gr/api/health` returns `{"status": "ok"}`
- [ ] SSL certificate is valid and not expiring within 30 days: `openssl s_client -connect lookla.gr:443 | openssl x509 -noout -dates`
- [ ] Nginx is serving from the correct upstream (api + web containers)

---

## Section 2 — Data Quality

- [ ] [BLOCKER] ≥50 salons marked `is_verified = true` by admin before launch
- [ ] Admin has manually checked and corrected phone numbers for ≥10 high-priority salons (Kolonaki, Glyfada, Kifissia focus areas)
- [ ] No salon has both `is_active = true` and empty `name` (spot check: `SELECT count(*) FROM salons WHERE is_active AND name IS NULL`)
- [ ] Area backfill validated: `SELECT address_district, count(*) FROM salons WHERE is_active GROUP BY 1 ORDER BY 2 DESC LIMIT 10` shows reasonable distribution
- [ ] Report: at least 3 major Athens districts have ≥ 50 active salons each

---

## Section 3 — Backend API

- [ ] [BLOCKER] `GET /api/areas` returns ≥8 districts with `salon_count > 0`
- [ ] [BLOCKER] `GET /api/salons?area=glyfada` returns filtered results
- [ ] [BLOCKER] `GET /api/salons?q=маникюр` returns non-empty results (Russian synonym working)
- [ ] [BLOCKER] `GET /api/salons/{id}` response includes `is_owner_claimed` field
- [ ] `POST /api/auth/register` works; returns 201 with correct body
- [ ] `POST /api/auth/login` works; sets httpOnly cookie
- [ ] `GET /api/auth/refresh` works; rotates token
- [ ] `/api/salons` with no params returns paginated results (items.length ≤ 24)
- [ ] `/api/salons/{id}/services?lang=ru` returns service names (translated or original Greek)
- [ ] `/api/salons/{id}/reviews` returns reviews with `source: "google"` field
- [ ] Turnstile verification verified on `/api/auth/register` (send request without token; expect 400 or 422)
- [ ] `GET /api/salons?city=Glyfada` still works (backwards compat check)
- [ ] [BLOCKER] slowapi connected to Redis: confirm `app/main.py` Limiter includes `storage_uri="redis://redis:6379"` (T-033)
- [ ] Rate limit survives restart: send 5 register requests, restart api container, 6th request blocked

---

## Section 4 — Frontend — DEC Compliance (Critical)

### 4.1 DEC-015 — No Booking Stubs
- [ ] [BLOCKER] Search for "book" in DOM on salon detail page: MUST return 0 results
- [ ] [BLOCKER] Search for "reserve" in DOM on salon detail page: MUST return 0 results
- [ ] [BLOCKER] "Call salon", "WhatsApp", "Visit website" CTAs visible on salon detail page
- [ ] All 3 CTAs accessible without login (incognito window)

### 4.2 DEC-013 — Google Review Attribution
- [ ] [BLOCKER] Review section header text: "Source: Google Reviews / Imported: Yes / Original: No" visible
- [ ] Label visible in el, en, ru locales (spot check)
- [ ] Label is NOT in a tooltip or behind a disclosure

### 4.3 DEC-014 — Verified Badge
- [ ] [BLOCKER] No ✓ icon visible on any verified salon (search DOM for checkmark or ✓ character)
- [ ] [BLOCKER] `is_verified=true` salon (no owner) shows "Information reviewed" text label
- [ ] Claimed salon shows "Owner verified" text label

### 4.4 DEC-010 — Area Filter
- [ ] [BLOCKER] Filter label shows "Area" (en), "Περιοχή" (el), "Район" (ru)
- [ ] [BLOCKER] Selecting "Glyfada" in filter returns only Glyfada-district salons
- [ ] Homepage section label: "Popular Areas" (en) / "Δημοφιλείς Περιοχές" (el) / "Популярные районы" (ru)

### 4.5 DEC-006 — No Pricing Exposure
- [ ] [BLOCKER] Header navigation does NOT contain a link to `/pricing` or `/plans`
- [ ] Footer does NOT contain a link to `/pricing` or `/plans`
- [ ] Direct GET `/pricing` returns 404 (page not found) or 301 redirect to home

### 4.6 DEC-016 — Anonymous Access
- [ ] [BLOCKER] All 3 contact CTAs work in incognito (no login required)
- [ ] Search, area filter, and salon detail page load in incognito (no redirect to /login)

---

## Section 5 — Analytics

- [ ] [BLOCKER] GA4 Measurement ID is live (not placeholder)
- [ ] [BLOCKER] GA4 Realtime shows pageview event when browsing the site
- [ ] [BLOCKER] Clicking "Call salon" fires `contact_action` event in GA4 Realtime
- [ ] [BLOCKER] Clicking "Message on WhatsApp" fires `contact_action` event with `action_type: whatsapp`
- [ ] [BLOCKER] Clicking "Visit website" fires `contact_action` event with `action_type: website`
- [ ] Each `contact_action` event includes `salon_id` and `salon_name` parameters
- [ ] Admin user session is filtered out from GA4 (verify by checking "Filters" in GA4 Admin)
- [ ] Google Search Console: property verified
- [ ] GA4 data retention = 14 months (verify in GA4 Admin → Data Settings → Data Retention)
- [ ] GA4 `contact_action` custom event appears in GA4 → Events list (may take 24h; verify event definition)

---

## Section 6 — Legal & GDPR

- [ ] [BLOCKER] `/el/privacy` returns 200 with Privacy Policy content
- [ ] [BLOCKER] Privacy Policy mentions "Google Analytics" by name
- [ ] [BLOCKER] Privacy Policy linked in footer on all pages
- [ ] [BLOCKER] Cookie consent banner appears on first visit (test in incognito)
- [ ] Cookie consent banner has "Accept" button and link to Privacy Policy
- [ ] After clicking Accept: `lookla_consent=1` cookie is set
- [ ] GA4 script does NOT fire on pages where consent cookie is absent
- [ ] `/uk/privacy`, `/en/privacy`, `/ru/privacy` also return 200
- [ ] No GDPR-sensitive data (IP, exact location, email) is logged in plaintext in application logs
- [ ] `/[locale]/privacy` mentions account deletion procedure: "email hello@lookla.gr to request account deletion within 30 days"

---

## Section 7 — New Pages

- [ ] `/el/about`, `/en/about`, `/ru/about` return 200
- [ ] `/el/contact`, `/en/contact`, `/ru/contact` return 200
- [ ] Both pages linked in footer
- [ ] About page does not mention booking, reservation, or payment features
- [ ] Contact page shows `hello@lookla.gr` for owner inquiries
- [ ] Contact page mentions the Report button on salon pages

---

## Section 8 — SEO & Crawlability

- [ ] [BLOCKER] `GET https://lookla.gr/robots.txt` returns 200 with Disallow rules for /admin, /api/, /dashboard (T-036)
- [ ] `<meta name="robots" content="noindex">` is NOT present on salon detail pages
- [ ] `<title>` is set on salon detail pages (SSR metadata)
- [ ] `<meta name="description">` is set on salon detail pages
- [ ] X-Robots-Tag: noindex on `/api/salons/*/services` (bot protection, SECURITY.md §3)
- [ ] Canonical URLs are correct (`https://lookla.gr/en/salons/slug` not `http://`)

---

## Section 9 — Performance

- [ ] [BLOCKER] PageSpeed Insights (mobile): LCP < 2.5s on any tested salon detail page
- [ ] PageSpeed Insights (mobile): CLS < 0.1 on salon detail
- [ ] Hero photo on salon detail: confirm it uses `next/image` with `priority={true}`
- [ ] Hero photo: confirm it loads from `cdn.lookla.gr` (R2), not Google Places proxy URL
- [ ] Search page: first load < 3s (incognito, no cache)
- [ ] `docker stats` under normal browsing: no service OOM

---

## Section 10 — Code Quality

- [ ] [BLOCKER] `pytest backend/tests/` passes with 0 failures
- [ ] [BLOCKER] Unit tests for `is_bot()` pass with ≥5 test cases
- [ ] [BLOCKER] Unit tests for `_batch_open_now()` pass with DST edge case
- [ ] `translate.py` has try/except for OpenAI API failures
- [ ] React error boundary wrapping `SalonDetailClient` is in place
- [ ] No `console.log` statements in production frontend code: `grep -r "console.log" frontend/app/ frontend/components/` returns 0 results
- [ ] No `print()` statements in production backend code: `grep -r "^print(" backend/app/` returns 0 results
- [ ] `ruff check backend/app/` passes with 0 errors
- [ ] `eslint frontend/app/` passes with 0 errors

---

## Section 11 — Manual QA Sign-off

Complete each journey in production (not localhost):

### J-01 — Primary conversion journey (Russian persona)
- [ ] Visit `https://lookla.gr/ru` (homepage in Russian)
- [ ] Search "маникюр" (manicure in Russian)
- [ ] Filter by area "Glyfada"
- [ ] Results show salons in Glyfada
- [ ] Open a salon page
- [ ] "Message on WhatsApp" button visible (no login required)
- [ ] Click: WhatsApp opens with correct salon number
- [ ] `contact_action` event appears in GA4 Realtime within 30 seconds

### J-02 — Call journey (Greek persona)
- [ ] Visit `https://lookla.gr/el` (homepage in Greek)
- [ ] Search "κομμωτήριο" (hairdresser in Greek)
- [ ] Open a salon page
- [ ] "Κλήση σαλονιού" (Call salon) button visible
- [ ] Phone number displayed on desktop is readable and correctly formatted
- [ ] `contact_action` event with `action_type: phone` appears in GA4 Realtime

### J-03 — Review and badge check
- [ ] Open any salon with ≥1 Google review
- [ ] "Source: Google Reviews / Imported: Yes / Original: No" header visible above reviews
- [ ] Open any `is_verified=true` salon
- [ ] Text "Information reviewed" or "Owner verified" visible (no ✓ icon)
- [ ] No booking buttons visible anywhere on the page

**QA pass date:** ___________
**QA signed off by:** ___________

---

## Post-Launch First Week

These items are not launch blockers but must be completed within 7 days of launch:

- [ ] Monitor `docker logs beauty_api` daily for unexpected errors
- [ ] Check GA4 Realtime daily for first 7 days
- [ ] Verify first organic Google sessions arrive via Search Console
- [ ] First week `contact_action` count: document in GA4 note
- [ ] Check `/opt/backups/` to confirm daily backup cron ran successfully

---

*Last updated: 2026-07-09*
