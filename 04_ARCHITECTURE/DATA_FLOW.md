---
title: Data Flow
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 06_ENGINEERING/AUDIT.md
  - 04_ARCHITECTURE/FEATURE_FLAGS.md
  - 01_PRODUCT/PRODUCT_TERMINOLOGY.md
  - 01_PRODUCT/MVP_DEFINITION.md
  - 00_GOVERNANCE/DECISION_LOG.md
implementation_status: Describes current implementation + MVP-required extensions
---

# Data Flow
**Lookla Beauty Marketplace**

> This document defines the MVP data model and how data moves through the system.
> 
> **Scope:** MVP entities only. Features not in MVP_SCOPE_LOCK.md are marked [Future].
> 
> **Technology is not prescribed here** — this is a logical model. Database technology (PostgreSQL), transport (FastAPI), and storage (R2) are described as current facts from the Engineering Audit, not as architecture decisions.

---

## Core MVP Entities

These entities are the data foundation of every MVP user flow.

---

### Entity 1 — User

**Purpose:** Represents a person who has created an account on Lookla.

**Note per DEC-016:** Account creation is NOT required for discovery or contact. A User entity is only created when someone explicitly registers.

**Attributes:**

| Attribute | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| email | String | Unique; login identifier |
| password_hash | String | Nullable when Google OAuth only |
| name | String | Display name |
| google_id | String | Nullable; from Google OAuth |
| role | Enum | `user`, `salon_owner`, `admin` |
| preferred_language | Enum | `el`, `en`, `ru`, `uk` |
| is_email_verified | Boolean | Required for some actions |
| is_active | Boolean | Soft-delete flag |
| created_at | DateTime | |

**MVP roles:**
- `user`: standard registered visitor
- `salon_owner`: after completing claim + verification (post-MVP)
- `admin`: columb@europe.com

**Not in MVP:** professional role, subscription status, avatar

**Relationships:**
- User → [Future] Claim → Salon (post-MVP owner flow)
- User → Report (submits data quality reports)

---

### Entity 2 — Salon (Listing)

**Purpose:** A Beauty Business listed on Lookla. May be aggregated (crawler data) or verified (owner-managed). This is the central entity of the platform.

**Attributes:**

| Attribute | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| slug | String | URL-safe identifier: `/salons/[slug]` |
| name | String | Original crawled name |
| name_el | String | Greek name (may equal name) |
| description | String | Nullable; may be Greek-only |
| description_ru | String | Nullable; on-demand translation (DEC-011) |
| description_uk | String | Nullable; on-demand translation |
| **address_street** | String | |
| **address_number** | String | |
| **address_city** | String | Current: contains districts (Glyfada, Kolonaki) — awaiting DEC-010 migration |
| **address_district** | String | **New field required by DEC-010** — district/neighbourhood |
| **address_region** | String | **New field required by DEC-010** — e.g. "Attica" |
| address_postal | String | Nullable |
| lat | Decimal | Latitude |
| lng | Decimal | Longitude |
| phone_primary | String | E.164 format preferred |
| phone_secondary | String | Nullable |
| email | String | Nullable |
| website | String | Nullable |
| rating_google | Decimal | Aggregated from Google |
| rating_count | Integer | Number of Google reviews |
| price_level | Integer | 1–4 (from crawled data) |
| is_verified | Boolean | true = "Information reviewed" by admin (DEC-014) |
| is_active | Boolean | false = hidden from public |
| needs_review | Boolean | true = in moderation queue |
| google_place_id | String | For deduplication |
| created_at | DateTime | |
| updated_at | DateTime | |

**DEC-010 migration note:** The `address_city` field currently stores district names (Glyfada, Kolonaki) as if they were cities. The MVP fix requires:
1. Adding `address_district` and `address_region` fields
2. Classifying existing `address_city` values into the hierarchy
3. Updating the area filter to use `address_district` instead of raw `address_city`

Until migration is complete: use a backend mapping table to translate area slug → `address_city` ILIKE pattern.

**DEC-014 note:** `is_verified = true` means "an admin has reviewed and confirmed this information." It does NOT mean "the owner has claimed and verified this business." The owner-verified state requires a separate `claimed_by_owner` flag [Future].

**Relationships:**
- Salon → Photos (many)
- Salon → SalonHours (7, one per weekday)
- Salon → Services (many)
- Salon → ServiceCategories (many-to-many)
- Salon → Reviews (many, all source=google in MVP)
- Salon → SocialLinks (many)
- Salon → [Future] ClaimRequest

---

### Entity 3 — Location Hierarchy

**Purpose:** Defines the approved location model per DEC-010.

**Note:** This is a logical model. Implementation may use lookup tables, enum values, or a dedicated geography table. Technology choice is an engineering decision.

**Hierarchy:**

```
Country
  └── Region
        └── City
              └── District (Area / Neighbourhood)
```

**MVP values (Athens focus, DEC-012):**

| Level | Examples |
|---|---|
| Country | Greece |
| Region | Attica, Central Macedonia, Crete, South Aegean |
| City | Athens, Piraeus, Thessaloniki, Heraklion |
| District | Glyfada, Kolonaki, Kallithea, Marousi, Chalandri, Kifissia, Nea Smyrni, Psirri, Exarchia, Pagkrati, Piraeus-centre, Voula, Vari, Ilioupoli, Peristeri, Koridallos |

**Relationship to Salon entity:**
- `salons.address_region` → Region.name
- `salons.address_city` → City.name (after migration: only city-level values here)
- `salons.address_district` → District.name (new field)

**Filter mapping (area filter → salon query):**
- User selects "Glyfada" → `WHERE address_district = 'Glyfada'`
- User selects "Athens" → `WHERE address_city = 'Athens'` (returns all districts within Athens)

---

### Entity 4 — Service

**Purpose:** A specific service offered by a Salon, with price information.

**Attributes:**

| Attribute | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| salon_id | Integer | FK → Salon |
| category_id | Integer | FK → ServiceCategory |
| name | String | Original (usually Greek) |
| name_el | String | Greek |
| name_en | String | Nullable; on-demand translation |
| name_ru | String | Nullable; on-demand translation |
| name_uk | String | Nullable; on-demand translation |
| duration_min | Integer | Nullable |
| price_from | Decimal | Minimum price (used for "from €15" display) |
| price_to | Decimal | Nullable; maximum price |
| currency | String | Default: EUR |
| is_active | Boolean | |

**Translation flow:**
1. First real-user view of salon detail with locale=ru → `GET /api/salons/{id}/services?lang=ru`
2. API checks `name_ru` — if NULL, triggers GPT-4o-mini batch translation
3. Translated names stored in `name_ru`, `name_uk`
4. Subsequent requests: return cached translation; no API call

**Bot protection:** `GET /api/salons/{id}/services` returns `[]` if `is_bot(user_agent)` is true

---

### Entity 5 — Review

**Purpose:** A review of a Salon from a user. In MVP, all reviews are aggregated from Google (source=google). Lookla-native reviews are a future feature.

**Attributes:**

| Attribute | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| salon_id | Integer | FK → Salon |
| source | Enum | `google` (only value in MVP) |
| author_name | String | Name from Google |
| rating | Integer | 1–5 |
| text | String | Original text (usually Greek) |
| text_el | String | Greek copy |
| text_en | String | Nullable; on-demand translation |
| text_ru | String | Nullable; on-demand translation |
| text_uk | String | Nullable; on-demand translation |
| published_at | DateTime | Original publish date from Google |
| is_verified | Boolean | Unused in MVP; legacy field |

**DEC-013 display rule:** `source = 'google'` → UI must show "Source: Google Reviews / Imported: Yes / Original: No" header. This is not optional.

**Translation flow:** Same as Service names — first real-user view triggers translation, result cached.

**Future:** When Lookla-native reviews exist, `source = 'lookla'` and the UI must visually distinguish them from Google reviews.

---

### Entity 6 — Contact Action (Analytics Event)

**Purpose:** Tracks the primary MVP success metric (DEC-008): user-initiated contact with a salon.

**This is NOT stored in the database.** It is a GA4 event fired from the frontend.

**Event name:** `contact_action`

**Parameters:**

| Parameter | Value | Notes |
|---|---|---|
| action_type | `phone`, `whatsapp`, `website` | Which CTA was tapped |
| salon_id | Integer | Which salon |
| salon_name | String | For readability in GA4 |
| locale | String | `el`, `en`, `ru`, `uk` |
| page_path | String | Automatic from GA4 |
| session_id | String | Automatic from GA4 |

**Trigger:** Each of the three contact buttons on the Salon Detail page fires this event on click/tap.

**Privacy:** No personally identifiable information is included. GA4 session IDs are anonymized. Per DEC-016, no login is required — the event captures behaviour, not identity.

**MVP success measurement:** `COUNT(contact_action events)` over 90-day window ≥ 500 = MVP validated (DEC-008).

---

### Entity 7 — Claim Request

**Status: [Future] — not in MVP. Backend implemented; not user-facing.**

**Purpose:** A Salon Owner requests ownership of a listing. After verification, they can manage the listing directly.

**Attributes:**

| Attribute | Type | Notes |
|---|---|---|
| id | Integer | |
| user_id | Integer | FK → User (must have role='user' initially) |
| salon_id | Integer | FK → Salon |
| token | String | 6-char hex verification code |
| channel | Enum | `email` (only working channel in MVP backend) |
| expires_at | DateTime | 1 hour TTL |
| used_at | DateTime | Nullable; set on successful verification |
| created_at | DateTime | |

**Current state (Engineering Audit):** API endpoints exist (`/api/owner/claim/request`, `/api/owner/claim/verify`). No user-facing entry point (no "Claim this listing" button on salon detail page). Blocked from MVP per FEATURE_FLAGS.md.

**Owner-verified state (post-MVP):** When a Claim Request is successfully verified:
- `salon_owners` record is created (user_id, salon_id)
- `users.role` → `salon_owner`
- UI should show "Owner verified" label instead of "Information reviewed" (DEC-014)

---

## Data Flows

### Flow A — User Discovers a Salon (Read Path)

```
Browser
  │
  ├─ SSR (page load, Nginx → Next.js)
  │     GET /api/salons/{id}
  │     ← name, address, hours, photos, rating, is_verified, phone, website
  │     Renders: name, photo, open/closed, rating, contact buttons, description
  │
  └─ CSR (IntersectionObserver triggers when section enters viewport)
        GET /api/salons/{id}/services?lang=ru
        ├─ if is_bot(user_agent) → return []
        ├─ if name_ru is NULL → batch translate via GPT-4o-mini → store → return
        └─ else return cached name_ru values

        GET /api/salons/{id}/reviews?lang=ru
        ├─ if is_bot(user_agent) → return []
        ├─ if text_ru is NULL → batch translate via GPT-4o-mini → store → return
        └─ else return cached text_ru values
```

### Flow B — User Contacts a Salon (Write Path to GA4)

```
User taps "WhatsApp" button
  │
  ├─ Opens wa.me/{phone} in new tab (browser action, no backend call)
  │
  └─ GA4 gtag('event', 'contact_action', {
         action_type: 'whatsapp',
         salon_id: 1234,
         salon_name: 'Glyfada Nails',
         locale: 'ru'
     })
     → sent to GA4 property
     → counted toward DEC-008 success metric
```

### Flow C — Search (Read Path)

```
User submits search form
  │
  └─ GET /api/salons?q=маникюр&area=glyfada&category=nail-salon&min_rating=4
          │
          ├─ _translate_query('маникюр') → 'nail' (SERVICE_SYNONYMS)
          ├─ area 'glyfada' → WHERE address_district = 'Glyfada'
          │  (or: WHERE address_city ILIKE 'Glyfada' until DEC-010 migration)
          ├─ category 'nail-salon' → CATEGORY_KEYWORDS['nail-salon'] → subquery on services.name
          ├─ min_rating 4 → WHERE rating_google >= 4
          ├─ ORDER BY rating_google DESC, rating_count DESC
          ├─ LIMIT 24 OFFSET {page * 24}
          ├─ + open/now enrichment (batch salon_hours query for current Athens weekday)
          └─ + min_price enrichment (batch MIN(price_from) from services)
          
          ← [{salon_id, name, address_district, rating, is_open, min_price, is_verified, ...}]
```

### Flow D — Photo Load (R2 Migration Path)

```
Browser loads photo URL
  │
  ├─ If URL is Google Places URL:
  │     → request goes to /api/media/photo/{id}
  │     → proxy fetches from Google
  │     → uploads to R2 (cdn.lookla.gr)
  │     → updates photos.r2_key and photos.url in DB
  │     → returns image bytes
  │
  └─ If URL is already cdn.lookla.gr:
        → served directly from R2 via Cloudflare CDN
        → no backend involvement
```

### Flow E — Admin Reviews a Salon (Write Path)

```
Admin taps "Mark as reviewed" on salon in admin panel
  │
  └─ PATCH /api/admin/salons
        body: { id: 1234, is_verified: true, needs_review: false }
        → updates salons table
        → salon now shows "Information reviewed" label on public detail page
```

---

## Data Not in MVP

| Entity | Status | Reason |
|---|---|---|
| Appointment | [Future] | Booking system not user-facing (DEC-015) |
| Conversation / Message | [Future] | Chat not user-facing |
| Subscription / Plan | [Future] | Payments not user-facing (DEC-006) |
| Favorite | [Future] | Not built |
| Lookla-native Review | [Future] | Only Google reviews in MVP |
| ClaimRequest | [Future] | Not user-facing in MVP |
| Professional | [Future] | Separate entity; not in MVP scope |
| Notification | [Future] | Not built |

---

## Translation Data Flow (Summary)

```
First real-user view of /salons/{id}/services?lang=ru
  │
  ├─ Check: services[].name_ru IS NULL?
  │     Yes → batch all service names for this salon
  │           POST to OpenAI gpt-4o-mini (single request, batch of names)
  │           UPDATE services SET name_ru = translated WHERE id IN (...)
  │           Return translated names
  │
  └─ No → return services[].name_ru directly (no API call)

Cost control:
  - Translation happens once per salon per language
  - Bot requests never trigger translation (is_bot check first)
  - Cost per salon per language: ~10–50 service names → < $0.001
```

---

## Analytics Data Flow (DEC-017)

```
User browser
  │
  ├─ GA4 script loaded from Google (via Next.js layout)
  │
  ├─ Automatic events: page_view, session_start, first_visit
  │
  └─ Custom events (instrumented manually):
        contact_action      → fired on contact button click (CRITICAL — DEC-008)
        search_submitted    → fired on search form submit
        filter_applied      → fired on filter change
        salon_card_clicked  → fired on card click from search
        locale_switched     → fired on language switcher use
        
        All events include: locale, page_path, salon_id (where applicable)

GA4 → Google Analytics property → BigQuery export (future)
Google Search Console → organic keyword data (separate, no code)
Microsoft Clarity → session recordings (optional, post-launch)
```

---

*Last updated: 2026-07-09*
