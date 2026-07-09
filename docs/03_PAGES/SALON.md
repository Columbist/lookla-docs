---
title: Salon Detail Page Specification
status: Draft
version: 0.1
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 01_PRODUCT/USER_JOURNEYS.md
  - 01_PRODUCT/PRODUCT_TERMINOLOGY.md
  - 04_ARCHITECTURE/DATA_FLOW.md
implementation_status: Implemented — spec pending approval
---

# Salon Detail Page (Listing)
**Lookla Beauty Marketplace**

> **DRAFT — awaiting approved product decisions.**

---

## Purpose

The Salon Detail Page displays a complete Listing for a specific Beauty Business. It is the page where a Visitor converts into a contact (call, WhatsApp, website visit) or a future Booking.

---

## Current Implementation (from Engineering Audit)

- Route: `/salons/[slug]`
- Metadata (title, description, OG image): Server-side rendered
- Main content: Client-side rendered via `SalonDetailClient`
- Photos: displayed immediately
- Services: lazy-loaded via IntersectionObserver when section enters viewport
- Reviews: lazy-loaded via IntersectionObserver when section enters viewport
- Translation: on-demand (first real-user view), cached in DB, labeled with translation badge
- Bot protection: services and reviews return empty for detected bots
- Booking buttons: present but non-functional (stub)

**Known issues documented:**
- `is_verified` badge (✓) reflects admin review, not Salon Owner verification — trust signal mismatch
- Reviews are Aggregated (Google), not Owned — not labeled as such to users

---

## Approved Specification

_[Awaiting approval]_

### Sections

_[Awaiting approval]_

### Translation Behaviour

_[Awaiting approval]_

### Booking CTA Behaviour

_[Awaiting approval — currently stubbed]_

### Empty States

_[Awaiting approval]_

### Mobile Behaviour

_[Awaiting approval]_

---

*Last updated: 2026-07-09*
