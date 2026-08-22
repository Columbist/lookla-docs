---
title: RFC — Owner-facing Team (staff) screen
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-08-22
related_documents:
  - 05_ROADMAP/FUTURE_FEATURES.md
  - 00_GOVERNANCE/DECISION_LOG.md
  - 06_ENGINEERING/DEVELOPMENT_STANDARDS.md
implementation_status: Approved — DEC-027
---

# RFC-0003 — Owner-facing Team (staff) screen

Date: 2026-08-22
Requested by: implementing session, following T-140/142/143/144/145 (OwnerShell restyle epic) — the design reference (`design/lookla-owner-portal-runnable/`) specs a "Team" nav item for salon accounts that has no backend today; `FUTURE_FEATURES.md` already lists "Staff profiles" as a candidate ("Data exists in DB") but unapproved.
Status: Approved

---

## Problem

The owner cabinet's design reference includes a `salonOnly` "Team" screen (add/edit staff members, presumably assign roles). No such screen exists in the shipped OwnerShell epic (T-140–T-145) because — unlike Business profile, Services, Master profile, and Settings — auditing the backend before writing anything surfaced a real complication specific to this one: staff data already exists, but nothing today establishes who is allowed to write to it, and something else already does.

## Evidence

- Code-confirmed: `backend/app/models/salon.py:189` — `Staff` table exists: `id, salon_id, name, bio, role, photo_url, is_active, last_seen_at, first_missing_at`. The last two columns are the same crawler-freshness-tracking pair `Review` uses (T-048) — not present on any owner-writable model in this codebase (`Salon`, `Service`, `Professional` have none).
- Code-confirmed: `crawler/beauty_crawler/spiders/treatwell.py`, `crawler/beauty_crawler/spiders/enrichment.py`, and `crawler/beauty_crawler/observation.py` all reference `staff` — the crawler actively populates and refreshes this table today, salon by salon.
- Code-confirmed: zero references to `Staff`/`staff` anywhere in `backend/app/routers/*.py` — no public endpoint, no owner endpoint, no admin endpoint. The data is fully dark: not shown on the public salon page, not manageable by anyone.
- Code-confirmed: `Staff` has no `user_id` or any link to `salon_owners` — there is no existing concept of "this staff row belongs to this account" for an owner-write path to hang off of, unlike `Service`/`SalonHours`/`SocialLink`, which are already salon-scoped and already owner-writable via `owner.py`.
- Design reference: `design/lookla-owner-portal-runnable/app/page.tsx` marks the Team nav item `salonOnly: true` — consistent with `Staff.salon_id` (no professional-scoped equivalent exists or is implied).
- `docs/05_ROADMAP/FUTURE_FEATURES.md` lists "Staff profiles" as a candidate feature with the note "Data exists in DB" — this RFC is that candidate's write-up, per that document's own required process ("Nothing here may be implemented without an approved RFC and Decision Log entry").

**The core problem this RFC exists to surface:** a naive "add owner CRUD over the `staff` table," copying the T-142/T-143/T-144 pattern exactly, would put two independent writers (the crawler and a salon owner) on the same rows with no conflict rule. The next scheduled crawl would silently overwrite an owner's edit, or an owner's edit would silently overwrite freshly-crawled data — either way, "silent overwrite of one writer by the other" is exactly the failure class `feedback_silent_degradation` (this session's own working principle) exists to catch before shipping, not after.

## Goal

Salon staff members become visible somewhere a real client or a real owner can see them, with a clear, non-conflicting answer to "who is allowed to change this row, and what happens to the other writer's version."

## Proposed Solution

Two independent phases, either of which can be approved without the other:

**Phase 1 — read-only, zero conflict risk.** Add `staff` to `GET /api/owner/salons/{id}`'s response (same shape T-143 already used to expose `Service.is_active`: an existing, crawler-verified column that simply wasn't selected back). Render a read-only "Team" tab on the salon Business profile screen — name, role, bio, photo, matching the existing crawler-sourced pattern the public salon page already uses for reviews. No write path, so no conflict with the crawler exists. This alone answers the "why is my team not shown anywhere, not even publicly" gap and is the same size/risk as T-143.

**Phase 2 — owner-writable, needs a conflict rule decided here, not improvised mid-implementation.** Three candidate rules, none implemented without this RFC's Decision section picking one:
  a. **Claim-and-freeze**: an owner edit sets a new `is_owner_edited` flag per row; the crawler skips any row with that flag on future passes. Mirrors how `is_owner_claimed` already gates salon-level crawler overwrites (T-024) — same shape, one level down.
  b. **Owner-only additions**: owners may add/remove/reorder staff members they enter themselves (a new `added_by_owner` boolean), but may not edit crawler-sourced rows at all — crawler rows stay crawler-owned, owner rows stay owner-owned, no shared row ever has two writers.
  c. **Full owner override, crawler stops writing entirely** once a salon is claimed — same trust model `is_owner_claimed` already implies for salon-level fields today (`update_salon` never checks against crawler freshness).

## Alternatives Considered

- **Ship Phase 2 directly, decide the conflict rule ad hoc in the implementing PR.** Rejected — this is exactly the shortcut that produced the `description_en` hotfix (T-142's companion bug) and the `salon_hours` off-by-one T-142 fixed in passing: an assumption made silently inside one ticket, discovered later as a production defect. The conflict rule affects data integrity for every claimed salon with staff, not just this screen.
- **Skip Team entirely, leave the nav item unbuilt.** Was the actual decision through T-140–T-145 (this epic simply didn't touch it). Rejected as a permanent answer only because the data already exists and is already dark — an owner cannot even see their own listed staff today, which is a worse gap than the salon-profile fields T-142 found (those were at least owner-editable once wired; this is invisible to the owner entirely).

## User Value

Salon owners can currently see and correct their business details, services, and hours, but have zero visibility into what Lookla shows (or would show) about their staff — a gap unrelated to whether Phase 2 ever ships. Phase 1 alone closes that. Phase 2 additionally lets an owner correct crawler mistakes (wrong role, stale photo, a staff member who left) the same way T-142 already lets them correct a wrong salon description.

## Implementation Complexity

- Phase 1: ~1–2 hours — one `SELECT`, one new tab on an existing screen, tests. Same order of magnitude as T-143.
- Phase 2: depends entirely on which conflict rule is chosen; rule (a) is the closest in shape to already-shipped code (`is_owner_claimed`) and is the implementing session's estimate for smallest Phase 2, but sizing it precisely is not useful before a rule is picked.

## Maintenance Impact

Phase 1: none beyond the existing crawler-freshness maintenance already in place for `Staff` (T-048 pattern, already running). Phase 2: whichever rule is picked becomes a second place (`salons.is_owner_claimed` being the first) where crawler and owner authority intersect, and needs the same care T-024/T-048 already document for that intersection — not a new maintenance class, but a second instance of an existing one.

## Architecture Impact

Phase 1: none — additive `SELECT`, no schema change. Phase 2: adds one column (whichever rule's flag) to `staff`, and a crawler-side check before any UPDATE — a real change to the crawler's write path, not just the API's.

## Mobile Impact

None — same REST endpoints either app would consume; no web-only mechanism proposed.

## AI Impact

None.

## Estimated Cost

| Item | Estimate |
|---|---|
| Implementation time (Phase 1) | ~1–2h |
| Implementation time (Phase 2) | Not sized — depends on Decision |
| Infrastructure cost (monthly) | €0 — no new infrastructure |
| AI/API cost | €0 |
| Maintenance burden | Low (Phase 1); one new crawler/owner intersection point (Phase 2) |

## Dependencies

None for Phase 1. Phase 2 depends on this RFC's Decision picking a conflict rule.

## Risks

- **Phase 1 risk:** none identified beyond the standard "crawler data can be wrong" risk that already exists for every crawler-sourced field shown publicly today (reviews, hours, description) — staff would carry the same, already-accepted risk profile, not a new one.
- **Phase 2 risk (if approved without picking a rule):** silent overwrite in either direction, as described in Evidence — the reason this RFC exists.
- **Rollback:** Phase 1 is a pure addition (new response field, new read-only tab) — revertible by dropping both in one PR, no data migration to undo. Phase 2's rollback depends on the rule chosen.

## Decision

Decision: APPROVED (Phase 1 only)
Reason: Phase 1 (read-only) closes a real, low-risk visibility gap immediately. Phase 2 (owner-writable) needs a conflict rule named before any code touches the write path — see DEC-027.
Conditions (if any): Phase 2 requires a follow-up decision naming one of the three candidate conflict rules before implementation begins.
Decision ID: DEC-027
Date: 2026-08-22
