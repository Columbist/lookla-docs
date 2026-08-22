---
title: RFC — Owner-facing Insights (profile views, contact actions)
status: Draft
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-08-22
related_documents:
  - 05_ROADMAP/FUTURE_FEATURES.md
  - 06_ENGINEERING/ANALYTICS_EVENTS.md
  - 07_RFC/RFC-0003-owner-team-staff-management.md
  - 07_RFC/RFC-0004-owner-reviews-visibility.md
  - 00_GOVERNANCE/DECISION_LOG.md
implementation_status: Pending approval
---

# RFC-0005 — Owner-facing Insights (profile views, contact actions)

Date: 2026-08-22
Requested by: implementing session, following RFC-0003 (Team) and RFC-0004 (Reviews) — the third and last of the design reference's unbuilt cabinet screens.
Status: Draft

---

## Problem

The owner cabinet's design reference includes an "Insights" dashboard: a 14-day profile-views sparkline, a contact-actions breakdown by channel (phone/WhatsApp/website), and a response-rate metric. Unlike Team and Reviews, this is **not** a case of "the data exists, nothing exposes it" — it is a genuine architecture decision, and this RFC exists to lay out the real options rather than pick one silently.

## Evidence

- Code-confirmed: `T-015` (✅ completed 2026-07-23, `docs/06_ENGINEERING/ANALYTICS_EVENTS.md`) already ships exactly the two events this dashboard needs, live in production today: `salon_open {salon_id, source, locale}` on every discovery-surface click, and `contact_action {salon_id, channel: 'phone'|'whatsapp'|'website', page, locale}` immediately before any contact action. Both are consent-gated, PII-clean by a two-layer allowlist/denylist, and keyed by the real numeric `salon_id`.
- Code-confirmed: these events go straight to GA4 via `gtag()` (`lib/analytics.ts`) — nothing is mirrored into Lookla's own Postgres. No `event_log` table or equivalent exists anywhere in `app/models/`.
- Code-confirmed: no backend code anywhere calls the Google Analytics Data (Reporting) API — no credentials, no service account, no query path exists today for "how many `salon_open` events did salon X get in the last 30 days."
- Code-confirmed: `.env` has no `FEATURE_MESSAGING`/`NEXT_PUBLIC_FEATURE_MESSAGING` set — the `MESSAGING` capability (`backend/app/core/capabilities.py`) is off in production today. The design reference's "Response rate" metric depends on message-reply timing; even fully instrumented, there is no live conversation data to compute it from while messaging stays off.
- `ANALYTICS_EVENTS.md` itself already flags `contact_action` as "the most plausible candidate for a future key event" but explicitly defers that decision "until real event quality and volume have been validated in production" — this RFC's dashboard question is adjacent to, but distinct from, that already-deferred one.

**The real problem this RFC surfaces:** "profile views" and "contact actions by channel" are both already well-defined and already flowing correctly — the gap is entirely about *where the numbers can be read back from*, and that has two materially different answers with different cost/risk shapes, not one obvious small addition like RFC-0003/0004.

## Goal

An owner sees real profile-view and contact-action trends for their own salon, sourced from data Lookla already collects (via T-015), without inventing a new metric or a fake number.

## Proposed Solution

Two architecture options. Recommending Option B, but this is the Product Owner's call — not something to default into mid-implementation.

**Option A — Query GA4's Data (Reporting) API server-side**, filtered to the salon's `salon_id` dimension, cached and refreshed periodically for the cabinet chart.
- Pros: no new write path, no duplicate instrumentation — reuses exactly what T-015 already ships.
- Cons: needs a GA4 service-account credential provisioned and rotated (a new secret in `.env`, a new failure mode if it expires); the Data API's standard reporting has a real freshness lag (typically 24–48h, not same-day); the API has daily quota shared across the whole GA4 property, so every cabinet page load querying it live does not scale without a caching layer; adds a hard external dependency (Google's API reachable and authorized) to a screen inside the product itself.

**Option B — First-party event mirror.** A new `salon_events(salon_id, event_type, occurred_at)`-shaped table, written server-side (either a lightweight endpoint the client's existing `trackEvent()` call sites also hit, or `trackEvent()` itself extended to fire twice). The cabinet reads this table directly with plain SQL aggregation.
- Pros: available immediately (no Google API lag), simple `GROUP BY`/date-bucket queries, no new external credential, no quota ceiling — matches this project's existing cost-and-simplicity bias (2GB host, `docs/06_ENGINEERING/...` cost-estimation discipline elsewhere).
- Cons: a second source of truth alongside GA4 — an ad-blocker or consent state could make the two disagree (e.g. a same-origin API call surviving where a third-party GA4 script is blocked, or vice versa); requires touching the three existing `trackEvent()` call sites (`SalonCard.tsx`, `MapView.tsx`, `ContactButtons.tsx`) or `analytics.ts` itself, not just adding a new backend read endpoint — a real (small) instrumentation change, with its own PII-shape discipline to carry forward from T-015's existing allowlist/denylist design.

**Response rate:** out of scope for either option until `MESSAGING` ships — a dependency on that capability's own launch decision, not something this RFC resolves.

## Alternatives Considered

- **Query GA4 client-side, per owner session, from the browser.** Rejected: GA4's reporting surface is not designed for authenticated per-property dashboards embedded in another product, and would expose Measurement/API details to the browser that Option A keeps server-side.
- **Leave Insights unbuilt indefinitely.** The actual status quo through T-140–T-145. Reasonable to keep choosing, explicitly, until an option here is approved — unlike Team/Reviews, where the data sitting unused was itself already a gap worth closing on its own, Insights' underlying data is already being used (by GA4, for aggregate site analytics) even while dark to individual owners, so there is no equivalent "dark and idle" argument for urgency here.

## User Value

Owners get feedback on whether their profile is being seen and acted on — the direct feedback loop T-142/143/144/145's "complete your profile" nudges (T-140's Dashboard "Profile strength" panel) currently promise but cannot yet honestly show real numbers for.

## Implementation Complexity

Materially larger than RFC-0003/0004, and not directly comparable to T-142–T-145's few-hour tickets:
- **Option A:** external credential provisioning (non-code time, needs Google Cloud console access) + a caching layer to survive quota + the read endpoint + the UI chart. Rough order of magnitude: a full day, split between setup and code.
- **Option B:** new table + migration + touching 3 existing instrumentation call sites (with the same PII discipline T-015 already established) + an aggregate read endpoint + the UI chart. Rough order of magnitude: 6–10h.

## Maintenance Impact

**Option A:** ongoing — a credential to rotate, a quota to monitor, a new external-outage failure mode for one cabinet screen. **Option B:** a second event pipeline to keep in sync with GA4's (same PII-shape rules must be maintained in two places if `trackEvent`'s own denylist ever changes) — real but bounded, no external dependency.

## Architecture Impact

**Option A:** new external integration (Google Analytics Data API), new secret. **Option B:** new table (`salon_events` or equivalent), a write-path change touching existing, already-reviewed T-015 instrumentation.

## Mobile Impact

Same either way — both options end in a plain REST read endpoint a future native app could consume identically.

## AI Impact

None.

## Estimated Cost

| Item | Estimate |
|---|---|
| Implementation time (Option A) | ~1 day (incl. external setup) |
| Implementation time (Option B) | ~6–10h |
| Infrastructure cost (monthly) | €0 either way (GA4 Data API free tier; Postgres already running) |
| AI/API cost | €0 |
| Maintenance burden | Option A: external credential/quota. Option B: second pipeline to keep in sync |

## Dependencies

None for the core dashboard. "Response rate" specifically depends on the `MESSAGING` capability's own launch (currently off in production) — unrelated to which option this RFC picks.

## Risks

- **Option A:** quota exhaustion or credential expiry silently breaking the Insights screen for every owner at once (a shared external dependency, not a per-owner failure).
- **Option B:** drift between what GA4 shows in aggregate reporting and what the cabinet shows per salon, if the two pipelines ever diverge in what they count as a qualifying event.
- **Rollback:** Option B is a pure addition (new table, new endpoint, new tab) if the `trackEvent()` double-send is implemented as a non-blocking side effect — revertible in one PR either way, no risk to T-015's existing GA4 path in either option.

## Decision

[To be filled by Product Owner after review]

Decision: APPROVED / REJECTED / DEFERRED
Reason:
Conditions (if any):
Decision ID: DEC-NNN
Date:
