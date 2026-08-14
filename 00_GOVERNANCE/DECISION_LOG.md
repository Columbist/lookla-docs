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
| Status | APPROVED — wording superseded in part by DEC-024 (2026-08-14); the disclosure requirement itself still stands |
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

### DEC-018 — Legal positions taken by the operator, without a lawyer's opinion

| Field | Value |
|---|---|
| Date | 2026-08-11 |
| Status | APPROVED |
| Decided by | Operator |

**Context**

`T-045_REMAINING_QUESTIONS.md` and `TERMS_LEGAL_EXTRACT.md` were prepared for review by a Greek lawyer. Answers were returned on 2026-08-11. Asked whether they were a lawyer's opinion, the operator instructed that they be recorded as **the operator's own decisions**.

That distinction is recorded rather than smoothed over, because the two are not interchangeable: an opinion transfers a judgement to someone qualified to make it, and a decision keeps it. Nothing here says the positions are wrong.

**Decision**

The following are the operator's positions, adopted without an external opinion:

| Position | Taken as |
|---|---|
| The §12 limitation is enforceable against a Greek consumer | Yes |
| §14 is compatible with Rome I and Brussels I recast | Yes |
| No specific Greek ADR body is named | Correct as drafted |
| 16 is appropriate as the product minimum age | Yes |
| Contractual capacity requires nothing further | Yes |
| Messaging does not change the age answer | Yes |
| No age verification or parental authorisation is required | Yes — no account can be created in this release |
| The DSA applies, category "providing information" | Yes |
| No size exemption applies | Yes |
| Article 14 is **not** satisfied by the present description | Yes |
| Notice-and-action and internal complaint handling must be built | Yes |
| The geographic address need not be published | Yes — and it is therefore absent from the frontend entirely |

**Reason**

Recorded by instruction. The operator has read the questions and taken the positions; no external opinion was obtained.

**Consequences**

- The two positions that create work stand: **T-084** builds notice-and-action, statements of reasons and internal complaint handling, because Article 14 cannot be satisfied by describing a system that does not exist.
- The publication gate for the Terms is **not** opened by this entry. `TERMS_PUBLICATION_ENABLED` remains `false`, and a test fails if it is set true while the backlog records no Greek legal review. Opening it on an operator decision instead is a separate, explicit change — see "Open" below.
- Three answers remain unusable as written and are not adopted here: what "It is" means about who builds the procedures, what "standard privacy" decides about an acceptance record, and what "we don't provide salon publicity in this release" covers. `T-045_ANSWERS.md` §3 keeps them open.

**Open**

Whether to publish the Terms on the operator's own reading, rather than waiting for an opinion, has not been decided. It is a change to the gate's condition, not a value, and needs its own entry here when it is made.

**Affected documents**

- `07_LEGAL/T-045_ANSWERS.md`
- `07_LEGAL/T-045_REMAINING_QUESTIONS.md`
- `05_ROADMAP/IMPLEMENTATION_BACKLOG.md` (T-084)

---

### DEC-019 — Publish the address, and settle the remaining questions the way comparable services do

| Field | Value |
|---|---|
| Date | 2026-08-11 |
| Status | APPROVED |
| Decided by | Operator |
| Supersedes | DEC-018, on the geographic address only |

**Context**

DEC-018 recorded, among the operator's positions, that the geographic address need not be published. `T-045_COMPARABLES.md` then read the live legal pages of Yelp, Trustpilot and (from search) Vrisko: **every one publishes a full postal address**, and none of them omits it. The operator adds that in Greek practice this address commonly becomes the registered address of an individual activity in any case.

**Decision**

1. **The geographic address is published:** `Megalou Alexandrou 38, Athens 16452, Greece`. It returns to the frontend module and to the publication gate's conditions, both of which had been changed the previous day to keep it out.
2. **The remaining open questions are settled the way comparable services settle them**, rather than left waiting:
   - **No acceptance checkbox and no version-stamped acceptance record.** Yelp accepts by continued use; Trustpilot lists a box as one route among several, not a requirement. This closes the "standard privacy" ambiguity of `T-045_ANSWERS.md` §3 in the direction the product already implements.
   - **DSA procedure lives in its own document**, linked from the Terms, rather than inside §9. Both comparables do this. T-084 builds a standalone notice-and-action page.
   - **"It is"** is read as *the procedures must be built* — which is what T-084 does and what the Article 14 answer requires either way.
3. **"We don't provide salon publicity in this release"** stays a statement of scope. Nothing in the product contradicts it: payments are off, there is no promoted placement, and owner editing is off.

**Reason**

Where a question has a settled market answer and no fact of ours makes it different, the market answer is adopted rather than waited on. Where our facts *are* different, they are not — see below.

**Consequences**

- `TERMS_PUBLICATION_ENABLED` is still `false`. Publishing the address makes the disclosure complete; it does not change what the gate asks for, which is a recorded review. Opening it needs its own entry.
- The comparables' documents inform structure and coverage only. Their wording is theirs, and all three are companies that took on the obligations of companies — the questions our facts raise are the ones their documents never had to answer.

**Affected documents**

- `frontend/app/[locale]/terms/content.ts`
- `07_LEGAL/T-045_COMPARABLES.md`, `07_LEGAL/T-045_ANSWERS.md`

---

### DEC-020 — Publish the Terms without a lawyer's opinion

| Field | Value |
|---|---|
| Date | 2026-08-11 |
| Status | APPROVED |
| Decided by | Operator |

**Context**

The Terms have been gated since T-045 on two conditions: a complete Article 5 disclosure, and a recorded Greek legal review. The first is now met — name, geographic address and a contact address for legally significant communication are published on the page itself, not merely held in the module. The second was never obtained: the answers of 2026-08-11 are the operator's own positions (DEC-018), and the remaining questions were settled by adopting what comparable services do (DEC-019).

**Decision**

Publish. `TERMS_PUBLICATION_ENABLED` is set to `true`, on the operator's decision and without a lawyer's opinion.

**Reason**

Recorded by instruction. The operator has read the questions, taken the positions, and judged that waiting on an opinion costs more than it removes.

**Consequences**

- `/terms` is served and the footer link appears, in all four locales.
- The gate itself is **not removed**. It now accepts two bases — a recorded legal review, or this entry — and a test fails if the flag is true with neither. Publishing without an opinion is a legitimate choice; publishing without anyone having decided is not, and that is what the check still prevents.
- **T-084 is unaffected.** Article 14 is answered "not satisfied", so notice-and-action, statements of reasons and internal complaint handling still have to be built, and §9 will be revised when they exist. Publishing the Terms today does not make that description accurate; it makes the gap visible on a live page.
- Nothing here is a view about whether the positions are right. It records who is answerable for them.

**Affected documents**

- `frontend/app/[locale]/terms/content.ts`, `frontend/lib/termsContent.test.ts`
- `07_LEGAL/T-045_ANSWERS.md`

---

### DEC-021 — Viber returns as a fourth contact action

| Field | Value |
|---|---|
| Date | 2026-08-12 |
| Status | APPROVED |
| Decided by | Operator |
| Supersedes | DEC-015, on the list of approved CTAs only |

**Context**

DEC-015 approved exactly three contact actions — Call, WhatsApp, Visit website — and T-010 implemented that list. A working Viber button existed at the time and was **removed** to match, down to deleting the `viber` key from all four locale files. Tests have enforced the absence since: `contactActions.test.ts` asserts exactly three action fields and bans the string "viber" from the component.

The operator's position, 2026-08-12: in Greece the primary contact channels are Viber, WhatsApp and Facebook Messenger, and **Viber's reach is greater than WhatsApp's**. A contact list that omits the most-used channel is not a shorter list, it is a worse one.

**Decision**

Viber is restored as a fourth action on the salon detail page. Call, WhatsApp, Visit website are unchanged.

**Reason**

DEC-015's purpose was to remove **fake** CTAs — buttons that did nothing. Viber is not that: it is a real channel, built from the same phone number as WhatsApp, reaching the same 5,964 salons on the day it ships. The rule it broke was "exactly three", and that number was a consequence of the approved list rather than a limit that was reasoned about.

**Consequences**

- The three-action contract in `lib/contactActions.ts` becomes four. The tests that enforce three are updated to enforce four, deliberately — they are not deleted, because their real subject is "no fake actions and no booking", which still holds.
- The `viber` locale key returns to all four locale files.
- Contact clicks are tracked per channel. Viber and WhatsApp must be counted separately, or the question this decision rests on — which channel Greeks actually use — stays unanswered.
- **An open question inherited, not created:** a phone number does not prove the number is on Viber, or on WhatsApp. We already show WhatsApp unconditionally, so this is not a new risk introduced by Viber; it is an existing one now visible twice. Whether to show these buttons only when the channel is confirmed is a separate decision, and it applies to both.

**Affected documents**

- `frontend/lib/contactActions.ts`, `frontend/components/ContactButtons.tsx`
- `05_ROADMAP/IMPLEMENTATION_BACKLOG.md` (T-086)

---

### DEC-022 — Favourites without registration, keyed by an opaque token

| Field | Value |
|---|---|
| Date | 2026-08-13 |
| Status | APPROVED |
| Decided by | Operator |
| Supersedes | DEC-016, on favourites only |

**Context**

DEC-016 settled that discovery and contact need no registration, and that favourites do. The operator's position of 2026-08-13 changes the second half: a visitor keeps favourites and their last ten viewed salons without creating anything, and an email or phone becomes a key they may give **later, if they want**, to move the list to another device.

**Decision**

Identity is an **opaque token** issued by us, held in the visitor's browser, carrying no personal data. Favourites and recent views hang off it. Email and phone are optional recovery keys, and reading a list by one requires proving control of it.

**Reason**

If a phone number were the key, anyone typing someone else's number would read their favourites — which salons a named person is interested in, alongside where those salons are. That is a disclosure designed in rather than a bug, and no care afterwards removes it. The token gives the same convenience while there is nothing to type.

**Consequences**

- Favourites work while accounts are switched off, and are deliberately **not** behind `feature_user_accounts` — this is what a visitor gets *instead of* an account.
- Recent views are trimmed to ten **in storage**, not only in the response. Keeping every view and showing ten would be a history nobody asked us to hold, invisible because the endpoint never shows it.
- `DELETE /api/visitor` erases everything held against a token, and exists from the first version. What we keep is small and voluntary; being unable to withdraw it would make it neither.
- `last_seen_at` gives retention a clock. The period itself is not decided here.
- **Appointments are out of scope** until there are confirmed salons — the operator's own sequencing.

**Open**

Attaching and verifying a recovery key is not built. It needs a delivery channel, which is the same unanswered question as T-085 — and the answer there now looks like the phone.

**Affected documents**

- `05_ROADMAP/IMPLEMENTATION_BACKLOG.md` (T-089)
- `04_ARCHITECTURE/PERSONAL_DATA_MATRIX.md` — three new tables to place

---
### DEC-023 — Visual Baseline v2: desktop composition redesign, conversion-baseline reset accepted

| Field | Value |
|---|---|
| Date | 2026-08-14 |
| Status | APPROVED |
| Decided by | Product Owner |

**Context**

A design review of current production screenshots (external design-architect pass over the live site) found that desktop pages — salon detail most visibly — render as a narrow mobile-width column centered in a wide viewport, and that navigation is inconsistent (real horizontal nav on home, forced hamburger on every other page). The proposed fix is a broad P0/P1 redesign sequence. Two things in that proposal conflict with decisions already on record: it reverses part of Direction B (`VISUAL_BASELINE_V1.md`: "no carousel, no full-height hero", confirmed by the user without reinterpretation) for the homepage hero, and shipping it will end the Beta Visual Baseline conversion-measurement window that has held unbroken since T-067 (2026-07-30) through T-071. The implementing session raised both conflicts before starting any code, per RFC-0001.

**Decision**

Proceed as **Visual Baseline v2**, a named, intentional continuation of the token/component work started in v1 — not a silent drift from it. Direction B's palette, type scale, and icon system carry forward unchanged; what changes is composition (desktop container/layout usage, salon detail structure, gallery, map, filters) and, for the homepage hero specifically only, an explicit revisit of the "no carousel/no full-height hero" stance toward an image-led treatment using real salon photography. Full scope, priority order, and per-ticket plan: RFC-0001, `06_ENGINEERING/VISUAL_BASELINE_V2.md`.

**Reason**

The desktop-narrow-column problem and the "reads like an MVP catalog, not a marketplace" problem share the same root files (container tokens, salon detail structure, gallery/image presentation discipline) — splitting them into a bugfix-only pass now and a "real" redesign later would mean touching the same components twice. The Product Owner chose to treat this as one deliberate v2 direction rather than defer the harder half.

**Consequences**

- The Beta Visual Baseline conversion-measurement window (2026-07-30 → present) ends when P0 ships; a new inception point is fixed at that point, same methodology as V1 (`beauty_web` container `State.StartedAt`, not merge time). Conversion data from before that point remains valid for its own comparisons but is no longer the "current" baseline going forward.
- P0 ships as nine sequenced tickets (T-095–T-103), each independently verified (lint/typecheck/tests/build + responsive check) before the next starts — not one large diff. P1 (T-104, homepage) does not start until P0 is verified in production.
- No product-model change: no booking, no fake listings/reviews, no discounts, no new brand colour, no rebrand — unchanged from both V1's and this review's own non-goals.
- `shell-grid`/`shell-content` container tokens from V1 are reused, not replaced with a new arbitrary width.

**Implementation status**

[→] In progress — T-095 starting 2026-08-14

**Affected documents**

- `06_ENGINEERING/VISUAL_BASELINE_V1.md` — cross-referenced, not superseded
- `06_ENGINEERING/VISUAL_BASELINE_V2.md` — new, opened by this decision
- `07_RFC/RFC-0001-visual-baseline-v2.md`
- `05_ROADMAP/IMPLEMENTATION_BACKLOG.md` (T-095–T-104)

---

### DEC-024 — Review source disclosure simplified to "Google reviews", drops the Imported/Original field dump

| Field | Value |
|---|---|
| Date | 2026-08-14 |
| Status | APPROVED |
| Decided by | Product Owner |
| Supersedes | DEC-013, wording only |

**Context**

DEC-013 mandated three explicit fields — `Source: Google Reviews / Imported: Yes / Original: No` — so users wouldn't mistake aggregated reviews for Lookla-native content (DEC-003, no fake activity). T-098 (Visual Baseline v2) flagged that this literal field:value phrasing reads as internal/admin metadata leaking onto a public page, not consumer copy — raised explicitly, not silently changed, since it's DEC-013's own mandated text under a dedicated exact-string test (`lib/reviewsSection.test.ts`).

**Decision**

The disclosure becomes a single label: **"Google reviews"** (localized, e.g. `googleReviewsSourceLabel`), replacing the three-field text everywhere it appears. Same visibility rule as before (`shouldShowReviewSourceLabel`: shown once per section, not per review, only once reviews have loaded and at least one exists) — presentation only, not the disclosure's existence or trigger condition.

**Reason**

DEC-013's actual goal was that a user never mistakes an aggregated review for Lookla-native content. Naming the source ("Google reviews") still communicates that on its own — nobody reads "Google reviews" and assumes a Lookla user wrote it. The literal `Imported: Yes / Original: No` fields added no fact a reasonable reader doesn't already get from "Google reviews" itself, while looking like exposed internal data-provenance flags rather than something written for a visitor. The Product Owner weighed this directly (not inferred from the redesign brief alone) and chose to drop the field dump.

**Consequences**

- `googleReviewsSourceLabel` string value changes in all 4 locale files; the key name is unchanged (no new key, no call-site churn beyond the string itself).
- `lib/reviewsSection.test.ts`'s "exact required text" test is updated to the new short text, with the DEC-013→DEC-024 supersession recorded inline — not deleted, since its real subject (one section-level disclosure exists, in all 4 languages, gated correctly) still holds.
- DEC-013 is not reversed: the requirement that aggregated reviews be identified as external stands. Only the literal wording changes.
- If Lookla-native reviews ever exist, DEC-013's "must be visually distinguished from imported reviews" consequence is inherited unchanged by this simplified label — that design work is still open, just as it was before.

**Affected documents**

- `frontend/messages/{el,en,ru,uk}.json` (`salon.googleReviewsSourceLabel`)
- `frontend/lib/reviewsSection.test.ts`
- `05_ROADMAP/IMPLEMENTATION_BACKLOG.md` (T-098)

---
