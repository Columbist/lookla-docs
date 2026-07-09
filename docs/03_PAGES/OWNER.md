---
title: Owner Dashboard Specification
status: Draft
version: 0.1
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 01_PRODUCT/PRODUCT_SCOPE.md
  - 01_PRODUCT/PRODUCT_TERMINOLOGY.md
  - 04_ARCHITECTURE/FEATURE_FLAGS.md
implementation_status: Partially implemented — spec pending approval
---

# Owner Dashboard
**Lookla Beauty Marketplace**

> **DRAFT — awaiting approved product decisions.**  
> Owner Dashboard is a Planned capability. Backend infrastructure exists. UI is partially implemented.  
> This page must not be publicly linked until formally approved.

---

## Purpose

The Owner Dashboard is where a Salon Owner manages their claimed Listing: edits business information, manages hours, services, and photos.

---

## Current Implementation (from Engineering Audit)

- Route: `/dashboard/salon`
- Claim flow UI: implemented (form → code verification)
- Owned salons list: implemented
- Edit individual salon: backend endpoints exist; frontend coverage partial
- Service management: backend endpoints exist; UI not confirmed
- Photo upload: backend R2 upload exists; UI not confirmed
- SMS/WhatsApp claiming: channel parameter exists in code but no API key configured — sends nothing

---

## Approved Specification

_[Awaiting approval]_

---

*Last updated: 2026-07-09*
