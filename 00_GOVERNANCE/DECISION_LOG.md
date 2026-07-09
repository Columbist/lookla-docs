---
title: Decision Log
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 00_GOVERNANCE/PROJECT_CHARTER.md
  - 00_GOVERNANCE/CHANGE_REQUEST_TEMPLATE.md
implementation_status: N/A — governance document
---

# Decision Log
**Lookla Beauty Marketplace**

> This log is the official record of all approved product and architecture decisions.  
> A decision is not official until it appears here.  
> Informal decisions (made in conversation) must be logged before implementation begins.

---

## How to use this log

1. Assign the next available Decision ID (`DEC-NNN`)
2. Fill all fields — no field may be left empty
3. Set Status to `APPROVED` only after Product Owner confirmation
4. Update `Implementation status` as work progresses
5. Link all affected documents

---

## Decision Template

```
### DEC-NNN — [Short title]

| Field | Value |
|---|---|
| Date | YYYY-MM-DD |
| Status | PROPOSED / APPROVED / REJECTED / SUPERSEDED |
| Decided by | |

**Context**
[Why did this decision need to be made?]

**Decision**
[What was decided?]

**Reason**
[Why this option over alternatives?]

**Consequences**
[What changes as a result? What becomes harder or easier?]

**Implementation status**
[ ] Not started / [→] In progress / [x] Complete

**Affected documents**
-
```

---

## Log

### DEC-001 — Project stage: private validation, no monetization

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
Project is in early development. Defining the official operating constraints for this stage.

**Decision**
The project operates as a private development project with no registered company, no commercial activity, no monetization, no subscriptions, no advertising, and no paid promotion. The primary goal is validating the product with real users.

**Reason**
Premature monetization distorts product decisions. Validation must come before revenue.

**Consequences**
- Stripe infrastructure exists in code but must not be exposed to users
- No pricing pages, no subscription gates, no ads
- All features are evaluated for user value, not revenue potential

**Implementation status**
[x] Reflected in Charter. Stripe endpoints exist but are not linked from any user-facing page.

**Affected documents**
- `00_GOVERNANCE/PROJECT_CHARTER.md` §2, §12

---

### DEC-002 — Documentation-first development process

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
Implementation has been proceeding without formal product documentation, making it hard to distinguish approved decisions from engineering choices.

**Decision**
No implementation starts before documentation is approved. `docs/` is the source of truth. Engineering follows approved product documentation.

**Reason**
Prevents feature creep, aligns engineering with product intent, creates an audit trail.

**Consequences**
- Every feature request must go through `CHANGE_REQUEST_TEMPLATE.md`
- Implementation without a logged decision is unauthorized
- Mismatches between code and docs must be reported, not silently fixed

**Implementation status**
[x] Process established. Directory structure created.

**Affected documents**
- `00_GOVERNANCE/PROJECT_CHARTER.md` §5, §13

---

### DEC-003 — No fake activity of any kind

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
Marketplaces are frequently tempted to seed fake activity to appear more popular. This decision draws a permanent line.

**Decision**
No fake statistics, reviews, discounts, bookings, ratings, or popularity signals are acceptable at any stage of the project.

**Reason**
Trust is the core asset of a marketplace. Fake activity destroys trust permanently if discovered.

**Consequences**
- All data shown to users must come from real sources
- Crawled data shown as-is, not inflated
- Review counts and ratings must reflect actual data only

**Implementation status**
[x] No fake data in current implementation. Crawler pulls real public data only.

**Affected documents**
- `00_GOVERNANCE/PROJECT_CHARTER.md` §3, §8

---

### DEC-004 — Evidence required before feature implementation

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
Features have been added based on engineering intuition rather than validated user need.

**Decision**
Every proposed feature must answer four questions before implementation: (1) what problem it solves, (2) what evidence proves the problem exists, (3) what the solution is, (4) why now. If any answer is missing, implementation must not start.

**Reason**
Prevents waste. Keeps the product focused on real user needs.

**Consequences**
- Change requests are mandatory for new features
- Features without evidence answers are rejected until evidence is provided
- This applies equally to UI changes, new endpoints, and infrastructure additions

**Implementation status**
[x] Process established via `CHANGE_REQUEST_TEMPLATE.md`.

**Affected documents**
- `00_GOVERNANCE/PROJECT_CHARTER.md` §15

---

### DEC-005 — AI features postponed until measurable user value is confirmed

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
AI tooling is widely available but often added without clear value. Current AI usage (on-demand translation) is infrastructure.

**Decision**
AI product features are intentionally postponed. Architecture remains AI-ready. No AI feature is added until it solves a specific, measurable user problem.

**Reason**
AI features carry cost and complexity. Without evidence of user value, the cost is not justified.

**Consequences**
- Current GPT-4o-mini usage (translation) is approved as infrastructure, not a product feature
- No AI recommendations, AI search ranking, AI content generation until approved via change request

**Implementation status**
[x] No unapproved AI features in current implementation.

**Affected documents**
- `00_GOVERNANCE/PROJECT_CHARTER.md` §11

---

### DEC-006 — Monetization postponed; architecture remains monetization-ready

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
Stripe infrastructure was built in anticipation of future subscriptions. Decision formalizes that it must not be user-facing yet.

**Decision**
Monetization is postponed. Stripe infrastructure may remain in code but must not be accessible from any user-facing page or flow. No pricing, subscription gates, or ads until a monetization decision is approved.

**Reason**
Monetizing before product validation drives away early users and distorts feedback.

**Consequences**
- `/pricing` page and Stripe checkout endpoints must not be linked from navigation
- Subscription plan table exists in DB but is invisible to users
- Future monetization decision will require its own Change Request

**Implementation status**
[ ] Verification needed: confirm `/pricing` is not linked in main navigation.

**Affected documents**
- `00_GOVERNANCE/PROJECT_CHARTER.md` §12

---

### DEC-007 — Monorepo: documentation lives with code

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
Decision between a separate documentation repository and keeping docs alongside code.

**Decision**
Documentation lives inside the main application repository (`lookla-platform`) under `/docs`. No separate repository for documentation.

**Reason**
Documentation and code must version together. A commit that changes a feature should also update the relevant docs in the same commit. This makes it possible to trace, via Git history, not only what changed but why it changed. Reduces the risk of documentation drifting from implementation.

**Consequences**
- `/docs` is part of the monorepo alongside `/apps/backend`, `/apps/frontend`, `/crawler`
- Every feature commit should include relevant documentation updates
- Pull request templates enforce documentation check

**Implementation status**
[x] `/docs` directory structure established in monorepo root.

**Affected documents**
- `00_GOVERNANCE/PROJECT_CHARTER.md` §5
- `docs/README.md`

---

*Last updated: 2026-07-09*
