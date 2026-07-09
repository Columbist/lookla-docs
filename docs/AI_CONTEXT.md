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

A multilingual directory of beauty salons, barbershops, spas, and independent professionals in Greece. Clients search by city, category, and language. The platform serves users in Greek, English, Russian, and Ukrainian.

Current data: ~6300 salons, aggregated from public sources (crawlers). No fake data. No paid listings.

---

## Current Phase

**Product definition.** The platform is built and deployed. The product decisions that should have preceded the build are now being documented formally.

The immediate task is: define the MVP formally so the next development phase is driven by approved decisions, not engineering intuition.

---

## What is Approved (source of truth)

| Document | What it defines |
|---|---|
| `00_GOVERNANCE/PROJECT_CHARTER.md` | Highest authority. All rules. Read this first. |
| `00_GOVERNANCE/DECISION_LOG.md` | All official decisions (DEC-001 to DEC-007) |
| `01_PRODUCT/PRODUCT_SCOPE.md` | What Lookla IS and IS NOT |
| `01_PRODUCT/PRODUCT_VISION.md` | Why Lookla exists, who it's for, how it differs from Google Maps / Fresha / Booksy / Treatwell |
| `01_PRODUCT/PRODUCT_TERMINOLOGY.md` | Official dictionary — use these terms in all documents |
| `04_ARCHITECTURE/AI_STRATEGY.md` | AI features postponed; current translation is infrastructure |
| `06_ENGINEERING/AUDIT.md` | Full technical audit of current implementation |

---

## What is Draft (needs Product Owner decisions)

| Document | Blocking question |
|---|---|
| `01_PRODUCT/MVP_DEFINITION.md` | 10 open questions (Q-01 to Q-10) — MVP cannot be approved without them |
| `01_PRODUCT/PERSONAS.md` | Which persona is primary for MVP? |
| `01_PRODUCT/USER_JOURNEYS.md` | Depends on persona priority and city filter decision |
| `03_PAGES/SEARCH.md` | City filter label decision (Q-03) |
| `03_PAGES/SALON.md` | Review labeling (Q-06), verified badge (Q-07), booking CTA (Q-08) |
| `02_DESIGN/*` | No design system approved yet |
| `05_ROADMAP/ROADMAP.md` | No milestones approved yet |

---

## Current Decisions (DEC-001 to DEC-007)

| ID | Decision |
|---|---|
| DEC-001 | Private project, no company, no monetization, no advertising |
| DEC-002 | Documentation-first: no implementation without approved docs |
| DEC-003 | No fake data, reviews, ratings, or activity of any kind |
| DEC-004 | Every feature requires evidence of user need before implementation |
| DEC-005 | AI product features postponed until measurable user value confirmed |
| DEC-006 | Stripe/subscriptions exist in code but must not be user-facing |
| DEC-007 | Monorepo: docs live with code in `lookla-platform` |

---

## Current Blockers

The following decisions are required from the Product Owner before development can proceed on MVP:

1. **Q-01** — MVP success metric: what proves the MVP worked?
2. **Q-02** — Primary persona: Greek local, Russian/Ukrainian resident, or English tourist?
3. **Q-03** — City filter: rename to "Area"? Group districts? Leave as-is?
4. **Q-04** — Language priority for MVP: all equal or ru/uk first?
5. **Q-05** — Geography: national or Athens-first for validation?
6. **Q-06** — Review labeling: show Google as source?
7. **Q-07** — Verified badge: keep, remove, or rename?
8. **Q-08** — Booking CTA: remove stubs or label "coming soon"?
9. **Q-09** — Registration: required to see contact info?
10. **Q-10** — Analytics: GA4, Plausible, or none for MVP?

All questions are documented in `01_PRODUCT/MVP_DEFINITION.md`.

---

## Known Mismatches (implementation ≠ documentation)

These are not bugs — they are product decisions that need to be made:

| Mismatch | Location |
|---|---|
| `is_verified` badge means "admin reviewed" not "owner verified" | SALON.md, PRODUCT_TERMINOLOGY.md |
| Reviews show as-is without "Source: Google" label | SALON.md |
| City filter says "City" but returns districts | SEARCH.md, PRODUCT_TERMINOLOGY.md |
| `/pricing` page exists — must not be linked per DEC-006 (unverified) | DECISION_LOG.md DEC-006 |

---

## What NOT to do

- Do not implement features without an approved RFC in `07_RFC/`
- Do not mark any document `Approved` without Product Owner confirmation
- Do not resolve mismatches by silently changing code or docs — report them
- Do not invent personas, journeys, or product decisions
- Do not expose Stripe, subscriptions, or monetization to users
- Do not add fake data or fake activity signals

---

## Next Milestone

**M-01 — MVP Definition Approved**  
Status: Not started  
Requires: All 10 questions in `MVP_DEFINITION.md` answered and logged as DEC-008+

After M-01: design and implementation can proceed against an approved spec.

---

## Where to Start

For any AI assistant entering this project:

1. Read `00_GOVERNANCE/PROJECT_CHARTER.md` — the rules
2. Read `01_PRODUCT/MVP_DEFINITION.md` — the current state and open questions
3. Read `01_PRODUCT/PRODUCT_SCOPE.md` + `01_PRODUCT/PRODUCT_VISION.md` — what the product is
4. Read `06_ENGINEERING/AUDIT.md` — what is actually built (if engineering context is needed)
5. Check `00_GOVERNANCE/DECISION_LOG.md` before making any recommendation

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
