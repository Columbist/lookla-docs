---
title: AI Strategy
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 00_GOVERNANCE/PROJECT_CHARTER.md
  - 00_GOVERNANCE/DECISION_LOG.md
  - 01_PRODUCT/PRODUCT_TERMINOLOGY.md
implementation_status: Current AI usage is infrastructure (translation). No AI product features implemented.
---

# AI Strategy
**Lookla Beauty Marketplace**

> Approved per Project Charter §11 and DEC-005.

---

## Approved Position

AI features are **intentionally postponed** until they provide measurable user value.

Architecture is AI-ready. AI tooling is available. Neither justifies adding AI product features before evidence of user need is established.

AI is a tool, not a feature. Any AI integration must solve a specific user problem and pass the same Evidence Before Features evaluation as any other change.

---

## Current AI Usage (Approved Infrastructure)

| Usage | Model | Purpose | Cost model | Status |
|---|---|---|---|---|
| On-demand translation | GPT-4o-mini | Translate service names and review text into user's locale | Per-token, cached in DB after first translation | Approved, deployed |

This usage is classified as **infrastructure**, not a product feature. It is invisible to the user except for the "🌐 Translated" label on content.

**Cost control:** Translation is only triggered on first real-user view. Bot traffic is filtered before the translation call. Translated content is cached permanently in the database.

---

## Prohibited (until approved via RFC)

- AI-powered search ranking or recommendations
- AI-generated content (descriptions, marketing copy, fake reviews)
- AI image analysis for public display
- Any AI feature that increases per-request cost without measurable user value

---

## Future AI Candidates (not approved — listed for awareness)

These are not roadmap commitments. They are documented to ensure architecture remains compatible:

| Candidate | Potential value | Evaluation status |
|---|---|---|
| Smart search suggestions | Reduce zero-result searches | Not evaluated |
| Automated data quality checks | Flag crawled data anomalies | Not evaluated |
| Review summarization | Quick overview of what clients say | Not evaluated |
| Booking time recommendation | Suggest best available slot | Not evaluated |

None of the above may be implemented without an approved RFC and Decision Log entry.

---

*Last updated: 2026-07-09*
