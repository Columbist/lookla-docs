---
title: Privacy Operations — Manual SOPs and Legitimate Interest Assessments
status: Approved
version: 1.0
owner: Zhuykov Andrey (data controller, hello@lookla.gr)
reviewers: []
last_updated: 2026-07-17
related_documents:
  - 04_ARCHITECTURE/SECURITY.md
  - 04_ARCHITECTURE/DATA_FLOW.md
  - 05_ROADMAP/IMPLEMENTATION_BACKLOG.md
implementation_status: Manual/operational — backs the public Privacy Policy (frontend/app/[locale]/privacy). Not itself published as a user-facing page.
---

# Privacy Operations

This document is the internal operational backing for the claims made in the public Privacy Policy (`frontend/app/[locale]/privacy`). The policy states specific retention targets and rights-response commitments; this document is *how* those commitments are actually met today, given that T-047/T-048 (automated deletion jobs, account-deletion workflow) have not shipped yet. It also contains the Legitimate Interest Assessments referenced by the policy's Section 2 (Purposes and legal bases), and the minor-account handling procedure referenced by Section 12 (Children).

**Operator today:** a single person (Zhuykov Andrey, the data controller). There is no support team. Every procedure below assumes one person executes it — deliberately simple rather than assuming operational capacity that doesn't exist yet.

**Where these procedures run:** all data lives in the `beauty_db` Postgres container. Every action below is a `psql` query run directly against production by the controller, following the project's existing read-only-first convention (`BEGIN ...; ...; COMMIT;` for anything destructive, always preceded by a `SELECT` to confirm the target rows before any `UPDATE`/`DELETE`).

---

## 1. Data-subject request SOP (access, rectification, erasure, restriction)

**Trigger:** an email to `hello@lookla.gr`.

**Step 1 — Log the request.** Record in a private, dated log (kept outside the public docs tree — see "Tracking," below): requester email, date received, request type, and the target completion date (received date + 1 month, per the policy's response-timing statement).

**Step 2 — Verify identity.** Confirm the request comes from the email address on the account. If the request arrives from a different address, ask the requester to confirm from the account's registered email, or to provide information reasonably sufficient to confirm account ownership (per the policy's identity-verification statement) — e.g. approximate registration date, last salon they messaged. Do not demand government ID for a simple account-data request; that would be disproportionate for the risk level of this MVP.

**Step 3 — Locate the account.** `SELECT id, email, name, created_at FROM users WHERE email = :email;`

**Step 4 — Execute the request, by type:**

- **Access / export:** query and hand the requester a plain-text or JSON summary of: `users` row (excluding `password_hash`), `messages` where they are sender, `availability_requests`/`appointments` where they are the client, `reports` they filed, `salon_owners` rows linking them to a salon. Send via the same email thread.

- **Rectification:** update the specific field(s) directly (`UPDATE users SET name = :new WHERE id = :id;` etc.) after confirming the correction with the requester.

- **Erasure (account deletion), target: 30 days from request.**
  Because several tables have a `NOT NULL` foreign key to `users.id` (e.g. `messages.sender_user_id`, confirmed via `chat.py`'s `JOIN users u ON m.sender_user_id = u.id`), a hard `DELETE FROM users` would break referential integrity and destroy the *other* party's conversation history in a shared conversation. The MVP approach is **anonymize in place**, not hard-delete the row. This is a checklist, not a single step — every item below must be worked through, not just the `users` row:

  1. **`users` row** — `UPDATE users SET email = 'deleted-user-' || id || '@lookla.gr', password_hash = '', name = 'Deleted user', phone = NULL, viber_phone = NULL, whatsapp_phone = NULL, avatar_url = NULL, google_id = NULL, is_active = false WHERE id = :id;` — clears email, password, name, phone, WhatsApp, Viber, avatar, and the Google account ID (`sub`) in one statement, and disables login.
  2. **Verification/reset tokens** — `DELETE FROM email_verifications WHERE user_id = :id;` and `DELETE FROM password_resets WHERE user_id = :id;`.
  3. **Sessions** — `DELETE FROM refresh_tokens WHERE user_id = :id;` (also sign the user out by invalidating the `access_token`/`refresh_token` cookies if they still hold an active browser session).
  4. **Reports** — `UPDATE reports SET reporter_user_id = NULL WHERE reporter_user_id = :id;` (the `reporter_ip` and report content stay, per the report-retention target below and the anti-abuse legitimate interest — only the link to this specific person is removed).
  5. **Salon-owner claim associations** — review `salon_owners` rows for this `user_id` manually before touching them; removing a live salon's owner link has a business-visible effect on that salon's "Owner verified" status (T-011). Confirm with the requester whether they also want the salon-owner relationship removed, or only their personal account data.
  6. **Availability requests / appointments** — for rows where `client_user_id = :id`, anonymize `client_name` and `client_phone` on the row itself (same placeholder pattern as step 1), rather than deleting the row outright — a salon may have a legitimate business reason to retain the fact that an appointment happened, distinct from *who* it was with. Also check `service_notes`/`reply_text` on these rows for free text — see step 7.
  7. **Free text — messages and notes, reviewed manually, not auto-scrubbed.** Replacing the `users` row does not remove personal data the person may have *typed into free text* elsewhere — a phone number or full name written directly into a message body or an availability-request note survives step 1 untouched. There is no automated free-text PII scrubber today; this step is a manual read-through, not optional:
     - Read every `messages.body` where `sender_user_id = :id` (or where the conversation involves this user, if reviewing from the other direction). Where a message contains personal data typed by the requester (a phone number, an email, a full name), redact only that specific text in place (`UPDATE messages SET body = '[redacted]' WHERE id = :message_id;` or a targeted string replacement) — do not delete the surrounding message or conversation, which would remove the other party's legitimate record of what was discussed.
     - Read `service_notes` and `reply_text` on this user's `availability_requests` rows for the same reason, and redact in place if personal data is found beyond the already-anonymized `client_name`/`client_phone` fields.
     - Record in the completion log which messages/notes (if any) were redacted, separately from the account-level anonymization — this is a distinct action with its own judgment call, not automatic.
  8. Record the completion date in the log.
  9. The anonymized row (and any redacted messages/notes) will also age out of any *pre*-anonymization backup within 7 days, per the already-published backup rotation.

- **Restriction:** set `is_active = false` on the `users` row (already-existing column) to block login/authentication while a dispute is resolved, without deleting anything.

**Step 5 — Confirm to the requester** that the action is complete, in the same email thread.

---

## 2. Periodic retention cleanup (manual, until T-048 automates it)

**Cadence: monthly, not quarterly.** A quarterly cadence against a 12-month target allows actual retention to reach up to ~15 months in the worst case (a row that crosses the 12-month line the day after a cleanup run waits a further 3 months for the next one). A monthly cadence bounds the worst case to ~13 months, which is close enough to the stated 12-month target to be an honest match for a "target" figure rather than a guaranteed exact cutoff. Run on the **1st of every month** by the controller, as a `psql` session against production:

1. **Messages/conversations** — `SELECT id, last_message_at FROM conversations WHERE last_message_at < NOW() - INTERVAL '12 months';` review the list, then delete the conversation's `messages` rows and the `conversations` row itself for any where the associated account is already anonymized/inactive, or where both parties' last activity is >12 months old.
2. **Availability requests / appointments** — `SELECT id, created_at FROM availability_requests WHERE created_at < NOW() - INTERVAL '12 months';` and the equivalent for `appointments.starts_at`; delete rows past the window.
3. **Reports** — `SELECT id, created_at FROM reports WHERE created_at < NOW() - INTERVAL '12 months';` delete rows past the window (this also removes the associated `reporter_ip`).
4. **Salon-owner claims** — `salon_owners` currently has no status/end-date column (flagged in T-048), so there is no 12-month clock to run at all for this table — the public policy's wording for claims was corrected (2026-07-17) to reflect this honestly: claim records are retained while the ownership link is active, and removed manually on discovery that a claim is no longer valid, not on a fixed post-end timer. Include a check for obviously-stale claims (e.g. cross-reference against salons that appear closed/duplicate via the `reports` table) in this monthly run as a best-effort discovery mechanism, but do not claim this guarantees timely removal — that requires the schema change tracked in T-048.

Record each monthly run (date executed, row counts affected) in the private log.

---

## 3. Minor-account handling procedure

Referenced by the public policy's Section 12 (Children): *"If we learn that a minor has created an account, we may request reasonable verification and delete or restrict the account and its associated personal data."*

**Trigger:** a report from any source (the account holder themselves, a parent/guardian, another user, or the controller noticing something during normal operation) that an account may belong to someone under 18.

**Step 1 — Reviewer.** The controller reviews every such report personally (single point of contact today).

**Step 2 — Verification.** Request reasonable confirmation from whoever raised the concern, or from the account holder directly (e.g. asking them to confirm their age). This is *not* a formal ID-check process — consistent with the public policy not claiming a technical age-verification system exists. The bar is "reasonable," not "certain."

**Step 3 — Once confirmed, act promptly** (target: within 5 business days of confirmation — a proactive child-safety action, handled faster than the general 1-month data-subject-request SLA, which governs requests *from* the account holder, not reports *about* them). Work through the full checklist in Section 1 step "Erasure," items 1–7, exactly as for a self-requested erasure — including the mandatory free-text review of this account's messages and availability-request notes (Section 1, item 7), since a minor may have typed a real name, phone number, or other identifying detail directly into a message even though the account profile itself is anonymized. Additionally for this case specifically:
1. `UPDATE users SET is_active = false WHERE id = :id;` — do this *first*, immediately on confirmation, before working through the rest of the checklist, to stop further use of the account without waiting for the full erasure process to complete.
2. If an appointment tied to this account is still pending (in the future), the controller manually contacts the salon to inform them the booking is cancelled — there is no automated appointment-cancellation notification today (a gap already disclosed in the public policy's Security section, regarding appointment confirmations generally).
3. Any salon-owner claim linked to the account is reviewed as a priority, not deferred — a minor should not be a salon's registered owner.

**Step 4 — Record** the report date, verification outcome, and actions taken in the private log.

---

## 4. Legitimate Interest Assessments

The public policy's Section 2 states five processing activities rely on Lookla's legitimate interest as their GDPR legal basis. Each assessment below follows the standard three-part test: **purpose** (is there a real, specific interest?), **necessity** (is this processing actually needed to achieve it, with no less intrusive way?), and **balancing** (does the interest outweigh the individual's rights and expectations?).

### 4.1 Public reviewer names and review text

- **Purpose:** displaying attributed reviews is the core trust mechanism of a review-aggregating marketplace — an unattributed review carries far less credibility for a user choosing a salon.
- **Necessity:** the reviewer's name is already public on the source platform (typically Google), which the reviewer chose to post to. Lookla republishes what is already public rather than collecting anything new; there is no less intrusive way to provide the same trust signal (a fully anonymized review would defeat the purpose).
- **Balancing:** reviewers are not Lookla users and have no direct relationship with Lookla, which weighs against processing. In favor: the review was already voluntarily made public by the reviewer on a comparable platform for a comparable purpose (helping other consumers), so the reuse is not a surprising or out-of-context one; Lookla discloses the source ("Source: Google Reviews," T-012) rather than obscuring provenance; no additional reviewer data is collected beyond name, rating, and review text (no photo, no profile link, no reviewer ID).
- **Conclusion:** legitimate interest applies. Mitigation already in place: source attribution label. Any reviewer who objects can be accommodated via `hello@lookla.gr` — removal of a specific review on a legitimate objection is operationally simple (delete the `reviews` row).

### 4.2 Professional/staff names

- **Purpose:** showing which staff work at a salon is core directory utility — helping a user pick a stylist or technician.
- **Necessity:** the name is already part of the business's own public listing (source platform); no less intrusive alternative conveys "who works here."
- **Balancing:** staff are named in a professional/business capacity, not as private individuals in a personal context — a materially lower privacy expectation than, say, a home address. Minimal fields only (name, role, optional bio/photo, all sourced from the crawled listing).
- **Conclusion:** legitimate interest applies; low risk. Removal on request via `hello@lookla.gr`.

### 4.3 Business contact data (salon phone/email/website)

- **Purpose:** enabling a user to contact a business is the core function of the marketplace.
- **Necessity:** essential — no alternative achieves the purpose of a business directory.
- **Balancing:** this is a commercial entity's public-facing contact data, already published by the business itself elsewhere; an extremely low privacy expectation applies (this is business data, not an individual's personal contact information).
- **Conclusion:** clearly legitimate; proceed without further mitigation.

### 4.4 Report/IP anti-abuse processing

- **Purpose:** preventing abuse of the report feature (e.g. repeated fake reports intended to get a legitimate listing wrongly flagged or removed).
- **Necessity:** IP-based deduplication is a standard, proportionate anti-abuse technique for an unauthenticated-capable endpoint; without it, the report feature is trivially abusable.
- **Balancing:** the IP address is used solely for duplicate-detection matching (`reports.py`'s dedup query), is not published, not cross-referenced with any other system, not used for tracking or marketing, and is retained only 12 months (Section 9 of the policy).
- **Conclusion:** legitimate interest applies; processing is minimal and proportionate to the anti-abuse purpose.

### 4.5 OpenAI translation of public review/service text

- **Purpose:** multilingual accessibility of already-public directory content is a stated, core part of Lookla's product (4 supported locales).
- **Necessity:** machine translation is the only practical way to provide 4-language coverage of thousands of crawled listings without prohibitive manual-translation cost; no less intrusive alternative exists at this scale.
- **Balancing:** verified (T-017 Section 6/8) that only the plain review/service text is sent — no reviewer name, rating, salon ID, or Lookla user identifier is included in the request. The content is already public. OpenAI processes EEA customers' data under contract with OpenAI Ireland (Section 8). Incremental risk from translation alone is low.
- **Conclusion:** legitimate interest applies.

**Review cadence:** these assessments should be revisited if the underlying processing changes materially (e.g. if OpenAI's data-handling terms change, or if a reviewer/professional formally objects and a pattern of objections emerges), not on a fixed schedule.

---

## 5. Tracking

A private, dated log of data-subject requests, minor-account reports, and monthly cleanup runs is kept by the controller outside this (public) documentation tree — this file records the *procedure*, not a live register of individual requests, which would itself be personal data.
