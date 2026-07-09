---
title: Product Vision
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 00_GOVERNANCE/PROJECT_CHARTER.md
  - 01_PRODUCT/PRODUCT_SCOPE.md
  - 01_PRODUCT/PRODUCT_TERMINOLOGY.md
implementation_status: N/A — product document
---


# 02 — Product Vision
**Lookla Beauty Marketplace**

Status: APPROVED  
Authority: Product Owner  
Last updated: 2026-07-09

> This document describes why Lookla exists.  
> It does not describe implementation, UI, or architecture.  
> Changes to vision require Product Owner approval and a log entry in `02_DECISION_LOG.md`.

---

## 1. Mission

Help people in Greece find the right beauty professional — quickly, in their language, with accurate information.

---

## 2. Vision

A single trusted source for beauty services in Greece.

A platform where every salon, studio, and independent professional has a complete, up-to-date, and verified presence — and where any client can find the right match without knowing Greek, without navigating multiple platforms, and without relying on paid recommendations.

---

## 3. Core Values

**Accuracy over completeness**  
A listing with correct information is more valuable than a listing with invented information. Where data is uncertain, it is shown as-is or not at all.

**Real over popular**  
Lookla does not simulate engagement. Ratings, review counts, and availability signals reflect real data from real sources. Nothing is inflated.

**Discovery before conversion**  
The first obligation is to help the client find the right place. Commercial relationships (booking, subscriptions, advertising) are secondary to that goal.

**Accessible to all residents**  
Greece has a large non-Greek-speaking resident population. The platform serves clients in Greek, English, Russian, and Ukrainian without treating any language as secondary.

**Owner participation is earned**  
Business information is initially sourced from public data. Owners can claim and improve their listing, but must verify their identity. Unverified changes are not published automatically.

---

## 4. Long-term Direction

Lookla is being built in stages. Each stage extends the previous one without breaking it.

**Near term:** Become the most complete and accurate beauty directory in Greece, with multilingual support and real working-hours data.

**Medium term:** Enable verified salon owners to manage their listings directly, improving data quality and creating a self-sustaining content loop.

**Long term:** Introduce booking as a natural extension of discovery — when the client has found the right place and wants to act immediately.

At no stage does Lookla prioritize commercial revenue over product quality. Monetization follows validation, not the other way around.

---

## 5. Target Market

### Primary audience: Clients

People living in or visiting Greece who need a beauty service and don't know where to go.

This includes:
- Greek-speaking residents who want a more structured alternative to Google Maps
- Russian and Ukrainian-speaking residents who struggle to discover services without knowing Greek
- English-speaking expats and tourists
- People relocating to a new city or neighborhood

The unifying characteristic is a **specific intent** (I need a haircut, I need a nail salon nearby) combined with **uncertainty** (I don't know which one to choose or how to contact them).

### Secondary audience: Beauty businesses

Salons, studios, barbershops, spas, and independent professionals who want to be found by more clients — without paying for advertising.

At the current stage, their participation is passive (data is aggregated from public sources). In future stages, they become active participants who manage their own listings.

---

## 6. Problems Lookla Solves

### For clients

| Problem | How Lookla addresses it |
|---|---|
| "I don't know which salon is near me" | Map view and city/region filter |
| "I don't know if it's open right now" | Real-time open/closed status based on working hours |
| "I don't speak Greek so I can't read the website" | Full multilingual interface and translated content |
| "I don't know if the price is in my range" | Minimum price displayed per category |
| "I can't find the phone number" | Direct contact buttons (phone, WhatsApp, website) |
| "I don't know if it's any good" | Aggregated ratings and reviews |
| "Search results show irrelevant businesses" | Beauty-specific, category-structured directory |

### For beauty businesses (future)

| Problem | How Lookla addresses it |
|---|---|
| "My information on the internet is outdated" | Owner can claim and update listing (planned) |
| "I'm invisible to non-Greek speakers" | Multilingual presence without any effort from the owner |
| "I have no online booking" | Booking capability (future stage) |

---

## 7. How Lookla Differs from Alternatives

### vs. Google Maps

| Dimension | Google Maps | Lookla |
|---|---|---|
| Scope | General — all business types | Specific — beauty services only |
| Data structure | Name, address, hours, reviews | Categories, services, pricing, staff |
| Language | Interface language only | Full content translation |
| Open/closed | Present | Present with Athens-timezone accuracy |
| Booking | Via third-party links | Native (future) |
| Discovery logic | Generic search | Beauty-category-aware search |
| Data quality control | Community-driven | Curated + owner verification (planned) |

Google Maps is not a competitor — it is a data source and a user starting point. The goal is not to replace Google Maps but to offer a deeper experience after the client knows they want a beauty service.

### vs. Fresha

| Dimension | Fresha | Lookla |
|---|---|---|
| Primary user | Salon owner (business software) | Client (discovery) |
| Model | SaaS for salons with client marketplace as byproduct | Client-first discovery platform |
| Coverage in Greece | Partial — only salons that pay and register | Comprehensive — all salons via public data |
| Barrier for salons | Must register and manage software | No barrier — listed by default |
| Languages | Limited localization | Greek, English, Russian, Ukrainian |
| Focus | Online booking management | Discovery and contact |

Fresha requires salon owners to adopt and pay for software. Lookla does not require owner participation for a salon to appear.

### vs. Booksy

| Dimension | Booksy | Lookla |
|---|---|---|
| Primary user | Salon owner (booking management) | Client (discovery) |
| Coverage model | Only salons registered on the platform | All salons from aggregated public data |
| Greece presence | Limited | National, all regions |
| Discovery layer | Thin — listing is secondary to booking | Core product |
| Languages | Limited | Greek, English, Russian, Ukrainian |

Booksy is a booking management tool with a client-facing marketplace layer. Its Greece coverage is limited by the requirement for owners to register. Lookla's coverage is not constrained by owner participation.

### vs. Treatwell

| Dimension | Treatwell | Lookla |
|---|---|---|
| Model | Commission-based booking marketplace | Discovery-first, no commission at current stage |
| Coverage | Registered salons only | All salons from aggregated public data |
| Salon barrier | Commission per booking | No barrier — listed by default |
| Revenue model | Transaction fee | Intentionally postponed |
| Languages | Limited localization | Greek, English, Russian, Ukrainian |
| Focus | Booking and commission | Discovery and accuracy |

Treatwell takes a commission on bookings. This creates a structural incentive to prioritize salons that generate revenue over salons that would be the best match for the client. Lookla's current model — no commission, no advertising — avoids this bias.

---

## 8. What Lookla Is Not Trying to Be

- The biggest platform in terms of salon count at any cost
- A tool that replaces salon management software
- A social platform for beauty content
- An advertising network
- A platform that earns money before it earns trust

---

*Last updated: 2026-07-09*  
*Authority: Product Owner*
