---
title: User Journeys
status: Draft
version: 0.2
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 01_PRODUCT/PERSONAS.md
  - 01_PRODUCT/PRODUCT_SCOPE.md
  - 01_PRODUCT/MVP_DEFINITION.md
  - 03_PAGES/HOME.md
  - 03_PAGES/SEARCH.md
  - 03_PAGES/SALON.md
implementation_status: N/A — awaiting approval
---

# User Journeys
**Lookla Beauty Marketplace**

> **DRAFT — not approved.**
>
> Journeys below are derived from approved Scope and Vision documents, combined with current implementation knowledge from the Engineering Audit.
>
> Each journey reflects what is **currently possible** in the product, with gaps explicitly marked. Steps that require a product decision are marked **❓**.
>
> Do not use these journeys to drive design or development until status is `Approved`.

---

## Purpose

User Journeys connect Personas to Pages. They reveal where the product works, where it breaks, and what decisions are needed to make a journey complete.

**Dependency:** Journey priority depends on which persona is primary for MVP. See MVP_DEFINITION.md Q-02.

---

## J-01 — Local finds a nail salon in her neighbourhood

**Persona:** P-01 (Greek Local)  
**Goal:** Find a nail salon near home that is open today  
**Entry point:** Google search → Lookla search page  
**Exit point:** Calls the salon to book  
**Current status:** Mostly works. Gap at step 7.

### Steps

1. User searches "νύχια Γλυφάδα" or "nail salon Glyfada" on Google
2. Lands on Lookla search page (via organic result or direct URL)
3. Sees a list of salons filtered to nail category in Glyfada area
4. Scans cards: photos, ratings, open/closed badge, price indicator
5. Clicks on a salon card that looks promising
6. Views salon detail page: photos, hours, services with prices
7. ❓ Decides to call — taps the phone button
8. Exit: call placed

### Decision points

- **Step 3:** Does the city/area filter return the right salons? (❓ Q-03 — city filter label and district grouping issue)
- **Step 6:** Are services and prices visible enough? (Currently lazy-loaded — loads when user scrolls)
- **Step 7:** Is the phone number shown directly or behind a registration wall? (❓ MVP_DEFINITION.md Q-09)

### Drop-off risks

- No organic Google ranking yet (SEO deferred) → hard to reach the platform at step 1
- City filter returns "Glyfada" as separate from "Athens" → user searching "Αθήνα" misses Glyfada salons
- Salon has no phone number in data → dead end at step 7

### Gaps

| Gap | Severity | Decision needed |
|---|---|---|
| SEO: Lookla may not rank for "nail salon Glyfada" | High | SEO strategy (deferred) |
| City filter confusion | Medium | ❓ Q-03 |
| Missing phone data in some listings | Medium | Data quality initiative |

---

## J-02 — Russian-speaking resident finds a hairdresser

**Persona:** P-02 (Russian/Ukrainian Resident)  
**Goal:** Find a hairdresser, read about services in Russian, contact via WhatsApp  
**Entry point:** Types "стрижка Афины" or "парикмахерская" in Lookla search  
**Exit point:** Sends WhatsApp message to the salon  
**Current status:** Works for multilingual search and translation. Gap at step 5.

### Steps

1. User opens Lookla in browser (or via a link from a friend in the Russian community)
2. Switches interface to Russian (language switcher in footer/header)
3. Types "стрижка" or "волосы" in the search bar
4. Platform translates the query internally (SERVICE_SYNONYMS: "стрижка" → "hair") and returns relevant salons
5. Sees salon cards in Russian interface — reviews and services in Russian after first real view
6. Opens a salon detail page
7. Service names are translated into Russian (with 🌐 badge indicating translation)
8. Reviews are translated into Russian
9. Taps WhatsApp button → opens WhatsApp with salon number
10. Exit: WhatsApp conversation started

### Decision points

- **Step 2:** Is the language switcher discoverable? Currently in the footer — may be missed
- **Step 5:** Do translated service names appear on the card or only on the detail page?
- **Step 9:** ❓ Is WhatsApp always available? (Depends on salon data having a phone number with WhatsApp)

### Drop-off risks

- User doesn't find Lookla at step 1 (no Russian-language SEO yet)
- Salon has no WhatsApp — only option is to call in Greek, which this persona avoids
- Translation quality is imperfect — AI translation of beauty terms may feel unnatural in Russian

### Gaps

| Gap | Severity | Decision needed |
|---|---|---|
| Language switcher placement (footer) may be too hidden | Medium | ❓ Product decision on header placement |
| No way to filter "salons with WhatsApp" | Low | Future feature candidate |
| No "staff speaks Russian" filter | Medium | ❓ Is this data worth collecting? |
| Translation quality not validated | Medium | Requires manual review of sample translations |

---

## J-03 — Tourist finds an open salon right now

**Persona:** P-03 (Expat/Tourist)  
**Goal:** Find any beauty service that is open right now, near current location  
**Entry point:** Mobile browser search or direct URL from hotel recommendation  
**Exit point:** Walks into the salon or calls ahead  
**Current status:** Open/closed status works. Geo search is not user-facing.

### Steps

1. Tourist opens Lookla on mobile
2. Sees homepage with search bar
3. Types service name in English ("nail salon", "massage")
4. ❓ Wants to filter "near me" — no geo-based filter available in UI currently
5. Filters by city manually (selects the district they're in — if they know the name)
6. Scans results with open/closed badge — filters visually to open ones
7. Taps salon card to view detail
8. Sees English interface, services available in English
9. Taps phone or website button
10. Exit: calls or visits

### Decision points

- **Step 4:** ❓ Is "near me" geo search in MVP scope? (Backend Haversine exists; no UI trigger)
- **Step 5:** Tourist may not know the district name → city filter is ineffective for this persona
- **Step 8:** English translation quality for this persona is critical

### Drop-off risks

- Biggest drop-off risk: tourist cannot find the right district name to filter by
- No geo search in UI means location-based discovery fails for this persona
- Tourist expects mobile-first experience — any friction on mobile is a hard exit

### Gaps

| Gap | Severity | Decision needed |
|---|---|---|
| No "near me" / GPS-based filter in UI | High for P-03 | ❓ MVP_DEFINITION.md Q-03 and geo question |
| City filter doesn't help tourists who don't know districts | High for P-03 | See Q-03 |
| Mobile UX not formally audited | Medium | Design review needed |

---

## J-04 — Salon owner discovers their listing and wants to update it

**Persona:** P-04 (Salon Owner)  
**Goal:** Find their salon on Lookla, claim it, fix wrong phone number  
**Entry point:** Client tells them "I found you on Lookla" → they search their salon name  
**Exit point:** Listing updated with correct information  
**Current status:** Backend claim flow exists. Not user-facing. ❓ Post-MVP.

### Steps

1. Owner searches their salon name on Lookla
2. Finds their listing (data from crawler)
3. Sees incorrect phone number
4. ❓ Wants to claim the listing — but no user-facing claim button currently
5. If claim were available: registers/logs in, requests claim, receives code, verifies
6. Updates phone number
7. Exit: listing corrected

### Decision points

- **Step 4:** ❓ Is owner claiming part of MVP? (See PERSONAS.md P-04 questions)
- **Step 5:** Claim code is sent to salon's email from the crawled data — what if the email is wrong?

### Gaps

| Gap | Severity | Decision needed |
|---|---|---|
| No user-facing claim button on salon page | Blocks entire journey | ❓ MVP_DEFINITION.md Q — is owner MVP scope? |
| No way to surface "claim this listing" CTA to salon owners | Blocks | Same |

---

## Journey Coverage Map

| Journey | Persona | MVP Scope | Current coverage |
|---|---|---|---|
| J-01 Find nail salon (local) | P-01 | ❓ TBD | ~80% — SEO gap, city filter gap |
| J-02 Find hairdresser (Russian) | P-02 | ❓ TBD | ~75% — language switcher placement, no WhatsApp filter |
| J-03 Find open salon (tourist) | P-03 | ❓ TBD | ~60% — no geo search, city filter problem |
| J-04 Owner claims listing | P-04 | ❓ Post-MVP | ~10% — backend only, no UI |

---

## Decisions Required Before Journeys Can Be Approved

| Decision | Affects | See |
|---|---|---|
| Primary MVP persona | All journey priorities | MVP_DEFINITION.md Q-02 |
| City filter label and grouping | J-01, J-02, J-03 steps | MVP_DEFINITION.md Q-03 |
| Geo search in MVP | J-03 heavily | MVP_DEFINITION.md |
| Registration requirement | J-01, J-02, J-03 step 7/9 | MVP_DEFINITION.md Q-09 |
| Language switcher placement | J-02 step 2 | Page spec decision |
| Owner claiming in MVP | J-04 entirely | MVP_DEFINITION.md |

---

*Last updated: 2026-07-09*
