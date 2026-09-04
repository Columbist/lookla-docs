# Lookla — Terms extract for legal review: liability, jurisdiction, age, moderation, acceptance

**Prepared:** 2026-08-10 · **Source of truth:** `frontend/app/[locale]/terms/content.ts` (17 sections, four locales: el, en, ru, uk)
**Status:** drafted, **not published**. `/terms` returns 404 and the footer link is hidden while `TERMS_PUBLICATION_ENABLED = false`. The gate opens only when the Article 5 operator disclosure is complete **and** this review is on file.

The English wording is reproduced below verbatim. The Greek, Russian and Ukrainian versions are translations of the same sections in the same file; if any wording changes as a result of this review, all four change together.

Everything in §7 below was verified against the running production system on 2026-08-10 — by calling the live API and reading the deployed code, not by reading documentation. Where a statement is unverified, it says so.

---

## 1. §12 — Disclaimers and limitation of liability

> Lookla is provided as it is. We do not promise that the site will be uninterrupted or error-free, that listing information is accurate, or that any salon will be suitable for you.
>
> We are not responsible for the services provided by salons or professionals found through Lookla, for their conduct, or for any agreement you make with them. Complaints about a service belong to the business that provided it.
>
> Nothing in these Terms excludes or limits our liability where the law does not allow it — including liability for death or personal injury caused by our negligence, for fraud, or for wilful misconduct or gross negligence. Your mandatory rights as a consumer under Greek and EU law are not affected by these Terms.

**Question:** is the remaining limitation enforceable against a Greek consumer?

---

## 2. §14 — Governing law and jurisdiction

> These Terms are governed by Greek law.
>
> If you are a consumer, this does not deprive you of the protection of the mandatory rules of the country in which you live, and you may bring proceedings in the courts of that country.
>
> Nothing in these Terms limits any mandatory right you may have to seek an available out-of-court dispute resolution procedure, or to bring a claim before a competent court.

The EU ODR platform is **deliberately not cited**: Regulation (EU) 2024/3228 repealed the ODR Regulation with effect from 20 July 2025, and the platform stopped accepting complaints on 20 March 2025. No specific Greek ADR body has been named, because it has not been confirmed that any applies to a service with no paid transactions.

**Questions:** is this compatible with Rome I and Brussels I recast for consumers? Should a specific Greek ADR body be named, and which?

---

## 3. Age — §4, second paragraph

> You must be at least 16 years old to create or use a Lookla account. This is a Lookla eligibility rule. It is not a statement that Greek data-protection law generally sets the relevant age at 16 — Greek law sets its own threshold for a minor's consent to data processing, which is a separate question from who may hold an account here.

The wording is careful on purpose. An earlier draft presented 16 as *the legal threshold*, which was wrong: **Article 21 of Law 4624/2019 sets 15** for a minor's own consent to data processing. The two questions — who may hold an account, and who may consent to processing — are separate, and the document no longer conflates them.

No age verification exists. Registration asks for an email address and does not ask for, or check, a date of birth.

**Questions:** is 16 appropriate as a product minimum for what Lookla actually does? What does contractual capacity require, separately from the data-protection threshold? Does the messaging feature change the answer? Is any verification or parental authorisation required in practice?

---

## 4. Moderation — §9, plus the removal power in §7

> Listings and reviews carry a report control. If you believe something is inaccurate, unlawful or abusive, report it, or write to hello@lookla.gr.
>
> Reports are read by a person, not decided automatically. Depending on what we find we may correct the content, remove it, contact the person who posted it, restrict or suspend an account, or take no action.
>
> To describe our moderation accurately: we do not automatically screen or filter content before it is published, and no decision to remove content or restrict an account is taken by an automated system. The only automated step is that a listing which attracts several reports about the same issue is flagged for a person to look at; the flag itself changes nothing that you can see.
>
> We do not currently operate a formal internal complaints or appeals procedure. If you disagree with a decision, write to hello@lookla.gr and a person will look at it again. If we are required to provide a formal complaint-handling procedure, we will build one and update these Terms before relying on it.

From §7:

> We may remove content that breaks these Terms, that is reported and found to break them, or that we are legally required to remove. We are not obliged to monitor content in advance, and removing one thing does not mean we have reviewed everything else.

**Verified state of the code, which is narrower than even this describes:** the automated moderation module exists but is **called from nowhere**. Nothing is screened, flagged or scored automatically today. The reporting endpoint records a report and can flag a listing for human review; it does not acknowledge receipt, give reasons, or offer an appeal.

**Questions (DSA, Regulation (EU) 2022/2065):** does Lookla fall within the DSA, and under which category? Does any exemption apply at this size? Does the present description satisfy Article 14? Must a formal notice-and-action and internal complaint-handling procedure be built?

---

## 5. Acceptance mechanics — §2

> By using Lookla you accept these Terms. If you do not accept them, please do not use the site.
>
> We deliberately do not ask you to tick a box saying you accept these Terms when you register. A tick-box would suggest we had determined exactly where acceptance is legally required and what it covers, and we have not yet had that determined. Until we have, we would rather state plainly that use of the site constitutes acceptance than collect a consent record that looks more considered than it is.

**Verified:** there is no acceptance checkbox at registration, and no acceptance record of any kind is stored. A test in the repository fails if a checkbox appears without a version reference and an evidence-storage contract, so the control cannot be added by accident without the record behind it.

**Questions:** where is assent required, and what must it cover? Must a version-stamped acceptance record be stored?

---

## 6. Answer — can a salon publicly edit its listing or upload content today?

**Editing: yes, immediately and without review. Uploading: no.**

Verified in the deployed code and against the live API.

**What an owner can change.** After claiming a listing (login required, and ownership is verified by a code sent to the contact address already held for that business), the dashboard at `/dashboard/salon/[id]` calls these endpoints, each of which checks ownership before writing:

| Endpoint | Effect |
|---|---|
| `PUT /api/owner/salons/{id}` | name, phones, email, website, street, street number |
| `POST` / `PUT` / `DELETE /api/owner/salons/{id}/services/...` | add, edit and delete services with prices |
| `PUT /api/owner/salons/{id}/hours` | opening hours |
| `PUT /api/owner/salons/{id}/social-links` | social profile links |

**No moderation stands between the owner and the public page.** `update_salon` writes straight to the `salons` table; the public API reads the same rows. There is no draft state, no approval queue and no review step on this path — an edit is live as soon as it is saved. Unauthenticated calls to these endpoints return **401**, verified against production.

**Uploading content: not possible.** `media.py` exposes a single **GET** photo proxy and no upload route at all. Photos in the system were imported by the crawler from public sources. There is no endpoint through which an owner, or anyone else, can upload an image or file. (Consistent with the standing note that `r2.py` has no delete function — the moment an upload endpoint is added, an external-deletion obligation becomes real and unimplemented.)

**Free-text an owner can publish:** service names and descriptions, and the salon fields above. Not arbitrary media.

---

## 7. Answer — does an action in Lookla create a confirmed record, or does the service only pass on a message or contact?

**Lookla only passes contact through, and creates no reservation.** Until 2026-08-10 that was true of the interface and false of the API; the section below records what existed, because the difference mattered and because it is what the review was commissioned against.

### What the interface offers

The salon page offers **"Call" / "WhatsApp" / "Visit website"**. These are ordinary links to the business's own details; following one leaves Lookla, and nothing is recorded as an appointment. There are **no booking buttons** — verified on a live salon page.

Messaging (`/account/messages`) is live between a signed-in user and a salon. It stores conversations and messages. That is a record of a communication, not of a reservation, and nothing in it asserts that a salon has agreed to anything.

### What the API offered until 2026-08-10, and no longer does

Recorded because it was true when this review was commissioned, and because the
Terms describe what the product does.

Two endpoints existed, were mounted and answered in production, though no page
linked to them:

- `POST /api/bookings` — created an `appointments` row with `status: "pending"`
  and replied *"Booking created. You will receive a confirmation."*
  Authentication was **optional**.
- `POST /api/chat/availability-requests` — created an `availability_requests`
  row, also with optional authentication. Verified live: an unauthenticated
  request with an empty JSON body returned **201 Created**.

A third path, `POST /api/chat/availability-requests/{id}/confirm`, inserted an
appointment with `status: 'confirmed'` once the salon had proposed a slot. It
required authentication and required the salon to act first, so it was not an
anonymous hole — but it was the one place in the product that produced a
confirmed reservation.

**All of it was removed on 2026-08-10** (T-082), together with an account-page
tile linking to `/account/bookings`, a page that returned 404. Online booking
is outside the MVP scope. The `appointments` and `availability_requests` tables
were kept — they are documented in the personal-data matrix and covered by
retention policies — but nothing writes to them.

### The answer, as the product now stands

**Lookla creates no reservation record at all — neither confirmed nor pending.**
It displays the business's own contact details and gets out of the way: "Call",
"WhatsApp" and "Visit website" are ordinary links, and following one leaves the
site.

The only records a user action creates are a conversation and its messages.
Those record that two parties communicated. They assert nothing about a salon
having accepted anything, and no status anywhere in the system represents a
salon's agreement.

This is now true by construction rather than by nobody having called the
endpoints: tests fail if any of those routes answers anything other than 404,
and they call the application the way the original probe did — empty body, no
credentials — rather than inspecting a dependency list.

## 8. What is being asked for

Either a written opinion, or precise required edits — both are actionable. Publication stays technically blocked until the operator disclosure is complete and this review is on file.

This document accompanies `T-045_LEGAL_REVIEW_BRIEF.md`, which sets out what the product does in full, the Article 5 disclosure question, and the remaining areas (crawled data, intellectual property, paid plans).

Contact for this review: `hello@lookla.gr`.
