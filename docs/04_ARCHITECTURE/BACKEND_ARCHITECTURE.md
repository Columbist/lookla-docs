---
title: Backend Architecture
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 04_ARCHITECTURE/DATABASE_SCHEMA.md
  - 04_ARCHITECTURE/API_SPECIFICATION.md
  - 04_ARCHITECTURE/SECURITY.md
  - 04_ARCHITECTURE/DATA_FLOW.md
  - 06_ENGINEERING/AUDIT.md
implementation_status: Describes current implementation + MVP-required changes
---

# Backend Architecture
**Lookla Beauty Marketplace**

> **Approved.** Describes the current FastAPI backend as deployed, plus required changes for MVP launch.
>
> Do NOT redesign what works. Target: surgical changes for M-01.

---

## 1. Technology Stack

| Component | Technology | Version | Notes |
|---|---|---|---|
| Runtime | Python | 3.12 | |
| Framework | FastAPI | latest | ASGI via uvicorn |
| ORM | SQLAlchemy | 2.x | Synchronous (psycopg2 driver) |
| DB driver | psycopg2-binary | — | Sync; no async ORM in use |
| Validation | Pydantic v2 | — | Via pydantic-settings for config |
| Auth | python-jose | — | HS256 internal JWT; RS256 for Google |
| Task queue | Celery | — | Crawlers only; Redis as broker |
| Translation | openai | 1.86.0 | gpt-4o-mini, on-demand, bot-protected |
| Email | Resend | — | Transactional only |
| Storage | Cloudflare R2 | — | boto3-compatible S3 API |
| Monitoring | Sentry | — | `traces_sample_rate=0.1` |
| Rate limiting | slowapi | — | In-process; Redis connection pending |
| CAPTCHA | Cloudflare Turnstile | — | Key configured; integration unverified |

---

## 2. Service Boundaries

The backend is a **monolithic FastAPI application** with a single process boundary. There is no microservice split. The only external worker process is the Celery crawler.

```
┌─────────────────────────────────────┐
│  FastAPI Application (uvicorn)       │
│  Port 8001 (internal, via Nginx)    │
│                                     │
│  13 routers, 4 services, 1 core     │
└────────────────────┬────────────────┘
                     │ SQLAlchemy (sync)
          ┌──────────▼──────────┐
          │   PostgreSQL 16     │
          │   Port 5432         │
          └─────────────────────┘

┌─────────────────────────────────────┐
│  Celery Worker (2 concurrent)        │
│  RAM cap: 500 MB                    │
│  Broker: Redis port 6379            │
└────────────────────┬────────────────┘
                     │ writes crawled data
          ┌──────────▼──────────┐
          │   PostgreSQL 16     │
          └─────────────────────┘

External services called by FastAPI:
  - OpenAI API (translation)
  - Google JWKS endpoint (OAuth verification)
  - Resend API (email)
  - Cloudflare R2 (photo upload)
  - Stripe API (payments — existing, not user-facing per DEC-006)
```

**Dependency rule:** FastAPI never calls Celery directly. Celery never calls FastAPI. They share the database.

---

## 3. Directory Structure

```
backend/
└── app/
    ├── main.py              # App factory: include_router × 13, CORS, Sentry init
    ├── core/
    │   ├── config.py        # Settings (pydantic-settings); loaded via lru_cache singleton
    │   ├── database.py      # SQLAlchemy engine + SessionLocal; get_db() dependency
    │   ├── deps.py          # FastAPI dependency: get_current_user, require_admin, etc.
    │   └── security.py      # JWT encode/decode, password hashing (bcrypt), token rotation
    ├── models/
    │   └── *.py             # SQLAlchemy ORM models (partial — see GAP below)
    ├── schemas/
    │   └── *.py             # Pydantic v2 request/response schemas per domain
    ├── routers/
    │   ├── salons.py        # GET /api/salons, /api/salons/{id}, /services, /reviews, /photos
    │   ├── search.py        # GET /api/search (unified; Haversine geo)
    │   ├── auth.py          # POST register/login/logout/refresh/forgot/reset; Google OAuth
    │   ├── owner.py         # Owner dashboard: claim flow, salon management
    │   ├── professionals.py # GET /api/professionals (list + detail)
    │   ├── masters.py       # PATCH /api/masters/me; portfolio; availability
    │   ├── bookings.py      # GET slots; POST/GET/PATCH bookings (backend-complete, not user-facing)
    │   ├── chat.py          # Conversations, messages, availability requests (not user-facing)
    │   ├── payments.py      # Stripe checkout/portal/webhook/subscription (not user-facing per DEC-006)
    │   ├── admin.py         # Stats, salon/user/professional management, reports, moderation
    │   ├── categories.py    # GET /api/categories (category tree with i18n)
    │   ├── media.py         # GET /api/media/photo/{id} (R2 lazy migration proxy)
    │   └── reports.py       # POST /api/reports (user abuse reports; requires auth)
    └── services/
        ├── translate.py     # OpenAI batch translation; bot-check; DB caching
        ├── email.py         # Resend wrappers: verify, reset, claim notification
        ├── moderation.py    # is_disposable_email(); Google Vision (key present, usage unclear)
        └── media.py         # R2 upload; presigned URL generation; image resize
```

**GAP — ORM models missing for SQL-only tables:**
The following tables exist in the DB and are accessed via `db.execute(text(...))` but have no SQLAlchemy model class:
`salon_owners`, `claiming_tokens`, `appointments`, `conversations`, `messages`, `availability_requests`, `moderation_queue`, `reports`, `subscription_plans`, `subscriptions`

These must be migrated to ORM models before any schema evolution on those tables. Not a blocker for MVP launch; is a blocker for any new feature touching these tables.

---

## 4. Application Layers

```
HTTP Request
    │
    ▼
┌───────────────────────────────────────────┐
│  Router Layer  (routers/*.py)             │
│  Responsibility: HTTP ↔ business boundary │
│  - Parse and validate input via Pydantic  │
│  - Authenticate via FastAPI dependency    │
│  - Call service or query DB directly      │
│  - Return Pydantic response schema        │
└──────────────────────────┬────────────────┘
                           │ direct DB access (acceptable in read-only endpoints)
                           │ service call (for side-effect operations)
                           ▼
┌───────────────────────────────────────────┐
│  Service Layer  (services/*.py)           │
│  Responsibility: reusable business logic  │
│  - translate.py: GPT call + DB cache      │
│  - email.py: Resend wrappers              │
│  - media.py: R2 upload + resize           │
│  - moderation.py: email checks            │
└──────────────────────────┬────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────┐
│  Database Layer  (core/database.py)       │
│  Responsibility: session lifecycle        │
│  - get_db() yields SQLAlchemy Session     │
│  - Session is synchronous (psycopg2)      │
│  - One session per request (dependency)   │
└──────────────────────────┬────────────────┘
                           │
                           ▼
                     PostgreSQL 16
```

**Dependency rule:** Routers may call services. Services may call the DB session. Neither layer reaches up — no circular imports. Models never import from routers or services.

**Where direct DB access in routers is acceptable:**
- Simple read queries (SELECT with filters)
- Single-table writes where no domain logic is involved

**Where service layer is required:**
- Any operation calling an external API (OpenAI, Resend, R2, Stripe)
- Any operation with multi-step state (claim flow, token rotation)
- Any operation needing retry, fallback, or transaction management

---

## 5. Validation Layer

**Input validation:** All request bodies are Pydantic v2 models. FastAPI enforces schema automatically; invalid input returns HTTP 422 with field-level error detail.

**Pattern:**
```
# Schema definition
class SalonFilterParams(BaseModel):
    q: Optional[str] = None
    area: Optional[str] = None          # DEC-010: was 'city', now 'area'
    category: Optional[str] = None
    min_rating: Optional[float] = None

# Router usage
@router.get("/salons")
def list_salons(params: SalonFilterParams = Depends(), db: Session = Depends(get_db)):
    ...
```

**Output validation:** Response schemas defined per endpoint. FastAPI serializes and validates before sending.

**Additional validations (custom):**
- Email: `is_disposable_email()` in `moderation.py` — called on register
- Honeypot: `website_url` field in register payload — if populated, return 400 silently
- Bot detection: `is_bot(user_agent)` in services and reviews endpoints

**Validation NOT done:**
- Phone number format (E.164) — not enforced at API level; stored as-is from crawlers
- URL format for website field — stored as-is; frontend renders with `target="_blank"` safely

---

## 6. Error Handling

**Standard HTTP status codes:**

| Status | When used |
|---|---|
| 200 | Successful GET |
| 201 | Successful POST (resource created) |
| 204 | Successful DELETE |
| 400 | Bad request (invalid input, honeypot triggered) |
| 401 | Unauthenticated (missing or expired token) |
| 403 | Forbidden (authenticated but wrong role) |
| 404 | Resource not found |
| 409 | Conflict (e.g., email already registered) |
| 422 | Pydantic validation error (FastAPI default) |
| 429 | Rate limit exceeded (slowapi) |
| 500 | Unhandled server error |

**Global exception handler:** Sentry captures all unhandled 500 errors with stack trace. `traces_sample_rate=0.1` means 10% of requests are traced.

**Error response format (FastAPI default):**
```json
{ "detail": "Error message" }
```
For 422 (validation):
```json
{ "detail": [{ "loc": ["body", "field_name"], "msg": "...", "type": "..." }] }
```

**Pattern — raising HTTP exceptions in routers:**
```python
from fastapi import HTTPException

if not salon:
    raise HTTPException(status_code=404, detail="Salon not found")
```

**Not implemented:** Custom error codes, error envelopes, problem+json format. Not needed for MVP.

---

## 7. Logging

**Current state:** Sentry for error reporting. No structured application logging confirmed.

**Minimum required for MVP:**
- Sentry error capture (configured)
- uvicorn access logs (default: method, path, status, response time)

**Recommended additions (post-MVP):**
- Structured JSON logging (via `structlog` or `python-json-logger`)
- Log levels: DEBUG (dev), INFO (prod), WARNING/ERROR captured by Sentry
- Request ID header: `X-Request-ID` for tracing across services

**What NOT to log:**
- Passwords, tokens, or full request bodies containing auth data
- Personal user data in log lines (GDPR concern)

---

## 8. Configuration

**Pattern:** `pydantic-settings` with `Settings` class loaded once via `lru_cache`.

```python
# core/config.py
class Settings(BaseSettings):
    # DB
    database_url: str
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    # Google OAuth
    google_client_id: str
    google_client_secret: str
    # OpenAI
    openai_api_key: str
    # Cloudflare R2
    r2_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket_name: str
    # Resend
    resend_api_key: str
    # Stripe (exists; not user-facing per DEC-006)
    stripe_secret_key: str
    stripe_webhook_secret: str
    # Sentry
    sentry_dsn: str
    # Admin
    admin_email: str = "columb@europe.com"

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Environment:** Single `.env` file at project root, shared across all Docker services. Do not commit `.env` to git (`.gitignore` enforced).

**Missing:** No separate `dev`/`staging`/`prod` config split. Acceptable for single-server MVP. Add when CI/CD is introduced.

---

## 9. Scheduled Jobs (Celery)

**Broker:** Redis (port 6379, internal)

**Worker:** `celery -A crawler.tasks worker --loglevel=info --concurrency=2 --max-memory-per-child=500000`

**Crawlers and schedule:**

| Task | Schedule | Source | Notes |
|---|---|---|---|
| Vrisko crawler | Every Tuesday | vrisko.gr | Greek business directory |
| XO crawler | Every Tuesday | xo.gr | Greek business directory |
| BeautyProject crawler | Every Wednesday | beautyproject.gr | Beauty-specific |
| Treatwell crawler | Every Thursday | treatwell.com/greece | European marketplace |
| Google Places | **Disabled** | Google Places API | Disabled July 2026 — cost incident |

**Crawler pattern:**
1. Fetch source → parse listings → upsert into `salons` table
2. Deduplicate by `google_place_id` (when available) or name+address fuzzy match
3. Set `needs_review=true` on new or significantly changed records
4. Never overwrite owner-verified data with crawled data (protect claimed listings)

**Rule:** Crawlers write to the same PostgreSQL instance as the API. No write conflicts at current volume; monitor `pg_stat_activity` if crawlers and API overlap.

---

## 10. File Storage and Image Pipeline

**Storage:** Cloudflare R2 (S3-compatible API). CDN: `cdn.lookla.gr` via Cloudflare.

### Image Pipeline

**Phase 1 — Lazy Migration (current state, already deployed):**
```
Crawled salon has Google Places photo URL
  → photo URL stored in photos.url
  → First real user requests /api/media/photo/{id}
  → Backend fetches image from Google
  → Resizes to [1200w, 800w, 400w] (if resize implemented)
  → Uploads to R2 at key: salons/{salon_id}/{photo_id}.jpg
  → Updates photos.r2_key and photos.url to cdn.lookla.gr/...
  → Returns image bytes
  → Next request: served from R2 CDN directly (no backend involvement)
```

**Phase 2 — Owner Upload (post-MVP, backend ready):**
```
Owner uploads photo via POST /api/owner/salons/{id}/photos
  → Validate: content-type image/*, max 10MB
  → Resize to [1200w, 800w, 400w]
  → Upload to R2: salons/{salon_id}/owner/{uuid}.jpg
  → Create photos record (salon_id, r2_key, is_primary)
  → Return photo URL
```

**R2 key structure:**
```
salons/{salon_id}/{photo_id}.webp          # crawled, migrated
salons/{salon_id}/owner/{uuid}.webp        # owner-uploaded
```

**Image format:** Target WebP (smaller, wide support). JPEG fallback for compatibility.

**Missing for MVP:** Explicit resize on lazy migration. Current code may upload full-size Google images to R2. Recommend adding resize step in `media.py` before MVP launch (reduces CDN bandwidth cost).

---

## 11. Required Changes for MVP Launch

Changes needed in the backend specifically for M-01. No new features — compliance with approved decisions.

| Change | Decision | File | Complexity |
|---|---|---|---|
| Add `area` filter param to `/api/salons` (replaces `city`) | DEC-010 | `routers/salons.py` | Low |
| Add Athens district → `address_city` mapping dict | DEC-010 | `routers/salons.py` | Low |
| Add `GET /api/areas` endpoint (returns districts with salon counts) | DEC-010 | new router or categories.py | Low |
| Clarify `is_verified` semantics in admin PATCH | DEC-014 | `routers/admin.py` | Low |
| Add `address_district`, `address_region` columns to salons | DEC-010 | DB migration | Medium |
| Connect slowapi to Redis (rate limits survive restarts) | Audit §21 | `main.py` | Low |
| Admin inline salon edit form | Audit §27 | `routers/admin.py` already exists | Low (API exists) |

---

## 12. What Must NOT Change

Per `06_ENGINEERING/AUDIT.md` Section 20:

- Cookie-based JWT auth flow (httpOnly, refresh rotation, CSRF compare_digest)
- `is_bot()` regex pattern
- `X-Robots-Tag` nginx headers on `/api/salons/*/services` and `/reviews`
- `_batch_open_now()` with `ZoneInfo("Europe/Athens")`
- Photo proxy `/api/media/photo/{id}`
- Docker Compose healthchecks
- `unaccent` PostgreSQL extension dependency
- `db/init.sql` (no in-place edits; use migration scripts)

---

*Last updated: 2026-07-09*
