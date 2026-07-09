---
title: Product Roadmap
status: Draft
version: 0.1
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 00_GOVERNANCE/DECISION_LOG.md
  - 05_ROADMAP/FUTURE_FEATURES.md
  - 01_PRODUCT/PRODUCT_SCOPE.md
implementation_status: N/A — planning document
---

# Product Roadmap
**Lookla Beauty Marketplace**

> **DRAFT — contains only approved milestones.**  
> Unapproved ideas and future exploration belong in `FUTURE_FEATURES.md`.  
> A milestone appears here only after a Decision Log entry approves it.

---

## How to read this roadmap

- **Milestone** = an approved, scoped unit of work with a clear goal
- **Milestone status:** `Planned` → `In Progress` → `Complete`
- No dates are committed unless explicitly approved
- This is a product roadmap, not a sprint backlog (engineering tasks live in `06_ENGINEERING/`)

---

## Current Stage: Discovery Validation

**Goal:** Validate that real users find Lookla useful for discovering beauty services in Greece.

**Success criteria:** 500 verified user interactions (phone/WhatsApp/website click) within 90 days of launch (DEC-008).

---

## Approved Milestones

### M-01 — MVP Athens Launch

| Field | Value |
|---|---|
| Status | In Progress |
| Decision | DEC-008 through DEC-017 |
| Target area | Athens metropolitan area |
| Primary persona | P-02 Russian/Ukrainian residents, P-01 Greek locals |

**Goal:** Deploy a production-ready, honest, multilingual beauty directory for Athens that allows real users to discover and contact salons without registration.

**Scope:**
- Location hierarchy: Country → Region → City → District (replaces flat City filter)
- Review source labels: "Source: Google Reviews / Imported: Yes / Original: No"
- Verified badge: replaced with "Information reviewed" / "Owner verified" labels
- Booking stubs removed: replaced with "Call salon" / "Message on WhatsApp" / "Visit website"
- GA4 + Search Console installed and verified
- Athens salon data quality: 100+ listings reviewed
- All 4 languages functional; el/en/ru QA-reviewed

**Out of scope for M-01:**
- Online booking
- Owner claim UI
- Favorites
- Geo search
- Thessaloniki or national focus
- Any Stripe or monetization exposure

**Success criteria (DEC-008):**
- 500 verified user interactions (phone/WhatsApp/website click) within 90 days
- Secondary: 100 Athens salons listed, 30 claimed, 10% visitor→contact conversion

**Pre-launch gate:**
See `01_PRODUCT/MVP_SCOPE_LOCK.md` — all items in the Pre-MVP Launch Gate must be confirmed before M-01 is declared complete.

---

## Milestone Template

```
### M-NN — [Milestone name]

Status: Planned | In Progress | Complete
Decision: DEC-NNN
Goal: [What this milestone achieves for the user]
Scope: [What is included]
Out of scope: [What is explicitly excluded]
Success criteria: [How we know it's done]
```

---

*Last updated: 2026-07-09*
