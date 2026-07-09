---
title: Search Page Specification
status: Draft
version: 0.1
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 01_PRODUCT/USER_JOURNEYS.md
  - 04_ARCHITECTURE/DATA_FLOW.md
  - 02_DESIGN/COMPONENT_LIBRARY.md
implementation_status: Implemented — spec pending approval
---

# Search Page
**Lookla Beauty Marketplace**

> **DRAFT — awaiting approved product decisions.**

---

## Purpose

The Search Page is the primary discovery surface. Users filter and browse listings to find a beauty business that matches their needs.

---

## Current Implementation (from Engineering Audit)

- Client-side rendered (CSR)
- Infinite scroll with IntersectionObserver sentinel
- Filters: city, category, minimum rating
- Views: list (card grid) and map
- URL as state: filters persist in query params
- 24 salons per page
- Multilingual query translation (Russian/Ukrainian → Greek/English)

**Known issue documented in Terminology:** the "City" filter maps to `address_city` which contains districts, not just cities. Selecting "Athens" returns only central Athens, not the full metro area. Requires a product decision before redesign.

---

## Approved Specification

_[Awaiting approval]_

### Search Behaviour

_[Awaiting approval]_

### Filter Behaviour

_[Awaiting approval]_

### Sort Order

_[Awaiting approval]_

### Map Behaviour

_[Awaiting approval]_

### Empty State

_[Awaiting approval]_

### Mobile Behaviour

_[Awaiting approval]_

---

*Last updated: 2026-07-09*
