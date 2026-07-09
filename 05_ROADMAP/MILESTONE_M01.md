---
title: Milestone M-01 — MVP Athens Launch
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 05_ROADMAP/ROADMAP.md
  - 05_ROADMAP/EPICS.md
  - 05_ROADMAP/IMPLEMENTATION_BACKLOG.md
  - 01_PRODUCT/MVP_SCOPE_LOCK.md
  - 00_GOVERNANCE/DECISION_LOG.md
implementation_status: In Progress — Technical architecture approved; development pending
---

# Milestone M-01 — MVP Athens Launch

---

## Summary

**M-01 ships Lookla as a functional, honest, multilingual beauty directory for Athens, Greece.**

The milestone is complete when: a resident of Athens can find a salon matching their needs, make contact (call, WhatsApp, or visit the website) without creating an account, and both the user and the platform benefit — user gets the service; Lookla records a contact action that counts toward the DEC-008 success metric.

**Success is measured, not assumed.** M-01 requires GA4 to be running and recording `contact_action` events.

---

## Scope

### What M-01 ships

| Area | What ships |
|---|---|
| Location | Athens metropolitan area (DEC-012) |
| Salons | ~6300 scraped salons with data quality sufficient for contact |
| Languages | Greek (el), English (en), Russian (ru) at full quality; Ukrainian (uk) at lower priority |
| Search | Full-text search + area filter (DEC-010) + category filter |
| Salon detail | Name, address, hours, services, contact buttons, Google reviews |
| Contact CTAs | "Call salon", "Message on WhatsApp", "Visit website" — all anonymous (DEC-016) |
| Reviews | Google Reviews with mandatory source attribution (DEC-013) |
| Verified label | Text: "Information reviewed" or "Owner verified" — not ✓ icon (DEC-014) |
| Analytics | GA4 events: pageview + `contact_action`; Google Search Console (DEC-017) |
| Legal | Privacy Policy page; cookie consent banner |
| New pages | /about, /contact |
| Admin | Inline edit (phone, address, verified flag); backup cron configured |

### What M-01 explicitly excludes

Refer to `01_PRODUCT/MVP_SCOPE_LOCK.md` for the complete WILL NOT HAVE list. Key exclusions:

- Booking or appointment scheduling
- Owner self-service claim UI (manual only via email)
- Favorites / saved salons
- Chat / messaging
- Stripe / subscriptions / payments UI
- National coverage beyond Athens metro
- Mobile app
- AI recommendations or rankings

---

## Success Criteria (DEC-008)

**Primary:** 500 `contact_action` events (phone + whatsapp + website combined) recorded in GA4 within 90 days of M-01 production deployment.

**Supporting indicators (not gates, but signals):**
- GA4 average session duration > 60 seconds (users engaged, not bouncing)
- Search Console: at least one indexed salon page for target keywords (e.g., "nail salon Athens")
- Bounce rate on salon detail < 60%
- Zero critical errors in production logs (no 500s on search / salon detail)

**Anti-success indicators:**
- `contact_action` events are firing but zero phone calls are actually happening (signal: users click but get wrong numbers). Check a sample of phone numbers manually.
- Events fire but salon data is wrong (test: call 3 random salons, verify they are real and active).

---

## Exit Criteria (Pre-Launch Gate)

**ALL of the following must be true before M-01 is declared launched:**

### Data Quality
- [ ] At least 500 Athens salons have a non-null `address_district` value
- [ ] At least 300 salons have `phone_primary` non-null and correct format
- [ ] Admin has reviewed at minimum 50 salons (`is_verified = true`) before launch

### Backend
- [ ] Alembic baseline committed; `alembic upgrade head` works
- [ ] `address_district` column exists with correct data
- [ ] `GET /api/areas` returns ≥ 8 Athens districts with salons
- [ ] `GET /api/salons?area=glyfada` returns correct results
- [ ] Daily pg_dump cron confirmed active on server

### Frontend — Critical DEC Compliance
- [ ] **DEC-015:** Zero booking stub buttons on any salon detail page
- [ ] **DEC-013:** Review section header "Source: Google Reviews / Imported: Yes / Original: No" visible
- [ ] **DEC-014:** is_verified=true shows "Information reviewed" text (no ✓ icon)
- [ ] **DEC-016:** All 3 contact CTAs work without logging in
- [ ] **DEC-006:** `/pricing` is NOT linked anywhere in navigation
- [ ] Language switcher is visible in header without scrolling

### Analytics
- [ ] GA4 property active with real tracking ID (not placeholder "G-XXXXXXXXXX")
- [ ] `contact_action` custom event verified in GA4 Realtime when testing contact buttons
- [ ] `contact_action` event sends `action_type`, `salon_id`, `salon_name` parameters
- [ ] GA4 data retention set to 14 months in GA4 admin
- [ ] GA4 IP anonymization enabled in GA4 admin
- [ ] Google Search Console property verified (DNS TXT)

### Legal
- [ ] `/[locale]/privacy` page live with Privacy Policy content
- [ ] Privacy Policy mentions Google Analytics
- [ ] Cookie consent banner appears on first visit
- [ ] GA4 script does not load until consent is given

### Pages
- [ ] `/[locale]/about` live in el/en/ru
- [ ] `/[locale]/contact` live in el/en/ru
- [ ] Both pages linked from footer

### Performance
- [ ] PageSpeed Insights LCP on salon detail (mobile) < 2.5s
- [ ] No CLS issues on salon detail (score < 0.1)
- [ ] GIN index on `salons` FTS tsvector confirmed present
- [ ] `idx_salons_address_district` index confirmed present

### Code Quality
- [ ] React error boundary wraps SalonDetailClient
- [ ] `translate.py` catches OpenAI API errors (returns original text)
- [ ] Unit tests pass: `is_bot()`, `_batch_open_now()`, `_translate_query()`
- [ ] `public/robots.txt` file exists and is served at lookla.gr/robots.txt

### Manual QA
- [ ] **J-01 (Primary flow):** Visitor → search "маникюр" in Russian → filter by "Glyfada" → open salon → click "Message on WhatsApp" → WhatsApp opens with correct number. All steps complete.
- [ ] **J-02 (Call flow):** Visitor → open any salon → tap "Call salon" → correct phone number dials on mobile. All steps complete.
- [ ] **J-03 (Review check):** Open a salon with Google reviews → "Source: Google Reviews" header visible → no ✓ badge icons on verified salons.
- [ ] Test in 3 browsers: Chrome 124+, Safari 17+, Firefox 125+

---

## M-01 Critical Path

```
[EPIC-01 Database]
     │
     ├──► [EPIC-02 Area Filter BE] ──► [EPIC-02 Area Filter FE]
     │                                        │
     │                                        ▼
     │                              [EPIC-03 Salon Detail]
     │
     └──► (parallel with below)

[EPIC-05 Legal/GDPR]  ◄── MUST COMPLETE BEFORE ──► [EPIC-04 Analytics]
         │                                                   │
         └─────────────────────────────────────────────────►│
                                                            │
[EPIC-06 New Pages]  ←─── independent ────────────────────-┘
[EPIC-07 Homepage]   ←─── depends on EPIC-02 area params

[EPIC-08 Admin]      ←─── depends on EPIC-01, EPIC-03 (is_verified semantics)
[EPIC-09 Code Quality] ← parallel; tests BEFORE changing tested functions
[EPIC-10 Translation QA] ← after EPIC-02 services accessible

                    ALL ↓
              [M-01 Pre-Launch Gate]
                    │
                    ▼
              [Manual QA J-01, J-02, J-03]
                    │
                    ▼
              [M-01 LAUNCHED]
```

**Estimated total development effort:** ~10.5 developer-days (see EPICS.md for per-epic estimates)

---

## M-01 Deployment Steps

After all pre-launch gate criteria pass:

```bash
# 1. Backup production DB before any change
docker exec beauty_db pg_dump -U postgres lookla | gzip > /opt/backups/lookla_pre_m01_$(date +%Y%m%d).sql.gz

# 2. Apply database migrations
cd /root/beauty-gr/backend
docker exec beauty_api alembic upgrade head

# 3. Rebuild and redeploy frontend and backend
docker buildx build -t lookla-api ./backend
docker buildx build -t lookla-web ./frontend
docker compose up -d api web

# 4. Verify health
curl -f https://lookla.gr/api/health
curl -f https://lookla.gr/el/about

# 5. Manual QA: J-01, J-02, J-03

# 6. Declare M-01 launched; set GA4 start date note
```

---

## Post-M-01 Measurement Window

- **T+1 day:** Check GA4 Realtime for first organic sessions
- **T+7 days:** First week report — sessions, bounce rate, `contact_action` count
- **T+30 days:** First monthly report — contact actions / unique salon viewed ratio
- **T+90 days:** M-01 success evaluation — did we reach 500 contact actions?

**If 500 actions in 90 days:** Proceed to M-02 planning with GA4 evidence of which features matter most.
**If <500 actions in 90 days:** Diagnose using GA4 funnel (where do users drop off?) before committing to M-02.

---

*Last updated: 2026-07-09*
