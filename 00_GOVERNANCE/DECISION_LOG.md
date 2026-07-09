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

---

### DEC-008 — MVP Success Metric

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
MVP requires a measurable success criterion to know when validation is complete. Financial metrics are excluded per current stage (DEC-001).

**Decision**
Primary metric: **500 verified user interactions with salons within the first 90 days.**

A verified interaction is any of:
- Click on phone number
- Click on WhatsApp button
- Click on website link
- Booking request (when available)

Secondary metrics:
- 100 salons listed in Athens focus area
- 30 salons with claimed profiles
- 10% visitor → contact conversion rate

**Reason**
At this stage there are no calendars, payments, or booking infrastructure user-facing. The hypothesis is "do people find Lookla useful for discovery?" Contact actions are the strongest signal of intent without requiring a full booking engine.

**Consequences**
- Analytics must be in place before MVP launch (see DEC-017)
- Contact button clicks must be tracked as events
- 90-day window starts from first real marketing push, not from deployment date

**Implementation status**
[ ] Analytics integration required before tracking is possible (DEC-017)

**Affected documents**
- `01_PRODUCT/MVP_DEFINITION.md`
- `05_ROADMAP/ROADMAP.md`

---

### DEC-009 — Primary MVP Persona

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
Multiple potential user types exist. Designing for all equally means optimizing for none.

**Decision**
Primary target: **local residents** (not tourists).

Priority order:
1. **P-02** — Russian/Ukrainian-speaking residents (strongest differentiation, underserved)
2. **P-01** — Greek-speaking residents
3. **P-03** — English-speaking expats
4. **P-04** — Tourists (out of MVP scope)

**Reason**
Tourists visit once. A salon needs repeat local clients. The Russian/Ukrainian-speaking segment in Athens is large, underserved by existing Greek-language tools, and has strong word-of-mouth network effects within communities. This persona has the highest potential for organic growth without marketing spend.

**Consequences**
- Russian/Ukrainian translation quality is the highest QA priority
- Multilingual UX must be first-class, not an afterthought
- WhatsApp contact is critical for P-02 (prefers messaging over calls in Greek)
- Tourist-specific features (geo-by-current-location, "open now" prominence) are secondary for MVP
- SEO in Russian for terms like "маникюр Афины" becomes a priority

**Implementation status**
[ ] QA review of Russian/Ukrainian translations needed
[ ] WhatsApp CTA prominence review needed

**Affected documents**
- `01_PRODUCT/PERSONAS.md`
- `01_PRODUCT/USER_JOURNEYS.md`
- `01_PRODUCT/MVP_DEFINITION.md`

---

### DEC-010 — Location Hierarchy: Area over City

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
The current "City" filter returns `address_city` values from crawled data, which contain districts (Kallithea, Glyfada, Marousi) as separate "cities." A user searching for salons in Athens sees only central Athens results — missing the entire metro area. This is a trust-breaking UX issue.

**Decision**
Replace the flat "City" filter with a **location hierarchy**:

```
Country (Greece)
  └ Region (e.g. Attica, Thessaloniki, Crete)
     └ City (e.g. Athens, Piraeus)
        └ District / Area (e.g. Kolonaki, Glyfada, Kallithea, Marousi)
```

For beauty services, users search by **District/Area** — not by city. The filter label must reflect this.

**Reason**
In Athens, people say "I want a salon in Glyfada" not "I want a salon in Athens." The current model conflates these, producing wrong results and eroding user trust in the first search interaction.

**Consequences**
- Data model change required: map existing `address_city` values to the new hierarchy
- UI change: replace single city dropdown with area selector (potentially hierarchical)
- This affects all 4 languages — filter labels and area names must be translated
- Significant data quality work: ~6300 salons must be re-classified
- This is a **pre-MVP blocker** for the Athens focus (DEC-012)

**Implementation status**
[ ] Data mapping: classify existing `address_city` values into Region/City/District
[ ] UI: replace city filter with area/district selector
[ ] Copy: update filter labels in el/en/ru/uk

**Affected documents**
- `03_PAGES/SEARCH.md`
- `01_PRODUCT/PRODUCT_TERMINOLOGY.md` (City / Region / District definitions)
- `06_ENGINEERING/AUDIT.md` (known mismatch)

---

### DEC-011 — Language Priority for MVP

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
All 4 languages (el/en/ru/uk) are implemented. Equal priority means equal QA burden but unequal user value.

**Decision**
- **Greek (el):** Mandatory. Core market.
- **English (en):** Mandatory. International standard; expats and business communication.
- **Russian (ru):** Mandatory for MVP. Primary underserved audience (DEC-009).
- **Ukrainian (uk):** Optional for MVP. Implemented but lower QA priority than ru.

**Reason**
Russian and Ukrainian speakers are closely related communities in Athens, but Russian has significantly higher volume. Ukrainian is valuable and already built — it ships — but translation QA effort is allocated to el/en/ru first.

**Consequences**
- Translation QA must cover el/en/ru before MVP launch
- uk translations may contain imperfections at MVP — acceptable
- All 4 languages remain in the product; this is a QA priority, not a feature removal

**Implementation status**
[ ] Manual QA of Russian UI strings and translated content sample

**Affected documents**
- `01_PRODUCT/MVP_DEFINITION.md`
- `01_PRODUCT/PERSONAS.md`

---

### DEC-012 — Geographic Focus: Athens First

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
The database contains ~6300 salons across all of Greece. Spreading validation effort nationally risks thin coverage everywhere and strong coverage nowhere.

**Decision**
**MVP validates in Athens metropolitan area only.**

National data remains in the database and is accessible, but:
- Data quality efforts focus on Athens salons
- Marketing for MVP targets Athens audience
- Success metrics (DEC-008) are measured against Athens interactions

**Reason**
Marketplace dynamics: 100 excellent Athens salons with accurate data deliver more user value than 5000 thin national listings. Athens has the highest density of the P-02 persona (Russian/Ukrainian community).

**Consequences**
- Data quality review prioritizes Athens salons
- Location hierarchy (DEC-010) must cover all Athens districts correctly
- National salons remain accessible but are not the quality-controlled focus
- Post-MVP: expand to Thessaloniki, then other regions

**Implementation status**
[ ] Athens salon data audit needed (hours accuracy, phone numbers, photos)

**Affected documents**
- `01_PRODUCT/MVP_DEFINITION.md`
- `05_ROADMAP/ROADMAP.md`

---

### DEC-013 — Review Source Labeling

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
Reviews currently shown are aggregated from Google. No label indicates this. Users may assume reviews are from Lookla clients. This is a trust integrity issue and conflicts with the "no fake activity" principle (DEC-003).

**Decision**
All aggregated reviews must be labeled with:
- **Source:** Google Reviews
- **Imported:** Yes
- **Original:** No (i.e., not written by Lookla users)

**Reason**
Creating any impression that aggregated data is platform-native violates the core value of honesty established in the Product Vision and DEC-003.

**Consequences**
- UI change required on salon detail page: add review section header or per-review label
- Applies to all 4 languages
- When Lookla-native reviews exist in future, they must be visually distinguished from imported reviews

**Implementation status**
[ ] UI update: add "Source: Google Reviews" label to review section on salon detail page

**Affected documents**
- `03_PAGES/SALON.md`
- `01_PRODUCT/PRODUCT_TERMINOLOGY.md` (Aggregated Review vs Owned Review)

---

### DEC-014 — Verified Badge Replacement

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
The current ✓ badge on salon cards means `is_verified = true` (set by admin or on claiming). Users interpret ✓ as "owner-verified business." This is a trust signal mismatch — it implies more certainty than the data supports.

**Decision**
The ✓ badge is **replaced** with explicit labeling that reflects what was actually verified:

- **"Information reviewed"** — when admin has checked the listing data
- **"Owner verified"** — only when Salon Owner has completed the full Claim + Verification process
- **No badge** — default state for unclaimed, unreviewed listings

The badge must never imply ownership verification when only admin review has occurred.

**Reason**
A misleading trust signal is worse than no trust signal. If users discover the badge doesn't mean what they think, it erodes confidence in all platform data.

**Consequences**
- UI change: replace ✓ with text label or two-tier badge system
- Backend: `is_verified` flag must be split or supplemented (admin-reviewed vs owner-verified)
- This is a **pre-MVP blocker** for the salon detail page

**Implementation status**
[ ] UI: replace ✓ badge with explicit label
[ ] Backend: clarify `is_verified` meaning or add `is_admin_reviewed` flag

**Affected documents**
- `03_PAGES/SALON.md`
- `01_PRODUCT/PRODUCT_TERMINOLOGY.md` (Verified / Verification)
- `06_ENGINEERING/AUDIT.md` (known mismatch)

---

### DEC-015 — CTA Buttons: No Fake Booking

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
The salon detail page currently shows booking CTA buttons that are non-functional stubs. Per Charter §9, stubs are only acceptable if clearly non-functional. A "Book" button that does nothing destroys first-impression trust.

**Decision**
Remove all fake booking CTAs from MVP. Replace with honest contact actions:

**Allowed CTAs:**
- "Call salon" (phone)
- "Message on WhatsApp"
- "Visit website"
- "Request appointment" (only when a real availability request flow exists)

**Prohibited CTAs in MVP:**
- "Book now"
- "Reserve"
- "Schedule"
- Any button that implies an automated booking system that does not exist

**Reason**
A user who taps "Book now" and nothing happens immediately loses trust. This is not recoverable in a first impression. Honest contact CTAs deliver real value without false promises.

**Consequences**
- UI change: remove or replace booking stub buttons on salon detail page
- This is a **pre-MVP blocker**
- When real booking is implemented, CTAs are added back — not before

**Implementation status**
[ ] UI: remove booking stubs, replace with contact action buttons

**Affected documents**
- `03_PAGES/SALON.md`
- `04_ARCHITECTURE/FEATURE_FLAGS.md`

---

### DEC-016 — Registration Not Required for Discovery or Contact

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
Decision on whether users must register to access contact information (phone, WhatsApp) or to use the platform at all.

**Decision**
- **View listings:** ✅ No registration required
- **Call salon (see phone number):** ✅ No registration required
- **WhatsApp salon:** ✅ No registration required
- **Save / Favorite a listing:** 🔒 Registration required

**Reason**
At MVP stage, friction before the core value (finding a salon) reduces the chance of validating the product. The primary hypothesis (DEC-008) measures contact actions — requiring registration before contact would suppress this signal and make the metric unmeasurable.

**Consequences**
- Current implementation is already anonymous — this confirms and locks the behavior
- Favorites/save feature (when built) must require login
- User registration is a path for returning users, not a gate for new ones

**Implementation status**
[x] Already implemented correctly — anonymous access to all discovery and contact features

**Affected documents**
- `01_PRODUCT/MVP_DEFINITION.md`
- `03_PAGES/SALON.md`

---

### DEC-017 — Analytics Stack for MVP

| Field | Value |
|---|---|
| Date | 2026-07-09 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**
Without analytics, DEC-008 success metrics cannot be measured. MVP cannot be validated without data.

**Decision**
Analytics stack for MVP:

| Tool | Purpose | Priority |
|---|---|---|
| **Google Analytics 4** | Core event tracking (contact clicks, page views, sessions) | Required before MVP launch |
| **Google Search Console** | Organic search performance, keyword rankings | Required before MVP launch |
| **Microsoft Clarity or Hotjar** | Session recordings, heatmaps | Optional for MVP; add post-launch |

GA4 is the primary tool. All DEC-008 metrics (contact clicks, visitor→contact conversion) must be tracked as GA4 events.

**Reason**
GA4 is the industry standard with the widest ecosystem support. Search Console is free and essential for understanding organic traffic — the primary acquisition channel at zero marketing spend. Clarity/Hotjar adds qualitative insight without additional cost (Clarity is free).

**Consequences**
- GA4 integration is a **pre-MVP blocker** — without it, no metric from DEC-008 can be measured
- Contact button clicks (phone, WhatsApp, website) must fire GA4 events
- Privacy policy must be updated to reflect GA4 data collection
- This is a code change in the frontend

**Implementation status**
[ ] GA4 property created and tracking ID obtained
[ ] GA4 snippet added to Next.js layout
[ ] Contact click events instrumented
[ ] Search Console property verified
[ ] Privacy policy updated

**Affected documents**
- `01_PRODUCT/MVP_DEFINITION.md`
- `03_PAGES/SALON.md`

---

*Last updated: 2026-07-09*
