---
title: RFC — Owner-facing Reviews screen (read-only)
status: Draft
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-08-22
related_documents:
  - 05_ROADMAP/FUTURE_FEATURES.md
  - 07_RFC/RFC-0003-owner-team-staff-management.md
  - 00_GOVERNANCE/DECISION_LOG.md
implementation_status: Pending approval
---

# RFC-0004 — Owner-facing Reviews screen (read-only)

Date: 2026-08-22
Requested by: implementing session, following RFC-0003 (Team) — same audit-before-code process applied to the design reference's other unbuilt `salonOnly`-adjacent screen.
Status: Draft

---

## Problem

The owner cabinet's design reference includes a "Reviews" screen (aggregate rating, star distribution, individual review feed). No such screen exists in the shipped OwnerShell epic. Unlike Team (RFC-0003), this one has no crawler-write-conflict problem — the design reference's own mockup is entirely read-only — but `GET /api/owner/salons/{id}` (the endpoint every other cabinet screen reads from) does not return reviews at all today, so an owner currently cannot see their own salon's reviews without leaving the cabinet and opening the public page.

## Evidence

- Code-confirmed: `backend/app/models/salon.py:133` — `Review`: `id, salon_id, source, source_id, author_name, rating, text, text_en, text_ru, text_uk, published_at, last_seen_at, first_missing_at`. Same crawler-freshness pattern (T-048) as `Staff` (RFC-0003) — third-party-sourced, not owner-authored.
- Code-confirmed: `GET /api/owner/salons/{id}` (`owner.py`) selects `services`, `hours`, `social_links` but never `reviews` — confirmed at T-142 audit time and unchanged since.
- Code-confirmed: `GET /salons/{id}/reviews` (`salons.py:597`) already exists and works — public, paginated-by-relevance, on-demand per-language translation. The rendering and translation problem is already solved; only the cabinet-visibility path is missing.
- Code-confirmed: `reports.py`'s own comment (line ~151) states plainly: "reviews are imported, so the author may never have visited the site" — reviews are third-party content (Google/Treatwell), not something submitted through Lookla.
- Design reference: `design/lookla-owner-portal-runnable/app/mockups.tsx`'s `ReviewsPage` is **read-only except a per-review "Report an issue" button** — no reply/response control anywhere in the mockup. This RFC does not need to resolve a Team-style conflict-of-authority question, because nothing in the reference proposes owner-authored content on this screen.
- Code-confirmed: `reports.py`'s `ReportIn` has `salon_id`/`professional_id` but no `review_id` — a per-review "Report an issue" cannot target a specific review yet; only a whole-salon report exists today.
- Design reference: the same `ReviewsPage` mockup includes a "TOP THEMES" panel (`Friendly staff · 42`, `Great results · 38`, ...) — no code anywhere computes theme/keyword extraction from review text. `OpenAI Moderation` (already integrated, per `CLAUDE.md`) is a safety classifier, not a topic-tagger; `DeepL` is translation-only. This is invented content with nothing behind it, the same class of gap T-142 dropped ("Business type"/"Public category") and T-143 dropped (category grouping).

## Goal

An owner sees their salon's real aggregate rating (average, count, star-by-star distribution) and the real review feed (author, rating, text, date) from inside the cabinet — the same data the public page already renders, surfaced where the owner actually looks, without leaving it.

## Proposed Solution

**Single phase — read-only, same risk class as T-142/T-143.**

- Backend: new `GET /api/owner/salons/{id}/reviews` (paginated, mirrors the public endpoint's shape rather than dumping every review into the existing `GET /api/owner/salons/{id}` payload — a salon with hundreds of reviews would otherwise bloat every load of the Business profile screen for a tab the owner may never open). Rating distribution (count per star 1–5) computed with one `GROUP BY rating` query — a real aggregate of existing data, not invented.
- Frontend: new "Reviews" tab/screen on OwnerShell (`salonOnly`, alongside Team) — average + count header, star-distribution bars, paginated review list with existing on-demand translation reused from the public page's own logic where practical.
- **Dropped entirely:** "Top themes" — no backing computation exists; adding it would need its own RFC (an NLP/tagging decision, plus an ongoing per-review compute cost) and is out of scope here.
- **"Report an issue" per review — separate, optional addition, not required to ship the core screen:** add `review_id: Optional[int]` to `ReportIn` and the `reports` table (nullable FK to `reviews.id`, validated to belong to the salon being reported), so a report can reference exactly which review triggered it instead of a free-text guess inside `description`. Without this addition, the button can still exist and file a salon-level report with the review's id/text pasted into `description` as an interim, functional-but-imprecise fallback.

## Alternatives Considered

- **Owner-authored public replies to reviews** (a "business responded" pattern some platforms support). Rejected for this RFC: reviews are third-party-imported content the review author never submitted through Lookla; the design reference itself does not propose this control; and it raises its own provenance/moderation questions (is an owner reply itself moderated? can it be edited/deleted? does it need its own erasure-workflow handling like reviews already have, T-076?) that deserve a dedicated RFC if ever wanted, not a decision folded into a visibility ticket.
- **Computing "Top themes" via a lightweight keyword-frequency pass** (no AI, just word counting) instead of dropping it. Rejected: even non-AI keyword extraction is a new maintained subsystem (stopword lists per language, minimum-frequency thresholds, what counts as a "theme" vs. noise) for a panel with no evidence anyone asked for beyond the design mockup — smaller than the AI version but still real net-new scope, not visibility of existing data.

## User Value

The same category of value as T-142/T-143: an owner today must leave the cabinet entirely to see their own reviews. This closes that gap with data Lookla already has, verified by the crawler, and already renders correctly on the public page.

## Implementation Complexity

~2–3h for the core screen (a little more than T-143: needs pagination plus one aggregate query, not a single flat `SELECT`). The optional `review_id` reporting addition is independent, roughly +1h, and can ship separately or not at all.

## Maintenance Impact

None beyond the existing crawler-freshness maintenance (T-048) already running for `reviews`. No new subsystem, no new ongoing compute — this is a read path over data already collected and already refreshed.

## Architecture Impact

None for the core screen — additive read endpoint, no schema change. The optional reporting addition is one nullable FK column on `reports`, backward compatible, no impact on existing report rows (which will simply have `review_id = NULL`).

## Mobile Impact

None — same REST shape either app would consume.

## AI Impact

None. Explicitly rejects the one AI-shaped idea in the design reference ("Top themes") as out of scope for this ticket.

## Estimated Cost

| Item | Estimate |
|---|---|
| Implementation time (core screen) | ~2–3h |
| Implementation time (per-review reporting, optional) | ~1h |
| Infrastructure cost (monthly) | €0 |
| AI/API cost | €0 |
| Maintenance burden | Low — read path only |

## Dependencies

None.

## Risks

- Same crawler-accuracy risk already accepted for reviews shown publicly today (a stale or mistranslated review is a pre-existing, already-tolerated risk class, not a new one this ticket introduces).
- Pagination is worth getting right the first time for a salon with a large review count — reusing the public endpoint's existing tested pagination shape rather than inventing a second one is the mitigation, not a new risk.
- **Rollback:** pure addition (new endpoint, new tab) — revertible by dropping both in one PR, no data migration to undo either way.

## Decision

[To be filled by Product Owner after review]

Decision: APPROVED / REJECTED / DEFERRED
Reason:
Conditions (if any):
Decision ID: DEC-NNN
Date:
