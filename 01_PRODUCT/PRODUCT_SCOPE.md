---
title: Product Scope
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 00_GOVERNANCE/PROJECT_CHARTER.md
  - 01_PRODUCT/PRODUCT_VISION.md
  - 01_PRODUCT/PRODUCT_TERMINOLOGY.md
implementation_status: N/A — product document
---


# 01 — Product Scope
**Lookla Beauty Marketplace**

Status: APPROVED  
Authority: Product Owner  
Last updated: 2026-07-09

> This document defines what Lookla is and what it is not.  
> All future product decisions, design work, and development must remain inside the boundaries defined here.  
> Changes to scope require a Change Request approved by the Product Owner.

---

## 1. Product Definition

Lookla is a **Beauty Discovery Platform** for Greece.

Its current purpose is to help clients find salons, beauty studios, barbershops, spas, and independent professionals — across all regions and in multiple languages.

**Evolution path:**

| Stage | Focus | Status |
|---|---|---|
| Stage 1 | Discovery — find the right place | Current |
| Stage 2 | Verification — trust that information is accurate | Planned |
| Stage 3 | Contact — reach out directly | Planned |
| Stage 4 | Booking — reserve a time slot | Future |
| Stage 5 | Loyalty and retention | Future |

The platform evolves incrementally. Each stage adds capability without breaking the previous stage.

**Discovery is the core product.** Booking capability, when introduced, extends discovery — it does not replace it.

---

## 2. Project Boundaries

### Lookla IS:

- A beauty services directory for Greece
- A discovery interface for clients looking for beauty services
- A multilingual platform (Greek, English, Russian, Ukrainian)
- A data aggregation platform with gradual owner verification
- A future booking channel between clients and beauty businesses
- A listing and visibility platform for beauty businesses

### Lookla IS NOT:

| Category | Examples | Reason excluded |
|---|---|---|
| ERP / Accounting | Invoicing, VAT reporting, payroll | Out of product scope |
| Point of Sale | Cash register, payment terminal integration | Out of product scope |
| Marketplace | Physical goods, products for purchase | Out of product scope |
| Delivery | Courier, logistics | Out of product scope |
| Inventory management | Stock tracking, product supply | Out of product scope |
| CRM replacement | Full client relationship management for salons | Partial overlap — contact is in scope, full CRM is not |
| Social Network | Public posts, follows, feeds, social graph | Out of product scope |
| General Messenger | Arbitrary conversations | In-context availability messaging only |
| Review platform | General purpose rating platform | Reviews exist as discovery signal, not as primary product |
| Aggregator with commission | Transaction fee per booking | Not current stage; future decision required |
| Advertising network | Display ads, promoted content | Intentionally excluded at current stage |

---

## 3. Primary Business Entities

These are the canonical entities of the Lookla platform. All terminology in this list is defined in `03_PRODUCT_TERMINOLOGY.md`.

### People

| Entity | Description | Status |
|---|---|---|
| **Visitor** | Anonymous user browsing without an account | Current |
| **Registered User** | Person with a Lookla account | Current |
| **Salon Owner** | Verified owner or manager of a Beauty Business | Planned |
| **Independent Professional** | Beauty specialist not affiliated with a salon | Current |
| **Administrator** | Lookla platform staff with moderation access | Current |

### Business entities

| Entity | Description | Status |
|---|---|---|
| **Beauty Business** | Any commercial entity offering beauty services (parent concept) | Current |
| **Salon** | Fixed-location beauty business (hair, nails, skin, etc.) | Current |
| **Barbershop** | Fixed-location business focused on men's grooming | Current |
| **Spa** | Fixed-location wellness and relaxation business | Current |
| **Beauty Studio** | Smaller or specialized fixed-location beauty business | Current |

### Catalog entities

| Entity | Description | Status |
|---|---|---|
| **Service** | A specific treatment or procedure offered by a Beauty Business | Current |
| **Category** | A classification grouping similar services | Current |
| **City / Region** | A geographic area used for search and filtering | Current |
| **Listing** | A published profile of a Beauty Business on Lookla | Current |

### Transactional entities (future)

| Entity | Description | Status |
|---|---|---|
| **Appointment** | A confirmed time slot between a client and a Beauty Business | Future |
| **Booking** | The act of reserving an Appointment | Future |
| **Review** | A client's rating and comment after a visit | Future (owned reviews) |

> Note: Reviews currently shown on the platform are sourced from public aggregated data, not from direct Lookla client interactions. Owned Lookla reviews are a future capability.

---

## 4. Current Platform Capabilities

These capabilities are implemented and available to users today.

### For Visitors and Registered Users

- Search salons and beauty professionals by name, city, or service type
- Filter search results by city, category, and minimum rating
- View salon listings with name, address, photos, working hours, contact information
- View current open/closed status based on working hours
- View minimum service price per category
- View service list with pricing
- Read aggregated reviews
- View salon on map
- Switch between list and map view
- Browse by category (hair, nails, barbershop, spa, etc.)
- Browse by city or region
- Use the platform in Greek, English, Russian, or Ukrainian
- Access translated service names and reviews (translation generated on first real-user view)
- Contact a salon directly (phone, WhatsApp, website)
- Report incorrect information
- Register an account
- Log in via email/password or Google account

### For Registered Users

- Manage account profile and language preference
- Reset password via email

### For Administrators

- View platform statistics
- Review and moderate salon listings
- Manage content moderation queue

---

## 5. Future Platform Capabilities

Planned and future capabilities are documented for architectural awareness only.  
No timeline is implied. No implementation is assumed.

| Capability | Status | Notes |
|---|---|---|
| Salon owner claim and verification | Planned | Backend infrastructure exists; not user-facing |
| Owner dashboard (edit listing, manage hours, services, photos) | Planned | Backend infrastructure exists; not user-facing |
| Online booking (reserve a time slot) | Future | Backend infrastructure exists; not user-facing |
| In-app availability request messaging | Future | Backend infrastructure exists; not user-facing |
| Client booking history | Future | — |
| Booking reminders and notifications | Future | — |
| Owned Lookla reviews (post-visit) | Future | — |
| Subscription plans for owners | Future | No monetization at current stage |
| Promoted listings (visibility features) | Future | No advertising at current stage |
| Independent professional booking | Future | Discovery exists; booking future |
| Portfolio for professionals | Planned | Backend infrastructure exists; not user-facing |
| Staff profiles | Future | Data exists; not shown to users |
| Geo-based search (near me) | Planned | Backend supports Haversine; no UI trigger |
| Favorite / saved listings | Future | — |
| Push notifications | Future | — |
| Mobile native application (iOS/Android) | Future | — |
| Partner application for salon owners | Future | — |

---

## 6. Out of Scope

The following are intentionally excluded from Lookla's scope at all stages, unless a future Change Request explicitly reconsiders them.

- Financial management for salons (invoicing, VAT, accounting)
- Point of sale or payment terminal integration
- Physical product sales or delivery
- Inventory or supply chain tracking
- Payroll or HR management for salons
- General social networking (public posts, follower graphs, content feeds)
- General-purpose messaging unrelated to a specific salon or professional
- Third-party advertising networks
- Affiliate programs
- Beauty product e-commerce

---

*Last updated: 2026-07-09*  
*Authority: Product Owner*
