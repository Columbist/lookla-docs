---
title: Future Features
status: Draft
version: 0.1
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 05_ROADMAP/ROADMAP.md
  - 01_PRODUCT/PRODUCT_SCOPE.md
  - 04_ARCHITECTURE/FEATURE_FLAGS.md
implementation_status: N/A — planning document
---

# Future Features
**Lookla Beauty Marketplace**

> This document is a holding area for ideas that have not yet been approved.  
> Nothing here is a commitment. Nothing here may be implemented without an approved RFC and Decision Log entry.  
> When an item is approved, it moves to `ROADMAP.md` as a milestone.

---

## Purpose

Future Features is the product backlog of unapproved ideas. It keeps ideas visible without polluting the Roadmap with uncommitted work.

---

## Candidate Features

The following are documented from the Engineering Audit and prior product conversations. They are candidates only — not approved.

| Feature | Value hypothesis | Dependency | Notes |
|---|---|---|---|
| Salon owner claim & verification (user-facing) | Owners improve data quality; trust increases | Verification flow design | Backend complete |
| Online booking | Direct conversion from discovery to action | Booking UX design, notification system | Backend complete |
| In-app availability request | Soft booking for salons without calendars | Chat UI design | Backend complete |
| Client booking history | User retention, repeat visits | Booking implemented first | Not started |
| Favorites / saved listings | User retention, return visits | Account system | Not started |
| Owned reviews (post-visit) | Trusted first-party ratings | Booking or check-in verification | Not started |
| Geo-based "near me" search | Reduce friction for location-aware search | UI trigger, GPS permission flow | Backend complete |
| Push notifications | Booking reminders, availability updates | Mobile app or PWA | Not started |
| Subscription plans (Premium) | Monetization | Monetization decision approved | DEC-006: postponed |
| Featured listings | Monetization + visibility for owners | Monetization decision approved | DEC-006: postponed |
| Staff profiles | Discovery depth for salons with multiple stylists | Page design | Data exists in DB |
| Portfolio for professionals | Visual discovery for independent professionals | Portfolio page design | Backend complete |
| City/Region filter rename | Fix misleading "City" filter label | Product decision on terminology | Documented in Terminology |
| Mobile native app (iOS) | Native experience, push notifications | Full booking flow, design system | Future |
| Mobile native app (Android) | Same as iOS | Same as iOS | Future |
| Partner app (salon owner) | Mobile owner dashboard | Owner dashboard fully implemented | Future |
| Analytics / Funnel tracking | Measure what users actually do | Decision on analytics provider | Not started |
| Review source labeling | Show users that reviews are from Google | Design decision | Known mismatch flagged in Terminology |

---

*Last updated: 2026-07-09*
