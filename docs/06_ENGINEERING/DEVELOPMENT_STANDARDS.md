---
title: Development Standards
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 04_ARCHITECTURE/BACKEND_ARCHITECTURE.md
  - 04_ARCHITECTURE/FRONTEND_ARCHITECTURE.md
  - 00_GOVERNANCE/PROJECT_CHARTER.md
implementation_status: N/A — standards document; applies to all future development
---

# Development Standards
**Lookla Beauty Marketplace**

> **Approved.** These standards apply to all code written for Lookla from this point forward.
>
> The goal is not ceremony — it is making the codebase understandable by a single developer returning after 3 months away, or by a new contributor without a lengthy onboarding.

---

## 1. Git Commit Messages

**Format:** [Conventional Commits](https://www.conventionalcommits.org/) — `type(scope): description`

### Types

| Type | When to use |
|---|---|
| `feat` | A new user-visible feature |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no logic change |
| `refactor` | Code restructure without behaviour change |
| `perf` | Performance improvement |
| `test` | Adding or updating tests |
| `chore` | Build system, dependencies, CI |
| `db` | Database schema changes (migrations, DDL) |
| `revert` | Reverts a previous commit |

### Scopes (optional but recommended)

| Scope | Applies to |
|---|---|
| `search` | Search page + `/api/salons` |
| `salon` | Salon detail page + `/api/salons/{id}` |
| `auth` | Auth flow |
| `admin` | Admin panel |
| `i18n` | Translation files or next-intl config |
| `analytics` | GA4 events |
| `db` | Database schema |
| `crawler` | Celery crawlers |
| `infra` | Docker, Nginx, Cloudflare config |

### Examples

```
feat(salon): add Google source label to reviews section (DEC-013)
fix(search): area filter now maps to address_district column
docs: add API_SPECIFICATION.md for all MVP endpoints
db: add address_district and address_region columns to salons
chore(infra): connect slowapi to Redis for persistent rate limits
perf(salon): add priority=true to hero photo for LCP improvement
refactor: extract localePrefix() utility from 8 inline usages
```

### Rules

- Subject line: max 72 characters, present tense, imperative mood ("add" not "added")
- Reference the Decision Log when a commit implements an approved decision: `(DEC-013)`
- Body (optional): explain WHY, not WHAT. The diff shows what changed; the message explains why.
- No "WIP", "fix", "update" as entire commit messages
- Do not commit commented-out code — delete it

---

## 2. Branching Strategy

**Model:** Trunk-Based Development (single `main` branch with short-lived feature branches)

This is appropriate for a solo or small team (1–3 developers) where long-lived branches cause unnecessary merge conflicts.

### Branch Naming

```
feat/dec-013-review-labels
fix/area-filter-district-mapping
docs/add-api-spec
db/add-address-district-column
chore/connect-redis-rate-limits
```

Pattern: `{type}/{short-kebab-description}`

When referencing a decision: include the DEC number.

### Rules

- **`main` is always deployable** — no broken commits on main
- Feature branches: created from `main`, merged back to `main` via PR (or direct push for solo work)
- Branch lifetime: max 2 days. If a branch lives longer, it needs to be decomposed
- No long-lived `develop`, `staging`, or `release` branches (unnecessary complexity at current scale)
- Delete branches after merge

### For solo development

Direct push to `main` is acceptable for small, reviewed changes. PR workflow is recommended for changes touching multiple systems (e.g., a backend + frontend + DB change).

---

## 3. Naming Conventions

### Python (Backend)

| Element | Convention | Example |
|---|---|---|
| Files | `snake_case.py` | `salon_owner.py` |
| Classes | `PascalCase` | `SalonService`, `UserSchema` |
| Functions/methods | `snake_case` | `get_current_user`, `_batch_open_now` |
| Constants | `UPPER_SNAKE_CASE` | `SERVICE_SYNONYMS`, `BOT_PATTERNS` |
| Private functions | `_snake_case` | `_translate_query`, `_verify_token` |
| Database columns | `snake_case` | `address_district`, `is_verified` |
| Pydantic models | `PascalCase` + Schema suffix | `SalonListSchema`, `RegisterRequest` |
| FastAPI routers | `router` variable | `router = APIRouter(prefix="/salons")` |

### TypeScript/React (Frontend)

| Element | Convention | Example |
|---|---|---|
| Files (components) | `PascalCase.tsx` | `SalonCard.tsx`, `ContactButtons.tsx` |
| Files (utilities) | `camelCase.ts` | `locale.ts`, `api.ts` |
| Files (hooks) | `use*.ts` | `useMe.ts`, `useAnalytics.ts` |
| Files (pages) | `page.tsx` | Next.js convention |
| React components | `PascalCase` | `function SalonCard()` |
| Hooks | `camelCase` prefixed `use` | `function useMe()` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_LOCALE` |
| TypeScript interfaces | `PascalCase` | `interface Salon {}` |
| TypeScript types | `PascalCase` | `type Locale = 'el' \| 'en' \| 'ru' \| 'uk'` |
| Tailwind class order | Layout → Spacing → Colour → Typography → State | `flex gap-4 bg-white text-gray-900 hover:bg-gray-50` |

### Database

| Element | Convention | Example |
|---|---|---|
| Tables | `snake_case` plural | `salons`, `salon_hours`, `service_categories` |
| Columns | `snake_case` | `address_district`, `is_verified`, `created_at` |
| Indexes | `idx_{table}_{columns}` | `idx_salons_address_district` |
| Foreign keys | `fk_{table}_{ref_table}` | `fk_services_salon_id` |
| Enums | `snake_case` | `user_role` |

### API Routes

| Rule | Example |
|---|---|
| Lowercase kebab | `/api/salon-categories` |
| Plural nouns for collections | `/api/salons`, `/api/areas` |
| Singular noun for specific resource | `/api/salons/{id}` |
| Verb-based for actions | `/api/auth/refresh`, `/api/owner/claim/verify` |
| No trailing slash | `/api/salons` not `/api/salons/` |

---

## 4. Code Style

### Python

- **Formatter:** `black` (line length 88)
- **Linter:** `ruff` (replaces flake8 + isort)
- **Type hints:** Required on all public functions
- **Docstrings:** Short summary only; no multi-paragraph docstrings for simple functions
- **Imports:** `ruff` sorts automatically; standard lib → third party → local

**Non-negotiable:** All new code must pass `ruff check` before commit.

### TypeScript / React

- **Formatter:** `prettier` (default config; no semi-colons optional — pick one and stick to it)
- **Linter:** `eslint` with Next.js defaults
- **Type coverage:** No `as any` in new code. Use proper types or `unknown` + type guard.
- **Component export:** Named exports preferred over default exports for components (except pages)

```typescript
// Preferred
export function SalonCard({ salon }: { salon: Salon }) { ... }

// Not preferred
export default function SalonCard() { ... }
```

- **No inline styles** — use Tailwind classes only
- **No magic numbers** — extract to named constants

---

## 5. Testing Standards

**Current state:** Zero test coverage. This is the highest non-security technical debt item.

**Pre-MVP target:** At minimum, the following must have tests before any change to them:

| Target | Test type | Why |
|---|---|---|
| `is_bot()` regex | Unit test | Previously had a bug; regression risk is high |
| `_batch_open_now()` | Unit test | Timezone-sensitive; DST bugs are subtle |
| `_translate_query()` synonym map | Unit test | Controls search quality; easy to break silently |
| `/api/auth/register` flow | Integration test | Auth bug = complete platform failure |
| `/api/salons` filter logic | Integration test | Core user-facing feature |

**Test framework:**
- Backend: `pytest` + `pytest-asyncio` (if async added later) + `httpx` (for FastAPI test client)
- Frontend: `vitest` + `@testing-library/react` for component tests

**Pattern (backend integration test):**
```python
# tests/test_salons.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_salon_list_returns_active_only():
    response = client.get("/api/salons")
    assert response.status_code == 200
    salons = response.json()["items"]
    assert all(s["is_active"] for s in salons)  # passive check — is_active=false never returned
```

**Definition of Done for tests:**
- A PR that changes `is_bot()`, `_batch_open_now()`, or search filter logic must include a test for the changed behaviour
- A PR that adds a new API endpoint must include a basic happy-path test

---

## 6. Code Review

**For solo development:** Self-review against this checklist before committing to `main`.

**For team development:** PR required for any change touching backend auth, DB schema, or payment-related code.

### Pre-commit Checklist

- [ ] Does the code implement what the approved document says? (Check page spec / API spec)
- [ ] Does it reference the correct DEC number in the commit message?
- [ ] No `as any` in TypeScript new code
- [ ] No hardcoded secrets or API keys
- [ ] No `console.log` or `print()` in production-path code
- [ ] No comments that say WHAT (the code says that); only comments that say WHY
- [ ] `ruff check` passes (Python) or `eslint` passes (TypeScript)
- [ ] If DB schema changed: migration file is included
- [ ] If new env var: added to `.env.example`
- [ ] If new API endpoint: documented in `API_SPECIFICATION.md`

---

## 7. Definition of Done

A piece of work is "Done" when:

1. **Implements the spec** — matches the approved page spec, API spec, or RFC
2. **No scope creep** — does not add features outside the spec
3. **Passes linting** — no warnings from ruff / eslint
4. **Tests updated** — if touching a tested module, tests pass; if touching an untested critical path (see §5), a test is added
5. **Document updated** — if the implementation differs from the spec, the spec is updated to match (with Product Owner approval for product changes)
6. **Committed with conventional commit message** referencing the DEC or page spec
7. **No broken behaviour on main** — the change does not break any existing user-visible functionality

---

## 8. Environment and Deployment

### Local Development

```bash
# Backend
cd backend && python -m uvicorn app.main:app --reload --port 8001

# Frontend
cd frontend && npm run dev

# Both services via Docker Compose (production-equivalent)
docker compose up --build
```

**Code-baked images:** Any backend or frontend code change requires:
```bash
docker buildx build -t lookla-api ./backend
docker buildx build -t lookla-web ./frontend
docker compose up -d
```

The crawler is volume-mounted — code changes apply without rebuild.

### Environment Variables

All configuration via `.env` (project root). Never hardcode values that differ between environments.

**Required for local `.env`:**
```
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=<generate: openssl rand -hex 32>
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
OPENAI_API_KEY=...
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=lookla
RESEND_API_KEY=...
SENTRY_DSN=...
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_GA4_ID=G-XXXXXXXXXX
```

### Deployment

Current: manual SSH + docker buildx + docker compose up. No CI/CD.

**Recommended pipeline (post-MVP):**
```
git push origin main
  → GitHub Actions:
    → ruff check (backend)
    → eslint (frontend)
    → pytest (backend)
    → docker buildx build + push to registry
    → SSH deploy: docker compose pull && docker compose up -d
```

---

## 9. Documentation Update Rules

Following DEC-002 (documentation-first), whenever a code change:

| Change type | Required doc update |
|---|---|
| New API endpoint | Add to `API_SPECIFICATION.md` |
| DB schema change | Update `DATABASE_SCHEMA.md` |
| New feature added | If MVP scope: update relevant page spec. If post-MVP: add to `FUTURE_FEATURES.md` |
| Behaviour diverges from spec | Report mismatch; update spec with Product Owner approval |
| Security change | Update `SECURITY.md` |
| Performance change | Update `PERFORMANCE.md` if target or strategy changes |

Never let code diverge silently from documentation.

---

*Last updated: 2026-07-09*
