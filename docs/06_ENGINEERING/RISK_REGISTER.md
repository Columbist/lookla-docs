---
title: Risk Register
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 08_REVIEWS/ARCHITECTURE_REVIEW.md
  - 05_ROADMAP/MILESTONE_M01.md
  - 04_ARCHITECTURE/SECURITY.md
  - 06_ENGINEERING/AUDIT.md
implementation_status: N/A — risk management document; reviewed before each milestone
---

# Risk Register
**Lookla Beauty Marketplace — M-01**

> **Probability:** L = Low (<25%), M = Medium (25–60%), H = High (>60%)
> **Impact:** L = Minor degradation, M = Feature unavailable, H = Launch blocked or data loss
> **Score:** P×I — HH = Critical, HM/MH = High, MM/HL/LH = Medium, ML/LM/LL = Low
>
> **Status:** Open = active risk; Mitigated = controls in place; Accepted = known, no action planned; Closed = no longer relevant

---

## Category 1 — Technical Risks

### R-001 — No database migrations (Alembic absent)
**Probability:** H | **Impact:** H | **Score:** Critical
**Category:** Technical
**Status:** Open (T-001 resolves this)

**Description:** DEC-010 requires adding `address_district` and `address_region` columns. Without Alembic, the migration is ad-hoc and untracked. If the production DB is rebuilt from backup or from scratch, these columns are absent. The API crashes on startup if models reference non-existent columns.

**Scenario:** Disk failure → restore from backup → deploy latest code → API crashes on first query → complete outage.

**Mitigation:**
- Set up Alembic before any schema change (T-001)
- Commit migration file alongside code change (T-002)
- Write Alembic downgrade step for every migration

**Residual risk after mitigation:** Low — Alembic tracks schema state in DB; mismatches are caught at startup.

---

### R-002 — Zero test coverage on critical path functions
**Probability:** H | **Impact:** M | **Score:** High
**Category:** Technical
**Status:** Open (T-030 resolves this)

**Description:** `is_bot()`, `_batch_open_now()`, `_translate_query()`, and JWT refresh have no tests. Any change to these functions is blind. Regressions are discovered in production.

**Scenario:** Developer updates `is_bot()` to block a new scraper → new regex accidentally matches Safari on iOS → real users are blocked → search returns bot protection response to real users.

**Mitigation:**
- Write tests before changing tested functions (T-030)
- Definition of Done requires tests when touching critical path (DEVELOPMENT_STANDARDS.md §5)

**Residual risk after mitigation:** Low — regression caught in tests, not production.

---

### R-003 — SalonDetailClient.tsx crashes blank page (no error boundary)
**Probability:** M | **Impact:** H | **Score:** High
**Category:** Technical
**Status:** Open (T-029 resolves this)

**Description:** A null reference, malformed API response, or Leaflet map error in `SalonDetailClient.tsx` crashes the entire salon detail page to a blank screen. No contact information is visible. Zero `contact_action` events can be recorded.

**Scenario:** A salon has `null` for `opening_hours` and the open/closed badge code doesn't guard for null → crash → blank page on 15% of salon pages.

**Mitigation:**
- Add React error boundary wrapping `SalonDetailClient` (T-029)
- Fallback shows salon name, address, contact buttons from SSR props

**Residual risk after mitigation:** Low — crash is contained; users can still make contact from fallback.

---

### R-004 — OpenAI API unavailability blocks first-view translation
**Probability:** L | **Impact:** M | **Score:** Medium
**Category:** Technical
**Status:** Open (T-031 resolves this)

**Description:** When a Russian-speaking user is the first to view an untranslated salon, the backend calls OpenAI. If OpenAI is down, the translate.py call raises an exception that propagates to a 500 response.

**Scenario:** OpenAI outage → first Russian user sees a 500 error instead of the salon page → user bounces.

**Mitigation:**
- Add try/except in translate.py (T-031) — return original Greek text on failure
- Translation failure is logged but does not crash the request

**Residual risk after mitigation:** Low — Greek text is shown instead of Russian; user sees the page, not an error.

---

### R-005 — Synchronous SQLAlchemy under concurrent load
**Probability:** L | **Impact:** M | **Score:** Medium
**Category:** Technical
**Status:** Accepted (post-MVP concern)

**Description:** FastAPI is async but SQLAlchemy is synchronous. Under concurrent traffic, all threads may block waiting for DB I/O. At MVP traffic levels (tens of users), this is not expected to manifest.

**Threshold:** If average response time exceeds 500ms under realistic load, investigate async migration.

**Mitigation:** None for MVP. Post-MVP: migrate to asyncpg + SQLAlchemy 2.0 async.

---

### R-006 — `is_verified` semantic ambiguity (CONTRADICTION-01)
**Probability:** H | **Impact:** M | **Score:** High
**Category:** Technical
**Status:** Open (T-011, T-024 resolve this)

**Description:** `is_verified` currently serves two meanings: admin-reviewed (DEC-014) and owner-claimed (claim flow). The frontend cannot display the correct label without additional data. Until T-024 adds `is_owner_claimed` to the API response, the badge will show a wrong or inconsistent label.

**Mitigation:**
- Resolve CONTRADICTION-01 by using LEFT JOIN on `salon_owners` (T-024)
- Update frontend badge to use `is_owner_claimed` field (T-011)

**Residual risk after mitigation:** Low — single source of truth for each state.

---

## Category 2 — Product Risks

### R-007 — MVP metric not reached (< 500 contact actions in 90 days)
**Probability:** M | **Impact:** H | **Score:** High
**Category:** Product
**Status:** Accepted (success is not guaranteed; that's the point of the metric)

**Description:** DEC-008 defines success as 500 `contact_action` events in 90 days. If Lookla does not acquire enough organic traffic, or if users find but don't contact salons, the metric will not be reached.

**Failure modes:**
- Zero SEO traction → no organic traffic
- Traffic exists but phone numbers are wrong → users call and get nothing → no repeat visits
- Language barrier → Russian-speaking users can't find relevant salons

**Mitigation:**
- GA4 + Search Console in place to diagnose early (DEC-017)
- Russian-language support mandatory (DEC-011)
- Manual data quality review of phone numbers before launch

**Residual risk after mitigation:** Medium — market risk cannot be fully engineered away. Post-M-01 evidence determines M-02 scope.

---

### R-008 — Wrong phone numbers in scraped data
**Probability:** M | **Impact:** M | **Score:** Medium
**Category:** Product
**Status:** Partially mitigated (admin review reduces, does not eliminate)

**Description:** 6300 salons were scraped from public sources. Not all phone numbers are current. A user who taps "Call salon" and reaches a wrong number has a bad experience and does not return.

**Scenario:** 20% of salons have outdated phone numbers → 20% of contact actions result in wrong connections → real conversion rate is 80% of measured.

**Mitigation:**
- Admin reviews and corrects phone numbers before launch (part of M-01 exit criteria: ≥300 verified phone numbers)
- Report button on salon detail allows users to flag wrong numbers
- Admin panel shows report flags

**Residual risk after mitigation:** Medium — scraped data will always have some errors; ongoing curation process needed.

---

### R-009 — Low search result quality due to district mapping errors
**Probability:** M | **Impact:** M | **Score:** Medium
**Category:** Product
**Status:** Open (T-003 backfill quality determines this)

**Description:** If the `address_city → address_district` backfill mapping is incomplete, salons in popular districts won't appear when users filter by that district. Users see fewer results than exist, reducing engagement.

**Scenario:** User filters by "Glyfada" → 50 results shown instead of 142 (because 92 salons have Greek-spelled `address_city` not in the mapping) → user concludes Lookla has poor coverage.

**Mitigation:**
- T-003 backfill targets ≥80% of Athens salons
- Verify backfill coverage query before launch: `SELECT address_district, count(*) FROM salons WHERE address_city ILIKE '%Athens%' GROUP BY 1`
- Edge case: salons with `address_city = NULL` map to no district (acceptable)

**Residual risk after mitigation:** Low-Medium — 80%+ coverage is sufficient for MVP; post-MVP improve mapping.

---

## Category 3 — Infrastructure Risks

### R-010 — Single database server, no backup
**Probability:** L | **Impact:** H | **Score:** High
**Category:** Infrastructure
**Status:** Open (T-026 resolves this)

**Description:** All Lookla data lives in a single PostgreSQL instance on a single VPS (10.10.0.1). No automated backup exists. Disk failure or accidental `docker compose down -v` destroys all data.

**Mitigation:**
- Daily pg_dump cron (T-026): backup at 03:00, 7-day retention
- Restore procedure: `zcat backup.sql.gz | docker exec -i lookla_db psql -U postgres lookla`

**Residual risk after mitigation:** Medium — daily backups mean max 24h data loss. For MVP, acceptable.

---

### R-011 — Single server, no redundancy
**Probability:** L | **Impact:** H | **Score:** High
**Category:** Infrastructure
**Status:** Accepted (acceptable for MVP)

**Description:** The entire stack (API, frontend, DB, crawlers) runs on 10.10.0.1. If the server goes down, Lookla is offline.

**Mitigation:** None for MVP. Post-MVP: second server with Nginx load balancer.

**Residual risk after mitigation:** High — but accepted for MVP scale. Downtime is bad but not catastrophic before the platform has users.

---

### R-012 — Cloudflare R2 / CDN dependency
**Probability:** L | **Impact:** M | **Score:** Low
**Category:** Infrastructure
**Status:** Accepted

**Description:** Salon photos are served from Cloudflare R2 (`cdn.lookla.gr`). If R2 is unavailable, photos don't load — degraded UX but not a complete outage.

**Mitigation:** None needed for MVP. `next/image` handles missing images with graceful fallback. Cloudflare has high availability SLA.

---

## Category 4 — Legal Risks

### R-013 — GDPR violation: GA4 without Privacy Policy or consent
**Probability:** H (if not resolved) | **Impact:** H | **Score:** Critical
**Category:** Legal
**Status:** Open (T-017, T-018, T-019 resolve this)

**Description:** Greece is an EU member. GDPR requires:
1. Disclosure of data collection (Privacy Policy)
2. User consent before analytics tracking
3. User rights (access, deletion, portability)

Deploying GA4 without a Privacy Policy and cookie consent banner is a GDPR violation.

**Scenario:** User complains to Hellenic Data Protection Authority (HDPA) → investigation → fine up to €20M or 4% of annual turnover.

**Mitigation:**
- Privacy Policy page live before GA4 activation (T-017)
- Cookie consent banner before GA4 script loads (T-018)
- GA4 IP anonymization enabled (T-019)
- GA4 data retention set to 14 months (T-019)

**Residual risk after mitigation:** Low — basic GDPR compliance achieved. Full DPA compliance is an ongoing process.

---

### R-014 — Google Reviews attribution compliance (DEC-013)
**Probability:** M | **Impact:** M | **Score:** Medium
**Category:** Legal
**Status:** Open (T-012 resolves this)

**Description:** Displaying Google Reviews without attribution violates Google's Terms of Service for Places API data and potentially EU copyright law (reviews are user-generated content, subject to copyright).

**Required attribution text:** "Source: Google Reviews / Imported: Yes / Original: No"

**Mitigation:**
- Add review source header (T-012, DEC-013)
- Label must be visible without scrolling, not behind a toggle

**Residual risk after mitigation:** Low — attribution is explicit and visible.

---

### R-015 — robots.txt absent — admin pages indexed by Google
**Probability:** H | **Impact:** M | **Score:** High
**Category:** Legal
**Status:** Open (T-029's robots.txt creation resolves this — see EPIC-09)

**Description:** Without `public/robots.txt`, Googlebot indexes all pages including `/admin`, `/dashboard`, `/account`. This:
- Exposes admin URL structure
- May allow sensitive admin page HTML to appear in Google search results
- Wastes crawl budget on non-public pages

**Mitigation:**
- Create `public/robots.txt` with Disallow rules for private paths (part of T-029 acceptance criteria)

```
User-agent: *
Disallow: /admin
Disallow: /dashboard
Disallow: /account
Disallow: /api/
Allow: /
```

---

## Category 5 — Performance Risks

### R-016 — LCP > 2.5s on salon detail page
**Probability:** M | **Impact:** M | **Score:** Medium
**Category:** Performance
**Status:** Open (verified by PageSpeed Insights before launch)

**Description:** The LCP element on salon detail is the hero photo. If the photo is served from Google Places proxy (not R2 CDN), or if `priority={true}` is missing on the `<Image>` component, LCP will exceed 2.5s. This harms SEO ranking.

**Mitigation:**
- Use `next/image` with `priority={true}` on hero photo (PERFORMANCE.md §3)
- Ensure hero photo is served from `cdn.lookla.gr` (R2), not Google Places proxy
- Verify with PageSpeed Insights before launch (M-01 exit criterion)

**Residual risk after mitigation:** Low — verified pre-launch.

---

### R-017 — Search returns 0 results in Russian due to wrong synonyms
**Probability:** M | **Impact:** H | **Score:** High
**Category:** Performance (user experience)
**Status:** Open (T-006 + T-032 resolve this)

**Description:** P-02 persona (Russian-speaking) searches for "маникюр" (manicure) or "стрижка" (haircut). If the SERVICE_SYNONYMS dict doesn't contain these terms or maps them incorrectly, search returns empty results.

**Scenario:** A Russian user searches "маникюр" → 0 results → user concludes Lookla has no nail salons in Athens → exits → lost conversion.

**Mitigation:**
- Verify `_translate_query()` handles all common Russian service terms (T-030 unit tests cover this)
- Manual translation QA in Russian locale before launch (T-032)
- CITY_SYNONYMS extended with district-level Russian names (T-006)

**Residual risk after mitigation:** Low — tested before launch.

---

## Category 6 — Security Risks

### R-018 — Cloudflare Turnstile integration unverified
**Probability:** M | **Impact:** M | **Score:** Medium
**Category:** Security
**Status:** Open

**Description:** SECURITY.md notes that Cloudflare Turnstile is "configured, integration unverified." If Turnstile is not actually enforced on the registration endpoint, bot registration is unlimited.

**Scenario:** Spam bots register accounts and submit claims or reports in bulk, flooding the admin panel.

**Mitigation:**
- Verify Turnstile is actually enforced on `/api/auth/register` before launch
- Test: submit registration without Turnstile token → if 200 is returned, Turnstile is not enforced
- If not enforced: either fix it or add server-side token validation

**Residual risk after mitigation:** Low if verified. Medium if left unverified.

---

### R-019 — JWT refresh token rotation race condition
**Probability:** L | **Impact:** H | **Score:** Medium
**Category:** Security
**Status:** Open (T-030 auth tests partially cover this)

**Description:** SECURITY.md documents refresh token rotation. If a client sends two simultaneous refresh requests (race condition on slow networks), one may succeed and the other may fail with 401 (token already rotated). The user is logged out unexpectedly.

**Scenario:** Mobile user with poor connection sends duplicate refresh → one succeeds → other fails → user must re-login.

**Mitigation:**
- Not blocking for MVP (edge case, acceptable UX cost)
- Post-MVP: implement token family tracking (see SECURITY.md)

**Residual risk after mitigation:** Low for MVP — rare edge case, non-destructive (user just re-logs in).

---

### R-020 — .env file accidentally committed
**Probability:** L | **Impact:** H | **Score:** Medium
**Category:** Security
**Status:** Accepted (policy mitigation)

**Description:** If `.env` is committed to git (monorepo includes `.env` at root), all secrets (JWT key, OpenAI API key, database credentials) are exposed in git history permanently.

**Mitigation:**
- `.gitignore` must include `.env` (verify)
- DEVELOPMENT_STANDARDS.md §8 explicitly states: "Never hardcode values that differ between environments"
- Pre-commit hook to block `.env` files (optional but recommended)

**Verification:**
```bash
git ls-files | grep "\.env"  # should return nothing except .env.example
```

---

## Risk Summary

| ID | Category | Description | Score | Status |
|---|---|---|---|---|
| R-001 | Technical | No Alembic | Critical | Open → T-001 |
| R-002 | Technical | Zero tests on critical functions | High | Open → T-030 |
| R-003 | Technical | No error boundary | High | Open → T-029 |
| R-004 | Technical | OpenAI SPOF | Medium | Open → T-031 |
| R-005 | Technical | Sync SQLAlchemy | Medium | Accepted |
| R-006 | Technical | is_verified ambiguity | High | Open → T-024 |
| R-007 | Product | MVP metric not reached | High | Accepted |
| R-008 | Product | Wrong phone numbers | Medium | Partial |
| R-009 | Product | District mapping gaps | Medium | Open → T-003 |
| R-010 | Infrastructure | No DB backup | High | Open → T-026 |
| R-011 | Infrastructure | Single server | High | Accepted |
| R-012 | Infrastructure | R2/CDN dependency | Low | Accepted |
| R-013 | Legal | GDPR without consent | Critical | Open → T-017/018/019 |
| R-014 | Legal | Google Reviews attribution | Medium | Open → T-012 |
| R-015 | Legal | robots.txt absent | High | Open → T-029 |
| R-016 | Performance | LCP > 2.5s | Medium | Open → verified pre-launch |
| R-017 | Performance | Russian search returns 0 | High | Open → T-006/T-032 |
| R-018 | Security | Turnstile unverified | Medium | Open → verify |
| R-019 | Security | JWT refresh race | Medium | Accepted |
| R-020 | Security | .env commit | Medium | Accepted (policy) |

**Critical risks (launch blockers):** R-001, R-013
**High risks that must be mitigated pre-launch:** R-002, R-003, R-006, R-010, R-015, R-017

---

*Last updated: 2026-07-09*
