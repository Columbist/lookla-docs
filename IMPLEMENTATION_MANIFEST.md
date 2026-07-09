---
title: Implementation Manifest
status: Active
version: 1.0
owner: Product Owner (columb@europe.com)
created: 2026-07-09
last_updated: 2026-07-09
related_documents:
  - 05_ROADMAP/IMPLEMENTATION_BACKLOG.md
  - 05_ROADMAP/MILESTONE_M01.md
  - 01_PRODUCT/MVP_SCOPE_LOCK.md
  - 00_GOVERNANCE/DECISION_LOG.md
---

# Implementation Manifest
**Lookla Beauty Marketplace — M-01**

> This is the single reference point for anyone writing code on Lookla.
>
> **Architecture is frozen.** Product scope is locked. This document defines HOW development proceeds — not WHAT is built (that's the backlog) or WHY (that's the decisions).

---

## Project State

| Layer | Version | Status |
|---|---|---|
| Architecture | v1.0 | **Frozen** — RFC required for changes |
| Product scope | v1.0 | **Locked** — see MVP_SCOPE_LOCK.md |
| API contract | v1.0 | **Frozen** — RFC required for new/changed endpoints |
| Database schema | Alembic baseline pending | **Active** — changes via migrations only |
| Backlog | v1.0 | **Active** — 36 tasks (T-001 – T-036) |
| Milestone | M-01 | **In Progress** |

---

## Development Approach

Work proceeds in **vertical slices** — each slice delivers a complete, testable unit of functionality from DB through API through frontend through analytics through tests. A slice is "Done" only when all layers are complete.

Do not do "all backend, then all frontend." A completed search filter that passes tests and fires analytics is worth more than six partially-done features.

---

## Implementation Order

### Slice 0 — Foundations (start here; no dependencies)

These tasks are independent of each other and have no prerequisites. Start all three on day one.

| Task | What | Why first |
|---|---|---|
| T-001 | Alembic setup (empty baseline + stamp) | Required before any schema change |
| T-036 | Create public/robots.txt | Required before any SEO traffic |
| T-033 | Connect slowapi to Redis | Rate limits must survive restarts |

**Exit:** `alembic current` returns a revision hash. `https://lookla.gr/robots.txt` returns 200. Rate limits persist after `docker compose restart api`.

---

### Slice 1 — Area Filter (the MVP's biggest schema change)

**Sequence:** must be executed in order.

```
T-001 (complete) → T-002 → T-003 → T-003a → T-004 → T-005 → T-006 → T-007 → T-008
```

| Task | What |
|---|---|
| T-002 | Add address_district + address_region columns (Alembic migration) |
| T-003 | Backfill address_district for all Athens salons |
| T-003a | Verify / create GIN index on FTS tsvector |
| T-004 | Add GET /api/areas endpoint |
| T-005 | Add ?area= param to GET /api/salons |
| T-006 | Update CITY_SYNONYMS with district-level Russian/Ukrainian synonyms |
| T-007 | Update SearchFilters.tsx: area dropdown from /api/areas |
| T-008 | Update homepage: CityGrid → AreaGrid |

**Exit:** `GET /api/salons?area=glyfada` returns Glyfada salons. Filter label shows "Район" in Russian locale. Homepage area tiles link to `?area=` params.

---

### Slice 2 — Honest Salon Detail (fixes all live DEC violations)

**Dependencies:** T-001 complete. T-024 must run before T-011.

| Task | What | Dependency |
|---|---|---|
| T-024 | Add is_owner_claimed to API response (LEFT JOIN salon_owners) | T-001 |
| T-009 | Remove booking stub buttons | None |
| T-010 | Implement contact CTAs (Call / WhatsApp / Website) | T-009 |
| T-011 | Replace ✓ badge with text label ("Information reviewed" / "Owner verified") | T-024 |
| T-012 | Add Google review source label | None |

**Exit:** Zero booking buttons. Three contact CTAs work in incognito. "Information reviewed" text visible (no ✓). "Source: Google Reviews" header present.

---

### Slice 3 — Legal + Analytics (in strict sequence)

**Rule: T-017 and T-018 MUST be complete and live before T-014 (GA4 script) is deployed.**

```
T-017 → T-018 → T-019 (GDPR)
T-013 → T-016 (GA4 property + Search Console — can do in parallel with GDPR)
T-014 → T-015 → T-034 (GA4 script + events — only after consent is live)
```

| Task | What |
|---|---|
| T-017 | Create /[locale]/privacy page |
| T-018 | Create cookie consent banner (sets lookla_consent=1) |
| T-019 | Configure GA4 data retention + IP anonymization |
| T-013 | Create GA4 property; get Measurement ID |
| T-016 | Verify Google Search Console |
| T-014 | Add GA4 script to Next.js root layout (conditional on consent) |
| T-015 | Implement useAnalytics() + contact_action events |
| T-034 | Add search analytics events (search_submitted, salon_card_clicked) |

**Exit:** `contact_action` fires in GA4 Realtime on contact button click. Privacy Policy live. Cookie banner works. Search Console verified.

---

### Slice 4 — New Pages + Homepage

**Dependencies:** Slice 1 complete (area grid needs ?area= params).

| Task | What |
|---|---|
| T-020 | Create /[locale]/about page |
| T-021 | Create /[locale]/contact page |
| T-022 | Add language switcher to header |
| T-023 | Update "How it works" step 3 copy (no registration required) |

Tasks T-020, T-021, T-022, T-023 can run in parallel.

**Exit:** `/en/about`, `/en/contact` return 200. Language switcher in header on desktop + mobile. Footer links to Privacy, About, Contact.

---

### Slice 5 — Admin Enhancement + Infrastructure

**Dependencies:** Slice 1 (address_district column needed for admin edits), Slice 2 (is_verified semantics resolved).

| Task | What |
|---|---|
| T-025 | Admin inline edit form (phone, address, is_verified flag) |
| T-026 | Configure daily pg_dump backup cron on server |

**Exit:** Admin can edit phone_primary inline. `crontab -l` shows pg_dump job. Manual backup created and validated.

---

### Slice 6 — Code Quality

**Dependencies:** T-001 complete (pytest needs DB setup). Run T-030 tests BEFORE changing the tested functions.

| Task | What |
|---|---|
| T-030 | Unit tests: is_bot(), _batch_open_now(), _translate_query(), auth refresh |
| T-027 | Extract useMe() hook |
| T-028 | Extract localePrefix() utility |
| T-029 | React error boundary for SalonDetailClient |
| T-031 | try/except in translate.py for OpenAI failures |
| T-035 | Deprecate GET /api/search (add Deprecation header) |

Tasks T-027, T-028, T-029, T-031, T-035 can run in parallel. T-030 must run before any change to the tested functions.

**Exit:** `pytest backend/tests/` green. Error boundary wraps SalonDetailClient. OpenAI failure returns original text (not 500).

---

### Slice 7 — Translation QA

**Dependencies:** Slices 1 + 2 complete (services accessible, area filter working).

| Task | What |
|---|---|
| T-032 | Manual review of 20 Russian service name translations |

**Exit:** 20 Russian translations reviewed; no machine-literal results.

---

### Pre-Launch Gate

After all slices complete, run the full Release Checklist (`06_ENGINEERING/RELEASE_CHECKLIST.md`).

**Manual QA journeys:**
- J-01: Russian persona → search "маникюр" → filter Glyfada → WhatsApp → GA4 Realtime event
- J-02: Greek persona → search → Call salon → GA4 event
- J-03: Compliance check — no ✓ badge, no booking buttons, review label visible, no /pricing link

After all checks pass: deploy M-01, set GA4 annotation "M-01 launch", start 90-day measurement window.

---

## Rules

### No code without a backlog task
Every code change maps to a task ID from IMPLEMENTATION_BACKLOG.md. Commit message includes the task ID: `fix(salon): remove booking stub buttons (T-009)`.

### Definition of Done
A task is Done when all of its acceptance criteria pass AND:
- [ ] The commit is on `main` (or merged via PR)
- [ ] No `console.log` or `print()` in new code
- [ ] `ruff check` passes (Python) or `eslint` passes (TypeScript)
- [ ] If a test was required: it passes
- [ ] If documentation was changed: change references the task ID

### No scope expansion
If a new requirement is identified during implementation: stop, file it as a note, discuss with Product Owner. Do not implement it inline. No new features sneak into M-01.

### No architecture changes without RFC
If the implementation reveals a problem with the architecture (wrong abstraction, missing field, wrong endpoint design): create an RFC in `07_RFC/`, get approval, then change. Do not "fix it" silently.

### Documentation updates follow code — never lead
Update `API_SPECIFICATION.md`, `DATABASE_SCHEMA.md`, or page specs only after the code change is complete and verified. Pre-emptive documentation changes create drift.

### If you discover a mismatch between code and docs
1. Stop
2. Report the mismatch (do not silently "fix" it)
3. Determine whether the code or the docs is wrong
4. Fix the one that is wrong, with Product Owner sign-off if it's a product decision

---

## Commit Message Format

```
type(scope): short description (T-NNN)

Examples:
feat(search): add area filter dropdown from /api/areas (T-007)
db: add address_district column + backfill migration (T-002, T-003)
fix(salon): remove booking stub buttons (T-009)
test(backend): add is_bot() regression tests (T-030)
feat(analytics): add contact_action GA4 events (T-015)
chore(infra): connect slowapi to Redis for persistent rate limits (T-033)
```

Scope matches DEVELOPMENT_STANDARDS.md. Type matches Conventional Commits.

---

## Contact

Product Owner: columb@europe.com
Architecture questions: check `08_REVIEWS/ARCHITECTURE_REVIEW.md` first
New decisions: create RFC in `07_RFC/`

---

*Implementation Manifest v1.0 — frozen 2026-07-09*
*Unfreeze requires Product Owner approval.*
