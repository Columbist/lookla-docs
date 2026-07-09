---
title: Personas
status: Draft
version: 0.2
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 01_PRODUCT/PRODUCT_SCOPE.md
  - 01_PRODUCT/PRODUCT_VISION.md
  - 01_PRODUCT/USER_JOURNEYS.md
  - 01_PRODUCT/MVP_DEFINITION.md
  - 01_PRODUCT/PRODUCT_TERMINOLOGY.md
implementation_status: N/A — awaiting approval
---

# Personas
**Lookla Beauty Marketplace**

> **DRAFT — not approved.**
>
> Personas below are derived from approved documents (PRODUCT_VISION.md, PRODUCT_SCOPE.md) and the known platform context (6320 salons, multilingual audience in Greece, el/en/ru/uk).
>
> They are working hypotheses, not validated research. Each persona includes open questions where the Product Owner must make decisions before personas can be approved and used in design.
>
> Do not use these personas in design or implementation until status is `Approved`.

---

## Purpose

Personas define the real people Lookla is built for. They determine which features matter, which languages are prioritized, what information appears on a listing page, and what constitutes a successful user interaction.

One key decision is outstanding: **❓ MVP_DEFINITION.md Q-02 — which persona is primary for MVP?** Until this is decided, all personas carry equal weight, which means nothing is optimized for anyone.

---

## P-01 — The Greek Local

**Role:** Visitor → User  
**Primary language:** Greek (el)  
**Location:** Athens metro area, Thessaloniki, other Greek cities  
**Age range:** 25–50

**Context**  
Lives in Greece, speaks Greek fluently. Knows the neighbourhood. Has probably used Google Maps to find salons before. May have a regular salon but is looking for something new — a specialist, a second option, or a salon in a new area after moving.

**Goals**  
- Find a specific type of salon (nail salon, barbershop, spa) in a specific area
- See if it's currently open
- Get the phone number to call and ask about availability

**Frustrations**  
- Google Maps shows businesses but not enough beauty-specific detail (which services, price range)
- Hard to compare two salons side by side
- Phone numbers are sometimes wrong or outdated

**Behaviours**  
- Searches in Greek by neighbourhood name + service type
- Checks photos and rating before clicking
- Calls directly rather than booking online

**Success looks like**  
Found a salon with a good rating in the right area, confirmed it's open, called to make an appointment.

**❓ Questions for Product Owner**  
- Is P-01 the primary MVP persona or a secondary one?
- What does P-01 expect from a "verified" badge — owner confirmation or just "not a fake listing"?
- Does P-01 trust aggregated Google reviews or would they prefer to see Lookla-native reviews?

---

## P-02 — The Russian/Ukrainian Resident

**Role:** Visitor → User  
**Primary language:** Russian (ru) or Ukrainian (uk)  
**Location:** Athens (Marousi, Glyfada, Kallithea), Thessaloniki  
**Age range:** 25–55

**Context**  
Permanent or long-term resident of Greece. Has been in Greece for months or years. Speaks limited Greek. Finding services is a daily challenge — most business directories are in Greek and the Google Maps interface in their language doesn't translate salon names or service lists. Finding a hairdresser who can cut Slavic hair types, or simply finding any salon where someone speaks Russian, is genuinely difficult.

**Goals**  
- Find a salon with the specific services they need, described in their language
- Ideally find a salon where staff speaks Russian or Ukrainian
- Not have to rely on a Greek-speaking friend to help find a phone number

**Frustrations**  
- Beauty service names in Greek mean nothing to them
- Google Translate on a Greek salon website produces inaccurate results
- Cannot evaluate a salon from its reviews if they're all in Greek
- Phone calls to Greek-language staff are stressful

**Behaviours**  
- Searches in Russian using Cyrillic (маникюр, стрижка, покраска)
- Reads reviews only if they're in their language
- Strongly prefers WhatsApp over phone calls
- Likely to share a useful link with friends from the community

**Success looks like**  
Found a nail salon or hairdresser, read the services in Russian, saw that reviews were translated, tapped WhatsApp to message the salon.

**❓ Questions for Product Owner**  
- Is P-02 the primary MVP persona? This is the persona where Lookla has the strongest differentiated value over Google Maps.
- Should Lookla surface language-of-staff information? (Currently not in the data model.)
- Is the Russian/Ukrainian community in Greece large enough to be a measurable validation audience?
- Should WhatsApp be the primary CTA for this persona over phone?

---

## P-03 — The Expat or Tourist

**Role:** Visitor  
**Primary language:** English (en)  
**Location:** Athens (tourist areas), islands (seasonal), expat communities  
**Age range:** 20–45

**Context**  
Either a tourist visiting Greece for 1–2 weeks, or an English-speaking expat (EU citizen, digital nomad, international employee). Does not speak Greek. Relies entirely on English-language search results and recommendations. May be looking for a haircut before an event, a nail appointment, or a massage.

**Goals**  
- Find a beauty service quickly, near current location or hotel
- Confirm the salon is open today
- Book or contact without a language barrier

**Frustrations**  
- English-language Google results for beauty services in Greece are sparse and unreliable
- Most salon websites are Greek-only
- Airbnb hosts and hotel concierges give generic recommendations

**Behaviours**  
- Searches on mobile, often while in a location
- Checks photos first, rating second
- More likely to use online booking if available; otherwise will call or WhatsApp
- Higher price tolerance than local users

**Success looks like**  
Found an English-friendly salon nearby that's open, seen its services and approximate prices, contacted it.

**❓ Questions for Product Owner**  
- Is P-03 in scope for MVP or a secondary persona for a later stage?
- Does the platform need to surface "English spoken" as a searchable attribute? (Not in current data model.)
- Is tourist traffic a meaningful validation signal, or is it too seasonal?

---

## P-04 — The Salon Owner (Future)

**Role:** Salon Owner  
**Primary language:** Greek (el)  
**Location:** Any Greek city  
**Age range:** 30–55

**Context**  
Owns or manages a beauty business. Has little time for technology. May be listed on Lookla already (from crawler data) but doesn't know it. If they find out, they either want to update incorrect information or want to understand what benefit Lookla gives them.

**Goals**  
- Ensure their listing shows correct hours, address, and phone
- Understand how many people find them through Lookla
- Eventually: receive booking requests through the platform

**Frustrations**  
- Their Google Maps listing is sometimes wrong and they don't know how to fix it
- They have no visibility into which platforms send them customers
- They don't want to pay for another subscription service

**Behaviours**  
- Typically discovers Lookla when a client mentions it
- Will update a listing if the process is simple and free
- Deeply skeptical of subscription fees

**Success looks like**  
Found their salon on Lookla, claimed the listing in under 5 minutes, corrected the phone number, and started seeing "found via Lookla" mentions from clients.

**❓ Questions for Product Owner**  
- Is P-04 in scope for MVP or post-MVP?
- Is salon owner claiming part of MVP validation, or is it a separate experiment?
- What is the value proposition to a salon owner at zero cost? (They gain visibility, but how do we communicate that?)

---

## Persona Priority

❓ **DECISION REQUIRED — see MVP_DEFINITION.md Q-02**

| Persona | MVP Priority | Rationale |
|---|---|---|
| P-01 Greek Local | ❓ TBD | Largest group; highest competition |
| P-02 Russian/Ukrainian Resident | ❓ TBD | Strongest differentiation; underserved |
| P-03 Expat/Tourist | ❓ TBD | Seasonal; higher intent |
| P-04 Salon Owner | ❓ TBD | Future stage; needed for data quality |

---

*Last updated: 2026-07-09*
