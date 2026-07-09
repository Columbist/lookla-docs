---
title: Admin Panel Specification
status: Draft
version: 0.1
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 04_ARCHITECTURE/DATA_FLOW.md
  - 06_ENGINEERING/AUDIT.md
implementation_status: Partially implemented — spec pending approval
---

# Admin Panel
**Lookla Beauty Marketplace**

> **DRAFT — awaiting approved product decisions.**

---

## Purpose

The Admin Panel is the internal moderation and data management interface for Lookla staff.

---

## Current Implementation (from Engineering Audit)

- Route: `/admin`
- Requires `role = 'admin'`
- Stats dashboard: total/verified salons, pending moderation, total users, bookings today/total, open reports
- Salon list with filters: needs_review, verified, text search
- Salon flag management: `is_active`, `is_verified`, `needs_review`
- Professional list
- User list
- Reports queue
- Moderation queue

No inline content editing. No merge/deduplication tools.

---

## Approved Specification

_[Awaiting approval]_

---

*Last updated: 2026-07-09*
