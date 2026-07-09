# Contributing to Lookla

Thank you for contributing to the Lookla platform.

## Before You Start

Read `docs/00_GOVERNANCE/PROJECT_CHARTER.md`. It is the highest-priority document in the repository and governs all contributions.

The most important rule: **implementation follows documentation, not the other way around.**

## How to Contribute

### Bug fixes

1. Open a Bug Report issue using the template in `.github/ISSUE_TEMPLATE/bug_report.md`
2. Fix the bug
3. Open a PR using the PR template
4. If the fix reveals a documentation mismatch, open a Documentation issue

### New features

New features require approval before implementation:

1. Write a Change Request using `docs/00_GOVERNANCE/CHANGE_REQUEST_TEMPLATE.md`
2. Create `docs/07_RFC/RFC-NNNN-title.md`
3. Open an RFC issue linking to the file
4. Wait for Product Owner approval
5. After approval: log the decision in `docs/00_GOVERNANCE/DECISION_LOG.md`
6. Implement and update relevant docs in the same PR

### Documentation

1. Open a Documentation issue describing what is missing or incorrect
2. Make the change
3. Open a PR — documentation-only PRs skip the RFC process unless they change an approved decision

## Documentation Rules

- Every document must have a YAML metadata header (see `docs/README.md`)
- Do not change the status of a document from `Draft` to `Approved` without Product Owner confirmation
- Do not silently fix a documentation/implementation mismatch — report it first
- If you discover a conflict with the Project Charter, do not resolve it — report it

## Commit Convention

```
type(scope): short description

Types: feat, fix, docs, refactor, chore, test
Scope: frontend, backend, crawler, docs, infra

Examples:
feat(frontend): add open/closed badge to salon cards
fix(backend): correct timezone handling in open_now batch
docs(03_PAGES): update SEARCH.md with filter specification
```

When a feature commit includes documentation updates, include both in the same commit.

## Code Style

- Backend: follow existing FastAPI patterns; no new dependencies without RFC
- Frontend: Tailwind CSS only; no new UI libraries without RFC
- No code comments explaining what the code does; only comments explaining non-obvious constraints

## Questions

Open a Discussion issue using `.github/ISSUE_TEMPLATE/discussion.md`.
