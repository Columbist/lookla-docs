---
title: Product Terminology
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 01_PRODUCT/PRODUCT_SCOPE.md
  - 01_PRODUCT/PRODUCT_VISION.md
implementation_status: N/A — product document
---


# 03 — Product Terminology
**Lookla Beauty Marketplace**

Status: APPROVED  
Authority: Product Owner  
Last updated: 2026-07-09

> This is the official project dictionary.  
> Every document, design file, UI string, and codebase comment must use these terms.  
> If a term is missing, submit a Change Request before using an undefined term in official documents.  
> If implementation uses different terminology, report the mismatch — do not silently update either the code or this document.

---

## How to read this dictionary

Each term contains:
- **Definition** — what the term means within Lookla
- **Purpose** — why this term exists as a distinct concept
- **Notes** — usage guidance, related terms, or disambiguation

Terms are listed in logical groups, not alphabetically.

---

## People

---

### Visitor

**Definition**  
A person browsing Lookla without a registered account.

**Purpose**  
Distinguishes anonymous traffic from registered users. Visitors have access to all discovery features. They cannot save listings, submit reviews, or request bookings.

**Notes**  
Do not call a Visitor a "guest" or "anonymous user" in product-facing contexts. "Guest" implies a temporary relationship. A Visitor is simply someone who has not yet registered.

---

### User

**Definition**  
A person with a registered Lookla account.

**Purpose**  
The base identity for all authenticated interactions on the platform.

**Notes**  
A User may have one of several roles: default User, Salon Owner, Independent Professional, or Administrator. The term "User" alone refers to the base role — a client with an account. When the role matters, use the specific term (Salon Owner, etc.).  
Do not use "Member" or "Customer" — the official term is User.

---

### Salon Owner

**Definition**  
A User who has claimed and had verified the ownership or management of one or more Beauty Businesses on Lookla.

**Purpose**  
Distinguishes Users who actively manage a Business Listing from Users who only search and browse.

**Notes**  
A Salon Owner does not necessarily own the physical business. The term covers both owners and authorized managers.  
Claiming a listing does not automatically make someone a Salon Owner — verification must be completed first.  
Do not use "Partner" or "Business Account" — the official term is Salon Owner.

---

### Independent Professional

**Definition**  
A beauty specialist who operates independently — not as part of a Beauty Business with a fixed location. May offer services at a home studio, at the client's location, or in rented spaces.

**Purpose**  
Distinguishes mobile or freelance beauty professionals from fixed-location businesses.

**Notes**  
An Independent Professional has their own profile on Lookla, separate from any Salon Listing.  
A professional who also works at a salon may appear in both contexts.  
Do not use "Freelancer" — the official term is Independent Professional.

---

### Administrator

**Definition**  
A Lookla team member with elevated platform access for moderation, data management, and operational oversight.

**Purpose**  
Separates operational access from product access. Administrators can see and act on information that ordinary Users and Salon Owners cannot.

**Notes**  
Administrator access is not for product management or configuration — it is for data integrity and moderation.  
Do not abbreviate as "Admin" in user-facing text. In internal documents "admin" is acceptable.

---

## Business Entities

---

### Beauty Business

**Definition**  
The parent concept for any commercial entity that offers beauty, grooming, or wellness services and appears on Lookla.

**Purpose**  
A single term that covers all types of businesses — salons, studios, spas, barbershops — without forcing a choice of sub-type when the distinction is irrelevant.

**Notes**  
Use "Beauty Business" when the specific type does not matter.  
Use the specific sub-type (Salon, Barbershop, Spa, Beauty Studio) when the type is relevant to the context.

---

### Salon

**Definition**  
A fixed-location Beauty Business offering personal care services, typically in hair, nails, skin, or a combination.

**Purpose**  
The primary and most common type of Beauty Business on the platform.

**Notes**  
In Greek contexts, "κομμωτήριο" (hair salon) is the most commonly used term. On Lookla, Salon is used as the broader concept covering hair salons, nail salons, and multi-service locations.  
Do not restrict "Salon" to hair services only.

---

### Barbershop

**Definition**  
A fixed-location Beauty Business focused primarily on men's grooming: haircuts, beard trimming, and shaving.

**Purpose**  
Distinguishes men's grooming businesses from general salons, which primarily serve a female clientele.

**Notes**  
A business that serves both men and women but markets primarily to men may be listed as a Barbershop.  
A salon that offers men's services as a minor part of its offering is a Salon, not a Barbershop.

---

### Spa

**Definition**  
A fixed-location Beauty Business focused on wellness, relaxation, and body treatments: massages, hydrotherapy, body wraps, and similar services.

**Purpose**  
Distinguishes wellness-oriented businesses from cosmetic-service-oriented salons.

**Notes**  
A Spa may also offer beauty services (facials, waxing). A business is categorized as a Spa when wellness treatments are its primary offering.  
Day spas and hotel spas are both Spas in Lookla terminology.

---

### Beauty Studio

**Definition**  
A fixed-location Beauty Business that is smaller or more specialized than a full-service Salon — often focused on a single category such as brows, lashes, or permanent makeup.

**Purpose**  
Accommodates specialized businesses that do not comfortably fit into the broader Salon category.

**Notes**  
Beauty Studio is a catch-all sub-type for specialized fixed-location businesses. If a business fits clearly into Salon, Barbershop, or Spa, prefer those terms.

---

## Catalog Concepts

---

### Listing

**Definition**  
A published profile of a Beauty Business on Lookla, containing its name, location, contact information, hours, services, and photos.

**Purpose**  
The core unit of content on the platform. Everything a client sees about a specific business is the Listing.

**Notes**  
A Listing exists independently of whether the Salon Owner has claimed it. Most Listings are initially created from aggregated public data.  
Do not use "Profile" or "Page" — the official term is Listing.

---

### Claim

**Definition**  
The act of a Salon Owner asserting that they are the authorized representative of a specific Listing.

**Purpose**  
The starting point of owner participation. Before a Salon Owner can edit a Listing, they must Claim it and complete Verification.

**Notes**  
Claiming a Listing does not immediately grant editing rights. Verification must follow.  
A Listing without a Claim is not an error — it is the normal state for most Listings at the current stage.

---

### Verification

**Definition**  
The process by which Lookla confirms that the person claiming a Listing is the authorized owner or manager of that business.

**Purpose**  
Protects Listings from unauthorized modification. Ensures that only legitimate representatives can edit business information.

**Notes**  
Verification is a future-stage capability. The infrastructure exists but the process is not currently user-facing.  
Verification is distinct from Claim — Claiming is the request; Verification is the confirmation.  
Do not use "Validated" or "Certified" — the official term is Verified / Verification.

---

### Service

**Definition**  
A specific treatment, procedure, or offering available at a Beauty Business, with a name, optional description, optional duration, and optional price.

**Purpose**  
The atomic unit of what a client can receive. Services are organized into Categories.

**Notes**  
A Service belongs to one Beauty Business. A Service may belong to one Service Category.  
Service pricing is shown when available. Absence of pricing data does not mean the Service is free — it means the data is not yet available.

---

### Category

**Definition**  
A classification that groups similar Services or Beauty Businesses for the purpose of search and filtering.

**Purpose**  
Allows clients to browse and filter without knowing the exact name of what they're looking for. "I want nail services" is answered by the Nails Category.

**Notes**  
Categories have two levels: top-level (e.g., Hair, Nails, Spa) and sub-level (e.g., Hair Color, Gel Nails, Massage).  
Categories are managed by Lookla administrators and are not editable by Salon Owners.  
Do not use "Tag" or "Type" for this concept — the official term is Category.

---

### City

**Definition**  
A named geographic area used as the primary location filter in Lookla search.

**Purpose**  
The most common way clients narrow their search to a relevant area.

**Notes**  
**Known limitation (not yet resolved):** The "City" filter currently maps to the `address_city` field in the database, which contains both city names and district names (e.g., Kallithea, Glyfada appear as separate cities rather than as districts of Athens). This creates a misleading filter label — selecting "Athens" returns only businesses in the central Athens district, not all of the Athens metropolitan area. This will require a product decision and a terminology update before UI design begins. See Section "Terminology Requiring Resolution" below.  
Do not rename or redesign this without an approved Change Request.

---

### Region

**Definition**  
A broader geographic grouping above City level. Used when a client's search intent covers multiple cities or districts.

**Purpose**  
Provides a higher-level filter for clients who are flexible about exact location.

**Notes**  
Region is not yet implemented as a separate filter. It is defined here for terminology consistency and future use.  
This term is the intended resolution to the City/District ambiguity described above.

---

## Transactional Concepts

---

### Booking

**Definition**  
The act of a client reserving an Appointment at a Beauty Business or with an Independent Professional through Lookla.

**Purpose**  
The core transactional interaction of the platform's future booking stage.

**Notes**  
Booking is a future capability. The term is defined now to prevent informal or inconsistent usage in planning documents.  
Do not conflate Booking (the act) with Appointment (the confirmed time slot that results from Booking).

---

### Appointment

**Definition**  
A confirmed, time-specific reservation between a client and a Beauty Business or Independent Professional.

**Purpose**  
The outcome of a Booking. An Appointment has a date, time, service, and participating parties.

**Notes**  
An Appointment is future functionality. The database infrastructure exists but is not user-facing.  
An Appointment may be created via Booking (client-initiated) or via Availability Request (inquiry-based).

---

### Review

**Definition**  
A rating and written comment submitted by a client about their experience at a Beauty Business.

**Purpose**  
A trust signal that helps future clients make informed decisions.

**Notes**  
**Two types exist and must be distinguished:**  
1. **Aggregated Reviews** — sourced from public data (Google, etc.), currently shown on Listings. Not submitted through Lookla.  
2. **Owned Reviews** — submitted by Lookla Users after a verified visit. A future capability.  
When the distinction matters, use the full term (Aggregated Review, Owned Review).  
Do not present Aggregated Reviews as if they were Owned Reviews.

---

### Rating

**Definition**  
A numerical score representing the average quality of a Beauty Business, derived from Reviews.

**Purpose**  
The primary quantitative trust signal displayed on Listings and used in search ordering.

**Notes**  
Current Ratings are derived from aggregated public data (primarily Google ratings).  
When Owned Reviews become available, Rating calculation may include both sources.  
Rating is displayed to one decimal place (e.g., 4.3, not 4.27).

---

### Favorite

**Definition**  
A saved Listing that a User has marked for quick future access.

**Purpose**  
Allows Users to build a personal shortlist of Beauty Businesses without making a Booking.

**Notes**  
Favorite is a future capability. It is defined here to standardize the term.  
Do not use "Bookmark," "Save," or "Like" — the official term is Favorite.

---

## Data Concepts

---

### Aggregated Data

**Definition**  
Information collected from public sources by Lookla's automated crawlers, without direct input from the Beauty Business or its owner.

**Purpose**  
The foundation of Lookla's data at the current stage. Most Listings consist entirely of Aggregated Data.

**Notes**  
Aggregated Data is real — it comes from real public sources. It is not fabricated.  
Aggregated Data may be incomplete, outdated, or inaccurate. It must never be presented to users as definitively verified.  
Sources include: business directories, map platforms, review sites.

---

### Verified Data

**Definition**  
Information that has been confirmed by an authenticated Salon Owner through the Claim and Verification process.

**Purpose**  
Distinguishes high-confidence data from aggregated data. Verified Data should be prioritized in display when both types exist for the same field.

**Notes**  
Verified Data is a future capability — the Verification process is not yet user-facing.  
When Verified Data exists for a field, it supersedes Aggregated Data for that field.  
Do not mark Aggregated Data as Verified, even if it appears correct.

---

### Refresh

**Definition**  
The automated process of updating a Listing's Aggregated Data from its original public sources.

**Purpose**  
Keeps Listings accurate over time without requiring manual intervention.

**Notes**  
Refresh frequency varies by data source and crawler configuration.  
A Refresh may update working hours, phone numbers, ratings, and review counts.  
A Refresh must not overwrite Verified Data with Aggregated Data.

---

### Synchronization

**Definition**  
The broader process of keeping the Lookla database consistent with external data sources and internal data integrity requirements.

**Purpose**  
Covers both Refresh (inbound from external sources) and internal consistency checks.

**Notes**  
Synchronization is an infrastructure concept. It is not exposed to Users or Salon Owners directly.

---

## Platform Concepts

---

### Search

**Definition**  
The process by which a Visitor or User queries the platform to find relevant Beauty Businesses or Services.

**Purpose**  
The primary client-facing interaction with Lookla's data.

**Notes**  
Search supports multiple input types: free text, category selection, city/region filter, and map-based location.  
Search results are ordered by rating by default.  
Multilingual query translation is handled automatically — a User searching in Russian is not required to know Greek terms.

---

### Search Result

**Definition**  
A single Beauty Business or Independent Professional returned in response to a Search query.

**Purpose**  
The unit of output from the Search function.

**Notes**  
A Search Result displays a summary of the Listing (name, city, photo, rating, open/closed status, minimum price).  
A Search Result is not the same as a Listing — the Listing is the full profile page; the Search Result is the card in the results list.

---

### Featured

**Definition**  
A designation that gives a Listing elevated visibility in Search Results or on category/city pages.

**Purpose**  
A future monetization and visibility mechanism for Salon Owners.

**Notes**  
Featured is a future capability. It is defined here to standardize the term before any implementation begins.  
Featured placement must always be labeled as such — it must never be presented as organic ranking.  
Do not use "Sponsored," "Promoted," or "Boosted" — the official term is Featured.

---

### Premium

**Definition**  
A subscription tier for Salon Owners that unlocks enhanced Listing capabilities, analytics, or Featured placement.

**Purpose**  
The primary future monetization mechanism for the platform.

**Notes**  
Premium is a future capability. No Premium tier exists at the current stage.  
Premium is defined here to reserve the term and prevent informal use of alternatives ("Pro," "Business," "Verified Plan").  
The specific benefits of a Premium subscription are not defined in this document — they require a separate approved product decision.

---

### Feature Flag

**Definition**  
A mechanism that allows a platform capability to exist in the codebase without being visible or accessible to Users.

**Purpose**  
Enables future capabilities to be built, tested, and deployed without premature exposure to users.

**Notes**  
Feature Flag is an architectural concept, not a user-facing concept.  
On Lookla, Feature Flags are currently managed conceptually (code exists but is not linked from user interfaces) rather than via a dedicated feature flag system.  
Any capability documented as "Future" in `01_PRODUCT_SCOPE.md` is implicitly behind a Feature Flag.

---

### Translation

**Definition**  
The automatic conversion of content (service names, review text, descriptions) from Greek or English into the User's selected language.

**Purpose**  
Makes Lookla accessible to non-Greek speakers without requiring manual translation of every Listing.

**Notes**  
Translation is generated on the first view by a real User and stored for all subsequent requests.  
Translation is not shown to search engine crawlers — it is a client-facing feature, not an SEO feature.  
Translated content is labeled as such (e.g., "Translated" badge) — it is never presented as original content.  
Translation quality depends on the AI model used and may contain errors. It is informational, not authoritative.

---

## Terminology Requiring Resolution Before UI Design Begins

The following terms have known ambiguity or implementation mismatch that must be resolved before UI design or copy work begins. A Change Request is required for each.

| Term | Issue | Status |
|---|---|---|
| **City** | Currently shows districts (Kallithea, Glyfada) as separate cities, not as sub-areas of Athens. The filter label "City" is misleading for users searching by metro area. The correct concept may be "Area" or "Region." | Acknowledged — pending Change Request |
| **Review** | Two types exist (Aggregated and Owned) but the UI does not distinguish them. Users may assume all reviews were submitted by Lookla users. | Acknowledged — requires UI and data labeling decision |
| **Verified** | The verification badge (✓) currently indicates that the salon's data has been administratively reviewed, not that the Salon Owner has completed the Verification process. This is a trust signal mismatch. | Acknowledged — requires product decision |

---

*Last updated: 2026-07-09*  
*Authority: Product Owner*
