---
title: Contact Page Specification
status: Approved
version: 1.0
owner: Product Owner (columb@europe.com)
reviewers: []
last_updated: 2026-07-09
related_documents:
  - 01_PRODUCT/MVP_SCOPE_LOCK.md
  - 03_PAGES/SALON.md
implementation_status: Not implemented — new page required for MVP
---

# Contact Page
**Lookla Beauty Marketplace**

---

## Purpose

The Contact page serves two audiences:

1. **Users** who want to report a problem with Lookla itself (not with a specific salon — that uses the Report button on the salon detail page)
2. **Salon owners** who want to inquire about their listing or request data correction before the owner claiming flow is available

This is a static informational page, not a functional tool. The primary mechanism for salon data corrections is still the "Report incorrect information" button on each salon page — this page is a landing point for users who navigate directly.

---

## Target Persona

- P-01, P-02, P-03: users who found a problem with platform behaviour
- P-04 (Salon Owner): discovered their listing and wants to contact Lookla before self-service claim is available

---

## Entry Points

| Source | How they arrive |
|---|---|
| Footer link | All pages → `/contact` |
| "For salon owners" CTA (future) | When owner landing page is added |
| Direct search ("contact lookla") | Organic |

---

## Page Content

### Section 1 — Intro

Short paragraph explaining that Lookla is a beauty salon directory for Greece and this is the way to reach the team.

### Section 2 — I want to report a salon listing issue

**Content:**
- "Use the Report button on the salon's page"
- Step-by-step: search for the salon → open its page → tap "Report incorrect information"
- This is the fastest way to get corrections into the queue

**Do not duplicate** the report form on this page. Direct the user to the salon page.

### Section 3 — I own a salon listed on Lookla

**Content:**
- Acknowledge they may have found their business listed from public sources
- Explain the data is aggregated, not user-submitted
- Inform them that a claiming flow will let them update their listing directly (coming soon)
- For now: send an email to `hello@lookla.gr` with the salon name and what needs to be corrected

**Note:** `/dashboard/claim` backend exists but is not user-facing in MVP (per FEATURE_FLAGS.md). This page should not link to it. Direct salon owners to email.

### Section 4 — General Inquiry

- Email: `hello@lookla.gr`
- Response time expectation: "We'll respond within 2–3 business days"

**No contact form required in MVP.** An email address is sufficient. A form introduces complexity (spam, email deliverability) that is not worth solving at this stage.

---

## Mobile Considerations

Static text page. Must be readable on mobile. No special mobile behaviour beyond standard responsive typography.

---

## Analytics Events

| Action | GA4 Event |
|---|---|
| Page viewed | `page_view` (automatic, GA4) |

No custom events required on this page.

---

## Implementation Notes

- Route: `/[locale]/contact`
- Render: SSR (static content)
- Create the page and add a link in the footer
- No form, no API calls, no auth requirement
- Localize all text into el/en/ru/uk

---

*Last updated: 2026-07-09*
