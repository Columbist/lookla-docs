# AI_CONTEXT.md — Lookla Project Context
**Entry point for AI assistants (Claude, GPT, Copilot, etc.)**

> Read this file first. It gives you the current state of the project in under 2 minutes.
> After reading this file, read the documents listed in "Where to start."

---

## Project

**Name:** Lookla  
**Type:** Beauty discovery marketplace for Greece  
**URL:** lookla.gr  
**Owner:** Andrey (columb@europe.com)  
**Documentation repo:** github.com/Columbist/lookla-docs (public)  
**Full monorepo:** github.com/Columbist/lookla-platform (private)

---

## What Lookla is

A multilingual directory of beauty salons, barbershops, spas, and independent professionals in Greece. Clients search by area, category, and language. The platform serves users in Greek, English, Russian, and Ukrainian.

Current data: ~6300 salons, aggregated from public sources (crawlers). No fake data. No paid listings.

---

## Current Phase

**M-01 — MVP Athens Launch. In Progress.**

Product decisions are approved (DEC-008 to DEC-017). Implementation can begin against the approved scope.

The MVP Definition is approved. The Scope Lock is set. The next step is implementing the pre-launch checklist in `01_PRODUCT/MVP_SCOPE_LOCK.md`.

---

## What is Approved (source of truth)

| Document | What it defines |
|---|---|
| `00_GOVERNANCE/PROJECT_CHARTER.md` | Highest authority. All rules. Read this first. |
| `00_GOVERNANCE/DECISION_LOG.md` | All official decisions (DEC-001 to DEC-017) |
| `01_PRODUCT/PRODUCT_SCOPE.md` | What Lookla IS and IS NOT |
| `01_PRODUCT/PRODUCT_VISION.md` | Why Lookla exists, who it's for, differentiators |
| `01_PRODUCT/PRODUCT_TERMINOLOGY.md` | Official dictionary — use these terms in all documents |
| `01_PRODUCT/MVP_DEFINITION.md` | Approved MVP scope, decisions, readiness checklist |
| `01_PRODUCT/MVP_SCOPE_LOCK.md` | Locked boundary — what MVP WILL and WILL NOT have |
| `04_ARCHITECTURE/AI_STRATEGY.md` | AI features postponed; translation is infrastructure |
| `06_ENGINEERING/AUDIT.md` | Full technical audit of current implementation |

---

## What is Draft (not yet approved)

| Document | Blocking question |
|---|---|
| `01_PRODUCT/PERSONAS.md` | Needs status update to Approved — DEC-009 resolves primary persona |
| `01_PRODUCT/USER_JOURNEYS.md` | Needs status update to Approved — all blocking decisions are resolved |
| `03_PAGES/SEARCH.md` | Needs update for DEC-010 location hierarchy |
| `03_PAGES/SALON.md` | Needs update for DEC-013 reviews, DEC-014 badge, DEC-015 CTA |
| `02_DESIGN/*` | No design system approved yet |

---

## All Decisions (DEC-001 to DEC-017)

| ID | Decision | Status |
|---|---|---|
| DEC-001 | Private project, no company, no monetization, no advertising | Approved |
| DEC-002 | Documentation-first: no implementation without approved docs | Approved |
| DEC-003 | No fake data, reviews, ratings, or activity of any kind | Approved |
| DEC-004 | Every feature requires evidence of user need before implementation | Approved |
| DEC-005 | AI product features postponed until measurable user value confirmed | Approved |
| DEC-006 | Stripe/subscriptions exist in code but must not be user-facing | Approved |
| DEC-007 | Monorepo: docs live with code in `lookla-platform` | Approved |
| DEC-008 | MVP success = 500 verified contact interactions in 90 days | Approved |
| DEC-009 | Primary persona: local residents; P-02 (ru/uk) → P-01 (el) → P-03 (expat); tourists last | Approved |
| DEC-010 | Location hierarchy: Country → Region → City → District; replace "City" filter label | Approved |
| DEC-011 | el/en/ru mandatory for MVP; uk optional (ships, lower QA priority) | Approved |
| DEC-012 | Athens metropolitan area first for MVP validation | Approved |
| DEC-013 | Keep Google reviews; label: "Source: Google Reviews / Imported: Yes / Original: No" | Approved |
| DEC-014 | Replace ✓ with "Information reviewed" (admin) or "Owner verified" (claimed); no badge = default | Approved |
| DEC-015 | Remove booking stubs; replace with "Call salon" / "Message on WhatsApp" / "Visit website" | Approved |
| DEC-016 | View/call/WhatsApp = anonymous; Save/favorites = registration required | Approved |
| DEC-017 | GA4 + Search Console required before launch; Clarity/Hotjar optional post-launch | Approved |

---

## Current Product Decisions: All Resolved

| Question | Decision | Reference | Impact |
|---|---|---|---|
| Q-01 — MVP success metric | 500 contact clicks in 90 days | DEC-008 | Defines analytics requirements and launch gate |
| Q-02 — Primary persona | P-02 (Russian/Ukrainian) first, then P-01 (Greek) | DEC-009 | ru QA priority; WhatsApp prominence; tourist features deferred |
| Q-03 — City filter | Full area hierarchy; district-level search | DEC-010 | Data reclassification + UI change required |
| Q-04 — Language priority | el/en/ru mandatory; uk optional | DEC-011 | QA allocation before launch |
| Q-05 — Geographic focus | Athens first | DEC-012 | Data quality focus; 100 salons reviewed |
| Q-06 — Review labeling | Show with Google source label | DEC-013 | UI change on salon detail page |
| Q-07 — Verified badge | Replace ✓ with text label | DEC-014 | UI change + backend `is_verified` clarification |
| Q-08 — Booking CTA | Remove stubs; real contact CTAs only | DEC-015 | UI change on salon detail page |
| Q-09 — Registration | Anonymous for discovery; required only for favorites | DEC-016 | Current implementation is correct — confirmed |
| Q-10 — Analytics | GA4 + Search Console required before launch | DEC-017 | Code change in frontend; privacy policy update |

**Status: All 10 questions resolved. No product decisions are currently blocking.**

---

## Pre-Launch Implementation Blockers

The following implementation tasks must be complete before M-01 can launch:

| Item | Decision | Status |
|---|---|---|
| Location hierarchy (area/district filter) | DEC-010 | ⬜ Not started |
| Review source label on salon detail page | DEC-013 | ⬜ Not started |
| Verified badge → text label | DEC-014 | ⬜ Not started |
| Booking stubs removed; contact CTAs only | DEC-015 | ⬜ Not started |
| GA4 installed + contact events tracked | DEC-017 | ⬜ Not started |
| Search Console verified | DEC-017 | ⬜ Not started |
| Privacy policy updated | DEC-017 | ⬜ Not started |
| Athens data quality (100+ salons) | DEC-012 | ⬜ Not started |
| Russian translation QA (sample) | DEC-011 | ⬜ Not started |
| /pricing and /plans: not in navigation | DEC-006 | ⬜ Unverified |

---

## Known Mismatches (implementation ≠ documentation)

| Mismatch | Decision that resolves it |
|---|---|
| ✓ badge means "admin reviewed" not "owner verified" | DEC-014 — replace with text label |
| Reviews show without "Source: Google" label | DEC-013 — add source label |
| City filter says "City" but returns districts | DEC-010 — implement area hierarchy |
| Booking stub buttons visible on salon page | DEC-015 — remove, replace with contact CTAs |
| `/pricing` page exists — may be linked (unverified) | DEC-006 — verify and remove from navigation if linked |

---

## What NOT to do

- Do not implement features without an approved RFC in `07_RFC/`
- Do not mark any document `Approved` without Product Owner confirmation
- Do not resolve mismatches by silently changing code or docs — report them
- Do not invent personas, journeys, or product decisions
- Do not expose Stripe, subscriptions, or monetization to users
- Do not add fake data or fake activity signals
- Do not add geo search "near me" UI (tourists deprioritized per DEC-009)
- Do not add AI-generated content or AI ranking (DEC-005)

---

## Next Milestone

**M-01 — MVP Athens Launch**  
Status: **In Progress**  
Reference: `05_ROADMAP/ROADMAP.md`  
Launch gate: `01_PRODUCT/MVP_SCOPE_LOCK.md`

All product decisions are resolved. Implementation of the pre-launch checklist can begin.

After M-01 completes (500 contact interactions measured): plan M-02 based on evidence from M-01.

---

## Where to Start

For any AI assistant entering this project:

1. Read `00_GOVERNANCE/PROJECT_CHARTER.md` — the rules
2. Read `01_PRODUCT/MVP_SCOPE_LOCK.md` — exactly what MVP includes and excludes
3. Read `01_PRODUCT/MVP_DEFINITION.md` — the approved decisions with context
4. Read `00_GOVERNANCE/DECISION_LOG.md` — all formal decisions
5. Read `06_ENGINEERING/AUDIT.md` — what is actually built (if engineering context is needed)

---

## Tech Stack (brief)

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), Tailwind CSS, next-intl |
| Backend | FastAPI (Python 3.12), SQLAlchemy, PostgreSQL 16 |
| Infrastructure | Docker Compose, Nginx, Cloudflare, R2 CDN |
| AI | OpenAI gpt-4o-mini (translation infrastructure only) |
| Payments | Stripe (configured, not user-facing per DEC-006) |
| Auth | Cookie-based JWT + Google OAuth |

Full technical detail: `06_ENGINEERING/AUDIT.md`

---

*Last updated: 2026-07-09*  
*Update this file whenever a major decision changes the project state.*
