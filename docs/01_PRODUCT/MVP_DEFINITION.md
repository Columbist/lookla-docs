---
title: MVP Definition
status: Draft
version: 0.1
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 00_GOVERNANCE/PROJECT_CHARTER.md
  - 01_PRODUCT/PRODUCT_SCOPE.md
  - 01_PRODUCT/PERSONAS.md
  - 01_PRODUCT/USER_JOURNEYS.md
  - 05_ROADMAP/ROADMAP.md
implementation_status: Partially implemented — MVP scope not yet formally approved
---

# MVP Definition
**Lookla Beauty Marketplace**

> **DRAFT — not approved. Do not use as implementation reference until status is `Approved`.**
>
> This document defines what constitutes the Minimum Viable Product for Lookla.
> Sections marked **❓ DECISION REQUIRED** cannot be finalized without Product Owner input.

---

## Purpose

The MVP is the smallest version of Lookla that can be placed in front of real users to validate the core hypothesis:

> *People in Greece — including non-Greek speakers — can find beauty services more easily through Lookla than through existing alternatives.*

The MVP is not the finished product. It is the minimum required to test whether the problem is real and the solution is useful.

---

## Core MVP Hypothesis

**Problem:** Finding a beauty service in Greece is unnecessarily difficult for a large segment of the population — especially non-Greek speakers — because existing tools (Google Maps, word of mouth) are fragmented, language-dependent, or unstructured.

**Solution hypothesis:** A structured, multilingual beauty directory with accurate working hours, contact information, and category filtering solves this problem well enough that users choose to return.

**Validation question:** Do real users find Lookla and use it to contact a salon they would not have found otherwise?

---

## MVP Scope

### ✅ In MVP — Implemented and working

The following capabilities are already built and functional:

| Capability | Status |
|---|---|
| Search salons by city, category, and text | Implemented |
| Filter by city, category, minimum rating | Implemented |
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

### ✅ In MVP — Needs decision before it can be called complete

The following exist in code but have known issues that require a product decision before MVP can be considered done:

| Capability | Issue | Decision needed |
|---|---|---|
| City/Region filter | Label says "City" but returns districts — misleading for Attica | ❓ See Q-03 below |
| Review display | Shows Google reviews without labeling the source | ❓ See Q-06 below |
| Verified badge (✓) | Reflects admin flag, not owner verification — misleading | ❓ See Q-07 below |
| Booking CTA buttons | Present in UI but non-functional (stubs) | ❓ See Q-08 below |

### ❌ Explicitly out of MVP scope

The following are built in code but must NOT be user-facing for MVP:

| Capability | Reason |
|---|---|
| Stripe / subscription plans | Monetization postponed (DEC-006) |
| Owner claim and verification | Planned stage, not MVP |
| Online booking flow | Future stage |
| In-app messaging / chat | Future stage |
| Staff profiles | Data exists; not surfaced |
| Portfolio for professionals | Backend ready; not surfaced |
| Favorites / saved listings | Not started |
| Push notifications | Not started |

---

## MVP Success Criteria

❓ **DECISION REQUIRED (Q-01)**

> What does MVP success look like? Without agreed criteria, there is no way to know when MVP is validated or when to move to the next stage.

Proposed options for Product Owner to choose from or replace:

**Option A — Traffic signal**
> _N_ unique visitors per week arrive via organic search (not direct URL), spend more than _N_ seconds on a salon page.

**Option B — Contact signal**
> _N_ click-throughs on phone/WhatsApp/website buttons per week.

**Option C — Return signal**
> _N_% of visitors return within 30 days without a direct link.

**Option D — Qualitative signal**
> At least _N_ real users can be interviewed and confirm Lookla solved a real discovery problem.

_Product Owner decision required: which metric, and what threshold constitutes success?_

---

## MVP Target User

❓ **DECISION REQUIRED (Q-02)**

> Which persona is the primary target for MVP validation? The answer determines where to focus limited attention on search quality, UX, and language priority.

Current candidates (see `PERSONAS.md`):

- **P-01** — Greek-speaking local (largest addressable group, highest competition from Google Maps)
- **P-02** — Russian/Ukrainian-speaking resident (underserved, strong differentiated value, multilingual is key)
- **P-03** — English-speaking expat / tourist (seasonal, high intent, mobile-first)

_If MVP targets P-02 first, multilingual quality and transliteration accuracy become the top priority. If P-01, then completeness of Athens coverage and search ranking matter most._

---

## Open Questions Blocking MVP Approval

Each question below must be answered by the Product Owner before this document can move to `Approved`.

---

### ❓ Q-01 — MVP success criteria
What metric proves MVP is validated? What is the threshold?

---

### ❓ Q-02 — Primary MVP persona
Which user type is the primary validation target: Greek local, Russian/Ukrainian resident, or English expat/tourist?

---

### ❓ Q-03 — City filter label
The current filter is labeled "City" but returns districts (Kallithea, Glyfada appear separate from Athens). Options:
- **A)** Rename to "Area" or "Neighbourhood" (requires copy change only)
- **B)** Group districts under parent cities (requires data restructuring + UI)
- **C)** Leave as-is for MVP, decide post-MVP

_This affects SEARCH.md spec and the filter label in all 4 languages._

---

### ❓ Q-04 — Language priority for MVP
All 4 languages (el/en/ru/uk) are implemented. For MVP:
- **A)** All 4 are equal — no priority
- **B)** Greek + Russian/Ukrainian are primary (target non-Greek speakers first)
- **C)** Greek + English are primary (tourist/expat focus)

_This affects copy quality, QA priorities, and marketing channels._

---

### ❓ Q-05 — Geographic focus for MVP
Is MVP national (all of Greece, 6320 salons) or focused on a specific region?
- **A)** National from day one (already the case technically)
- **B)** Athens metro area only for MVP validation (higher density, easier to test)
- **C)** Athens + Thessaloniki

_This affects SEO strategy, data quality focus, and marketing channel choices._

---

### ❓ Q-06 — Review source labeling
Current state: Google reviews are shown without any label indicating they're from Google.
Options:
- **A)** Add "Source: Google" label to each review — honest, slightly reduces visual cleanliness
- **B)** Add a section header "Reviews from Google" — cleaner
- **C)** Hide reviews entirely for MVP — simplifies trust question
- **D)** Keep as-is for MVP — decide after seeing user reaction

_Affects SALON.md page spec and the Terminology mismatch flagged in PRODUCT_TERMINOLOGY.md._

---

### ❓ Q-07 — Verified badge (✓) meaning
The ✓ badge currently means "an admin has reviewed this listing," not "the owner has verified this business."
Options:
- **A)** Remove badge entirely for MVP — show it only when owner verification exists
- **B)** Change badge label to "Reviewed" instead of implying owner verification
- **C)** Keep as-is for MVP — document known mismatch

_This is a trust signal. Getting it wrong can undermine credibility._

---

### ❓ Q-08 — Booking CTA in MVP
Currently there are booking/contact buttons on the salon detail page that are non-functional stubs.
Options:
- **A)** Remove booking buttons entirely for MVP — only show real contact options (phone, WhatsApp, website)
- **B)** Keep stubs but label them "Coming soon"
- **C)** Keep as-is

_Per Charter §9: stubs are only acceptable if clearly non-functional._

---

### ❓ Q-09 — User registration requirement
Is registration required to contact a salon, or is discovery fully anonymous?
- **A)** Fully anonymous — no login required for any discovery or contact action (current state)
- **B)** Login required to reveal phone number (increases registration, reduces friction for discovery)
- **C)** Login required to see WhatsApp link only

_Affects conversion funnel and how user base is measured._

---

### ❓ Q-10 — Analytics for MVP
Without analytics, there is no way to measure MVP success criteria.
- **A)** Add Google Analytics 4 or Plausible before MVP launch
- **B)** Use server-side request logs only (privacy-friendly, less granular)
- **C)** No analytics for now — validate qualitatively

_Without Q-10 answered, Q-01 (success criteria) cannot be measured._

---

## MVP Readiness Checklist

To be completed once open questions are answered:

- [ ] Q-01 answered: success metric defined
- [ ] Q-02 answered: primary persona identified
- [ ] Q-03 answered: city filter decision made
- [ ] Q-04 answered: language priority set
- [ ] Q-05 answered: geographic focus set
- [ ] Q-06 answered: review labeling decision made
- [ ] Q-07 answered: verified badge decision made
- [ ] Q-08 answered: booking CTA decision made
- [ ] Q-09 answered: registration requirement set
- [ ] Q-10 answered: analytics approach decided
- [ ] MVP_DEFINITION.md status changed to `Approved`
- [ ] Relevant decisions logged in DECISION_LOG.md (DEC-008+)
- [ ] Roadmap milestone M-01 created

---

*Last updated: 2026-07-09*
