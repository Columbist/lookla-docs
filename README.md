# Lookla — Product Documentation

> **This directory is the single source of truth for all product decisions.**  
> Implementation follows documentation. Documentation never follows implementation automatically.

---

## Purpose

This repository contains the official product documentation for the Lookla Beauty Marketplace platform. It covers product management, UX, UI design, architecture decisions, feature specifications, roadmap, and RFC proposals.

Engineering documentation (code, deployment, troubleshooting) lives in `06_ENGINEERING/` and is kept separate from product documentation.

---

## Documentation Hierarchy

```
00_GOVERNANCE/      Project Charter, Decision Log, Change Request process
01_PRODUCT/         Vision, Scope, Personas, User Journeys, Terminology
02_DESIGN/          Design System, Components, Brand Guidelines
03_PAGES/           Page-level specifications
04_ARCHITECTURE/    Data Flow, Feature Flags, Mobile and AI Strategy
05_ROADMAP/         Approved milestones and future features
06_ENGINEERING/     Audit, Troubleshooting (implementation-facing)
07_RFC/             One file per proposal
08_REVIEWS/         External and internal product reviews
09_IMAGES/          Diagrams, wireframes, screenshots referenced in docs
10_DIAGRAMS/        Architecture and flow diagrams
```

**Priority order (highest to lowest):**

```
00_GOVERNANCE/PROJECT_CHARTER.md   ← Highest authority
        ↓
Approved Product Documents (01_PRODUCT, 02_DESIGN, 03_PAGES)
        ↓
Approved RFC
        ↓
Engineering Documentation (06_ENGINEERING)
        ↓
Implementation
```

If a conflict exists between any two levels — **do not resolve it automatically. Report it.**

---

## Document Status

Every document begins with a YAML metadata block:

```yaml
---
title:
status: Draft | Approved | Locked | Deprecated
version:
owner:
reviewers:
last_updated:
related_documents:
implementation_status:
---
```

| Status | Meaning |
|---|---|
| **Draft** | Being written. Not authoritative. May not be implemented. |
| **Approved** | Approved by Product Owner. Authoritative. Implementation may begin. |
| **Locked** | Approved and frozen. Changes require a new RFC. |
| **Deprecated** | Superseded by another document. Kept for historical reference. |

A document is not authoritative until its status is `Approved` or `Locked`.

---

## How Documents Are Approved

1. A need is identified — a problem, a feature request, or a clarification.
2. A Change Request is written using `00_GOVERNANCE/CHANGE_REQUEST_TEMPLATE.md`.
3. The request is reviewed against `00_GOVERNANCE/PROJECT_CHARTER.md`.
4. If approved by the Product Owner: status changes to `Approved`, decision is logged in `00_GOVERNANCE/DECISION_LOG.md`.
5. Implementation begins only after the decision is logged.
6. Upon completion, relevant documents are updated and `implementation_status` is set.

Decisions made informally (in conversation, chat, or email) are **not official** until logged.

---

## How RFC Works

RFCs (Requests for Change) live in `07_RFC/`.

Naming convention: `RFC-0001-short-title.md`, `RFC-0002-short-title.md`, etc.

Each RFC follows the template in `00_GOVERNANCE/CHANGE_REQUEST_TEMPLATE.md` and addresses:
- Problem and evidence
- Proposed solution
- Alternatives considered
- Cost, risk, and impact assessment
- Decision

An RFC is either `Approved`, `Rejected`, or `Deferred`. Approved RFCs result in a `DECISION_LOG` entry before implementation begins.

---

## How Documentation Affects Implementation

- **No implementation without an approved document.** A feature without a corresponding Approved status in the relevant spec or a logged Decision is not authorized.
- **Mismatches are reported, not silently fixed.** If code diverges from documentation, the mismatch is flagged in the Decision Log or an RFC is opened.
- **Engineering docs describe what is built.** Product docs describe what is approved. They are complementary, not interchangeable.

---

## Contributing

See `CONTRIBUTING.md` at the repository root for contribution guidelines.

---

*Repository: lookla-platform (monorepo)*  
*Documentation root: /docs*  
*Last updated: 2026-07-09*
