---
title: Architecture Review
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 04_ARCHITECTURE/BACKEND_ARCHITECTURE.md
  - 04_ARCHITECTURE/FRONTEND_ARCHITECTURE.md
  - 04_ARCHITECTURE/DATABASE_SCHEMA.md
  - 04_ARCHITECTURE/API_SPECIFICATION.md
  - 04_ARCHITECTURE/SECURITY.md
  - 04_ARCHITECTURE/PERFORMANCE.md
  - 03_PAGES/SALON.md
  - 02_DESIGN/UX_FLOWS.md
implementation_status: N/A — review document; no code changes
---

# Architecture Review
**Lookla Beauty Marketplace**

> This document is a cross-document consistency audit of all approved technical architecture and product specifications.
>
> **Methodology:** Every section below is grounded in a specific inconsistency, gap, or risk found by comparing documents against each other. No finding is invented — each references the exact documents that contradict, overlap, or omit.
>
> **Scope:** Contradictions between documents, overengineering, underengineering, single points of failure, scalability risks, MVP violations.
>
> **Action required:** Each finding is marked `[BLOCKER]`, `[HIGH]`, `[MEDIUM]`, or `[LOW]`. Blockers must be resolved before development begins on the affected area.

---

## SECTION 1 — Cross-Document Contradictions

These are cases where two approved documents say different things. Both cannot be correct.

---

### CONTRADICTION-01 — `is_verified` has two incompatible meanings
**Severity: [BLOCKER]**
**Documents:** DATABASE_SCHEMA.md §Salon, BACKEND_ARCHITECTURE.md §Owner, DEC-014, API_SPECIFICATION.md §PATCH /api/admin/salons

**Finding:**

`DATABASE_SCHEMA.md` states:
> "`is_verified = true` means 'Information reviewed by admin' (DEC-014). NOT owner-claimed."

`BACKEND_ARCHITECTURE.md §Owner claiming flow` states:
> "On successful claim verification: `salons.is_verified = true`"

`DATABASE_SCHEMA.md §ClaimRequest` also states:
> "On successful verification: `salons.is_verified` is set to true (representing owner-verified)"

**Contradiction:** The same boolean column is used to represent two different states:
- Admin-reviewed (set by admin via `PATCH /api/admin/salons/{id}`)
- Owner-claimed (set by claim verification flow)

DEC-014 explicitly distinguishes these states: "Information reviewed" (admin) vs "Owner verified" (claimed). A single boolean cannot express this distinction.

**Impact:**
- UI cannot display the correct label from `is_verified` alone
- An admin-reviewed salon and an owner-claimed salon will show the same label (whichever is implemented)
- The frontend has no way to know which state to display without additional data

**Resolution required before implementation:**

Option A: Add `is_owner_claimed` boolean column to `salons` table
- `is_verified = true AND is_owner_claimed = false` → "Information reviewed" (admin)
- `is_verified = true AND is_owner_claimed = true` → "Owner verified"
- Both false → no badge

Option B: Derive owner-claimed from `salon_owners` table (already exists as a junction table)
- `EXISTS (SELECT 1 FROM salon_owners WHERE salon_id = ?)` → "Owner verified"
- `is_verified = true AND NOT EXISTS(...)` → "Information reviewed"
- No new column needed; requires a JOIN on every salon fetch

**Recommendation:** Option B — no schema change, uses existing data.

**Resolved (2026-07-14, T-024):** Implemented via the correlated `EXISTS` form already described above, **not** a `LEFT JOIN`. `salon_owners` has no unique constraint on `salon_id` alone (only a composite PK on `(user_id, salon_id)`), so a plain join risked duplicating a salon row if it ever had more than one owner row; `EXISTS` always yields exactly one boolean per salon regardless. `is_owner_claimed` is now a required boolean on `GET /api/salons` and `GET /api/salons/{id_or_slug}`. T-011 (the frontend label) is unblocked.

---

### CONTRADICTION-02 — `GET /api/areas` is not in BACKEND_ARCHITECTURE.md router list
**Severity: [HIGH]**
**Documents:** API_SPECIFICATION.md §Areas, BACKEND_ARCHITECTURE.md §Directory Structure

**Finding:**

`API_SPECIFICATION.md` defines `GET /api/areas` as a new required endpoint:
> "This endpoint does not exist yet. Required for MVP."

`BACKEND_ARCHITECTURE.md §Directory Structure` lists 13 routers:
> `salons.py, search.py, auth.py, owner.py, professionals.py, masters.py, bookings.py, chat.py, payments.py, admin.py, categories.py, media.py, reports.py`

`GET /api/areas` appears in no router. It is also not listed in the required MVP changes table in `BACKEND_ARCHITECTURE.md`.

**Impact:** A developer following BACKEND_ARCHITECTURE.md exclusively would not create this endpoint. A developer following API_SPECIFICATION.md would create it but not know where to put it.

**Resolution:** Add to `BACKEND_ARCHITECTURE.md §11 Required Changes for MVP`:

```
| Add GET /api/areas endpoint | DEC-010 | categories.py (extend) or new areas.py | Low |
```

Suggest placing in `categories.py` since areas are reference/classification data — same nature as categories.

---

### CONTRADICTION-03 — `address_district` migration plan is undefined
**Severity: [HIGH]**
**Documents:** DATABASE_SCHEMA.md §DEC-010, BACKEND_ARCHITECTURE.md §Required Changes, API_SPECIFICATION.md §GET /api/salons

**Finding:**

Three documents reference `address_district`:
- `DATABASE_SCHEMA.md`: "NEW — required by DEC-010... DEC-010 migration note: mapping `address_city` values into hierarchy"
- `BACKEND_ARCHITECTURE.md`: "Add `address_district`, `address_region` columns to salons"
- `API_SPECIFICATION.md`: "`area` param maps to `address_district` filter"

None of these documents define HOW the 6300 existing salons get their `address_district` value populated. The column is added empty; all existing salons have `NULL` district.

**Consequence:** After adding the column and deploying the new area filter:
- All existing salons appear in "All areas" but not in any specific district
- Searching by "Glyfada" returns 0 results even if salons have `address_city = 'Glyfada'`
- The MVP area filter is non-functional until data is backfilled

**Resolution required:** A data migration script must be defined:

```sql
-- Backfill approach A: map address_city → address_district directly
-- (when address_city already contains the district name)
UPDATE salons SET address_district = address_city
WHERE address_city IN ('Glyfada', 'Kolonaki', 'Kallithea', 'Marousi', 'Kifissia', ...);

-- Backfill approach B: use address_city → district mapping dict from backend
-- Apply via a Python migration script (can use existing mapping dict)
```

This must be a planned migration task, not a side note. Add to IMPLEMENTATION_BACKLOG.md as T-002a (data backfill).

---

### CONTRADICTION-04 — Legacy `?city=` param compatibility undefined
**Severity: [MEDIUM]**
**Documents:** API_SPECIFICATION.md §GET /api/salons, FRONTEND_ARCHITECTURE.md §URL State

**Finding:**

`API_SPECIFICATION.md` states:
> "`area` param takes precedence over `city` param when both provided"

But no document specifies what happens to existing URLs using `?city=Athens` after the area filter migration:
- Bookmarked links with `?city=` will silently switch to legacy behavior
- The `CityGrid` on homepage links to `?city=` params (current implementation)
- `FRONTEND_ARCHITECTURE.md` says rename `CityGrid → AreaGrid` but doesn't specify URL param migration

**Consequence:** After deployment, homepage city tile links still generate `?city=Glyfada` URLs. The new filter uses `?area=glyfada`. These are different and produce different results.

**Resolution:** Define explicitly in API_SPECIFICATION.md that during transition:
1. Backend accepts both `city` and `area` params (already noted)
2. Frontend migrates to `?area=` only at the same time as UI update (atomic change)
3. Old `?city=` URLs continue working via the legacy filter fallback

---

### CONTRADICTION-05 — `ClaimRequest.channel` only email works, but spec lists others
**Severity: [LOW]**
**Documents:** DATABASE_SCHEMA.md §ClaimRequest, BACKEND_ARCHITECTURE.md §Owner, API_SPECIFICATION.md §Owner

**Finding:**

All three documents note:
> "Only `channel = 'email'` works. SMS/WhatsApp channel param exists but no API key configured."

The `ClaimRequest.channel` CHECK constraint allows `('email', 'sms', 'whatsapp')`. The schema accepts values that the application cannot process.

**Consequence:** An API caller could send `channel: 'whatsapp'` and the request would pass validation, but no message would be sent — silent failure.

**Resolution (MVP):** Add a backend validation check: if `channel != 'email'`, return 400 with "Only email channel is currently supported." This prevents silent failures without requiring SMS/WhatsApp infrastructure.

---

## SECTION 2 — Overengineering

These are fully implemented features that are out of MVP scope and add maintenance burden without user value.

---

### OVER-01 — Three fully-implemented systems with zero user exposure
**Severity: [MEDIUM] — not a blocker, but a maintenance risk**

The following backend systems are complete, tested (partially), and consuming maintenance attention:

| System | Code complexity | User exposure | Decision |
|---|---|---|---|
| Booking (`bookings.py`, `appointments` table, slots API) | High | 0% | DEC-015 prohibits booking CTA |
| Chat (`chat.py`, `conversations`, `messages`, `availability_requests` tables) | High | 0% — `/account/messages` exists but unverified | No decision to expose |
| Stripe payments (`payments.py`, `subscription_plans`, `subscriptions` tables, webhook) | High | 0% — `/pricing` page exists; must not be linked (DEC-006) | DEC-006 prohibits exposure |

**Risk:** Every schema migration, dependency update, or security patch to FastAPI must be tested against these systems even though no user can reach them. Three "invisible" routers add ~1000 lines of code that must be understood by any new developer.

**Recommendation:** These are not bugs — they were built speculatively. Do not remove them. But:
1. Add `# [NOT USER-FACING — DEC-006/DEC-015]` comment header to `payments.py`, `bookings.py`
2. Add HTTP 503 response guard at router level: if feature not enabled → 503 "Coming soon"
3. Document in `FEATURE_FLAGS.md` that these are code-complete but intentionally inaccessible

---

### OVER-02 — Two independent search systems with different behavior
**Severity: [HIGH]**
**Documents:** BACKEND_ARCHITECTURE.md §12, AUDIT.md §8

**Finding:** From Engineering Audit §8:
> "There are two independent search systems. System B's category filter is weaker than System A's. The header SearchBar likely routes to System A via the /search page."

- `GET /api/salons` (System A): full CATEGORY_KEYWORDS dict, SERVICE_SYNONYMS, multilingual
- `GET /api/search` (System B): crude `name ILIKE %cat%` filter, Haversine geo

`API_SPECIFICATION.md` documents both endpoints. `FRONTEND_ARCHITECTURE.md` says "Search page uses `/api/salons`."

**Risk:** System B exists and is documented, suggesting future use. But it gives different results for the same query. A developer adding a new feature might route to System B by mistake, giving users worse results.

**Recommendation:**
- Deprecate `GET /api/search` — mark it in the API spec as `[Deprecated — use GET /api/salons]`
- When geo search is needed (post-MVP), extend System A to support `lat/lng/radius` params rather than using System B

---

## SECTION 3 — Underengineering

These are missing capabilities that create real risk before MVP launch.

---

### UNDER-01 — No database migration tooling
**Severity: [BLOCKER]**
**Documents:** AUDIT.md §14, BACKEND_ARCHITECTURE.md §12, DATABASE_SCHEMA.md §Schema Evolution Policy

**Finding:** Every document acknowledges this. No document defines how to solve it before MVP.

The DEC-010 change requires adding 2 new columns (`address_district`, `address_region`) to the `salons` table with 6300 rows. Without Alembic:
- The change is applied as a raw `ALTER TABLE` via `psql` or `docker exec`
- It is not tracked in version control
- If the production DB is rebuilt from scratch, the column is missing
- There is no way to know the exact current state of the production schema

**Risk scenario:** Production DB is corrupted or needs to be restored from backup. The `db/init.sql` (initial schema) does not include `address_district`. Restore → deploy → crash.

**Resolution (MVP-critical):** Before any schema change:
1. Install Alembic: `pip install alembic`
2. `alembic init alembic` in `/backend`
3. Configure `alembic.ini` to use `DATABASE_URL` from environment
4. Import existing SQLAlchemy models into `env.py`
5. `alembic revision --autogenerate -m "baseline"` — captures current state
6. Then create `alembic revision -m "add_address_district_region"` for DEC-010

Without Alembic, do not change the production schema. The risk of an unrecoverable schema drift is too high.

---

### UNDER-02 — Zero test coverage on 4 critical functions
**Severity: [BLOCKER]**
**Documents:** DEVELOPMENT_STANDARDS.md §5, AUDIT.md §14

**Functions that must have tests before any change:**

1. `is_bot(user_agent)` — previously had a bug matching legitimate browsers. No test exists to prevent regression.
2. `_batch_open_now()` — timezone-dependent; DST transitions produce wrong results if `ZoneInfo("Europe/Athens")` is incorrect. Wrong open/closed status = user drives to a closed salon.
3. `_translate_query()` — the SERVICE_SYNONYMS dict controls what "маникюр" becomes in search. A wrong synonym silently produces empty results for Russian-speaking users (primary persona, DEC-009).
4. JWT refresh token rotation — a bug in rotation logic could create orphaned sessions or allow token reuse attacks.

**Consequence:** These functions will be touched during MVP development:
- `is_bot()` — may need updating for new scraper patterns
- `_batch_open_now()` — could be affected by `salon_hours` schema changes
- `_translate_query()` — must be updated when `area` replaces `city` in CITY_SYNONYMS

Changing them without tests is implementing blindly.

---

### UNDER-03 — No error boundaries in React
**Severity: [HIGH]**
**Documents:** FRONTEND_ARCHITECTURE.md §11

**Finding:** `FRONTEND_ARCHITECTURE.md` documents this gap:
> "Current state: No React error boundaries implemented. A runtime error in a client component crashes the visible page."

If `SalonDetailClient.tsx` throws (malformed API response, null reference, Leaflet map error), the entire salon detail page shows a blank screen. The user sees nothing — not even the contact buttons.

**Consequence:** A single-null-pointer crash on the salon detail page blocks ALL contact actions and prevents ANY DEC-008 metric from being recorded.

**Minimum fix:** Wrap `SalonDetailClient` in an error boundary with a degraded fallback showing at minimum the name, address, and contact buttons (from SSR data that is already in the initial HTML).

---

### UNDER-04 — No Privacy Policy before GA4 activation
**Severity: [BLOCKER — legal]**
**Documents:** SECURITY.md §6, FRONTEND_ARCHITECTURE.md §14

**Finding:**
- `SECURITY.md` states: "Privacy Policy page (`/privacy`) must be created before MVP launch"
- `FRONTEND_ARCHITECTURE.md` states: "Create `/[locale]/about` and `/[locale]/contact` pages" but does not explicitly list Privacy Policy
- GA4 is required before launch (DEC-017)
- GDPR requires disclosure of analytics data collection

**Consequence:** Deploying GA4 without a Privacy Policy that discloses GA4 usage is a GDPR violation. Greece is in the EU. No opt-out mechanism + no disclosure = legal risk.

**Resolution:** Before GA4 goes live:
1. Create `/[locale]/privacy` page
2. Add cookie consent banner (minimal: "This site uses analytics to improve the service" + Accept)
3. Configure GA4 IP anonymization in GA4 dashboard

---

### UNDER-05 — No backup schedule documented
**Severity: [HIGH]**
**Documents:** None — this is an omission across all architecture documents

**Finding:** No architecture document mentions database backups. The entire product's data (6300 salons, user accounts, translation cache, claimed listings) lives in a single PostgreSQL instance on a single server.

**Consequence:** A disk failure, accidental `docker compose down -v`, or misconfigured migration wipes the entire dataset.

**Resolution:** At minimum, before MVP launch:
```bash
# Daily backup cron (add to crontab on 10.10.0.1)
0 3 * * * docker exec lookla_db pg_dump -U postgres lookla | gzip > /opt/backups/lookla_$(date +%Y%m%d).sql.gz
find /opt/backups -name "*.sql.gz" -mtime +7 -delete
```

This is not in any current document. Add to `RELEASE_CHECKLIST.md` as a pre-launch gate.

---

## SECTION 4 — Single Points of Failure

All SPOFs below exist today and cannot be fully eliminated without significant infrastructure changes. The goal is to document them, not necessarily fix them before MVP.

---

### SPOF-01 — Single PostgreSQL instance, no documented backup
**Risk:** Complete data loss on disk failure
**Currently mitigated by:** Nothing documented
**MVP mitigation:** Daily pg_dump cron (see UNDER-05)
**Post-MVP:** Read replica + automated backup to separate storage (Cloudflare R2 or S3)

---

### SPOF-02 — OpenAI API downtime blocks first-view translation
**Risk:** First user to view an untranslated salon in Russian sees untranslated Greek content
**Currently mitigated by:** Translation is cached after first success — subsequent views unaffected
**MVP mitigation:** Add try/except in `translate.py`; if OpenAI fails, return original Greek text without crashing. Currently: unclear if this exists.
**Verify:** Check `translate.py` for error handling on OpenAI API call. If absent, add:
```python
try:
    result = client.chat.completions.create(...)
except Exception:
    return original_names  # graceful degradation
```

---

### SPOF-03 — Resend email API downtime breaks owner claim flow
**Risk:** Owner requests claim code; Resend is down; code never arrives; owner cannot claim
**Scope:** Not user-facing in MVP (claim UI is hidden). Not a launch blocker.
**Post-MVP:** Add retry queue (Celery task for email) or fallback email provider

---

### SPOF-04 — Single server, no redundancy
**Risk:** Server 10.10.0.1 goes down → Lookla is completely offline
**Currently mitigated by:** Nothing (single VPS)
**MVP acceptance:** Acceptable for MVP scale. Single-server architecture is appropriate for validation phase.
**Post-MVP threshold:** If M-01 succeeds and traffic justifies it, add a second server with Nginx load balancer before M-02.

---

### SPOF-05 — Redis is a SPOF for Celery crawlers
**Risk:** Redis goes down → crawlers cannot run → salon data stops updating
**Currently mitigated by:** Crawlers run on a schedule (weekly); if one run fails, next week's run recovers
**MVP impact:** Low — crawler data freshness is weekly anyway

---

## SECTION 5 — Scalability Issues

Not relevant for MVP, but should be documented before architecture decisions lock them in.

---

### SCALE-01 — Synchronous SQLAlchemy blocks FastAPI event loop
**Documents:** BACKEND_ARCHITECTURE.md §1, PERFORMANCE.md §9

**Finding:** FastAPI is an async framework (ASGI), but SQLAlchemy is used synchronously with psycopg2. This means each DB query blocks the event loop thread. Under concurrent requests, threads pile up.

**MVP impact:** Negligible (expected <100 concurrent users at launch)
**Threshold:** When average response time under load exceeds 500ms, migrate to `asyncpg` + `SQLAlchemy 2.0 async`
**Cost of migration:** High — all `db.query()` calls become `await db.execute()`. Do not migrate speculatively.

---

### SCALE-02 — Photo R2 migration happens synchronously in request thread
**Documents:** BACKEND_ARCHITECTURE.md §10, PERFORMANCE.md §3

**Finding:** When a user views a salon with un-migrated Google Places photos:
1. API receives GET /api/media/photo/{id}
2. Fetches photo from Google (network I/O, ~200-500ms)
3. Uploads to R2 (network I/O, ~500ms-2s)
4. Returns image bytes

This is 700ms-2.5s of blocking I/O in a synchronous request thread.

**MVP impact:** Acceptable — each photo is migrated once. After migration, requests go to CDN directly.
**Post-MVP:** Move to Celery task with placeholder returned immediately.

---

### SCALE-03 — No cache invalidation strategy
**Documents:** PERFORMANCE.md §6

**Finding:** Categories and areas are cached with `revalidate: 86400` (24h). If a new category is added, users see stale category lists for up to 24 hours.

**MVP impact:** Categories don't change during MVP. Not a concern.
**Post-MVP:** Add a manual cache bust endpoint (`POST /api/admin/cache-invalidate`) when categories change.

---

## SECTION 6 — MVP Violations (live in production now)

These are confirmed gaps between current code and approved product decisions. They are regressions against specifications, not future work.

| ID | Violation | Decision | Current State | Fix Required |
|---|---|---|---|---|
| MVP-V01 | Booking stub buttons visible on salon detail | DEC-015 | Stub CTAs present in SalonDetailClient | Remove; replace with contact CTAs |
| MVP-V02 | Reviews shown without Google source label | DEC-013 | No source header in reviews section | Add section header |
| MVP-V03 | ✓ badge instead of "Information reviewed" text | DEC-014 | is_verified shows as ✓ icon | Replace with text label |
| MVP-V04 | "City" filter returns districts without area hierarchy | DEC-010 | `?city=` param, flat list | Add `?area=` param + district list |
| MVP-V05 | Language switcher only in footer | HOME.md spec | Header has no language switcher | Move/add to header |
| MVP-V06 | `/pricing` page may be linked in navigation | DEC-006 | Navigation links unverified | Audit Header.tsx for /pricing link |

**All 6 violations must be resolved before MVP launch.** None require product decisions — they are implementation tasks against approved decisions.

---

## SECTION 7 — Summary Findings Table

| ID | Severity | Type | Resolution required |
|---|---|---|---|
| CONTRADICTION-01 | BLOCKER | is_verified ambiguity | Add Option B JOIN on salon_owners |
| CONTRADICTION-02 | HIGH | Missing router for /api/areas | Add to BACKEND_ARCHITECTURE.md |
| CONTRADICTION-03 | HIGH | No data backfill plan | Define migration script for address_district |
| CONTRADICTION-04 | MEDIUM | URL param migration undefined | Specify atomic `?city→?area` transition |
| CONTRADICTION-05 | LOW | ClaimRequest channel validation | Add 400 for non-email channels |
| OVER-01 | MEDIUM | 3 unused complete systems | Add feature guard headers |
| OVER-02 | HIGH | Duplicate search systems | Deprecate /api/search |
| UNDER-01 | BLOCKER | No Alembic | Set up before any schema change |
| UNDER-02 | BLOCKER | No tests on 4 critical functions | Write before changing those functions |
| UNDER-03 | HIGH | No React error boundaries | Wrap SalonDetailClient |
| UNDER-04 | BLOCKER | No Privacy Policy before GA4 | Create /privacy page first |
| UNDER-05 | HIGH | No DB backup | Add daily pg_dump cron |
| SPOF-01 | HIGH | Single DB, no backup | pg_dump cron (see UNDER-05) |
| SPOF-02 | MEDIUM | OpenAI SPOF | Add try/except in translate.py |
| SCALE-01 | LOW | Sync SQLAlchemy | Post-MVP migration path documented |
| SCALE-02 | LOW | Sync photo migration | Post-MVP Celery task |
| MVP-V01–V06 | BLOCKER | 6 live DEC violations | All 6 must be fixed before launch |

---

## Architecture Review: Verdict

**The architecture is sound and deployable for MVP scale.**

The tech stack choices (FastAPI, Next.js 14, PostgreSQL, Cloudflare R2) are well-matched to the problem. The bot-protection layering is sophisticated and correct. The translation caching pattern is cost-effective. The JWT auth implementation is secure.

**Three blockers must be resolved before writing any implementation code:**

1. **CONTRADICTION-01** — Resolve `is_verified` column ambiguity (Option B: JOIN on salon_owners)
2. **UNDER-01** — Set up Alembic before any DB schema change
3. **UNDER-04** — Create Privacy Policy page before GA4 script is deployed

**Two blockers must be resolved before the affected code is touched:**

4. **UNDER-02** — Write tests for `is_bot()`, `_batch_open_now()`, `_translate_query()`, auth refresh before changing them
5. **CONTRADICTION-03** — Define and run `address_district` backfill migration script

Everything else is either medium-term improvement or post-MVP work.

---

*Last updated: 2026-07-09*
