# Lookla — Terms of Service: brief for Greek legal review

**Prepared:** 2026-08-04 · **Document under review:** `frontend/app/[locale]/terms/content.ts` (17 sections, four locales)
**Status:** drafted, not published. The page returns 404 and the footer link is hidden until the operator disclosure is complete and this review is received.

This brief exists so the reviewing lawyer works from what the product actually does. Every factual statement below was verified against the running application, not assumed. Where something is unknown, it says so rather than guessing.

---

## 1. What Lookla is, factually

A directory of beauty salons and independent beauty professionals in Greece, at `lookla.gr`. Visitors search listings and contact businesses directly.

| Capability | Status, verified |
|---|---|
| Browsing and search | **Live** |
| Contacting a salon | **Live** — the listing shows the business's own phone/contact details |
| Online booking | **Not available.** Availability-request endpoints exist in the API, but no page links to them; a reservation cannot be made through the site |
| Messaging user ↔ salon | **Live** — `/account/messages` |
| User accounts | **Live**, open registration |
| Owner accounts | **Live** — a listing is claimed with a code sent to the contact address already held for that business |
| Reviews | **Live** |
| Reporting content | **Live** — a report button on listings and reviews |
| Paid subscriptions | **Cannot be bought.** The pricing page redirects to the homepage and no payment provider is configured. Plan data (Pro €29/month for salons, €14/month for professionals) is nonetheless returned by a public API endpoint |
| Automated content moderation | **Not in operation.** The code exists but is called from nowhere; nothing is screened before publication |
| Internal appeals procedure | **Does not exist** |

**Data provenance.** Most listings were compiled by an automated crawler from publicly available sources — Google, Vrisko, Treatwell and Foursquare — plus information submitted by owners. Business owners can claim a listing and correct it, or ask for removal by email without an account.

**Operator.** A natural person resident in Greece. There is no company, so no company registration number and no corporate VAT number exist.

---

## 2. Blocking question — the Article 5 disclosure

Article 5 of Directive 2000/31/EC requires an information-society service to make easily, directly and permanently accessible: the provider's name, the geographic address at which it is established, contact details including email, and — where applicable — registration and VAT details.

The document currently gives the name and `hello@lookla.gr`. **No geographic address is published, and none has been invented.** Publication is technically blocked until this is resolved.

Please advise on:

1. The correct legal spelling of the operator's name for this document.
2. Whether Lookla, as it stands (free to use, no transactions, no payments), is an information-society service provided by this natural person for the purposes of Article 5.
3. Whether the activity requires registration of professional or business activity in Greece, and whether that changes the disclosure.
4. Which address must be published — place of establishment, professional address, a service address, or a home address only if genuinely required. **The operator does not wish to publish a home address unless it is legally unavoidable.**
5. Whether a personal ΑΦΜ must appear in the public disclosure.
6. Whether `hello@lookla.gr` is sufficient as the address for legally significant communication, or whether a separate formal address is needed.

---

## 3. DSA classification (Regulation (EU) 2022/2065)

Lookla hosts information provided by its users: owner-submitted listing content, reviews, and messages. It has a reporting mechanism and can restrict or suspend accounts.

If Lookla is an intermediary or hosting service, Article 14 requires the terms to describe restrictions on user information, the policies, procedures, measures and tools used for content moderation, including algorithmic decision-making and human review, and the internal complaint-handling system.

The document already describes moderation accurately: no pre-publication screening, no automated removal or restriction, one automated step that flags a repeatedly-reported listing for a person to review, and no formal appeals procedure.

Please advise:

1. Whether Lookla falls within the DSA, and under which category.
2. Whether any exemption applies at this size.
3. Whether the present description satisfies Article 14, or whether more is required.
4. Whether a formal notice-and-action and internal complaint-handling procedure must be built. The existing reporting endpoint records a report and flags a listing for human review; it does not acknowledge receipt, give reasons, or offer an appeal.

---

## 4. Age and capacity

The document sets **16** as a Lookla eligibility rule for holding an account, and states explicitly that this is not a claim about the age Greek data-protection law sets. An earlier draft presented 16 as the legal threshold, which was wrong: Article 21 of Law 4624/2019 sets **15** for a minor's own consent to data processing.

Please advise:

1. Whether 16 is appropriate as a product minimum given what Lookla does.
2. What contractual capacity requires, separately from the data-protection threshold.
3. Whether the messaging feature changes the answer.
4. Whether any age-verification or parental-authorisation mechanism is required in practice.

---

## 5. Liability and jurisdiction

**Section 12** disclaims accuracy of listing data and responsibility for services provided by listed businesses, and preserves the carve-outs: no exclusion for death or personal injury caused by our negligence, for fraud, or for wilful misconduct and gross negligence, with mandatory consumer rights expressly unaffected.

**Section 14** states Greek law, preserves the consumer's right to the mandatory rules and courts of their country of residence, and adds a neutral statement that nothing limits a mandatory right to an available out-of-court procedure. The EU ODR platform is deliberately **not** cited: Regulation (EU) 2024/3228 repealed the ODR Regulation with effect from 20 July 2025 and the platform stopped accepting complaints on 20 March 2025.

Please advise:

1. Whether the remaining limitation in Section 12 is enforceable against a Greek consumer.
2. Whether the Section 14 clause is compatible with Rome I and Brussels I recast for consumers.
3. Whether a specific Greek ADR body should be named, and if so which. None has been named without confirmation that it applies to a service with no paid transactions.

---

## 6. Crawled data

Section 3 discloses that listings were compiled from Google, Vrisko, Treatwell and Foursquare, states that information may be out of date or wrong, advises users to confirm details with the business, and offers correction and removal.

Please advise whether this wording is adequate under Greek unfair-competition law and EU database rights, and whether the disclosure of sources itself creates any exposure.

---

## 7. Acceptance

There is **no acceptance checkbox** at registration, and the document says so, explaining that it would imply a determination about where assent is legally required that has not been made.

Please advise where assent is required, what it must cover, and whether a version-stamped acceptance record must be stored. If a control is needed, it will be implemented together with the version reference and the evidence-storage contract — a test currently fails if a checkbox appears without them.

---

## 8. What we are asking for

Either a written opinion, or precise required edits. Both are actionable. Publication stays technically blocked until the operator disclosure is complete and this review is on file.

Contact for this review: `hello@lookla.gr`.
