---
title: UX Flows
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 01_PRODUCT/USER_JOURNEYS.md
  - 01_PRODUCT/PERSONAS.md
  - 01_PRODUCT/MVP_DEFINITION.md
  - 03_PAGES/HOME.md
  - 03_PAGES/SEARCH.md
  - 03_PAGES/SALON.md
  - 02_DESIGN/WIREFRAME_REQUIREMENTS.md
implementation_status: N/A — specification document
---

# UX Flows
**Lookla Beauty Marketplace**

> All flows below are for MVP scope only. Features not in MVP_SCOPE_LOCK.md are marked as **[Future]** and must not be implemented now.
>
> Flows describe behaviour, not visual design. Visual design is specified in WIREFRAME_REQUIREMENTS.md.

---

## Flow 1 — Visitor → Search → Filter → Salon → Contact

**Primary persona:** P-02 (Russian/Ukrainian resident), also serves P-01 and P-03  
**Entry:** Homepage or direct URL to search  
**Exit:** Contact action (phone call, WhatsApp, website visit)  
**Success metric:** This flow is what DEC-008 measures

---

### Happy Path

```
1. User lands on Homepage (/)
   - Sees hero with search bar in their locale
   - Language switcher is visible in header
   └─ [If wrong language] → taps language switcher → locale changes → stays on same page

2. User types search query
   - Types "маникюр" (Russian), "νύχια" (Greek), or "nail salon" (English)
   - Submits search (tap button or press Enter)
   └─ Navigates to /search?q=маникюр

3. Search page loads (CSR)
   - Shows salon cards matching query
   - Area filter visible: "All areas"
   - Contact actions not visible yet (user is on search results)

4. User applies Area filter
   - Opens Area dropdown
   - Selects "Glyfada"
   └─ URL updates to /search?q=маникюр&area=glyfada
   - Results refresh in-place
   - "23 salons in Glyfada" shown

5. User scans results
   - Sees open/closed badges
   - Sees rating and min price on cards
   - Optionally toggles Map view to see locations

6. User clicks SalonCard
   └─ Navigates to /el/salons/[slug] (or locale-appropriate)

7. Salon Detail page loads
   - SSR: name, photos, open/closed, contact buttons visible above fold
   - CSR: services and reviews lazy-load as user scrolls

8. User taps "Message on WhatsApp"
   └─ Opens wa.me/{phone} in new tab
   - GA4 event: contact_action {action_type: whatsapp}

EXIT: User is in WhatsApp with the salon's number pre-filled
```

---

### Alternative Path A — User doesn't search, uses category from homepage

```
1. User lands on homepage
2. Taps "Nail salon" category tile (CategoryGrid)
   └─ /search?category=nail-salon
3. Sees filtered results for nail salons across all areas
4. Applies Area filter → Glyfada
5. Continues to steps 6–8 of happy path
```

---

### Alternative Path B — Map-first discovery

```
1. User arrives at /search (any filter state)
2. Taps "Map" toggle
3. Map renders with pins for all matching salons
4. User drags/zooms map to their area of interest
5. Taps a pin → mini card appears (name, rating, open/closed)
6. Taps mini card → navigates to salon detail
7. Continues to steps 7–8 of happy path
```

---

### Alternative Path C — Direct URL to salon (e.g. from a WhatsApp link)

```
1. User receives a WhatsApp message with a lookla.gr link
2. Taps link → opens /ru/salons/[slug] (Russian locale pre-set in URL, or browser default)
3. Lands directly on Salon Detail
4. Sees contact buttons immediately above fold
5. Taps WhatsApp → exits
```

No search involved. This is a valid flow and a likely P-02 distribution mechanism (community referrals).

---

### Edge Cases

| Scenario | Behaviour |
|---|---|
| Search returns 0 results | Empty state: "No salons found. Try a different area or clear filters." |
| User searches with Cyrillic for category | SERVICE_SYNONYMS translates "маникюр" → "nail"; returns nail salon results |
| Salon has no phone AND no WhatsApp AND no website | Contact section shows "Contact information not available" + Report link; no CTAs |
| Salon is CLOSED | Badge shows "Closed · Opens Tuesday 10:00"; user can still contact |
| User taps back from salon to search | Returns to same filter state (URL-preserved) |
| Language mismatch (search URL is /ru but browser sends Accept-Language: el) | next-intl routes to /ru as specified in URL — explicit locale wins |

---

## Flow 2 — Visitor → Salon Profile → Review → Contact

**Primary persona:** P-01 (Greek local), P-02 (Russian/Ukrainian)  
**Entry:** Direct URL or search → salon detail  
**User intent:** Validate the salon via reviews before deciding to contact

---

### Happy Path

```
1. User arrives on Salon Detail page (from search or direct URL)

2. User scrolls past photos and contact buttons to reviews section

3. Reviews section loads (IntersectionObserver trigger)
   - Section header: "Reviews / Source: Google Reviews / Imported: Yes / Original: No"
   - Reviews shown in current locale (translated if needed)
   - 🌐 badge on translated reviews

4. User reads 2–3 reviews
   - Satisfied with quality
   └─ Scrolls back up to contact buttons

5. User taps "Call salon"
   └─ Opens tel:{phone} dialer
   - GA4 event: contact_action {action_type: phone}

EXIT: User is calling the salon
```

---

### Alternative Path — User is dissatisfied with reviews

```
1–4. Same as happy path

5. User sees negative reviews or few reviews
6. User navigates back to search results
7. Selects a different salon
8. Continues in Flow 1
```

---

### Edge Cases

| Scenario | Behaviour |
|---|---|
| No reviews available | "No reviews available for this salon" (section shows but is empty) |
| Reviews are all in Greek, locale is Russian | Translation badge shown; GPT-4o-mini translates on first real-user view |
| Bot reaches review section | IntersectionObserver never fires for non-scrolling bots; endpoint returns [] for bot User-Agents |
| User is on mobile, reviews section is below the fold | Scroll required — ensure contact buttons are duplicated at bottom of page OR floating |
| Translation fails (GPT error) | Show original Greek text without translation badge; do not show error |

---

## Flow 3 — Salon Owner Discovers Listing and Requests Claim

**Persona:** P-04 (Salon Owner)  
**MVP status:** Owner claim UI is NOT user-facing in MVP (FEATURE_FLAGS.md). This flow documents the workaround available in MVP.

---

### MVP State (no self-service claim UI)

```
1. Salon owner hears from a client "I found you on Lookla"

2. Owner searches their salon name on Lookla
   └─ /search?q=Salon+Name or types in search bar

3. Owner finds their listing
   └─ Clicks on SalonCard

4. Owner sees their salon detail page
   - May see incorrect information (wrong phone, wrong hours)

5. Owner taps "Report incorrect information"
   - Fills in: what is wrong (Phone / Hours / Address)
   - Submits report
   └─ POST /api/reports (requires login)

   [If not logged in]
   5a. Owner is redirected to /login
   5b. Owner registers or logs in
   5c. Report form is submitted

6. Admin receives report in admin panel reports queue
7. Admin reviews and corrects the data
8. Owner's listing is updated

EXIT: Salon data corrected (via admin, not self-service)
```

**Gap:** Step 5 requires login to submit a report. This is friction for a salon owner discovering Lookla for the first time. Consider allowing anonymous reports in a future change request.

---

### Post-MVP Flow (when claim UI is user-facing)

```
1–4. Same as above

5. Owner sees "Is this your salon?" CTA on salon detail page
6. Owner clicks → /dashboard/claim?salon_id={id}
7. Registers if needed → enters salon email
8. Receives 6-char verification code at salon's email
9. Enters code → claim verified
10. Owner is redirected to /dashboard/salon/{id}
11. Owner edits phone, hours, description, photos

EXIT: Owner managing their own listing
```

**Not in MVP** — document only. Implementation blocked by:
- Claim CTA not user-facing (FEATURE_FLAGS.md)
- SMS/WhatsApp claiming channel not wired (only email works)
- Claim flow UI partially implemented but not linked

---

## Flow 4 — Admin Reviews and Approves a Salon Listing

**Actor:** Admin (columb@europe.com)  
**Entry:** `/admin` panel  
**Goal:** Set "Information reviewed" status on a salon that has been checked for accuracy (DEC-014)

---

### Happy Path

```
1. Admin logs in → navigates to /admin

2. Admin sees Stats dashboard
   - Checks "Salons needing review" count
   - Checks "Open reports" count

3. Admin navigates to Salons → filter: needs_review=true

4. Admin selects a salon from the list
   - Opens public salon detail page in new tab to verify data

5. Admin checks:
   - Phone number (call or check against external source)
   - Address (exists on Google Maps)
   - Business category is correct
   - No obvious spam or fake listing

6. If data is correct:
   - Admin sets is_verified=true (displays as "Information reviewed" per DEC-014)
   - Admin sets needs_review=false
   └─ PATCH /api/admin/salons — update flags

7. If data has errors:
   - Admin edits phone/address inline (requires inline edit form — see ADMIN.md gap)
   - Admin sets is_verified=true after correction
   - Admin sets needs_review=false

8. Admin proceeds to next salon in queue

EXIT: Salon shows "Information reviewed" label on public detail page
```

---

### Handling a User Report

```
1. Admin navigates to Reports queue
2. Sees open report: "Wrong phone number" for Salon X
3. Clicks "View salon" → salon detail opens in new tab
4. Admin verifies the correct phone number (external lookup)
5. Admin edits salon phone via inline edit (when implemented)
6. Admin marks report "Resolved"
   └─ PATCH /api/admin/reports/{id}

EXIT: Report resolved, salon data corrected
```

---

### Edge Cases

| Scenario | Behaviour |
|---|---|
| Salon in moderation queue with no original data | Admin marks needs_review=false without verifying; documents as "data unavailable" |
| Report is invalid (user made a mistake) | Admin marks resolved with no data change |
| Admin edits phone to wrong number | No rollback mechanism in MVP — accept this risk; add edit history post-MVP |
| Admin accidentally sets is_active=false | No confirmation dialog currently — this immediately removes salon from public listing; admin must manually re-enable |

---

## Cross-Flow Notes

### Language Switching in All Flows

Language switching is available on every page via the header language switcher (after HOME.md spec is implemented). Switching locale in the middle of any flow:
- Preserves the current page (same URL, locale prefix changes)
- All translated content re-renders in the new locale
- Any in-progress form inputs are cleared (acceptable)
- URL changes: `/ru/salons/[slug]` → `/el/salons/[slug]`

### Registration in All Flows

Per DEC-016: No flow in MVP requires registration except:
- Submitting a "Report incorrect information" (current API requires auth — known friction)
- Favorites / saved listings (not in MVP)

Admin flows always require login.

---

## Flows Explicitly Not in MVP

| Flow | Why not in MVP |
|---|---|
| User books an appointment | No booking engine; DEC-015 prohibits fake booking CTA |
| Owner manages listing (self-service) | Feature flag — not user-facing |
| User chats with salon | Chat backend exists; UI not linked |
| User saves a favourite salon | Not started |
| User receives push notification | Not started |
| User subscribes to a plan | DEC-006 prohibits user-facing payments |

---

*Last updated: 2026-07-09*
