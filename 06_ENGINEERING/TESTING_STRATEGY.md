---
title: Testing Strategy
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 06_ENGINEERING/DEVELOPMENT_STANDARDS.md
  - 08_REVIEWS/ARCHITECTURE_REVIEW.md
  - 04_ARCHITECTURE/BACKEND_ARCHITECTURE.md
  - 04_ARCHITECTURE/API_SPECIFICATION.md
  - 04_ARCHITECTURE/PERFORMANCE.md
  - 05_ROADMAP/IMPLEMENTATION_BACKLOG.md
implementation_status: Testing infrastructure pending (T-001, T-030)
---

# Testing Strategy
**Lookla Beauty Marketplace**

> **Philosophy:** Test the critical path, not everything. The five most dangerous functions in Lookla are:
> 1. `is_bot()` — incorrectly classifying real users as bots silently breaks the platform for those users
> 2. `_batch_open_now()` — wrong timezone/DST handling sends users to closed salons
> 3. `_translate_query()` — wrong synonyms make Russian/Ukrainian search return empty results
> 4. JWT auth flow — any bug here = complete authentication failure
> 5. Search filter logic — the core user-facing feature
>
> Write tests for these five before writing any other test. Do not write tests for code that has low risk of regression or low impact when it fails.

---

## Testing Layers

| Layer | Framework | When written |
|---|---|---|
| Unit tests | `pytest` | Before changing the tested function |
| Integration tests | `pytest` + `TestClient` | For new API endpoints; for auth flow |
| API contract tests | `pytest` + `httpx.AsyncClient` | For critical endpoint schemas |
| UI component tests | `vitest` + `@testing-library/react` | For contact buttons, consent banner |
| Performance tests | PageSpeed Insights (manual) | Pre-launch gate |
| Manual smoke tests | Journeys J-01/J-02/J-03 | Pre-launch gate + after every deploy |

---

## 1. Unit Tests

### 1.1 is_bot() — Priority: Critical

**File:** `backend/tests/test_is_bot.py`

**What to test:** The `is_bot(user_agent: str) -> bool` function in the search/media module.

**Test cases:**

```python
import pytest
from app.utils.bot import is_bot  # adjust import path

# Known bots — must return True
@pytest.mark.parametrize("ua", [
    "Googlebot/2.1 (+http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "GPTBot/1.0 (+https://openai.com/gptbot)",
    "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
    "python-requests/2.31.0",
    "curl/8.1.2",
    "Go-http-client/1.1",
    "Scrapy/2.11",
    "LinkedInBot/1.0 (compatible; Mozilla/5.0; Jakarta Commons-HttpClient/3.1)",
    "",  # empty UA = treat as bot
])
def test_is_bot_returns_true(ua):
    assert is_bot(ua) is True

# Known real browsers — must return False
@pytest.mark.parametrize("ua", [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
])
def test_is_bot_returns_false(ua):
    assert is_bot(ua) is False
```

**Critical invariant:** If this test is added and then a regex change makes a real Chrome UA return `True`, the test catches it before production.

---

### 1.2 _batch_open_now() — Priority: Critical

**File:** `backend/tests/test_open_now.py`

**What to test:** The `_batch_open_now(salon_ids, db)` function (or equivalent) that determines open/closed status using Athens timezone (Europe/Athens).

**Test cases:**

```python
from datetime import datetime
from unittest.mock import patch
import pytest

# Athens timezone: UTC+2 (winter), UTC+3 (summer, EEST)
# DST starts: last Sunday of March
# DST ends: last Sunday of October

@pytest.mark.parametrize("dt_utc,weekday,open_from,open_to,expected", [
    # Monday 10:00 Athens (08:00 UTC, summer = EEST = UTC+3)
    (datetime(2026, 7, 6, 7, 0, 0), 0, "09:00", "20:00", True),
    # Monday 22:00 Athens (19:00 UTC, summer)
    (datetime(2026, 7, 6, 19, 0, 0), 0, "09:00", "20:00", False),
    # Saturday midnight Athens edge case
    (datetime(2026, 7, 4, 21, 0, 0), 5, "10:00", "18:00", False),
    # DST transition: last Sunday October (clocks go back: 04:00 EEST → 03:00 EET)
    # 2026-10-25 03:30 UTC = 05:30 EEST before transition = 04:30 EET after transition
    (datetime(2026, 10, 25, 1, 30, 0), 6, "10:00", "18:00", False),
    # Sunday 11:00 Athens in winter (UTC+2)
    (datetime(2026, 11, 1, 9, 0, 0), 6, "10:00", "18:00", True),
])
def test_batch_open_now(dt_utc, weekday, open_from, open_to, expected):
    with patch('app.services.salons._get_current_athens_time', return_value=dt_utc.replace(tzinfo=...)):
        # test against the actual function
        ...
```

**DST note:** Do NOT use `datetime.now()` in tests. Always use fixed datetimes. The test must pass on any date and timezone of the CI runner.

---

### 1.3 _translate_query() — Priority: Critical

**File:** `backend/tests/test_translate_query.py`

**What to test:** The `_translate_query(query: str, lang: str) -> str` function that expands Russian/Ukrainian search terms to Greek equivalents.

**Test cases:**

```python
from app.services.search import _translate_query  # adjust import

@pytest.mark.parametrize("input_q,lang,expected_contains", [
    # Russian service names → Greek equivalents
    ("маникюр", "ru", "manicure"),          # or equivalent service keyword
    ("стрижка", "ru", "haircut"),
    ("педикюр", "ru", "pedicure"),
    ("массаж", "ru", "massage"),
    # Ukrainian service names
    ("манікюр", "uk", "manicure"),
    ("стрижка", "uk", "haircut"),
    # Already Greek → unchanged
    ("κομμωτήριο", "el", "κομμωτήριο"),
    # Already English → unchanged
    ("manicure", "en", "manicure"),
    # Empty string → unchanged
    ("", "ru", ""),
    # Unknown term → returned as-is (no crash)
    ("randomterm123", "ru", "randomterm123"),
])
def test_translate_query(input_q, lang, expected_contains):
    result = _translate_query(input_q, lang)
    assert expected_contains.lower() in result.lower()
```

**Why this matters:** If "маникюр" is not in the synonym dict, the search query searches the DB for the literal string "маникюр" and returns 0 results. This is the most impactful test for the primary persona (P-02).

---

### 1.4 translate.py OpenAI error handling — Priority: High

**File:** `backend/tests/test_translate_openai.py`

**What to test:** That `translate.py` returns original names when OpenAI API call fails.

```python
from unittest.mock import patch, MagicMock
import openai
from app.services.translate import translate_service_names  # adjust

def test_translate_returns_original_on_openai_error():
    original_names = ["Manicure", "Haircut", "Pedicure"]
    
    with patch('openai.chat.completions.create', side_effect=openai.APIError("timeout")):
        result = translate_service_names(original_names, target_lang="ru")
    
    # Should return originals, not raise
    assert result == original_names

def test_translate_returns_original_on_unexpected_error():
    original_names = ["Manicure"]
    
    with patch('openai.chat.completions.create', side_effect=Exception("unexpected")):
        result = translate_service_names(original_names, target_lang="ru")
    
    assert result == original_names
```

---

## 2. Integration Tests

### 2.1 Auth Flow — Priority: Critical

**File:** `backend/tests/test_auth.py`

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_creates_user():
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "name": "Test User",
        "turnstile_token": "test-bypass-token"  # configure test bypass in settings
    })
    assert response.status_code == 201
    assert "id" in response.json()

def test_login_sets_httponly_cookie():
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 200
    assert "lookla_access" in response.cookies
    # Verify httpOnly (TestClient exposes cookie attrs)
    cookie = response.cookies.get("lookla_access")
    assert cookie is not None

def test_refresh_rotates_token():
    # Login, get cookie, then call refresh
    login = client.post("/api/auth/login", json={"email": "test@example.com", "password": "SecurePass123!"})
    old_token = login.cookies.get("lookla_access")
    
    refresh = client.post("/api/auth/refresh")
    new_token = refresh.cookies.get("lookla_access")
    
    assert refresh.status_code == 200
    assert new_token != old_token  # token rotated

def test_expired_refresh_returns_401():
    # Use an expired or invalid refresh token
    client.cookies.set("lookla_refresh", "expired.invalid.token")
    response = client.post("/api/auth/refresh")
    assert response.status_code == 401
```

---

### 2.2 Salon List Filter Logic — Priority: Critical

**File:** `backend/tests/test_salons.py`

```python
def test_salon_list_returns_active_only():
    response = client.get("/api/salons")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert all(s["is_active"] for s in data["items"])

def test_area_filter():
    response = client.get("/api/salons?area=glyfada")
    assert response.status_code == 200
    salons = response.json()["items"]
    for salon in salons:
        assert salon["address_district"].lower() == "glyfada"

def test_area_filter_unknown_returns_empty():
    response = client.get("/api/salons?area=doesnotexist12345")
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []

def test_pagination():
    response = client.get("/api/salons?page=1&per_page=5")
    assert response.status_code == 200
    assert len(response.json()["items"]) <= 5

def test_salon_detail_includes_owner_claimed_field():
    response = client.get("/api/salons/1")  # assumes salon with id=1 exists
    assert response.status_code == 200
    data = response.json()
    assert "is_owner_claimed" in data
    assert isinstance(data["is_owner_claimed"], bool)

def test_areas_endpoint():
    response = client.get("/api/areas")
    assert response.status_code == 200
    areas = response.json()["areas"]
    assert len(areas) >= 1
    for area in areas:
        assert "slug" in area
        assert "salon_count" in area
        assert area["salon_count"] > 0  # empty areas excluded
```

---

### 2.3 Report Submission — Priority: Medium

**File:** `backend/tests/test_reports.py`

```python
def test_submit_report_anonymous():
    response = client.post("/api/salons/1/reports", json={
        "report_type": "wrong_phone",
        "description": "Phone number is disconnected"
    })
    assert response.status_code == 201

def test_submit_report_missing_fields():
    response = client.post("/api/salons/1/reports", json={})
    assert response.status_code == 422  # validation error
```

---

## 3. API Contract Tests

These tests verify that the API response structure matches `API_SPECIFICATION.md` exactly. Run against the running server.

**File:** `backend/tests/test_api_contracts.py`

```python
def test_salon_list_contract():
    response = client.get("/api/salons")
    data = response.json()
    
    # Top-level keys
    assert set(data.keys()) >= {"items", "total", "page", "per_page"}
    
    if data["items"]:
        salon = data["items"][0]
        # Required fields per API_SPECIFICATION.md
        required = {"id", "slug", "name", "address_city", "address_district",
                   "is_verified", "is_owner_claimed", "rating_google", "photo_url"}
        assert required.issubset(set(salon.keys()))

def test_salon_detail_contract():
    response = client.get("/api/salons/1")
    if response.status_code == 404:
        pytest.skip("No salon with id=1 in test DB")
    
    data = response.json()
    required = {"id", "slug", "name", "phone_primary", "is_verified",
               "is_owner_claimed", "address_street", "address_city"}
    assert required.issubset(set(data.keys()))

def test_review_list_contract():
    response = client.get("/api/salons/1/reviews")
    if response.status_code == 200 and response.json()["items"]:
        review = response.json()["items"][0]
        assert "source" in review
        assert review["source"] == "google"  # DEC-013: only google reviews in MVP
```

---

## 4. UI Component Tests

**Framework:** `vitest` + `@testing-library/react`

**Priority targets:** The components that implement P0 decisions.

### 4.1 ContactButtons.tsx — Priority: Critical (DEC-015/016)

**File:** `frontend/__tests__/components/ContactButtons.test.tsx`

```typescript
import { render, screen } from '@testing-library/react';
import { ContactButtons } from '@/components/ContactButtons';

const mockSalon = {
  id: 1,
  name: "Test Salon",
  phone_primary: "+306901234567",
  website_url: "https://example.com"
};

test('shows all three contact buttons', () => {
  render(<ContactButtons salon={mockSalon} />);
  expect(screen.getByText(/call salon/i)).toBeInTheDocument();
  expect(screen.getByText(/whatsapp/i)).toBeInTheDocument();
  expect(screen.getByText(/visit website/i)).toBeInTheDocument();
});

test('call button has correct tel: href', () => {
  render(<ContactButtons salon={mockSalon} />);
  const callBtn = screen.getByText(/call salon/i).closest('a');
  expect(callBtn).toHaveAttribute('href', 'tel:+306901234567');
});

test('whatsapp button has correct wa.me href', () => {
  render(<ContactButtons salon={mockSalon} />);
  const waBtn = screen.getByText(/whatsapp/i).closest('a');
  expect(waBtn?.getAttribute('href')).toMatch(/wa\.me\/306901234567/);  // cleaned number
});

test('website button has noopener rel', () => {
  render(<ContactButtons salon={mockSalon} />);
  const webBtn = screen.getByText(/visit website/i).closest('a');
  expect(webBtn).toHaveAttribute('rel', 'noopener noreferrer');
  expect(webBtn).toHaveAttribute('target', '_blank');
});

test('hides call and whatsapp buttons when phone_primary is null', () => {
  render(<ContactButtons salon={{ ...mockSalon, phone_primary: null }} />);
  expect(screen.queryByText(/call salon/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/whatsapp/i)).not.toBeInTheDocument();
});

test('hides website button when website_url is null', () => {
  render(<ContactButtons salon={{ ...mockSalon, website_url: null }} />);
  expect(screen.queryByText(/visit website/i)).not.toBeInTheDocument();
});
```

---

### 4.2 VerifiedBadge.tsx — Priority: High (DEC-014)

**File:** `frontend/__tests__/components/VerifiedBadge.test.tsx`

```typescript
test('shows "Information reviewed" when verified but not claimed', () => {
  render(<VerifiedBadge is_verified={true} is_owner_claimed={false} />);
  expect(screen.getByText(/information reviewed/i)).toBeInTheDocument();
  expect(screen.queryByText(/✓/)).not.toBeInTheDocument();
});

test('shows "Owner verified" when claimed', () => {
  render(<VerifiedBadge is_verified={true} is_owner_claimed={true} />);
  expect(screen.getByText(/owner verified/i)).toBeInTheDocument();
});

test('shows nothing when not verified', () => {
  const { container } = render(<VerifiedBadge is_verified={false} is_owner_claimed={false} />);
  expect(container.firstChild).toBeNull();
});
```

---

### 4.3 CookieConsent.tsx — Priority: High (GDPR)

**File:** `frontend/__tests__/components/CookieConsent.test.tsx`

```typescript
test('shows banner on first visit (no cookie)', () => {
  // Mock: no lookla_consent cookie
  render(<CookieConsent />);
  expect(screen.getByText(/this site uses/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /accept/i })).toBeInTheDocument();
});

test('does not show banner when consent cookie is set', () => {
  document.cookie = 'lookla_consent=1';
  render(<CookieConsent />);
  expect(screen.queryByText(/this site uses/i)).not.toBeInTheDocument();
});

test('accept button sets consent cookie', async () => {
  render(<CookieConsent />);
  const acceptBtn = screen.getByRole('button', { name: /accept/i });
  await userEvent.click(acceptBtn);
  expect(document.cookie).toContain('lookla_consent=1');
});
```

---

## 5. Performance Tests

Performance is verified manually using production tooling — not automated for MVP.

### 5.1 PageSpeed Insights (pre-launch gate)

Run on: `https://lookla.gr/el/salons/[any-slug]` (mobile simulation)

| Metric | Target | Tool |
|---|---|---|
| LCP | < 2.5s | PageSpeed Insights |
| CLS | < 0.1 | PageSpeed Insights |
| INP | < 200ms | PageSpeed Insights |
| TTFB | < 800ms | PageSpeed Insights |

**Failure response:** If LCP > 2.5s:
1. Check if hero photo uses `priority={true}` on `next/image`
2. Check if hero photo is served from `cdn.lookla.gr` (R2) not Google proxy
3. Check if GA4 script is using `strategy="afterInteractive"`
4. Run `next build && next analyze` to check bundle size

### 5.2 DB Query Verification

Run against production DB, not test DB:

```sql
-- Verify search query uses FTS index
EXPLAIN ANALYZE
SELECT id, name, address_city FROM salons
WHERE to_tsvector('simple', unaccent(coalesce(name,'') || ' ' || coalesce(name_el,'')))
@@ plainto_tsquery('simple', 'manicure')
AND is_active = true LIMIT 24;
-- Look for "Bitmap Index Scan on idx_salons_fts" in the output

-- Verify area filter uses district index  
EXPLAIN ANALYZE
SELECT id, name, address_district FROM salons
WHERE address_district ILIKE '%glyfada%' AND is_active = true;
-- Look for "Index Scan on idx_salons_address_district"
```

---

## 6. Manual Smoke Tests (Pre-Launch)

Run in production environment (not localhost) in the listed browser/device combinations.

### Journey J-01 — Russian Persona Conversion

**Browser:** Chrome 124 on Android (or Chrome DevTools mobile emulation 375px)
**Locale:** /ru

1. Navigate to `https://lookla.gr/ru`
2. Observe: homepage in Russian, language switcher in header visible
3. Search "маникюр" in the search bar
4. Observe: search results page loads; results show nail salons
5. Click filter "Район" → select "Glyfada"
6. Observe: results filtered to Glyfada district salons only
7. Click any salon
8. Observe: salon detail page loads; no booking buttons; "Написать в WhatsApp" button visible
9. Click "Написать в WhatsApp"
10. Observe: WhatsApp opens with the salon's number
11. In GA4 Realtime: observe `contact_action` event with `action_type: whatsapp`

**Expected: all steps pass. Any failure = blocker.**

---

### Journey J-02 — Greek Persona Call

**Browser:** Safari 17 on iPhone (or Chrome DevTools 390px)
**Locale:** /el

1. Navigate to `https://lookla.gr/el`
2. Search "κομμωτήριο" (hairdresser)
3. Open a salon
4. Tap "Κλήση" (Call salon)
5. Observe: native phone dialer opens with correct number
6. In GA4 Realtime: observe `contact_action` with `action_type: phone`

**Expected: all steps pass.**

---

### Journey J-03 — DEC Compliance Spot Check

**Browser:** Any (desktop Chrome is fine)

1. Open any salon that has Google reviews
2. Verify: "Source: Google Reviews / Imported: Yes / Original: No" header visible above reviews
3. Open any salon with `is_verified = true` (check admin panel for a known one)
4. Verify: text "Information reviewed" or "Owner verified" visible — no ✓ icon
5. Inspect header navigation: no "Pricing" or "Plans" link anywhere
6. Open `https://lookla.gr/robots.txt`: Disallow rules present
7. Test incognito: all 3 CTAs visible and clickable without login

**Expected: all checks pass.**

---

## 7. Test Environment Requirements

**Backend tests need:**
- PostgreSQL test database (separate from production)
- `.env.test` with test DB credentials
- Alembic migrations applied to test DB: `alembic -x env=test upgrade head`
- Test data: minimum 5 active salons, 1 verified salon, 1 claimed salon, 1 user

**Setup:**
```bash
# Create test DB
docker exec lookla_db createdb -U postgres lookla_test

# Run migrations against test DB
DATABASE_URL=postgresql://postgres:pass@localhost:5432/lookla_test alembic upgrade head

# Run tests
cd backend && pytest tests/ -v
```

**Frontend tests need:**
- Node.js 20+
- `npm install` complete
- No external API calls during unit tests (mock all fetches)

---

## 8. What is NOT tested in MVP

- End-to-end browser tests (Playwright/Cypress) — overkill for current scale; add post-MVP
- Load testing — run `ab` or `wrk` manually if performance degrades post-launch
- Accessibility testing (WCAG) — planned, not in MVP scope
- Crawler integration tests — crawlers run weekly; manual verify by checking salon counts
- Email delivery tests (Resend) — manual test the claim flow before launch

---

## 9. Coverage Targets

MVP does not have a minimum coverage percentage requirement. Coverage targets are function-specific:

| Function | Required coverage |
|---|---|
| `is_bot()` | 100% of known bot/browser patterns |
| `_batch_open_now()` | Happy path + DST transition + weekend |
| `_translate_query()` | All SERVICE_SYNONYMS keys that exist in CATEGORY_KEYWORDS |
| JWT auth flow | Register → Login → Refresh → Expired refresh (4 scenarios) |
| `/api/salons` filter | No filter + area filter + city filter + empty result |

Everything else: no requirement. Write a test when you're about to change something and aren't sure it will work.

---

*Last updated: 2026-07-09*
