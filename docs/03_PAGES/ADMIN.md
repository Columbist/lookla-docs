---
title: Admin Panel Specification
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 04_ARCHITECTURE/DATA_FLOW.md
  - 06_ENGINEERING/AUDIT.md
  - 01_PRODUCT/MVP_SCOPE_LOCK.md
implementation_status: Partially implemented — inline editing gap, see Section 4
---

# Admin Panel
**Lookla Beauty Marketplace**

---

## Purpose

The Admin Panel is the internal data management and moderation tool for Lookla staff (currently: one person, columb@europe.com).

Admin Panel goals for MVP:
1. Review and approve/reject user-submitted reports
2. Set verified status on salons after manual review (DEC-014 — "Information reviewed")
3. Monitor platform health (counts, pending queue)
4. Manage data quality for Athens focus area (DEC-012)

The Admin Panel is not a public-facing product. Its UX priority is effectiveness over aesthetics.

---

## Access Control

- Route: `/[locale]/admin`
- Requires: `user.role == 'admin'`
- Authorized users: `columb@europe.com` (hardcoded in config)
- Unauthorized access: redirect to login, then back to `/admin`
- Not linked from public navigation (not reachable without knowing the URL)

---

## Section 1 — Stats Dashboard

**Purpose:** At-a-glance platform health for the admin session.

**Data displayed:**

| Metric | Source | Notes |
|---|---|---|
| Total salons | COUNT salons WHERE is_active=true | |
| Verified salons | COUNT salons WHERE is_verified=true | This now means "Information reviewed" per DEC-014 |
| Claimed salons | COUNT salon_owners (distinct salon_id) | Owner has completed claim + verification |
| Pending moderation | COUNT moderation_queue WHERE status='pending' | |
| Open reports | COUNT reports WHERE status='open' | |
| Total users | COUNT users | |
| Salons needing review | COUNT salons WHERE needs_review=true | |

**Data source:** `GET /api/admin/stats`

**Update frequency:** On page load; no real-time streaming

---

## Section 2 — Salon Management

**Purpose:** Moderation and data quality management for all salons.

### Salon List View

**Filters:**
- `needs_review=true` — salons flagged by users or crawlers
- `is_verified=true/false` — already reviewed vs not yet reviewed
- Text search on salon name

**Columns per row:**
- Salon name
- City / District
- `is_active` toggle
- `is_verified` flag (displayed as "Reviewed" label per DEC-014, not ✓)
- `needs_review` flag
- Link to public salon detail page (opens in new tab)
- "Review" action button

**Action: Set "Information reviewed" (is_verified=true)**

Admin can set `is_verified=true` after confirming:
- Phone number is present and appears correct
- Address is present
- Business appears to be a real active beauty business

**This is the only path for the "Information reviewed" label (DEC-014).**

Admin must NOT set `is_verified=true` just because the salon appears in Google data. Manual spot-check is required.

**Action: Set needs_review=false**

Clears the moderation flag after admin has reviewed the item.

**Action: Set is_active=false**

Removes salon from public listing. Use for: closed business, duplicate, inappropriate content.

**Data source:** `GET /api/admin/salons` + `PATCH /api/admin/salons` (bulk update flags)

---

### Inline Content Editing (GAP — not yet implemented)

**Gap identified in Engineering Audit:** The current admin UI has no inline editing of salon content (name, address, phone, hours, description).

**MVP requirement:** Admin needs to be able to correct obvious data errors (wrong phone number, wrong address) without requiring the salon owner to claim the listing first. This is necessary for data quality in the Athens focus area (DEC-012).

**Required for MVP:**
- Edit `phone_primary`
- Edit `address_street`, `address_city`
- Edit `is_verified` status with confirmation dialog

**API endpoint:** `PATCH /api/admin/salons/{id}` — exists; frontend form is missing

**Future (post-MVP):**
- Edit description, name, photos
- Merge duplicate listings
- Bulk import / data correction tools

---

## Section 3 — Reports Queue

**Purpose:** Process user-submitted "Report incorrect information" requests.

**Columns per report:**
- Salon name + link
- Report type (Phone / Hours / Address / Name / Photos / Other)
- User's description (if provided)
- Submitted at date
- Status: Open / Resolved

**Actions per report:**
- "View salon" → open salon detail in new tab
- "Mark resolved" → `PATCH /api/admin/reports/{id}` sets `status='resolved'`

**Workflow:**
1. Admin reads report
2. Admin opens salon detail to verify the issue
3. If valid: admin edits salon data (via inline edit, when implemented), then marks report resolved
4. If invalid: admin marks report resolved with "No action needed"

**Empty state:** "No open reports" — with date of last resolved report if available

**Data source:** `GET /api/admin/reports` + `PATCH /api/admin/reports/{id}`

---

## Section 4 — Moderation Queue

**Purpose:** Review content items pending approval before they go public.

**Current state:** The moderation_queue table exists. What triggers items to enter this queue is not clearly documented.

**MVP assumption:** Items in the moderation_queue are added when:
- A salon owner updates their listing data (pending review before publishing)
- A user submits a review via a future Lookla-native review feature (not in MVP)

**Actions:**
- View item
- Approve → publishes content
- Reject → discards content, optionally notifies submitter

**Data source:** `GET /api/admin/moderation` — implement full CRUD as needed

---

## Section 5 — User Management

**Purpose:** Internal reference only. Not a moderation tool in MVP.

**Content:** Paginated list of users with: email, role, registration date, is_email_verified

**Actions:** None in MVP (no suspension, no role change via UI)

**Data source:** `GET /api/admin/users`

---

## Section 6 — Analytics Bridge

**Not implemented — future admin feature**

Post-MVP, the admin dashboard should show:
- Top salons by contact clicks (GA4 data)
- Search queries with no results (GA4 data)
- User-facing report volume trend

This section is a placeholder for when GA4 is installed (DEC-017) and data can be pulled via API or BigQuery.

---

## Navigation (Admin Panel)

```
Admin Panel
├── Dashboard (stats)
├── Salons
│   ├── Needs review
│   ├── All salons
│   └── [Salon detail / edit]
├── Reports
├── Moderation queue
└── Users
```

---

## Mobile Considerations

The Admin Panel is not a mobile-first interface. It is used by one admin on a desktop browser.

Minimum: responsive layout that doesn't break on a laptop (1024px+). Mobile support is not a priority.

---

## User Actions and Analytics

Admin actions are internal. No GA4 events required for admin panel actions.

However, the admin panel is a user on the platform — if GA4 is installed, exclude admin email from GA4 tracking to avoid polluting the MVP metrics (DEC-008).

---

## Implementation Checklist (pre-MVP)

- [ ] Update "is_verified" display label from ✓ to "Reviewed" text (DEC-014 compliance)
- [ ] Add inline phone/address edit form for salons (critical for DEC-012 data quality)
- [ ] Verify reports queue shows all open reports correctly
- [ ] Confirm admin email is excluded from GA4 tracking (DEC-017)

---

*Last updated: 2026-07-09*
