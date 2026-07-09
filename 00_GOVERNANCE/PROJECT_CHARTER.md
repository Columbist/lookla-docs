---
title: Project Charter
status: Locked
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 00_GOVERNANCE/DECISION_LOG.md
  - 00_GOVERNANCE/CHANGE_REQUEST_TEMPLATE.md
implementation_status: N/A — governance document
---

# Project Charter
**Lookla Beauty Marketplace**

> **Highest priority document in the repository.**  
> All other documents must conform to this Charter.  
> If any document conflicts with the Charter: **do not resolve — report the conflict.**

---

## 1. Project Purpose

Lookla is a beauty services marketplace for Greece. It connects clients with salons and independent beauty professionals across all Greek regions.

The platform aggregates publicly available salon data, provides multilingual discovery (el/en/ru/uk), and is designed to grow into a verified, bookable directory with owner participation.

---

## 2. Current Project Stage

- Private development project
- No registered company
- No commercial activity
- No monetization
- No subscriptions
- No advertising
- No paid promotion
- **Primary goal:** validate the product with real users

The project is in the evidence-gathering phase. Every product decision must serve validation, not revenue.

---

## 3. Product Philosophy

- **MVP first** — ship the smallest thing that tests the assumption
- **Documentation first** — no implementation starts before documentation
- **Cost first** — every feature must justify its cost before it is built
- **Future-ready architecture** — decisions must not close off future options
- **Modular architecture** — components are independent and replaceable
- **No fake activity** — no fake statistics, reviews, discounts, bookings, or popularity signals of any kind

---

## 4. Development Principles

Every feature must be evaluated before implementation across four dimensions:

1. **User value** — what problem does it solve for a real user?
2. **Implementation cost** — how long and how much?
3. **Maintenance cost** — what does it cost to keep running?
4. **Long-term impact** — does it simplify or complicate future work?

Default to simple solutions. Avoid unnecessary complexity. Do not build for hypothetical users.

---

## 5. Documentation Policy

- No implementation starts before documentation is approved
- Documentation is the source of truth
- Engineering follows approved product documentation, not the reverse
- If implementation diverges from documentation: **report the mismatch, do not silently update either side**
- Engineering documents (AUDIT, TROUBLESHOOTING) describe what is built
- Product documents (this directory) describe what is approved

**Document hierarchy (highest to lowest):**
1. `00_GOVERNANCE/PROJECT_CHARTER.md` — this file
2. Approved product documents (`01_PRODUCT/`, `02_DESIGN/`, `03_PAGES/`)
3. Approved RFC (`07_RFC/`)
4. Engineering documentation (`06_ENGINEERING/`)
5. Implementation

---

## 6. Architecture Policy

- Architecture must remain modular — no monolithic coupling between features
- Each feature must be independently deployable and removable
- Use feature flags conceptually — do not expose unfinished features to users
- The API must remain versioning-ready (even if not yet versioned)
- Every component must be reusable across web, iOS, Android, and partner applications
- No architecture decisions are made without a documented rationale in `DECISION_LOG.md`

---

## 7. Cost Strategy

Every new feature requires a cost evaluation before implementation approval.

Mandatory evaluation fields:

| Field | Description |
|---|---|
| User value | What user problem is solved and how measurably |
| Implementation complexity | Effort estimate (hours/days) |
| Maintenance cost | Ongoing operational burden |
| Infrastructure cost | Additional hosting, API, or storage spend |
| Future scalability | Does this decision constrain future options? |

**No feature is approved without this evaluation being documented.**

---

## 8. Data Strategy

- Current data comes from public aggregated sources (crawlers)
- Data must support periodic refresh without breaking existing records
- Future owner verification is planned — owners can claim and update their listings
- **Current crawled data must never be treated as permanently verified or authoritative**
- No fabricated data of any kind is acceptable (ratings, prices, hours, photos)

---

## 9. Feature Strategy

- The platform must support future functionality without exposing unfinished functionality to users
- Use feature flags conceptually: infrastructure can exist in code without being user-visible
- Do not expose unfinished features to users — stubs are acceptable only if they are clearly non-functional (e.g., "coming soon")
- Features are delivered complete or not at all

---

## 10. Mobile Strategy

Every UI component must be designed with future reuse in mind for:

- Web (current)
- iOS native application
- Android native application
- Partner application (salon-owner-facing)

No frontend decision should create a web-only dependency that would require a full rewrite for mobile.

---

## 11. AI Strategy

- Architecture must remain AI-ready
- AI features are intentionally postponed until they provide **measurable user value**
- AI is not a feature — it is a tool to solve a specific user problem
- Any AI integration must pass the same cost/value evaluation as any other feature
- Current AI usage (on-demand translation via GPT-4o-mini) is infrastructure, not a product feature

---

## 12. Monetization Strategy

- Monetization is intentionally postponed
- No pricing, subscriptions, or advertising until product validation is complete
- Architecture must allow future monetization (subscriptions, promoted listings, booking fees) without major redesign
- The Stripe infrastructure already in place must not be exposed to users until a monetization decision is approved

---

## 13. Decision Process

1. A need or opportunity is identified
2. A Change Request is written using `CHANGE_REQUEST_TEMPLATE.md`
3. The Change Request is reviewed against this Charter
4. If approved, it is logged in `DECISION_LOG.md`
5. Implementation begins only after the log entry is confirmed
6. Upon completion, the relevant documentation is updated to reflect the implementation

Decisions made informally (in conversation) are not official until they appear in `DECISION_LOG.md`.

---

## 14. Definition of Done

A feature is considered complete only when **all four** conditions are met:

1. **Implemented** — code is deployed and functional in production
2. **Documented** — relevant product and engineering docs are updated
3. **Tested** — automated or manual tests confirm correct behavior (where applicable)
4. **Charter-consistent** — the feature does not violate any principle in this document

---

## 15. Evidence Before Features

Every proposed feature must answer all four questions before implementation begins:

1. **What problem does it solve?**
2. **What evidence proves this problem exists?** (user feedback, data, observed behavior)
3. **What is the proposed solution?**
4. **Why should it be implemented now, not later?**

If any answer is missing or speculative, implementation must not start.

---

*Last updated: 2026-07-09*  
*Authority: Product Owner (columb@europe.com)*
