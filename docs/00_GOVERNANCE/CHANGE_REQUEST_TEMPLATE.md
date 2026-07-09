---
title: Change Request Template (RFC)
status: Locked
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 00_GOVERNANCE/PROJECT_CHARTER.md
  - 00_GOVERNANCE/DECISION_LOG.md
  - 07_RFC/
implementation_status: N/A — template document
---

# Change Request Template (RFC)
**Lookla Beauty Marketplace**

> Use this template for every proposed feature, change, or removal.  
> Copy the template into `07_RFC/RFC-NNNN-short-title.md`.  
> No implementation begins until the Change Request is approved and logged in `DECISION_LOG.md`.

---

## How to submit a Change Request

1. Copy the template below into `07_RFC/RFC-NNNN-short-title.md`
2. Fill in all sections — no section may be skipped
3. Submit to Product Owner for review
4. If approved: assign a `DEC-NNN` ID and log in `DECISION_LOG.md`
5. Set RFC status to `Approved`
6. Implementation begins only after the log entry exists

---

## Naming Convention

```
07_RFC/RFC-0001-short-title.md
07_RFC/RFC-0002-another-title.md
```

Use lowercase, hyphen-separated titles. Keep them short and descriptive.

---

## Template

```markdown
---
title: RFC — [Short title]
status: Draft
version: 1.0
owner:
reviewers:
last_updated: YYYY-MM-DD
related_documents: []
implementation_status: Pending approval
---

# RFC-NNNN — [Short title]

Date: YYYY-MM-DD
Requested by:
Status: Draft | Under Review | Approved | Rejected | Deferred

---

## Problem

[What is broken, missing, or suboptimal? Be specific. One problem per RFC.]

---

## Evidence

[What proves this problem exists?
Acceptable evidence: user feedback, observed behavior, data, error logs, competitor analysis.
Speculation is not evidence. If no evidence exists, state that and explain why the problem is still worth solving.]

---

## Goal

[What does success look like? What is the measurable outcome after this change?]

---

## Proposed Solution

[Describe what will change. Be concrete: which pages, which endpoints, which data.]

---

## Alternatives Considered

[What other solutions were evaluated? Why were they rejected?]

---

## User Value

[Who benefits and how? Quantify if possible.]

---

## Implementation Complexity

[Estimated effort in hours or days. Which files/systems are affected?]

---

## Maintenance Impact

[What ongoing cost does this add? Who is responsible for keeping it working?]

---

## Architecture Impact

[Does this change the data model, API contract, or component boundaries?
Does it conflict with any principle in PROJECT_CHARTER.md?]

---

## Mobile Impact

[Is this implementation reusable for iOS/Android/Partner app?
Does it create a web-only dependency?]

---

## AI Impact

[Does this feature use AI? If yes, what is the measurable user value?
Does it increase AI API costs?]

---

## Estimated Cost

| Item | Estimate |
|---|---|
| Implementation time | |
| Infrastructure cost (monthly) | |
| AI/API cost (per request or monthly) | |
| Maintenance burden | |

---

## Dependencies

[What must exist or be completed before this can be implemented?]

---

## Risks

[What could go wrong? What is the rollback plan?]

---

## Decision

[To be filled by Product Owner after review]

Decision: APPROVED / REJECTED / DEFERRED
Reason:
Conditions (if any):
Decision ID: DEC-NNN
Date:
```

---

*Last updated: 2026-07-09*
