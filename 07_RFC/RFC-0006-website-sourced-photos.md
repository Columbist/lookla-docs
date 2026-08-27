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
- **Vendor pricing, checked live 2026-08-27** (this RFC's own "no cost estimate without a live rate card" rule, now resolved): Google's Custom Search JSON API — the one already half-wired in `.env`'s key names — is **closed to new customers and being discontinued 2027-01-01**; `GOOGLE_SEARCH_API_KEY` being empty isn't an oversight, it's not obtainable fresh. Brave's Search API dropped its free tier in February 2026 and now bills $5/1,000 queries with no hard spending cap and a site-attribution requirement. **Serper.dev** is a viable cheap option: a 2,500-query free trial, then prepaid credit packs starting at $50 for 50,000 queries (~$1/1,000, cheaper at volume) — one salon-website lookup per salon, once, is one query each. For 4,319 salons: the first 2,500 are free; the smallest paid pack ($50, 50,000 credits) covers the rest with over 45,000 credits to spare for retries or a future phase.
- **OpenAI's web-search tool is a second, roughly equal-cost option worth naming**, because this codebase already has a funded, wired, compliance-tracked OpenAI integration (`translate_batch`, T-077's `test_openai_call_sites.py` inventory) — using it here means no new vendor account, no new API key, no new billing relationship to onboard. Pricing checked live 2026-08-27: **$10 per 1,000 tool calls** plus token cost (search-result content is billed as a fixed ~8,000-input-token block per call, ≈$0.0012 at gpt-4o-mini rates — negligible next to the tool fee). For 4,319 lookups: **≈$47–52 one-time**, essentially the same as Serper's $50 pack. The one thing to get right: prompt it to return a URL **only when grounded in an actual search result**, and still run that URL through the same `classify_website()`/`same_site()` verification as any other candidate — a model asked "what's this salon's website" without search grounding will confidently hallucinate a plausible-looking domain, which is a worse failure than an ungrounded SERP link, since it can look like a real hit and isn't.
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
- **Use Claude for Chrome (browser-automation agent) to search for each salon's website instead of a paid API.** Rejected: it's an interactive, human-supervised assistant, not built for an unattended batch of ~4,300 sequential lookups (order-of-days wall-clock at that scale, one query at a time); running it that way against Google's search UI is functionally the same automated-SERP-querying this RFC already rejected as a default (real ToS exposure, same as scraping result pages directly) — it doesn't change the mechanism, only which tool drives the browser; and it still wouldn't remove the need for the same `classify_website()`/`same_site()` own-site verification per candidate, since a browser agent's search result is exactly as unverified as an API's. The Serper.dev cost this RFC already prices (~$45–50 one-time) is cheaper and safer than the compute cost of running an agentic browser session per salon at this volume.
- **Use the interactive ChatGPT app (not the API) as the production mechanism — feed it batches of salon names, get back a CSV of website/image URLs.** Same category of rejection as the Chrome-agent option, for the same underlying reason: it's a human-driven chat session, not an automatable pipeline. At production scale (2,577–6,896 salons) it means an operator manually pasting batches into a chat window, waiting on each response, and copy-pasting results out — no API call, no scheduling, no unattended run, and no write path into Lookla's own DB (the output is a CSV a human still has to review and a separate ingestion step still has to consume — effectively rebuilding `website_run.py`'s apply logic downstream of a manual export). It also has no `classify_website()`/`same_site()`-equivalent verification and no robots.txt/rate-limit discipline under our own bot identity. **Genuinely useful for a different purpose, though:** since it costs nothing beyond an already-paid ChatGPT subscription and a few minutes, it's a good free way for the Product Owner to sanity-check expected output quality on a handful of real salons *before* any spend or implementation — exactly the "test 5–10 first" step it itself proposes. It also implicitly bundles AI-vision-based photo classification (interior/facade/team vs. stock/logo) which is more capable than this RFC's phase-1 heuristic filter (Decision 2) — worth knowing as a data point for whether heuristics prove sufficient, but not something to commit to at production scale until it can run unattended via API, with its own per-image cost estimated the same way the search-vendor cost was.

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
| Search-vendor cost (Option A's discovery half) | **≈$45–52 one-time, either of two comparable options**: Serper.dev (2,500 of 4,319 lookups free via trial, remainder on the smallest $50/50,000-credit pack), or OpenAI's web-search tool ($10/1,000 calls + negligible token cost ≈$47–52, no new vendor since OpenAI is already integrated). No recurring cost either way — one lookup per salon, not a subscription. Google CSE is unusable (closed to new customers, discontinued 2027); Brave dropped its free tier in Feb 2026 and would run ~$21 with no spending cap. |
| Maintenance burden | Low — extends existing, already-maintained pipelines |

## Dependencies

None for Option B. A future search-discovery phase depends on funding a Serper.dev account (~$50 one-time prepaid pack — the only viable option checked live 2026-08-27; Google CSE is closed to new customers, Brave has no spending cap) — no further vendor research needed once that spend is approved.

## Risks

- **Misattribution:** extracting a photo from the wrong business's site. Bounded in Option B by only crawling URLs already sitting in `salons.website` (operator- or crawler-confirmed, not a fresh unverified search hit) and reusing T-088's existing `classify_website()`/`same_site()` own-site verification before trusting a page at all.
- **Quality regression:** a heuristic-only filter admits an off-brand or low-quality photo (e.g. a sponsor logo, a stock banner) that a human would reject. Mitigated by soft-replace (reversible) and a conservative filter tuned narrow rather than broad on first pass.
- **Bot politeness at scale:** photo extraction adds requests (gallery pages, image fetches) on top of T-088's existing 2s-delay single-page crawl — needs its own rate-limit budgeting so it doesn't look like a heavier bot to the same 1,677+ sites already crawled once.
- **Rollback:** pure addition + soft-replace — revertible in one PR, no risk to existing aggregator photos, which stay in the DB either way.

## Pilot Results (2026-08-27)

Before committing to Decision 1, ran a manual, zero-cost pilot: 500 real active salons (100 `known`-website, for calibration against ground truth already in our DB; 400 `unknown`-website, the actual target population for a future search-discovery phase) handed to the interactive ChatGPT app with a fixed output schema, then verified independently here — not taken on trust, per this project's own "green ≠ actually checked" discipline. Full data: `images_from_gpt/websites_final.csv`, `images_from_gpt/images_final.csv` (gitignored, not committed — real production `salon_id`s and a third party's raw output, kept local).

**Headline numbers, self-reported vs. independently verified — they matched:** 95 confirmed + 5 uncertain + 400 not_found = 500/500. No discrepancy between what the tool claimed and what the files actually contained.

**Known-group calibration (n=100, we already have the answer):** 83 confirmed + 4 uncertain, 13 not_found. Of the 87 non-`not_found`, 86 matched our existing `website` column exactly (after normalizing scheme/`www`/trailing slash) and 1 was a genuine, real upgrade — salon 11356 (Fairynails): our stored URL was a Treatwell booking widget, the pilot found the real `fairynails.gr`. **Take-away:** the method doesn't invent false answers on cases we can check, but it misses 13% of websites we already know exist — a real recall gap, not just a discovery-side limitation.

**Unknown-group yield (n=400, the actual Decision-1-Option-A population):** only **12 confirmed + 1 uncertain out of 400 — a 3.25% raw hit rate.** Of those 13, 4 turned out to be wrong-category on inspection (a hotel spa page ×2, a supermarket chain site, a residential complex) — leaving **9 plausible real beauty-business matches out of 400**, before any of our own verification.

**Independent live verification of a 5-URL sample from that unknown-group "confirmed" set** (plain HTTP check, our own `LooklaBot` UA): 3 resolved and loaded correctly; **2 — `deluxe.com.gr` and `exadaktilos.com`, both labeled `confirmed`, both with an evidence URL pointing at a third-party directory listing rather than the domain itself — failed outright with DNS `Could not resolve host`.** A 40% failure rate on this small sample is not something to extrapolate precisely, but it is a concrete demonstration, not a hypothetical one: **`confirmed` alone is not trustworthy enough to write to production without our own verification pass** — exactly what Decision 2's `classify_website()`/`same_site()` requirement already assumed, now confirmed necessary rather than merely prudent.

**Data-quality finding, orthogonal to this RFC but discovered because of it:** across the full 500, **35 of the 100 confirmed/uncertain matches (35%) are for a hotel, resort, restaurant, supermarket, or other non-salon business** already sitting in `salons.website` in production. Roughly two-thirds of those are hotel/resort spas — a genuinely ambiguous category (a hotel spa can be a real, bookable, walk-in beauty business, or it can be a guests-only amenity with no business being in this catalogue at all — this RFC does not resolve which). The unambiguous remainder (~11 of 100 — a restaurant, a rock bar, retail, serviced apartments, a residential complex, and **the same supermarket chain, Sklavenitis, appearing as two separate `salon_id`s**, both resolving to the chain's own site) has no such ambiguity: these are not beauty businesses by any reading, and were already live in the catalogue before this pilot touched anything. Checked downstream: **8 of the pilot's 48 photo rows (17%) point at pages belonging to these flagged non-salon businesses** — i.e., a blind import of this batch's photos would have put hotel/resort interior shots on 8 salon pages under a `source='website'` label implying they were verified. This is the clearest evidence yet for why Decision 2's soft-replace + verification gate is load-bearing, not a formality, and it's a strong argument for adding a category sanity check as its own explicit step (not currently listed under Decision 2 — should be added regardless of which Decision 1 option is chosen), separate from whether a URL is real.

**What this changes about Decision 1:** the search-discovery half's real yield is much smaller than 4,319 salons might suggest — roughly 1–3% clean, verified new websites (a few dozen to ~130 salons, not thousands), each still needing the same per-candidate verification this RFC already prices in engineering time. That doesn't make Option A worthless (the Serper/OpenAI cost is trivial either way, ~$50, and every genuine find like Fairynails is a real win), but it does mean the discovery half is a **long tail of small wins requiring careful per-result verification**, not a bulk win — reinforcing, with real numbers now instead of a judgment call, this RFC's original recommendation to ship Option B (known-website salons) first and treat search-discovery as a deliberately modest follow-up rather than bundling both into one release.

**Recommendation for a follow-up ticket, separate from this RFC:** audit the scale of wrong-category contamination in `salons`/`photos` beyond this 500-salon sample — the Sklavenitis double-entry suggests this may be a systematic import artifact (e.g. a POI category from Google Places bleeding across multiple branches of the same non-salon chain), not isolated noise.

## Decision

Decision: PENDING
Reason: —
Conditions (if any): —
Decision ID: —
Date: —
