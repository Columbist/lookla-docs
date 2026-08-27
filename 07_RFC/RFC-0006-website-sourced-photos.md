---
title: RFC — Replace aggregator photos with salon-website photos
status: Draft
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-08-27
related_documents:
  - 04_ARCHITECTURE/SECURITY.md
  - 06_ENGINEERING/RISK_REGISTER.md
  - 07_RFC/RFC-0005-owner-insights.md
  - 00_GOVERNANCE/DECISION_LOG.md
implementation_status: Draft — awaiting Product Owner decision
---

# RFC-0006 — Replace aggregator photos with salon-website photos

Date: 2026-08-27
Requested by: Product Owner, live instruction: "надо создать умного паука, задача заменить максимальное количество фотографий которое мы притащили с площадок на фотографии с сайтов" (build a spider to replace as many aggregator photos as possible with photos from salons' own websites; crawl known websites first, search for a website where none is known, mark everything replaced as sourced from the website).
Status: Draft — this RFC exists to lay out the real options before any code is written, per this project's own governance rule (implementation follows documentation) and its "cost before launch" discipline for any mass API cycle.

---

## Problem

~44,000 salon photos in production (`photos` table) all come from three aggregators — Google Places (43,740), Treatwell (271), Fresha (22) — across 5,057 of the 6,896 active salons (1,839 active salons have no photo at all). None come from the salons' own websites, even though a mature, legally-conscious own-website crawler already exists (T-088) and 2,577 active salons already have a known website URL in the DB.

Separately, and discovered while scoping this: `photos.source` is written on every row but never read back by anything — not `PhotoOut` (`backend/app/schemas/salon.py`), not the frontend `Photo` interface (`frontend/lib/api.ts`). Google-sourced reviews already carry a visible "Source: Google Reviews" label per Google's ToS (DEC-013, `SECURITY.md` §7, `RISK_REGISTER.md` R-014); Google-sourced photos, on the same legal footing, currently carry none. The Product Owner's own instruction — mark what gets replaced as website-sourced — reads as wanting that marking to be real and visible, not just an internal column value, so this RFC treats minimal source surfacing as in scope, not a separate follow-up.

## Evidence

- Code-confirmed: `crawler/beauty_crawler/spiders/website.py` + `website_run.py` (T-088) already do own-website crawling correctly and carefully — robots.txt-respecting (`robots_allows()`, real per-host parsing), URL-classification that tells a salon's *own* site apart from social/directory/platform/shortener/parked domains (`classify_website()`), Greek-aware `registrable_domain()`, redirect-safety (`same_site()`), a 2s politeness delay, a named bot UA (`LooklaBot/1.0 (+https://lookla.gr/about-bot)`). It currently extracts phone numbers and social links only — never photos, never email (email was a deliberate 2026-08-13 exclusion). This is the machinery to extend, not duplicate.
- Live DB query, 2026-08-25: `active_total=6896, active_with_website=2577, active_no_website=4319, photos_google=43740, photos_treatwell=271, photos_fresha=22, salons_with_photos=5057`.
- `website_crawl_results` (T-088's own outcome log) shows 1,677 of the known-website salons already crawled successfully for phone/social — meaning the harder infrastructure problem (finding the page, getting past robots.txt, confirming it's really the salon's own site) is already solved and validated for most of this group. Extending extraction to photos on an already-crawled, already-verified site is a materially smaller step than the search-discovery half of the ask.
- No search-engine API is currently configured or funded: `.env` defines `GOOGLE_SEARCH_API_KEY=`, `GOOGLE_CSE_CX=`, `SERPER_API_KEY=` — all present as keys, all empty. The only code that reads them (`crawler/beauty_crawler/spiders/facebook.py`, `search_facebook_pages_via_google()` / `_search_via_serper()`) has a dormant fallback path and no evidence of ever having produced a saved result in production. Discovering a website for the 4,319 salons that don't have one means either provisioning and funding a search vendor from scratch, or scraping search-engine result pages directly (fragile, ToS-risk of its own, no existing precedent in this codebase).
- `backend/app/services/r2.py` (T-152) already has a working, reviewed upload/delete path (`upload_bytes`, `delete_object`, `r2_key_from_cdn_url`) for the one prior case of storing images this codebase itself fetched rather than merely displaying (`professional_portfolio`). Its own docstring on `delete_object` notes it was the *first* path that let anything be deleted from R2 — worth remembering here, since this feature is the first path that would *replace* an existing, already-public asset rather than add a new one.

**The real problem this RFC surfaces:** the ask bundles two jobs with very different risk/cost shapes — (1) extract photos from websites we already trust are the salon's own, a contained extension of proven T-088 machinery, and (2) discover a website for salons where none is known, which requires picking and funding a search vendor and then trusting an unverified search hit enough to crawl and photograph it. Picking one option silently for both halves would be exactly the kind of undocumented feature-sized decision this project's governance model exists to catch.

## Goal

Salon pages show real photos of the actual business, sourced from a page the salon itself controls, wherever one is available and photographable — replacing generic aggregator photography without silently discarding it, and with every website-sourced photo visibly and honestly marked as such.

## Proposed Solution

Two decisions, not one — scope (how much of the ask ships now) and mechanics (how the shipped part behaves). Recommending the smaller option on each, but both are the Product Owner's call.

### Decision 1 — Scope: known websites now, search-discovery later (Option B) vs. both halves at once (Option A)

**Option A — full scope now.** Extend T-088's crawler to extract photos on the 2,577 known-website salons *and* add search-engine-based website discovery for the other 4,319, in one pass.
- Pros: matches the literal ask in one shot; covers up to 6,896 salons instead of 2,577.
- Cons: requires picking and funding a search vendor blind, before any data exists on how often extraction actually finds usable photos on the *known-good* sites; an unverified search-engine hit is a materially higher misattribution risk than a URL already sitting in `salons.website` — crawling and photographing the wrong business's site under `LooklaBot`'s own name is a real reputational/legal exposure this RFC should not wave through without seeing Option B's real hit-rate first.

**Option B — phased, known websites first.** Ship photo extraction against the 2,577 already-known, already-verified website salons only. Defer search-based discovery for the remaining 4,319 to a second RFC, informed by real hit-rate/quality numbers from this phase.
- Pros: no search-vendor decision needed to ship anything; reuses T-088's already-crawled, already-trusted set (1,677 already have a clean crawl outcome); real production data on "how often does a salon's own site actually have decent photos" before spending on the harder, riskier half.
- Cons: doesn't touch the 4,319 salons with no known website at all — the majority of active salons — until a follow-up is approved.

**Recommendation: Option B.** Matches this project's repeated pattern of shipping the safe increment and deciding the next one with real data (RFC-0005's own Option A/B split makes the same kind of call), and specifically respects the standing "cost before launch" rule for any mass API cycle — there is no cost estimate to give for search-API usage yet because no vendor or pricing has been confirmed against a live rate card.

### Decision 2 — Mechanics (apply to whichever scope is approved)

- **Storage:** download and re-host in R2 (`upload_bytes`, matching the `professional_portfolio` pattern), not hotlink the salon's own site. Hotlinking makes every salon page's photos depend on that salon's own server staying up and fast; T-088's own outcome log already shows this codebase treats "site alive but blocks our bot" (403, T-093) and "domain not responding" (180 salons) as real, common states — multiplying live exposure to that by hotlinking every photo is worse than the one-time fetch cost of downloading.
- **Replace semantics:** soft-replace, not delete. Existing aggregator photos get deprioritized (moved out of the primary display slots, not removed from the DB) when a website photo is accepted as a replacement, so a bad extraction is reversible without re-crawling. Matches `r2.py`'s own documented caution about this being new, undertested territory for deletion.
- **Quality filter:** cheap heuristics only for the first pass — minimum pixel dimensions, perceptual/hash-based de-duplication, filename/alt-text pattern exclusion for obvious logos/icons/banners, a per-salon cap. No AI-vision filtering in phase 1: at the scale of tens of thousands of candidate images, per-image vision-model cost is real money that has not been estimated or approved, and heuristics may prove good enough — the same reasoning as the Insights RFC's Option B vs A split. Revisit only if heuristic-only hit quality proves poor.
- **Marking (the Product Owner's explicit ask):** every replacement photo is written with `photos.source = 'website'` (new value alongside the existing `google`/`treatwell`/`fresha`). Minimal surfacing bundled into this RFC's scope: `PhotoOut` gains the `source` field, and the salon page shows a small, honest label on website-sourced photos — not because Google's ToS requires it (it doesn't, for a salon's own site), but because it's the most literal reading of "mark everything we find and replace as being from the website," and because leaving `source` unexposed after deliberately writing a new distinguishing value would recreate the exact gap this RFC opened with for Google photos.

## Alternatives Considered

- **Skip the phasing, just extract photos and leave discovery for "later" without an RFC boundary.** Rejected — "later" with no scope line tends to become "whoever's turn it is decides silently," which is the failure mode RFC-0005 was written to avoid for Insights.
- **Scrape search-engine result pages directly instead of a paid API**, to avoid a vendor decision. Rejected as the default: fragile against markup changes, real ToS exposure of its own, and no existing precedent in this codebase (the one place that pattern exists today, `facebook.py`, treats direct scraping as a last-resort fallback behind two paid APIs, not the primary path).
- **Hotlink instead of re-host.** Rejected above under Mechanics — see Storage.

## User Value

Salon pages look like the actual business instead of generic aggregator photography, for the (currently) up to 2,577 salons with a known, crawlable website — and, transparently, viewers can tell which photos came from the salon itself versus an aggregator.

## Implementation Complexity

- **Option B (recommended):** extend `website.py`'s `extract()` to also pull candidate photo URLs (og:image, gallery/portfolio pages already reached via existing link-following, JSON-LD `image` fields) + heuristic filtering + R2 download/upload + `website_run.py` orchestration changes (new `PHOTO_SQL`, soft-replace of existing rows) + `PhotoOut`/frontend `source` surfacing + a source label on the salon page. Rough order of magnitude: comparable to a mid-sized owner-cabinet ticket, roughly 1–2 days including the display-side change.
- **Option A's extra half** (search discovery for 4,319 salons) is not estimated here — it depends entirely on the vendor decision this RFC deliberately defers.

## Maintenance Impact

A third photo-source pipeline alongside the two existing crawler-photo paths (Google Places import, the smaller Treatwell/Fresha imports) — bounded, no new external dependency beyond what T-088 already has (the salon's own site, already handled).

## Architecture Impact

Extends existing `website.py`/`website_run.py` (T-088) and existing `r2.py` (T-152) — no new services, no new dependency, no RFC-worthy infrastructure addition of its own for Option B. A new `photos.source` value (`'website'`) is additive, no migration needed if `source` is already a free-text column (confirm at implementation time).

## Mobile Impact

None — same REST photo payload either way.

## AI Impact

None for Option B (heuristic filtering only, no model in the loop). Would become relevant only if a future phase adds AI-vision quality filtering — not proposed here.

## Estimated Cost

| Item | Estimate |
|---|---|
| Implementation time (Option B) | ~1–2 days |
| Infrastructure cost (monthly) | R2 storage for new photos — negligible at this scale (existing bucket, existing pricing tier) |
| Search-vendor cost (Option A's discovery half) | **Not estimated** — no vendor picked, no live rate card checked; must be priced before any approval to spend, per standing cost-before-launch rule |
| Maintenance burden | Low — extends existing, already-maintained pipelines |

## Dependencies

None for Option B. A future search-discovery phase depends on: picking a vendor (Google Custom Search JSON API vs. Serper.dev vs. other), funding it, and a fresh cost estimate against real 2026 pricing before launch.

## Risks

- **Misattribution:** extracting a photo from the wrong business's site. Bounded in Option B by only crawling URLs already sitting in `salons.website` (operator- or crawler-confirmed, not a fresh unverified search hit) and reusing T-088's existing `classify_website()`/`same_site()` own-site verification before trusting a page at all.
- **Quality regression:** a heuristic-only filter admits an off-brand or low-quality photo (e.g. a sponsor logo, a stock banner) that a human would reject. Mitigated by soft-replace (reversible) and a conservative filter tuned narrow rather than broad on first pass.
- **Bot politeness at scale:** photo extraction adds requests (gallery pages, image fetches) on top of T-088's existing 2s-delay single-page crawl — needs its own rate-limit budgeting so it doesn't look like a heavier bot to the same 1,677+ sites already crawled once.
- **Rollback:** pure addition + soft-replace — revertible in one PR, no risk to existing aggregator photos, which stay in the DB either way.

## Decision

Decision: PENDING
Reason: —
Conditions (if any): —
Decision ID: —
Date: —
