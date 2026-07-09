---
title: MVP Definition
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 00_GOVERNANCE/PROJECT_CHARTER.md
  - 00_GOVERNANCE/DECISION_LOG.md
  - 01_PRODUCT/PRODUCT_SCOPE.md
  - 01_PRODUCT/PERSONAS.md
  - 01_PRODUCT/USER_JOURNEYS.md
  - 01_PRODUCT/MVP_SCOPE_LOCK.md
  - 05_ROADMAP/ROADMAP.md
implementation_status: Partially implemented — proceed against this document
---

# MVP Definition
**Lookla Beauty Marketplace**

> **APPROVED — this is the authoritative MVP reference.**
>
> All decisions in this document are formally logged in `00_GOVERNANCE/DECISION_LOG.md` (DEC-008 to DEC-017).
> Implementation may proceed against this document. Any divergence from this document must be reported as a mismatch — not silently resolved.

---

## Purpose

The MVP is the smallest version of Lookla that can be placed in front of real users to validate the core hypothesis:

> *People in Greece — including non-Greek speakers — can find beauty services more easily through Lookla than through existing alternatives.*

The MVP is not the finished product. It is the minimum required to test whether the problem is real and the solution is useful.

---

## Core MVP Hypothesis

**Problem:** Finding a beauty service in Greece is unnecessarily difficult for a large segment of the population — especially non-Greek speakers — because existing tools (Google Maps, word of mouth) are fragmented, language-dependent, or unstructured.

**Solution hypothesis:** A structured, multilingual beauty directory with accurate working hours, contact information, and category filtering solves this problem well enough that users choose to contact a salon they found through Lookla.

**Validation question:** Do real users find Lookla and use it to contact a salon they would not have found otherwise?

---

## MVP Scope

### ✅ In MVP — Implemented and working

| Capability | Status |
|---|---|
| Search salons by city, category, and text | Implemented |
| Filter by area/district, category, minimum rating | Implemented (label update needed per DEC-010) |
| View salon listing (name, address, hours, photos, contact) | Implemented |
| Open/closed status based on working hours | Implemented |
| Minimum price indicator per category | Implemented |
| Map view | Implemented |
| Multilingual interface (el/en/ru/uk) | Implemented |
| Translated service names and reviews (on-demand) | Implemented |
| Contact buttons (phone, WhatsApp, website) | Implemented |
| User registration and login | Implemented |
| Google OAuth | Implemented |
| Report incorrect information | Implemented |

### ⚠️ In MVP — Requires UI/copy change before MVP can launch

| Capability | Decision | Reference |
|---|---|---|
| City/Area filter label | Replace "City" with area hierarchy: Country → Region → City → District | DEC-010 |
| Review display | Add label: "Source: Google Reviews / Imported: Yes / Original: No" | DEC-013 |
| Verified badge | Replace ✓ with "Information reviewed" or "Owner verified" (context-dependent) | DEC-014 |
| Booking CTA | Remove stub buttons; replace with "Call salon" / "Message on WhatsApp" / "Visit website" | DEC-015 |
| Analytics | GA4 tracking required before launch to measure success criteria | DEC-017 |

### ❌ Explicitly out of MVP scope

| Capability | Reason |
|---|---|
| Stripe / subscription plans | Monetization postponed (DEC-006) |
| Owner claim and verification | Post-MVP stage |
| Online booking flow | Future stage (DEC-015) |
| In-app messaging / chat | Future stage |
| Staff profiles | Backend exists; not surfaced |
| Portfolio for professionals | Backend exists; not surfaced |
| Favorites / saved listings | Registration required; builds on confirmed user base |
| Push notifications | Not started |
| Geo search "near me" UI | Backend Haversine exists; UI not MVP scope (DEC-009 — tourists deprioritized) |
| "Staff speaks Russian" filter | Data not in model; post-MVP |

---

## MVP Success Criteria

**Decision: DEC-008**

Primary metric: **500 verified user interactions with salons within the first 90 days of active availability.**

A verified interaction is any of:
- Click on phone number
- Click on WhatsApp button
- Click on website link

Secondary metrics (tracked but not blocking):
- 100 salons listed and data-quality reviewed in Athens focus area
- 30 salons with claimed profiles
- 10% visitor → contact conversion rate

The 90-day window starts from the first marketing push, not from deployment date.
GA4 must be installed before tracking begins (DEC-017).

---

## MVP Target User

**Decision: DEC-009**

Primary target: **local residents** (not tourists).

Priority order for all product decisions:
1. **P-02** — Russian/Ukrainian-speaking residents (strongest differentiation, underserved)
2. **P-01** — Greek-speaking residents
3. **P-03** — English-speaking expats
4. **P-04** — Salon Owners (post-MVP)

Tourists (P-03) are explicitly deprioritized for MVP. Features that serve only tourists are deferred.

---

## Approved Decisions (Q-01 through Q-10)

### Q-01 — MVP success criteria → DEC-008
**Approved answer:** 500 verified user interactions (phone/WhatsApp/website click) in 90 days.
Secondary: 100 salons listed, 30 claimed, 10% visitor→contact conversion.

### Q-02 — Primary persona → DEC-009
**Approved answer:** Local residents. Priority: P-02 (Russian/Ukrainian) → P-01 (Greek) → P-03 (expat) → tourists last.

### Q-03 — City filter label → DEC-010
**Approved answer:** Implement full location hierarchy: Country → Region → City → District. Users search by Kolonaki/Glyfada/Kallithea/Marousi, not "Athens." Replace "City" with "Area" or "Neighbourhood" in all 4 languages. Data reclassification required.

### Q-04 — Language priority → DEC-011
**Approved answer:** el/en/ru mandatory for MVP quality. uk ships but is lower QA priority than ru.

### Q-05 — Geographic focus → DEC-012
**Approved answer:** Athens metropolitan area first. National data remains accessible but data quality effort focuses on Athens. 100 excellent Athens salons > 5000 thin national listings.

### Q-06 — Review source labeling → DEC-013
**Approved answer:** Keep Google reviews, label clearly: "Source: Google Reviews / Imported: Yes / Original: No."

### Q-07 — Verified badge → DEC-014
**Approved answer:** Replace ✓ with explicit label. "Information reviewed" when admin-checked. "Owner verified" only after full Claim + Verification process. No badge = default for unclaimed listings.

### Q-08 — Booking CTA → DEC-015
**Approved answer:** Remove all booking stubs. Replace with real contact CTAs: "Call salon," "Message on WhatsApp," "Visit website." "Request appointment" only when a real flow exists.

### Q-09 — Registration requirement → DEC-016
**Approved answer:** View, call, WhatsApp = no registration required. Save/favorites = registration required. Current anonymous implementation is correct and confirmed.

### Q-10 — Analytics → DEC-017
**Approved answer:** GA4 (required before launch) + Google Search Console (required before launch) + Microsoft Clarity or Hotjar (optional, add post-launch).

---

## MVP Readiness Checklist

### Product decisions (complete)
- [x] Q-01 answered: success metric defined (DEC-008)
- [x] Q-02 answered: primary persona identified (DEC-009)
- [x] Q-03 answered: city/area hierarchy decided (DEC-010)
- [x] Q-04 answered: language priority set (DEC-011)
- [x] Q-05 answered: geographic focus set (DEC-012)
- [x] Q-06 answered: review labeling decided (DEC-013)
- [x] Q-07 answered: verified badge decided (DEC-014)
- [x] Q-08 answered: booking CTA decided (DEC-015)
- [x] Q-09 answered: registration requirement confirmed (DEC-016)
- [x] Q-10 answered: analytics approved (DEC-017)
- [x] MVP_DEFINITION.md status changed to `Approved`
- [x] Decisions logged in DECISION_LOG.md (DEC-008 to DEC-017)
- [x] Roadmap milestone M-01 created

### Implementation pre-conditions (required before MVP launch)
- [ ] Area filter: location hierarchy implemented (DEC-010)
- [ ] Review labels: "Source: Google Reviews" added to salon detail page (DEC-013)
- [ ] Verified badge: replaced with explicit label (DEC-014)
- [ ] Booking stubs: removed, replaced with contact CTAs (DEC-015)
- [ ] GA4: installed, contact events tracked (DEC-017)
- [ ] Search Console: property verified (DEC-017)
- [ ] Privacy policy: updated to reflect GA4 (DEC-017)
- [ ] Athens data quality: 100 salons reviewed for accuracy (DEC-012)
- [ ] Russian translation quality: sample reviewed (DEC-011)

---

*Last updated: 2026-07-09*
