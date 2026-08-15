---
title: Privacy Operations — Manual SOPs and Legitimate Interest Assessments
status: Approved
version: 1.5
owner: Zhuykov Andrey (data controller, hello@lookla.gr)
reviewers: []
last_updated: 2026-08-06
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

- **Access / export:** the export walks **the same matrix as erasure** (`PERSONAL_DATA_MATRIX.md` §2), not a shorter hand-written list — a subject whose professional profile, webhooks, moderation submissions or second-role records were omitted has not received their data. Cover at minimum: the `users` row (excluding `password_hash`), `messages` where they are sender, `conversations` they belong to, `availability_requests`/`appointments` where they are the client, `reports` they filed, `moderation_queue` rows they submitted, `salon_owners` rows linking them to a salon, `professionals` and its child rows if they are a professional, and `webhooks` they own. Alongside the data itself, state the **purposes**, the **categories**, the **recipients** and the **retention period** for each — a copy of the data alone is an incomplete answer. Send via the same email thread.

- **Rectification:** update the specific field(s) directly (`UPDATE users SET name = :new WHERE id = :id;` etc.) after confirming the correction with the requester.

- **Erasure (account deletion), target: 30 days from request.**
  Because several tables have a `NOT NULL` foreign key to `users.id` (e.g. `messages.sender_user_id`, confirmed via `chat.py`'s `JOIN users u ON m.sender_user_id = u.id`), a hard `DELETE FROM users` would break referential integrity and destroy the *other* party's conversation history in a shared conversation. The MVP approach is **pseudonymise in place** (previously described here as "anonymize"), not hard-delete the row — the stable `users.id` and the history referencing it survive on purpose, so the result reduces risk without taking the data outside the protection regime. Three constraints (`messages.sender_user_id`, `conversations.client_user_id`, `claiming_tokens.user_id` — all `NOT NULL` with `ON DELETE NO ACTION`) mean the database refuses a **direct** hard delete while those dependent rows exist. That is not the same as the delete being impossible: the dependent rows could be deleted first. Lookla deliberately preserves the shared history instead, so it pseudonymises the anchor rather than destroying the other party's record. The constraint makes the shortcut unavailable; the choice is still a choice, and it is made on those grounds. This is a checklist, not a single step — every item below must be worked through, not just the `users` row:

  1. **`users` row** — `UPDATE users SET email = 'deleted-user-' || id || '@lookla.gr', password_hash = '', name = 'Deleted user', phone = NULL, viber_phone = NULL, whatsapp_phone = NULL, avatar_url = NULL, google_id = NULL, apple_id = NULL, is_active = false, is_email_verified = false WHERE id = :id;` — clears email, password, name, phone, WhatsApp, Viber, avatar, and **both** federated identities (`google_id` and `apple_id`) in one statement, and disables login. `apple_id` and `is_email_verified` were both missing from this statement until 2026-08-06 — leaving `is_email_verified` true asserts that an address nobody controls was confirmed.
  2. **Verification/reset/claim tokens** — `DELETE FROM email_verifications WHERE user_id = :id;`, `DELETE FROM password_resets WHERE user_id = :id;` and `DELETE FROM claiming_tokens WHERE user_id = :id;`. The last one was missing from this checklist until 2026-08-06; it is `NOT NULL` with `ON DELETE NO ACTION`, so it also blocks any hard delete.
  3. **Sessions** — `DELETE FROM refresh_tokens WHERE user_id = :id;` (also sign the user out by invalidating the `access_token`/`refresh_token` cookies if they still hold an active browser session).
  4. **Reports** — `UPDATE reports SET reporter_user_id = NULL WHERE reporter_user_id = :id;` (the `reporter_ip` and report content stay, per the report-retention target below and the anti-abuse legitimate interest — only the link to this specific person is removed).
  5. **Salon-owner claim associations — a completion blocker, not a courtesy question.** `salon_owners.user_id` is `ON DELETE CASCADE`, but this procedure never deletes the `users` row, so the cascade never fires and the row survives. Every reader treats its existence as an *active* ownership — the claim guard, `_require_ownership`, chat access and unread counters, booking access, subscription ownership, and the public "Owner verified" badge — so a pseudonymised account would keep owner access to a live salon. Resolve as exactly one of three, and record which and why:
     1. **transferred** to another verified account;
     2. **ended** — until the `ended_at` column exists (T-048), this means `DELETE FROM salon_owners WHERE user_id = :id AND salon_id = :sid;`, which flips that salon's "Owner verified" state, so tell the salon;
     3. **retained** on a separately written basis — and even then access is revoked, because a pseudonymised account must never authorise anything.

     Do not mark the erasure complete while this is unresolved.
  6. **Availability requests / appointments** — for rows where `client_user_id = :id`, apply the exact operations below — the name takes a placeholder, the contact fields are cleared, and they are not the same operation:

    ```sql
    UPDATE availability_requests SET client_name = 'Deleted user', client_phone = NULL
     WHERE client_user_id = :id;
    UPDATE appointments SET client_name = 'Deleted user', client_phone = NULL, client_email = NULL
     WHERE client_user_id = :id;
    ```

    rather than deleting the rows outright — a salon may have a legitimate business reason to retain the fact that an appointment happened, distinct from *who* it was with. Also check `service_notes`, `reply_text` and `preferred_dates` on availability requests, and `notes` and `cancellation_reason` on appointments, for free text — see step 7. `client_email`, `preferred_dates`, `notes` and `cancellation_reason` were all missing from this step until 2026-08-06.
  7. **Free text — messages and notes, reviewed manually, not auto-scrubbed.** Replacing the `users` row does not remove personal data the person may have *typed into free text* elsewhere — a phone number or full name written directly into a message body or an availability-request note survives step 1 untouched. There is no automated free-text PII scrubber today; this step is a manual read-through, not optional:
     - Read every `messages.body` where `sender_user_id = :id` (or where the conversation involves this user, if reviewing from the other direction). Where a message contains personal data typed by the requester (a phone number, an email, a full name), redact only that specific text in place (`UPDATE messages SET body = '[redacted]' WHERE id = :message_id;` or a targeted string replacement) — do not delete the surrounding message or conversation, which would remove the other party's legitimate record of what was discussed.
     - Read `service_notes` and `reply_text` on this user's `availability_requests` rows for the same reason, and redact in place if personal data is found beyond the already-anonymized `client_name`/`client_phone` fields.
     - Record in the completion log which messages/notes (if any) were redacted, separately from the account-level anonymization — this is a distinct action with its own judgment call, not automatic.
  8. **Second roles — the account may not only be a client.** Check and act on each, added 2026-08-06:
     - `professionals` where `user_id = :id` — a self-registered professional's public profile is **not** touched by step 1. `name` is `NOT NULL`, so it takes a placeholder, not a `NULL`; `slug` is a public URL derived from the name, so it takes a unique non-identifying value rather than being cleared:

       ```sql
       UPDATE professionals SET
         name = 'Deleted professional',
         slug = 'deleted-professional-' || id,
         user_id = NULL, specialty = NULL, phone = NULL, email = NULL,
         instagram = NULL, base_city = NULL,
         bio = NULL, bio_el = NULL, bio_ru = NULL, bio_uk = NULL,
         base_lat = NULL, base_lng = NULL, service_radius_km = NULL,
         does_home_visits = false, has_home_studio = false,
         is_active = false, is_verified = false, needs_review = false
       WHERE user_id = :id;
       ```

       Then delete the matching `professional_social_links`, `professional_availability` and `professional_portfolio` rows. Do not delete the `professionals` row itself — it is referenced by conversations, requests, appointments and reports.
     - `webhooks` where `owner_user_id = :id` — disable, revoke the `secret`, delete the row. Never leave an active integration without an owner.
     - `moderation_queue` where `submitter_user_id = :id` — null the submitter and read `content_text`, which is a verbatim copy of the user's content taken at submission and is not touched by redacting the original.
     - If the account is an **administrator**: `UPDATE reports SET resolved_by = NULL WHERE resolved_by = :id;` and `UPDATE moderation_queue SET reviewed_by = NULL WHERE reviewed_by = :id;` — the decision and its timestamp stay as an unattributed audit record.
  9. **Verify before closing.** Two things make this check trustworthy, and both were missing from the first version of it:

     **(a) Capture the professional ids *before* step 8 runs.** That step sets `professionals.user_id = NULL`, which destroys the only link back to the subject — after it, no query can tell whether the profile was properly tombstoned. Record the ids first, in the request log:

     ```sql
     SELECT id FROM professionals WHERE user_id = :id;   -- keep these, call them :prof_ids
     ```

     **(b) Count the anchors that must *exist*, not only the values that must be right.** Every residual check has the shape `count(*) … WHERE id = :id AND (wrong values)`. If the row were deleted outright — the one thing this procedure must never do, since dependent history points at it — that count is zero and the check reports success. Absence and correctness are different questions and need different queries.

     **(c) Compare with `IS DISTINCT FROM`, never with `<>` or a bare boolean.** `name`, `password_hash`, `is_active` and `is_email_verified` are all nullable in the schema, and in Postgres `name <> 'Deleted user'` is `UNKNOWN` when `name` is `NULL` — so a row left in a wrong state is silently excluded from the count and the check reports success.

     ```sql
     SELECT
       (SELECT count(*) FROM users WHERE id = :id)                      AS user_anchor,
       (SELECT count(*) FROM unnest(:prof_ids) e(id)
          LEFT JOIN professionals p ON p.id = e.id
         WHERE p.id IS NULL)                                            AS missing_prof_anchors,
       (SELECT count(*) FROM users WHERE id = :id
         AND (email             IS DISTINCT FROM ('deleted-user-' || id || '@lookla.gr')
           OR name              IS DISTINCT FROM 'Deleted user'
           OR password_hash     IS DISTINCT FROM ''
           OR is_active         IS DISTINCT FROM false
           OR is_email_verified IS DISTINCT FROM false
           OR phone IS NOT NULL OR viber_phone IS NOT NULL
           OR whatsapp_phone IS NOT NULL OR avatar_url IS NOT NULL
           OR google_id IS NOT NULL OR apple_id IS NOT NULL))            AS users_residual,
       (SELECT count(*) FROM refresh_tokens      WHERE user_id = :id)    AS sessions,
       (SELECT count(*) FROM email_verifications WHERE user_id = :id)    AS verifications,
       (SELECT count(*) FROM password_resets     WHERE user_id = :id)    AS resets,
       (SELECT count(*) FROM claiming_tokens     WHERE user_id = :id)    AS claim_tokens,
       (SELECT count(*) FROM webhooks        WHERE owner_user_id = :id)  AS webhooks,
       (SELECT count(*) FROM reports
         WHERE reporter_user_id = :id OR resolved_by = :id)              AS report_links,
       (SELECT count(*) FROM moderation_queue
         WHERE submitter_user_id = :id OR reviewed_by = :id)             AS moderation_links,
       (SELECT count(*) FROM appointments WHERE client_user_id = :id
         AND (client_name IS DISTINCT FROM 'Deleted user'
           OR client_phone IS NOT NULL OR client_email IS NOT NULL))     AS appointment_residual,
       (SELECT count(*) FROM availability_requests WHERE client_user_id = :id
         AND (client_name IS DISTINCT FROM 'Deleted user'
           OR client_phone IS NOT NULL))                                 AS request_residual,
       (SELECT count(*) FROM professionals WHERE id = ANY(:prof_ids)
         AND (name IS DISTINCT FROM 'Deleted professional'
           OR slug IS DISTINCT FROM ('deleted-professional-' || id)
           OR user_id IS NOT NULL
           OR specialty IS NOT NULL
           OR phone IS NOT NULL OR email IS NOT NULL OR instagram IS NOT NULL
           OR bio IS NOT NULL OR bio_el IS NOT NULL
           OR bio_ru IS NOT NULL OR bio_uk IS NOT NULL
           OR base_city IS NOT NULL OR base_lat IS NOT NULL OR base_lng IS NOT NULL
           OR service_radius_km IS NOT NULL
           OR does_home_visits IS DISTINCT FROM false
           OR has_home_studio  IS DISTINCT FROM false
           OR is_active        IS DISTINCT FROM false
           OR is_verified      IS DISTINCT FROM false
           OR needs_review     IS DISTINCT FROM false))                  AS professional_residual,
       (SELECT count(*) FROM professional_portfolio
         WHERE professional_id = ANY(:prof_ids))                         AS prof_portfolio,
       (SELECT count(*) FROM professional_social_links
         WHERE professional_id = ANY(:prof_ids))                         AS prof_social,
       (SELECT count(*) FROM professional_availability
         WHERE professional_id = ANY(:prof_ids))                         AS prof_availability,
       (SELECT count(*) FROM salon_owners WHERE user_id = :id)           AS owner_links;
     ```

     Completion requires:

     ```text
     user_anchor          = 1          the tombstone still exists
     missing_prof_anchors = 0          every captured profile still exists
     every other count    = 0          nothing was left in a wrong state
     ```

     `owner_links` is the single exception to the last line, and only under outcome 3 of step 5 — retained on a written basis with access revoked — and only when that decision is recorded.

     **Keep this query and step 1/step 8 in step with each other.** Every column an `UPDATE` above clears must appear in the predicate here; `specialty` was cleared by step 8 and unchecked here until 2026-08-06, and `apple_id`, `is_email_verified` and `client_email` each had the same gap earlier. When a column is added to either side, add it to the other in the same edit — this checklist has drifted from the schema three times, and each time the verification looked clean.

  10. Record the completion date in the log.
  11. The anonymized row (and any redacted messages/notes) will also age out of any *pre*-anonymization backup within 7 days, per the already-published backup rotation.

- **Restriction:** set `is_active = false` on the `users` row (already-existing column) to block login/authentication while a dispute is resolved, without deleting anything.

**Step 5 — Confirm to the requester** that the action is complete, in the same email thread.

---

## 2. Periodic retention cleanup (manual, until the job is scheduled)

**2026-08-15 update.** T-048 built the engine this section describes running by hand — `backend/app/services/retention/policies.py` declares every clock below as data, `runner.py` runs them with a dry-run default and a per-policy cap, and `cli.py` (PR #160) is a real entrypoint: `python -m app.services.retention.cli [--apply]`. **What is still missing is the crontab line that calls it on a schedule** — deleting personal data on a timer is a production infra change held for the same confirmation as any other T2-tier change, so until that line exists, the monthly manual run below remains the actual operative process, and the CLI is available today for a controller to run by hand in its place (`docker exec beauty_api python -m app.services.retention.cli --apply`, which is strictly more complete than the `psql` steps below — it also covers tokens, the observation clock and the tombstone-anchor GC, none of which this manual procedure ever listed).

**Cadence: monthly, not quarterly.** A quarterly cadence against a 12-month target allows actual retention to reach up to ~15 months in the worst case (a row that crosses the 12-month line the day after a cleanup run waits a further 3 months for the next one). A monthly cadence bounds the worst case to ~13 months, which is close enough to the stated 12-month target to be an honest match for a "target" figure rather than a guaranteed exact cutoff. Run on the **1st of every month** by the controller, as a `psql` session against production (or, preferably, `python -m app.services.retention.cli --apply` — see above):

1. **Messages/conversations** — `SELECT id, last_message_at FROM conversations WHERE last_message_at < NOW() - INTERVAL '12 months';` review the list, then delete the conversation's `messages` rows and the `conversations` row itself for any where the associated account is already anonymized/inactive, or where both parties' last activity is >12 months old.
2. **Availability requests / appointments** — `SELECT id, created_at FROM availability_requests WHERE created_at < NOW() - INTERVAL '12 months';` and the equivalent for `appointments.starts_at`; delete rows past the window.
3. **Reports** — `SELECT id, created_at FROM reports WHERE created_at < NOW() - INTERVAL '12 months';` delete rows past the window (this also removes the associated `reporter_ip`).
4. **Salon-owner claims** — `salon_owners.ended_at` shipped in T-048 (PR #88, migration `0005_salon_owner_lifecycle.py`), so the clock this row used to be unable to run now runs: 12 months past `ended_at`. The public policy's wording, corrected on 2026-07-17 to describe the schema gap honestly, has been restored to the fixed 12-month-post-end target now that the gap is closed. `SELECT user_id, salon_id, ended_at FROM salon_owners WHERE ended_at < NOW() - INTERVAL '12 months';` delete rows past the window.

Record each monthly run (date executed, row counts affected) in the private log.

---

## 3. Minor-account handling procedure

Referenced by the public policy's Section 12 (Children): *"If we learn that a minor has created an account, we may request reasonable verification and delete or restrict the account and its associated personal data."*

**Trigger:** a report from any source (the account holder themselves, a parent/guardian, another user, or the controller noticing something during normal operation) that an account may belong to someone under 18.

**Step 1 — Reviewer.** The controller reviews every such report personally (single point of contact today).

**Step 2 — Verification.** Request reasonable confirmation from whoever raised the concern, or from the account holder directly (e.g. asking them to confirm their age). This is *not* a formal ID-check process — consistent with the public policy not claiming a technical age-verification system exists. The bar is "reasonable," not "certain."

**Step 3 — Once confirmed, act promptly** (target: within 5 business days of confirmation — a proactive child-safety action, handled faster than the general 1-month data-subject-request SLA, which governs requests *from* the account holder, not reports *about* them). Work through **every item of the current erasure checklist** in Section 1 (do not cite a fixed range of item numbers here — the checklist has gained items twice, and a fixed range silently excludes them), exactly as for a self-requested erasure — including the mandatory free-text review of this account's messages and availability-request notes (Section 1, item 7), since a minor may have typed a real name, phone number, or other identifying detail directly into a message even though the account profile itself is anonymized. Additionally for this case specifically:
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
- **Balancing:** reviewers are not Lookla users and have no direct relationship with Lookla, which weighs against processing. In favor: the review was already voluntarily made public by the reviewer on a comparable platform for a comparable purpose (helping other consumers), so the reuse is not a surprising or out-of-context one; Lookla discloses the source ("Source: Google Reviews," T-012) rather than obscuring provenance; no additional reviewer data is **displayed or imported** beyond name, rating and review text. **Corrected 2026-08-06:** the earlier claim that no photo and no profile link are *collected* was wrong. The stored crawl payload (`crawler_sources.raw_data`) retains `authorAttribution.photoUri` and `authorAttribution.uri` — the reviewer's profile photo URL and a link to their public profile on the source platform — for 6,245 of 7,481 rows. Neither is shown, imported into `reviews`, or used to identify anyone, but both are retained, and retention is collection. This weighs against the balancing test as it stood, and the honest position until the data is removed is that we hold more than the purpose requires. T-076 removes both fields from stored payloads; the public Privacy Policy was corrected in all four locales on the same date rather than waiting for that ticket.
- **Conclusion:** legitimate interest applies. Mitigation already in place: source attribution label. Any reviewer who objects can be accommodated via `hello@lookla.gr` — but **removal is not the single-step operation this document previously described.** See the corrected procedure in §5 below; the earlier wording ("delete the `reviews` row") was wrong in both halves and is retracted.

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

## 5. Review objection: durable removal (T-076, PR #103 + PR #162)

This section replaces the claim in §4.1 that honouring a reviewer's objection is a single `DELETE FROM reviews`. Two facts, established by reading the schema and the crawler (see `PERSONAL_DATA_MATRIX.md` §4.1), used to make that false:

1. **The review exists in two places.** The author name and text are also inside `crawler_sources.raw_data`, for 6,245 of 7,481 rows — together with a reviewer photo URI and a link to their profile, neither of which the `reviews` table imports. Deleting the `reviews` row alone left that copy.
2. **The delete did not hold.** The crawler's insert is guarded by `ON CONFLICT (source, source_id) DO NOTHING`, which conflicts on nothing once the row is gone, so the next enrichment run reinserted the review with the same author name.

Both are now fixed, and enforced structurally rather than by an operator remembering a checklist:

- `app.services.review_suppression.suppress()` records a suppression matched by the upstream immutable id where the source has one (Google), or by a folded-name-plus-date fingerprint where it doesn't (Treatwell, Fresha) — see the module's own docstring for the full matching rules, including why "identical re-import" is not the test that proves it works.
- `reviews_suppression_guard`, a `BEFORE INSERT` trigger on `reviews` (migration `0009`), checks every import path against it — not a call each importer has to remember, a thing an insert cannot bypass.
- `suppress()` also strikes the matching element out of `crawler_sources.raw_data` for Google reviews (the only source that has anything stored there), so the second copy does not survive either.
- `authorAttribution.uri`/`photoUri` — the reviewer's profile link and avatar — are stripped from every newly-crawled place going forward, and migration `0016` removed them from the rows already on disk. `displayName` is kept; nothing else reads or shows the other two.

**Operator action on an objection**, now: call `suppress()` (or the admin surface once one exists — none does yet, same gap T-047 has) with the review's `salon_id`, `source`, and `source_id` if the source has one. One call, no re-check-after-the-next-crawl step — the trigger and the strike are what used to require that step, and both now run every time, not once by hand.

---

## 6. Tracking

A private, dated log of data-subject requests, minor-account reports, and monthly cleanup runs is kept by the controller outside this (public) documentation tree — this file records the *procedure*, not a live register of individual requests, which would itself be personal data.
