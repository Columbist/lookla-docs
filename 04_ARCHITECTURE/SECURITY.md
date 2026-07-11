---
title: Security Architecture
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-11
related_documents:
  - 04_ARCHITECTURE/BACKEND_ARCHITECTURE.md
  - 04_ARCHITECTURE/API_SPECIFICATION.md
  - 00_GOVERNANCE/DECISION_LOG.md
  - 06_ENGINEERING/AUDIT.md
  - 05_ROADMAP/IMPLEMENTATION_BACKLOG.md
implementation_status: Describes current security posture + gaps for MVP
---

# Security Architecture
**Lookla Beauty Marketplace**

> **Approved.** Documents the current security implementation and identifies gaps before MVP launch.
>
> Security decisions already implemented correctly must NOT be changed without an explicit Change Request.

---

## 1. Authentication

### Mechanism

Cookie-based JWT with refresh token rotation.

```
Login/Register
  → FastAPI validates credentials
  → Issues access_token (JWT, HS256, 15 min TTL)
  → Issues refresh_token (JWT, HS256, 30 days TTL)
  → Both stored as httpOnly, Secure, SameSite=Lax cookies
  → SHA-256 hash of refresh_token stored in refresh_tokens table
```

**Why httpOnly cookies:**
- XSS cannot read httpOnly cookies — prevents token theft via injected JS
- Do not change to localStorage or Authorization headers without a security review

**Token lifetime:**
- Access token: 15 minutes — short enough to limit exposure
- Refresh token: 30 days — persistent session without re-login

**Refresh token rotation:**
- On every `/api/auth/refresh` call: old refresh token is revoked (SHA-256 hash marked `revoked_at`), new token pair issued
- If a stolen refresh token is used after legitimate refresh: the legitimate user's next refresh attempt fails → session expires naturally
- This is a correct sliding-window security model — do not change

### Google OAuth

```
GET /api/auth/google/start
  → Generates CSRF state token
  → Stores in oauth_csrf httpOnly cookie (10 min TTL)
  → Redirects to Google consent page

GET /api/auth/google/callback
  → Verifies state vs oauth_csrf cookie (secrets.compare_digest — constant-time comparison)
  → Exchanges code for id_token
  → Verifies id_token via Google's live JWKS (RS256)
    - Fetches JWKS from https://www.googleapis.com/oauth2/v3/certs
    - Verifies signature with the correct kid
    - Checks aud == GOOGLE_CLIENT_ID
    - Checks exp (token not expired)
  → Upserts user by google_id or email (no duplicate accounts)
  → Sets auth cookies
  → Redirects to /account
```

**Security-critical:** `secrets.compare_digest` on CSRF state prevents timing attacks. Do not replace with `==`.

---

## 2. Authorization

### Role Model

| Role | Capabilities |
|---|---|
| `user` | Search, view salons, submit reports, view own account |
| `salon_owner` | All of `user` + manage claimed salons via owner dashboard |
| `professional` | All of `user` + manage professional profile |
| `admin` | All above + admin panel, salon flags, user list, reports queue |

### FastAPI Dependency Pattern

```python
# core/deps.py

def get_current_user(token: str = Cookie(None), db: Session = Depends(get_db)) -> User:
    if not token:
        raise HTTPException(401, "Not authenticated")
    payload = decode_token(token)
    user = db.query(User).get(payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(401)
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(403, "Admin required")
    return user
```

### MVP Authorization Rules

| Endpoint group | Requires | Note |
|---|---|---|
| GET /api/salons* | None | DEC-016: anonymous access |
| GET /api/categories | None | |
| GET /api/areas | None | |
| POST /api/reports | `get_current_user` | Deliberate: anonymous reports create spam risk; auth required. Decision: 2026-07-09. |
| GET /api/auth/me | `get_current_user` | |
| /api/owner/* | `get_current_user` + `role in [salon_owner, admin]` | Not user-facing in MVP |
| /api/admin/* | `require_admin` | |

### Admin Authorization

Admin email is hardcoded in `Settings.admin_email = "columb@europe.com"`. The role is set in the DB and checked at runtime — the email constant is used only for comparison during initial setup.

**Risk:** If the admin email changes or a second admin is needed, both the DB role and the settings constant must be updated. Document this in deployment notes.

---

## 3. Rate Limiting

**Library:** `slowapi` (in-process, IP-based)

**Current configuration:**

| Scope | Limit | Endpoint(s) |
|---|---|---|
| Global | 200 requests/minute per IP | All endpoints |
| Register | 5/minute, 20/hour | POST /api/auth/register |
| Password reset | 3/minute, 10/hour | POST /api/auth/forgot-password |

**Known gap:** `slowapi` with in-process storage resets on API restart. Rate limits do not persist across restarts and do not work across multiple API instances.

**MVP fix:** Connect `slowapi` to the Redis instance that is already running:
```python
# main.py
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address, storage_uri="redis://redis:6379")
```
This is a one-line config change — no application logic changes needed.

**Recommended additions (post-MVP):**
- Per-endpoint limit on `/api/salons/{id}/services` and `/reviews` to limit translation cost abuse
- Per-user rate limits (requires auth context in slowapi)

---

## 4. Bot Protection (Multi-Layer)

Lookla uses layered bot protection specifically to prevent AI scrapers from triggering expensive GPT translation API calls.

**Layer 1 — User-Agent regex (`is_bot()`):**
```python
BOT_PATTERNS = re.compile(r'(bot|crawl|spider|slurp|mediapartners|ahrefsbot|semrushbot|...)', re.IGNORECASE)
def is_bot(user_agent: str) -> bool:
    return bool(BOT_PATTERNS.search(user_agent))
```
Applied in: `/api/salons/{id}/services`, `/api/salons/{id}/reviews`
Effect: Returns `[]` immediately if true — no DB query for translation, no OpenAI call.

**Layer 2 — Nginx X-Robots-Tag:**
```nginx
location ~* ^/api/salons/[^/]+/(services|reviews) {
    add_header X-Robots-Tag "noindex, nofollow";
}
```
Prevents Google from indexing translation endpoints. Unstable translated content would harm SEO.

**Layer 3 — JavaScript-required lazy loading:**
Services and reviews are lazy-loaded via `IntersectionObserver`. Bots that do not execute JavaScript never trigger these endpoints (they never "scroll").

**Layer 4 — Registration honeypot:**
```python
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    website_url: str = ""  # honeypot: bots fill this; humans don't see it

# In register handler:
if request.website_url:
    raise HTTPException(400, "Registration failed")
```

**Layer 5 — Cloudflare Turnstile (configured, integration unverified):**
Key is configured. Frontend integration status not confirmed. Verify before MVP launch.

**Do not change Layer 1 regex or Layer 2 nginx config without testing.** A previous bug in the `is_bot()` regex accidentally matched `Mozilla/5.0` — this was fixed and must not regress.

---

## 5. Input Validation and Injection Protection

### SQL Injection

All database queries use SQLAlchemy ORM or parameterized `text()` queries:
```python
# Correct: parameterized
db.execute(text("SELECT * FROM salons WHERE id = :id"), {"id": salon_id})

# Never: string interpolation
db.execute(f"SELECT * FROM salons WHERE id = {salon_id}")  # PROHIBITED
```

**Status:** Current codebase uses parameterized queries throughout. No SQL injection vectors identified in audit.

### XSS (Cross-Site Scripting)

React renders are XSS-safe by default — all text content is escaped via `{variable}` interpolation. `dangerouslySetInnerHTML` is not used.

**Additional:** Salon website URLs are rendered as `<a href={url} target="_blank" rel="noopener noreferrer">`. The `rel="noopener noreferrer"` prevents tab-napping attacks.

**Nginx:** No `X-XSS-Protection` header set (deprecated in modern browsers). Cloudflare adds security headers.

### CSRF

- **API calls (JSON):** CSRF protection via SameSite=Lax cookies. JSON APIs with SameSite=Lax are safe from cross-origin form submission attacks.
- **Google OAuth CSRF:** Explicit state token comparison via `secrets.compare_digest`. Correct.
- **No CSRF token needed** for standard JSON API calls when using SameSite cookies — do not add CSRF middleware unnecessarily.

### Path Traversal

File uploads (salon photos) use UUIDs for filenames — no user-controlled path components in R2 keys. Safe.

### Content Type

FastAPI rejects requests with wrong `Content-Type` (expects `application/json`). File upload endpoints expect `multipart/form-data`.

---

## 6. GDPR and Privacy

**Applicable law:** GDPR (EU) — Greece is an EU member state.

**Current state:** Basic compliance. Formal DPO designation and full DPIA not required at current user count.

### Data Collected

| Data | Source | Purpose | Retention |
|---|---|---|---|
| Email | User registration | Auth, account | Until account deletion |
| Password hash | Registration | Auth | Until account deletion |
| Google ID, avatar | Google OAuth | Auth, display | Until account deletion |
| Preferred language | User setting | UI localisation | Until changed |
| Refresh token hashes | Auth flow | Session management | Until revoked or expired (30d) |
| IP address (in logs) | Nginx access log | Security, rate limiting | 90 days log rotation |
| GA4 session data | Tracking script (DEC-017) | Analytics | Per GA4 data retention settings |

### Required Actions Before MVP Launch

- **Privacy Policy page** (`/privacy`) must be created. Must include:
  - What data is collected (GA4 analytics, registration data)
  - How data is used (service improvement, auth)
  - User rights (access, deletion, portability)
  - GA4 data processing disclosure
  - Google as a sub-processor
  - Contact email for data requests: `hello@lookla.gr`

- **GA4 IP anonymization:** Enable in GA4 property settings (anonymize_ip). Not a code change — GA4 dashboard setting.

- **Cookie consent banner** (minimal, for analytics only): Required for GDPR when using GA4. A simple banner with "This site uses analytics cookies" + Accept is sufficient for MVP. Full CMP (consent management platform) is overkill at this stage.

### Data not collected (by design)

- No credit card data (Stripe handles this; DEC-006)
- No health or biometric data
- No location tracking (no GPS; address filtering is user-typed text)
- No behavioral profiling (GA4 used for aggregate analytics only)

### User Rights

| Right | Current mechanism |
|---|---|
| Access | GET /api/auth/me returns user data |
| Deletion | No self-service delete yet — email `hello@lookla.gr` for manual deletion |
| Portability | No export API — manual on request |
| Correction | Users can update name/language in account settings |

Account deletion must be available before full public launch. Implement as POST /api/auth/delete-account.

---

## 7. Google Reviews Attribution (DEC-013)

**Legal context:** Google's Terms of Service require that when Google Maps/Places data is displayed, proper attribution is given.

**Implementation requirement (DEC-013):** All reviews imported from Google must display:
- "Source: Google Reviews"
- "Imported: Yes"
- "Original: No"

This is both a product decision (honesty) and a legal requirement (Google ToS compliance). It is not optional.

**Additional consideration:** Review aggregation must stay within Google's allowed data use. The reviews are displayed for informational purposes only, not repackaged for sale or API redistribution.

---

## 8. Audit Logging

**Current state:** No application-level audit log. Nginx access logs capture IP, path, method, status, timestamp.

**What should be logged for MVP (minimum):**
- Admin flag changes: when `is_verified`, `is_active`, or `needs_review` is changed — log who changed it, what was changed, when
- Salon claim events: when a claim is verified — log user_id, salon_id, timestamp

**Implementation pattern:**
```python
# In admin.py PATCH handler, after update:
logger.info("admin_action", extra={
    "action": "set_is_verified",
    "salon_id": salon_id,
    "admin_user_id": current_user.id,
    "new_value": True,
    "timestamp": datetime.utcnow().isoformat()
})
```

Until structured logging is set up, write to console — uvicorn will capture it in Docker logs.

---

## 9. Security Headers

**Via Nginx:**
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

**Via Cloudflare:** Cloudflare adds additional security headers at edge.

**Content-Security-Policy:** Not yet implemented. Required when adding GA4 script — CSP must allow `googletagmanager.com` and `google-analytics.com`. Add with GA4 implementation.

---

## 10. Secrets Management

**Current state:** Single `.env` file at project root, shared by all Docker services.

**Rules:**
- `.env` is in `.gitignore` — never commit (enforced)
- `.env.example` with placeholder values should be committed for documentation
- No secrets in Docker image layers (no `COPY .env` in Dockerfile — verify)
- No secrets in Next.js client bundle — only `NEXT_PUBLIC_*` vars are safe to expose

**Post-MVP recommendation:** Migrate to Docker Swarm secrets or HashiCorp Vault when team size grows. Not needed for single-admin setup.

---

## 11. Known Security Gaps (Not Blocking MVP)

| Gap | Risk Level | Recommended Fix |
|---|---|---|
| Cloudflare Turnstile not confirmed active | Medium | Verify frontend integration before launch |
| No account deletion endpoint | Medium | Add POST /api/auth/delete-account |
| Rate limits don't survive API restart | Low | Connect slowapi to Redis (one-line fix) |
| No audit log for admin actions | Low | Add structured logging to admin PATCH |
| Content-Security-Policy not set | Low | Add when GA4 is implemented |
| Cookie consent banner absent | Low | Required for GDPR; add with GA4 |
| Privacy Policy page missing | High (pre-launch) | Must exist before MVP launch |

---

## 12. Static Analysis (CodeQL) — Disabled, Platform Limitation

**Status:** Disabled — platform/licensing limitation (2026-07-11)

**Reason:** `lookla-platform` is a private repository. GitHub Code
Scanning (the CodeQL workflow's upload step) requires GitHub Code
Security to be enabled on the repository; confirmed via a real run that
this is not a workflow-permissions issue — `github/codeql-action/analyze`
returns `Code scanning is not enabled for this repository` even with
`contents: read`, `actions: read`, and `security-events: write` all
granted. No workflow change or personal access token can work around a
missing license.

**Decision:** Not worth making the repository public or purchasing
GitHub Code Security at the current MVP stage solely to unblock this.
`.github/workflows/codeql.yml` is kept (not deleted) with only
`workflow_dispatch` (manual) triggers, so it can be restored by
re-adding `push`/`pull_request`/`schedule` once Code Security is
enabled or the repo's visibility policy changes.

**Not an M-01 release blocker.** Backend and frontend CI (lint + build/tests)
remain the blocking, required checks and are green. CodeQL must not be
configured as a required branch-protection check while in this state.

**Re-enable condition:** GitHub Code Security becomes available for this
repository (or it becomes public), tracked as T-039 in
`05_ROADMAP/IMPLEMENTATION_BACKLOG.md`.

---

*Last updated: 2026-07-11*
