# Lookla — what still needs a Greek lawyer, for a read-only catalogue release

**Prepared:** 2026-08-11 · **Replaces the scope of:** `T-045_LEGAL_REVIEW_BRIEF.md`, which was written when Lookla was a platform
**Companion:** `TERMS_LEGAL_EXTRACT.md` — the five sections of the drafted Terms, verbatim

The product changed between the brief and today. Most of what the brief asked about is now switched off, and the questions that remain are fewer and sharper. Nothing has been dropped: everything the brief asked is either **live** below, **deferred** with the capability it belongs to, or **moot** because the feature is gone.

---

## 1. What Lookla is now, verified

A **directory**. A visitor searches listings, reads them, and contacts the business themselves.

> Lookla shows reference information and helps you contact a salon directly.
> Lookla does not take or confirm appointments, is not a party to any contract,
> and takes no payments.

| Capability | State, verified in code and against the API |
|---|---|
| Search, browse, salon detail | **Live** |
| Contacting a salon | **Live** — Call / WhatsApp / Visit website, ordinary links to the business's own details; following one leaves the site |
| Imported reviews | **Live**, displayed with author name |
| Reporting a listing or review | **Live** |
| Analytics | GA4, script not rendered until consent is granted |
| User registration and accounts | **Off** — the endpoint answers 404 |
| Messaging | **Off** — 404 |
| Claiming a listing, owner self-editing | **Off** — 404 |
| Payments | **Off** — 404, and the plan prices are no longer served |
| Booking, availability requests | **Removed**, not switched off |

Nothing a *user* submits appears in public. Every public listing and every public review was selected and published by Lookla itself.

**Operator, confirmed:** no company, no ΓΕΜΗ number, no corporate ΑΦΜ. A natural person in Greece.
**Published contact:** `hello@lookla.gr` generally, `admin@lookla.gr` for legally significant communication — a distinct address, on the operator's instruction. Confirmed as receiving.
**Not published:** the geographic address. See question 1 below — this is the point most in need of your reasoning in writing.

---

## 2. Questions that block publication

### 2.1 The Article 5 disclosure

1. **Must the geographic address be published?** The operator's position, taken on advice, is that it need not be. Article 5(1)(b) of Directive 2000/31/EC on its face requires *"the geographic address at which the service provider is established"*, so this departs from the plain wording. It may well be right — there are arguments about what "established" means for a natural person with no registered activity, and about what a supervisory authority requires in practice — but the file needs the reasoning, not the conclusion. **Publication stays blocked until this is on record.**
2. The correct legal spelling of the operator's name for the disclosure. Currently *"Zhuykov Andrey"*, taken from project documentation and **never checked against a passport or the Greek tax register**.
3. Does operating a free directory of this kind require registration of professional activity in Greece (`έναρξη ατομικής δραστηριότητας`), and does that change the disclosure?
4. Must a personal ΑΦΜ appear in a public disclosure?
5. Is a distinct address for legally significant communication the right arrangement, or should one address serve both purposes?

### 2.2 The catalogue itself — now the central question

The whole product is compiled data. With everything user-facing switched off, this is no longer one issue among many.

6. On what basis may a directory of 6,365 active Greek business listings, compiled by an automated crawler from Google, Vrisko, Treatwell and Foursquare, be published? Consider EU database rights, the terms of those sources, and Greek unfair-competition law.
7. The listings disclose their sources and offer correction and removal by email. Is that adequate, and does disclosing the sources itself create exposure?
8. Business contact details — name, address, phone — of sole traders are personal data. What is the lawful basis for publishing them, and what must the privacy notice say about it?

### 2.3 Reviews, which are staying

Reviews were considered for removal and deliberately kept. So the obligations they carry stay live: **26,204 review rows carry an author's display name**, and **6,338 crawler payloads carry a reviewer photo URI and profile link** (the latter are not displayed and are scheduled for removal from storage).

9. With no user accounts, every published review was imported and published by Lookla. Does that make Lookla a **hosting service or online platform** under the DSA, or an editorial publisher of third-party content — and does the answer change the moderation obligations?
10. If the DSA applies: does the exemption for micro and small enterprises cover Article 20's internal complaint-handling? What is the minimum notice-and-action mechanism required? Is registration with EETT required?
11. What is the lawful basis for publishing a named third party's review text, and what must a suppression procedure guarantee when that person objects? A suppression record exists in the product: it survives re-import, matches by identity *and* by fingerprint so that editing a display name does not defeat it, and it never deletes silently.
12. Does displaying the reviewer's **name** change the answer relative to publishing the text anonymously?

### 2.4 The four documents of a read-only release

13. **Legal Notice**, **Privacy Policy**, **Cookie Policy**, **Website Terms** — is that the right set, and does anything else have to be published?
14. With nobody registering and nobody submitting anything, is any acceptance mechanism required at all? The drafted Terms have **no acceptance checkbox** and say so explicitly; a test in the codebase fails if a checkbox appears without a version reference and an evidence-storage contract.
15. GA4 loads only after consent is granted, and the script is not rendered before it. Is a consent banner on those terms sufficient, and does the Cookie Policy need more than a short statement?
16. §12 (disclaimers) and §14 (governing law) as drafted — see the companion document. Is the remaining limitation in §12 enforceable against a Greek consumer, and is §14 compatible with Rome I and Brussels I recast? The EU ODR platform is deliberately not cited: Regulation (EU) 2024/3228 repealed the ODR Regulation from 20 July 2025 and the platform stopped accepting complaints on 20 March 2025. Should a Greek ADR body be named instead, and which?

---

## 3. Deferred — they return with the capability

Not asked now, recorded so they are not lost. Each comes back **before** the switch is flipped, not after.

| Returning capability | Questions it brings back |
|---|---|
| Owner claiming and self-editing (**next**) | owner's acceptance of terms with a version; confirmation of authority to act for the business and of being 18; whether owner-edited listings make Lookla an online platform; illegal-content notice form; acknowledgement and outcome notification; reasons given for removal |
| User accounts and messaging | age threshold — the product sets 16, while Article 21 of Law 4624/2019 sets 15 for a minor's own consent to processing, and contractual capacity is a separate question; acceptance record; rules for user-submitted content; retention of correspondence; safety of minors in messaging |
| Payments | consumer contract, right of withdrawal, invoicing, VAT, and whatever the payment provider requires |

## 4. Moot — the feature is gone

Online booking and availability requests were **removed from the code**, not switched off: both endpoints answer 404 and there are tests that fail if either returns anything else. So the marketplace-qualification question, the consumer-contract questions that came with taking a reservation, and the risk of a false confirmation no longer arise. If booking is ever built, they return with it.

---

## 5. What is being asked for

Either a written opinion, or precise required edits — both are actionable, and the second is faster to apply.

**Publication of the Terms is technically blocked** until the review is on file: the page returns 404 and the footer link is hidden, enforced by tests, so no unrelated deployment can turn a partial disclosure into a live one.

Question 1 is the single item blocking the first release. Everything else can follow.

Contact for this review: `admin@lookla.gr`.
