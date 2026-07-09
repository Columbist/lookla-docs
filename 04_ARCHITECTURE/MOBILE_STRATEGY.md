---
title: Mobile Strategy
status: Draft
version: 0.1
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 00_GOVERNANCE/PROJECT_CHARTER.md
  - 01_PRODUCT/PRODUCT_SCOPE.md
  - 04_ARCHITECTURE/DATA_FLOW.md
implementation_status: N/A — future capability
---

# Mobile Strategy
**Lookla Beauty Marketplace**

> **DRAFT — awaiting approved product decisions.**  
> Mobile applications are a Future capability. No implementation has started.  
> This document ensures current decisions do not close off the mobile path.

---

## Purpose

This document captures architectural constraints and decisions that keep the platform compatible with future mobile applications (iOS, Android, Partner App).

---

## Charter Requirement (§10)

> "Every UI component must be designed with future reuse in mind for: Web, iOS, Android, Partner Application. No frontend decision should create a web-only dependency that would require a full rewrite for mobile."

---

## Current Constraints (from Engineering Audit)

### Risks for future mobile (from AUDIT.md §24)

1. **httpOnly cookie auth** — Native HTTP clients (URLSession, OkHttp) do not persist httpOnly cookies naturally. A mobile client will need a Bearer token path or a dedicated `/api/auth/token` JSON response endpoint.

2. **No push notification infrastructure** — No FCM/APNs token storage, no notification service.

3. **No API versioning** — All endpoints under `/api/` with no version prefix. Breaking changes affect all clients simultaneously.

4. **Synchronous translation** — Blocks API thread for 1–3 seconds. Mobile apps expect <500ms. Will require an async queue before mobile launch.

5. **Large response payloads** — List endpoints return full objects. Mobile clients need a compact schema variant.

---

## Planned Requirements (awaiting approval)

_[Awaiting approval — no mobile decisions finalized]_

---

*Last updated: 2026-07-09*
