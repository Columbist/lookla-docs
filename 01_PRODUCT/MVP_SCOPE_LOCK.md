---
title: MVP Scope Lock
status: Locked
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 01_PRODUCT/MVP_DEFINITION.md
  - 00_GOVERNANCE/DECISION_LOG.md
  - 05_ROADMAP/ROADMAP.md
implementation_status: N/A — governance boundary document
---

# MVP Scope Lock
**Lookla Beauty Marketplace**

> **LOCKED — do not add or remove items without a formal Change Request (see `00_GOVERNANCE/CHANGE_REQUEST_TEMPLATE.md`).**
>
> This document is the concrete boundary of what MVP includes. It exists to prevent scope creep and to give engineering a clear, unambiguous reference.
>
> If something is not on the WILL HAVE list, it is not in MVP — regardless of how easy it would be to add.

---

## How to use this document

- Before starting any implementation task, confirm the feature is on the **WILL HAVE** list.
- If a requested feature is not on the list, do not implement it — escalate to Product Owner.
- If a feature naturally suggests another feature, document the suggestion but do not implement it.
- Any change to this document requires a filed Change Request and a new Decision Log entry.

---

## MVP WILL HAVE

These capabilities must be present and working at MVP launch.

### Discovery and Search
- [ ] Search salons by text query (Greek, English, Russian, Ukrainian)
- [ ] Filter by area/district within city (location hierarchy: Country → Region → City → District)
- [ ] Filter by category (nail salon, hairdresser, barbershop, spa, etc.)
- [ ] Filter by minimum rating
- [ ] Open/closed status visible on salon cards and detail page
- [ ] Price indicator per category (from/minimum)
- [ ] Map view of search results

### Salon Listing Page
- [ ] Salon name, address, phone, website, WhatsApp
- [ ] Photos gallery
- [ ] Working hours (structured, current open/closed state)
- [ ] Services with prices (lazy-loaded)
- [ ] Reviews with **explicit Google source label**: "Source: Google Reviews / Imported: Yes / Original: No"
- [ ] Verified label: **"Information reviewed"** (if admin-checked) or **"Owner verified"** (if Claim complete) or no badge
- [ ] Contact CTAs: "Call salon" / "Message on WhatsApp" / "Visit website" — **no fake booking buttons**
- [ ] Report incorrect information form

### Multilingual Interface
- [ ] Greek (el) — fully functional, no placeholders
- [ ] English (en) — fully functional, no placeholders
- [ ] Russian (ru) — fully functional, QA reviewed
- [ ] Ukrainian (uk) — functional, ships as-is
- [ ] On-demand service name translation (el → en/ru/uk) on first real-user view
- [ ] On-demand review translation on first real-user view

### User Accounts
- [ ] Registration (email + password)
- [ ] Login (email + Google OAuth)
- [ ] Anonymous access to all discovery and contact features (no login gate)

### Analytics (required before launch)
- [ ] Google Analytics 4 installed
- [ ] Contact click events tracked in GA4 (phone, WhatsApp, website)
- [ ] Google Search Console verified
- [ ] Privacy policy updated to reflect GA4

### Data Quality (Athens focus)
- [ ] 100+ Athens salons reviewed for data accuracy (hours, phone, photos)
- [ ] Location hierarchy mapped for Athens metro area districts

---

## MVP WILL NOT HAVE

These are explicitly excluded. Do not implement, hint at, or stub any of the following.

### Features excluded (with reason)
| Feature | Why excluded | When it might come |
|---|---|---|
| Online booking / appointment scheduling | No availability engine, no backend; fake CTA destroys trust (DEC-015) | Post-MVP stage |
| Stripe / subscription plans | Monetization postponed (DEC-001, DEC-006) | Never without a formal decision |
| Owner claim and verification UI | Backend exists; user-facing flow not validated yet | M-02 or later |
| Favorites / saved listings | Registration-gated feature; build after base user volume confirmed | Post-MVP |
| In-app chat / messaging | No infrastructure; not in scope | Post-MVP |
| Staff profiles | Backend ready; not surfaced until owner adoption confirmed | Post-MVP |
| Portfolio for independent professionals | Backend ready; same reason | Post-MVP |
| Push notifications | Not started | Post-MVP |
| "Near me" / GPS-based search | Tourists deprioritized (DEC-009); backend Haversine exists | M-02 or later |
| "Staff speaks Russian" filter | Not in data model | Post-MVP when claim flow exists |
| AI search ranking | Postponed (DEC-005) | Requires measurable user base first |
| AI-generated content | Prohibited (DEC-005, AI_STRATEGY.md) | Not without approval |
| Promotional pages (/pricing, /plans) | Must not be user-facing (DEC-006) | Never without monetization decision |
| National marketing / SEO | Athens focus only for MVP (DEC-012) | Post-MVP |
| Thessaloniki focus | Post-Athens | M-02 or later |

---

## Pre-MVP Launch Gate

MVP cannot launch until **all items below are confirmed**:

- [ ] All WILL HAVE items marked complete
- [ ] GA4 tracking confirmed working in production
- [ ] No booking stubs visible anywhere
- [ ] Review source labels visible on salon detail page
- [ ] Verified badge replaced with correct text label
- [ ] Location hierarchy functional for Athens districts
- [ ] /pricing and /plans pages: confirmed not linked in navigation (DEC-006 compliance)
- [ ] Privacy policy updated
- [ ] At least one complete test run of J-01 (P-01 journey) and J-02 (P-02 journey) in production

---

## Change Procedure

To add something to WILL HAVE or move something from WILL NOT HAVE:

1. File a Change Request using `00_GOVERNANCE/CHANGE_REQUEST_TEMPLATE.md`
2. Get Product Owner approval
3. Log new decision in `00_GOVERNANCE/DECISION_LOG.md`
4. Update this document
5. Update `01_PRODUCT/MVP_DEFINITION.md` if scope changes

**No exceptions. Scope creep kills MVPs.**

---

*Last updated: 2026-07-09*
