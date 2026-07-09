---
title: Feature Flags
status: Draft
version: 0.1
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 00_GOVERNANCE/PROJECT_CHARTER.md
  - 01_PRODUCT/PRODUCT_SCOPE.md
  - 00_GOVERNANCE/DECISION_LOG.md
implementation_status: Conceptual — no dedicated feature flag system
---

# Feature Flags
**Lookla Beauty Marketplace**

> **DRAFT — awaiting approved product decisions.**

---

## Purpose

This document tracks which product capabilities exist in the codebase but are intentionally not exposed to users.

Per Project Charter §9: "The platform must support future functionality without exposing unfinished functionality to users."

At the current stage, Feature Flags are managed **conceptually** — functionality exists in code but has no user-facing entry point. No dedicated feature flag system (LaunchDarkly, Unleash, custom) is in use.

---

## Current Feature Flag State

| Capability | Code status | User-facing | Notes |
|---|---|---|---|
| Online booking | Backend complete | No | `/api/bookings` endpoints exist; frontend buttons are stubs |
| In-app messaging | Backend complete | No | `/api/chat` endpoints exist; `/account/messages` UI status unconfirmed |
| Availability request | Backend complete | No | Chat-based soft booking inquiry |
| Stripe checkout | Backend complete | No | `/api/payments/checkout` exists; must not be linked per DEC-006 |
| Subscription plans | Backend complete | No | Plans table exists; no user-facing plan selection |
| Owner claim & verification | Backend complete | Partial | Dashboard exists but not linked from main nav |
| Portfolio (professionals) | Backend complete | No | Upload endpoints exist; detail page shows "Σύντομα..." |
| Staff profiles | Data in DB | No | `staff` table populated by crawlers; not shown in UI |
| Geo-based search (near me) | Backend complete | No | Haversine in API; no UI trigger |
| Favorites | Not started | No | — |
| Push notifications | Not started | No | — |

---

## Approved Hidden Features (per DEC-006 and Charter §9)

The following must remain hidden until a new Decision is approved:

- All Stripe/payment flows
- Subscription plan display
- Booking confirmation flows

---

*Last updated: 2026-07-09*
