---
title: About Page Specification
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 01_PRODUCT/PRODUCT_VISION.md
  - 01_PRODUCT/PRODUCT_SCOPE.md
  - 03_PAGES/CONTACT.md
implementation_status: Not implemented — new page required for MVP
---

# About Page
**Lookla Beauty Marketplace**

---

## Purpose

The About page builds trust with two audiences:

1. **First-time visitors** who want to understand what Lookla is and why it exists before trusting it with their search
2. **Salon owners** who discovered their listing and want to know what Lookla is and whether they should be concerned

This is a static marketing/trust page. It must be honest, simple, and consistent with the Product Vision.

---

## Entry Points

| Source | How they arrive |
|---|---|
| Footer link | All pages → `/about` |
| Direct organic search | "What is Lookla" |
| Referral link | Someone explains Lookla and links to this page |

---

## Page Content

### Section 1 — What Lookla is

Short paragraph (3–5 sentences) derived from PRODUCT_VISION.md:

- A multilingual beauty salon directory for Greece
- Data aggregated from public sources; no fake listings
- Available in Greek, English, Russian, and Ukrainian
- Independent, not funded by commissions from salons

Tone: clear, direct, trustworthy. Not marketing-speak. Not hyperbole.

### Section 2 — Who we serve

Two audiences called out directly:

**People looking for beauty services**
- Finding beauty services in Greece is harder than it should be, especially for non-Greek speakers
- Lookla gives you real hours, real contacts, and service information in your language
- No account required to search or contact a salon

**Salon owners**
- If your salon appears on Lookla, it was discovered from public information (Google, directories)
- You can report data corrections via the Report button on your listing
- A self-service claiming flow is being built (link to Contact page for now)
- There is no fee. Lookla does not charge commissions or require subscriptions.

### Section 3 — What Lookla is not

Derived from PRODUCT_SCOPE.md:

- Not a booking platform (no online appointments in this version)
- Not affiliated with Google Reviews (reviews are aggregated and labelled as such)
- Not a salon management tool (CRM, scheduling, POS)
- Not an advertising platform

### Section 4 — Data and privacy

Brief, honest statement:
- Data is collected from public sources
- No user data is sold
- Analytics: GA4 is used to understand how the platform is used (link to Privacy Policy)

### Section 5 — Link to Contact

"Have a question? See the Contact page."

---

## Tone

Matches Product Vision: honest, multilingual, community-first. Not corporate. Not startup-pitch mode.

Avoids:
- Buzzwords ("disrupt", "revolutionize", "the future of beauty")
- Unverifiable claims ("the best", "the most complete")
- Marketing promises about features that don't exist yet

---

## Mobile Considerations

Static text page. Readable on mobile. No special behaviour.

---

## Analytics Events

| Action | GA4 Event |
|---|---|
| Page viewed | `page_view` (automatic) |

No custom events required.

---

## Implementation Notes

- Route: `/[locale]/about`
- Render: SSR (static)
- Localize all content into el/en/ru/uk
- Add footer link from all pages
- No auth requirement
- No API calls

---

*Last updated: 2026-07-09*
