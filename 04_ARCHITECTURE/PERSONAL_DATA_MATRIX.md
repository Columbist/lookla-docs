---
title: Personal Data Matrix — joint design basis for T-047 (erasure) and T-048 (retention)
status: Draft — for review
version: 0.7
owner: Zhuykov Andrey (data controller, hello@lookla.gr)
reviewers: []
last_updated: 2026-08-06
related_documents:
  - 04_ARCHITECTURE/PRIVACY_OPERATIONS.md
  - 05_ROADMAP/IMPLEMENTATION_BACKLOG.md
implementation_status: Design only. Nothing in this document is built yet.
---

# Personal Data Matrix

T-047 automates erasure — **event-driven**, one data subject, every table at once. T-048 automates retention — **time-driven**, one table, every data subject at once. They ship as separate PRs with no shared runtime code and no shared schedule, but they are two projections of a single table: *for each column holding personal data, what happens to it, and when.*

Splitting that decision across two tickets is how the two disagree. If erasure empties a row that retention deletes outright, the work was wasted; if retention keeps a row that erasure was supposed to empty, the erasure was incomplete and the policy is wrong. This document fixes the decision once, before either job is written.

## How this was derived

From the running database and the code that writes to it, not from the existing documentation:

- table and column inventory from `information_schema`;
- the foreign-key graph and every `ON DELETE` rule from `pg_constraint`, which is what actually decides whether a hard delete is possible at all;
- writers located by reading the routers, the services and the crawler, because three tables that hold personal data have no ORM model and would be invisible to a model-only survey.

Every count in this document is reproducible from Appendix A, which carries the exact read-only queries, the snapshot time, and the writer files read.

Where this document contradicts `PRIVACY_OPERATIONS.md` or the ticket text, the schema is the authority and the contradiction is called out.

**38 tables. 15 foreign keys to `users` across 13 tables; 4 cascade, 3 block a hard delete outright.**

## 1. Vocabulary

The matrix uses eight actions. They are not synonyms, and the distinction between the first three is the point of this section.

| Action | Meaning |
|---|---|
| **DELETE ROW** | the row is removed |
| **CLEAR VALUE** | the column is set to `NULL` or empty; the row stays |
| **TOMBSTONE** | the column is set to a fixed non-identifying value, so the row stays valid and readable |
| **RETAIN** | the data stays, under the purpose, basis and terminal event named in §1.2 |
| **MANUAL REVIEW** | free text a human must read; the job lists it and never claims to have scrubbed it |
| **EXTERNAL DELETE** | an object outside Postgres; needs its own call and its own confirmation |
| **SET VALUE** | the column is set to a specific non-null value that is not an identifier (a flag, a status) |
| **MANUAL DECISION** | the operator must decide before completion; blocks the run |

Version 0.2 used one word, `DELETE`, for removing a row and for nulling a column. Version 0.3 split that but still wrote compound cells — `MANUAL REVIEW + EXTERNAL DELETE`, `DELETE ROW; EXTERNAL DELETE`, and a bare `set false` that was not in the vocabulary at all. An implementer still had to interpret.

The matrix below therefore has **four action columns, not one**. Each holds at most one verb, and a compound requirement occupies two columns instead of one cell:

```text
DB         one of DELETE ROW / CLEAR VALUE / TOMBSTONE / SET VALUE / RETAIN
Manual     MANUAL REVIEW or MANUAL DECISION, or —
External   EXTERNAL DELETE, or —
Condition  when this row applies at all, or —
```

Every table in §2 uses the same six-column shape — `Column | DB | Manual | External | Condition | Clock` — even where most cells are `—`. §2.6 uses the same shape with the Clock column named *Terminal event / clock*, since crawled data ends on an event rather than a fixed period. Version 0.4 declared the Condition column and then omitted it, so conditions went back into prose inside other cells.

### 1.1 What survives erasure is pseudonymised, not anonymised

Version 0.1 of this document called the account operation "anonymise in place". That was wrong, and the error mattered: after erasure the stable `users.id` survives, and with it the conversations, messages, appointments and timestamps that reference it, plus a deterministic `deleted-user-{id}@lookla.gr` address and the controller's own request log. Data that can be re-linked to a person using additional information remains personal data. This is pseudonymisation — a real risk reduction, not an exit from the protection regime.

The consequence is concrete: **"no residual personal data by column" is not an achievable acceptance criterion** for rows deliberately kept linked to a stable anchor, and version 0.1 proposed it anyway. The completion contract for T-047 is instead:

```text
1. every direct identifier is cleared
2. every column that still holds data is on an explicit allowlist
3. each retained category names its purpose, its basis and its retention clock
4. no active credential, session, token, integration or public profile survives
5. the completion record lists the retained categories rather than
   asserting the subject is gone
```

Erasure has never meant deleting every row that ever referenced a person. It means removing what has no remaining basis and being explicit about what stays and why. The word "anonymised" hid that judgement; these five lines expose it.

### 1.2 What is retained, and on what basis

`RETAIN` is only meaningful with a purpose, a basis and an end. Storage limitation does not permit "kept because the schema has nowhere to put a deletion".

| Retained | Purpose | Lawful basis | Terminal event |
|---|---|---|---|
| `users.id` (tombstone anchor) | keeps the other party's conversation, booking and moderation history internally consistent | legitimate interest (integrity of another person's records) | **GC**: once every dependent row of §2.2, §2.3 and §2.5 has aged out under its own clock and no evidence hold is open, the anchor row is deleted. Never reused. |
| `users.role`, `preferred_language`, `created_at` | interpreting the retained history — which side of a conversation this anchor was, in which locale | legitimate interest, same as the anchor | with the anchor |
| `professionals.id` (tombstone anchor) | same, for a professional referenced by conversations, requests, appointments and reports | legitimate interest | with the last dependent row, same GC rule |
| `professionals.rating_avg`, `review_count` | aggregate figures that no longer identify a person once §2.4 has run | legitimate interest | with the anchor |
| `conversations.*`, `messages.*` timestamps and slots | the other party's record of what was agreed | legitimate interest of that other party | 12 months past `last_message_at` |
| `appointments` business fields | the salon's record that a booking happened, distinct from who it was with | legitimate interest of the salon | 12 months past `starts_at` |
| `reports.reporter_ip`, `description` | anti-abuse, LIA 4.4 | legitimate interest | 12 months past `created_at` |
| `email_bans.email` | keeping a ban effective after the account is gone | legitimate interest | 24 months past `created_at`, §4.3 |
| completion record | demonstrating the request was handled | legal obligation (accountability) | 24 months, §3 |
| `reviews` author name and text | attributed reviews as the trust mechanism of the directory, LIA 4.1 | legitimate interest | suppression on objection, source removal confirmed by a refresh, salon delisted, or 24 months without re-confirmation — §2.6 |
| `crawler_sources.raw_data` | provenance of the current listing | legitimate interest | overwritten each crawl; reviewer photo and profile link removed entirely by T-076 |
| `staff` name, bio, photo | showing who works at a salon, LIA 4.2 | legitimate interest | salon delisted, or 24 months without re-confirmation |

The anchor GC is the part version 0.2 got wrong by writing "never deleted" with no end at all. A tombstone whose last dependent row has aged out is not holding anything together; it is a name-shaped hole kept out of habit. T-047 does not delete it inline — the dependents outlive the request — so the GC belongs to T-048 as one more scheduled job with its own clock.

## 2. The matrix

Four action columns per §1: **DB**, **Manual**, **External**, **Condition**. **Clock** is what T-048 deletes on a timer. Appendix B classifies every column of every in-scope table, including the ones with no action; this section carries the ones that need one.

### 2.1 The account and its credentials

| Column | DB | Manual | External | Condition | Clock |
|---|---|---|---|---|---|
| `users.id` | TOMBSTONE anchor | — | — | — | GC per §1.2 |
| `users.email` | TOMBSTONE → `deleted-user-{id}@lookla.gr` | — | — | — | with the anchor |
| `users.password_hash` | CLEAR VALUE (empty string) | — | — | — | — |
| `users.name` | TOMBSTONE → `Deleted user` | — | — | — | with the anchor |
| `users.phone`, `viber_phone`, `whatsapp_phone` | CLEAR VALUE | — | — | — | — |
| `users.avatar_url` | CLEAR VALUE | — | — | third-party host, nothing of ours to delete — §4.2 | — |
| `users.google_id`, **`users.apple_id`** | CLEAR VALUE | — | — | — | — |
| `users.is_active` | SET VALUE `false` | — | — | — | — |
| **`users.is_email_verified`** | SET VALUE `false` | — | — | — | — |
| `users.preferred_language`, `role`, `created_at` | RETAIN — §1.2 | — | — | — | with the anchor |
| `refresh_tokens.*` | DELETE ROW (also cascades) | — | — | — | past `expires_at` |
| `email_verifications.*` | DELETE ROW (also cascades) | — | — | — | past `expires_at` |
| `password_resets.*` | DELETE ROW (also cascades) | — | — | — | past `expires_at` |
| **`claiming_tokens.*`** | DELETE ROW | — | — | — | past `expires_at` |

`is_email_verified` left `true` on a tombstone asserts that an address nobody controls was verified; it is cleared with the rest.

### 2.2 Conversations and bookings

| Column | DB | Manual | External | Condition | Clock |
|---|---|---|---|---|---|
| `conversations.client_user_id` (NOT NULL) | RETAIN — points at the tombstone | — | — | — | 12 months past `last_message_at` |
| `conversations.last_message_at`, `client_unread`, `owner_unread`, `created_at` | RETAIN | — | — | — | with the row |
| `messages.sender_user_id` (NOT NULL) | RETAIN — points at the tombstone | — | — | — | with the conversation |
| `messages.body` | RETAIN | MANUAL REVIEW — redact typed personal data in place | — | — | with the conversation |
| `messages.attachment_url` | RETAIN | MANUAL REVIEW | EXTERNAL DELETE | only if the object is ours — §4.2 | with the conversation |
| `messages.proposed_slot`, `read_at`, `created_at`, `message_type` | RETAIN — the other party's record | — | — | — | with the conversation |
| `availability_requests.client_user_id` | RETAIN — points at the tombstone | — | — | — | 12 months past `created_at` |
| `availability_requests.client_name` | TOMBSTONE → `Deleted user` | — | — | — | with the row |
| `availability_requests.client_phone` | CLEAR VALUE | — | — | — | with the row |
| `availability_requests.service_notes`, `reply_text`, `preferred_dates` | RETAIN | MANUAL REVIEW | — | — | with the row |
| `availability_requests.proposed_slot`, `status`, `created_at`, `updated_at` | RETAIN | — | — | — | with the row |
| `appointments.client_user_id` | RETAIN — points at the tombstone | — | — | — | 12 months past `starts_at` |
| `appointments.client_name` | TOMBSTONE → `Deleted user` | — | — | — | with the row |
| `appointments.client_phone`, **`client_email`** | CLEAR VALUE | — | — | — | with the row |
| **`appointments.notes`**, **`cancellation_reason`** | RETAIN | MANUAL REVIEW | — | — | with the row |
| `appointments.starts_at`, `ends_at`, `duration_min`, `status`, `source`, `created_at`, `updated_at` | RETAIN — the salon's business record | — | — | — | with the row |

`appointments.client_email` is not in the SOP's erasure checklist, which covers `client_name` and `client_phone` and stops. An erasure executed exactly as documented before 2026-08-06 left the person's email address in the appointments table.

### 2.3 Reports, moderation, bans

| Column | DB | Manual | External | Condition | Clock |
|---|---|---|---|---|---|
| `reports.reporter_user_id` | CLEAR VALUE | — | — | — | 12 months past `created_at` |
| `reports.reporter_ip` | RETAIN — anti-abuse LIA 4.4 | — | — | — | with the row |
| `reports.description` | RETAIN | MANUAL REVIEW — free text written by the reporter | — | — | with the row |
| `reports.resolved_by` | CLEAR VALUE | — | — | the subject is the admin who resolved it — §2.5 | with the row |
| `reports.reason`, `status`, `resolved_at`, `created_at`, `salon_id`, `professional_id` | RETAIN | — | — | — | with the row |
| `moderation_queue.submitter_user_id` | CLEAR VALUE | — | — | — | reviewed: 12 months past `reviewed_at`; pending: 12 months past `created_at` |
| `moderation_queue.content_text` | RETAIN | MANUAL REVIEW — a verbatim copy taken at submission | — | — | with the row |
| `moderation_queue.content_url` | RETAIN | MANUAL REVIEW | EXTERNAL DELETE | only if the object is ours — §4.2 | with the row |
| `moderation_queue.reviewed_by` | CLEAR VALUE | — | — | the subject is the admin who reviewed it — §2.5 | with the row |
| `moderation_queue.content_type`, `content_id`, `auto_flags`, `status`, `reviewed_at`, `created_at` | RETAIN | — | — | — | with the row |
| `ip_bans.ip` | RETAIN — not linked to an account | — | — | — | `expires_at` set: 12 months past it. **`expires_at IS NULL`: annual logged review, §5** |
| `ip_bans.reason`, `created_at` | RETAIN | — | — | — | with the row |
| `email_bans.email` | RETAIN — deliberately survives erasure | — | — | — | **24 months past `created_at`, §4.3** |
| `email_bans.reason`, `created_at` | RETAIN | — | — | — | with the row |
| `blocked_email_domains.*` | — domain only, not personal | — | — | — | — |

A ban that dies with the account is not a ban, so `email_bans` surviving erasure is deliberate. That makes its period a decision to be written down rather than inherited from a missing column.

### 2.4 Professional identity

A self-registered professional is a natural person running a business. The public profile is business-facing, but the name, mobile number, personal email, biography, home-service base coordinate **and the service geography** remain their personal data: `does_home_visits`, `has_home_studio` and `service_radius_km` together describe whether this person works out of their home and how far around it they travel.

| Column | DB | Manual | External | Condition | Clock |
|---|---|---|---|---|---|
| `professionals.id` | TOMBSTONE anchor | — | — | — | GC per §1.2 |
| `professionals.user_id` | CLEAR VALUE | — | — | — | — |
| `professionals.name` (NOT NULL) | TOMBSTONE → `Deleted professional` — **must be a tombstone, not a clear: the column rejects NULL** | — | — | — | with the anchor |
| `professionals.slug` | TOMBSTONE → non-identifying unique value (slugs derive from names and are public URLs) | — | — | — | with the anchor |
| `professionals.specialty`, `base_city` | CLEAR VALUE | — | — | — | — |
| `professionals.phone`, `email`, `instagram` | CLEAR VALUE | — | — | — | — |
| `professionals.bio`, `bio_el`, `bio_ru`, `bio_uk` | CLEAR VALUE — all four; the locale copies are separate columns | — | — | — | — |
| `professionals.base_lat`, `base_lng` | CLEAR VALUE — a home-service base is close to a home address | — | — | — | — |
| **`professionals.service_radius_km`** | CLEAR VALUE — service geography of a natural person | — | — | — | — |
| **`professionals.does_home_visits`, `has_home_studio`** | SET VALUE `false` — whether this person works out of their home | — | — | — | — |
| `professionals.is_active`, `is_verified` | SET VALUE `false` | — | — | — | — |
| **`professionals.needs_review`** | SET VALUE `false` — a tombstone must not sit in a moderation queue | — | — | — | — |
| `professionals.rating_avg`, `review_count`, **`price_level`** | RETAIN — aggregate, no longer identifying — §1.2 | — | — | — | with the anchor |
| `professionals.created_at`, `updated_at` | RETAIN — technical | — | — | — | with the anchor |
| `professional_social_links.*` | DELETE ROW | — | — | — | — |
| `professional_availability.*` | DELETE ROW | — | — | — | — |
| `professional_portfolio.*` | DELETE ROW | — | EXTERNAL DELETE | only if the object is ours — §4.2 | — |

Hard-deleting the parent row is rejected: `professionals.id` is referenced by conversations, availability requests, appointments and reports, so deleting it either destroys another party's history or forces an FK redesign this ticket has no reason to carry.

### 2.5 Users in a second role

Every table above treats the subject as a client. An account can also be a **salon owner**, a **professional**, a **webhook owner**, a **report submitter**, and — for staff accounts — the **resolver** or **reviewer** of someone else's report.

| Column | DB | Manual | External | Condition | Clock |
|---|---|---|---|---|---|
| **`salon_owners.user_id`** | one of the three outcomes in §2.5.1 | **MANUAL DECISION — blocks completion** | — | always, whenever the subject holds any row here | needs `ended_at`; §2.5.1 |
| `professionals.user_id` | CLEAR VALUE — §2.4 | — | — | — | — |
| `webhooks.secret` | CLEAR VALUE **before** the row is deleted, so a partial failure cannot leave a live secret | — | revoke at the consumer — §4.4 | the webhook was ever delivered to | — |
| `webhooks.*` (row) | DELETE ROW | — | — | — | — |
| `moderation_queue.submitter_user_id` | CLEAR VALUE — §2.3 | — | — | — | with the row |
| `reports.resolved_by` (admin) | CLEAR VALUE | — | — | — | with the row |
| `moderation_queue.reviewed_by` (admin) | CLEAR VALUE | — | — | — | with the row |

`reports.resolved_by` and `moderation_queue.reviewed_by` are written by `admin.py:132` and `admin.py:154`. If the erasure subject is an administrator, these record which specific person made a moderation decision — their personal data. Both are nullable with `ON DELETE NO ACTION`, so both are cleared and the decision and its timestamp survive as an unattributed audit record.

Erasure must query the subject in **every** role listed above, not only through `client_user_id`.

#### 2.5.1 `salon_owners` — the role T-047 cannot decide by itself

Version 0.2 omitted this table from the second-role list, which was an error with teeth. `salon_owners.user_id` is `ON DELETE CASCADE`, but **T-047 never deletes the `users` row**, so the cascade never fires. The row survives, and every reader treats its mere existence as an active ownership:

```text
owner.py     duplicate-claim guard (broken today — see below), owned-salon list, _require_ownership → 403 gate
chat.py      owner side of a conversation, message access, conversation list, unread counters, access predicate
booking.py   owner booking access, appointment access
payments.py  subscription ownership
salons.py    _owner_claimed_expr → the public is_owner_claimed badge (ORM, not raw SQL)
```

```python
# salons.py:266 — the public badge, ORM rather than raw SQL
exists().where(SalonOwner.salon_id == Salon.id).correlate(Salon)
```

That helper (`_owner_claimed_expr`) feeds `is_owner_claimed` on both the list and the detail endpoints, so an ended link would keep a salon publicly marked *Owner verified* even if every raw-SQL reader above were fixed. Version 0.3 missed it by listing raw SQL only, and by asserting a count of reader sites — which was both wrong and the wrong kind of acceptance criterion.

A tombstoned account would therefore keep owner access to a live salon. The ownership link is also not the subject's to unilaterally destroy — removing it flips that salon's "Owner verified" state and can strand a business. So it is a **MANUAL DECISION** that blocks completion, resolved as exactly one of three outcomes, each recorded with its reason:

| Outcome | DB action | Condition |
|---|---|---|
| transferred | `UPDATE salon_owners SET user_id = :successor WHERE user_id = :id AND salon_id = :sid` | a verified successor account exists and has accepted |
| ended | `SET ended_at = now()` once T-048 adds the column; until then `DELETE ROW`, which flips the salon's *Owner verified* state — tell the salon | no successor, the relationship is over |
| retained | RETAIN the row | a separately written basis exists **and** access is revoked regardless — a pseudonymised account must never authorise anything |

**For T-048, `ended_at` alone is not enough.** Adding the column without updating the readers leaves every site still treating an ended link as active. Acceptance is not a list of files — that list was wrong twice — but a property:

- a repo-wide sweep for every SQL **and ORM** reference to `salon_owners` / `SalonOwner`, across `backend/`, `crawler/` and the frontend;
- one reusable *active ownership* predicate (`ended_at IS NULL`), used by all of them;
- applied to the claim guard, `_require_ownership`, chat access and unread counters, availability-request and booking access, subscription ownership, the admin views, and the public `is_owner_claimed` badge on both list and detail;
- tests asserting `is_owner_claimed` on list **and** detail for an ended link;
- tests for each of the three outcomes below — ended, transferred, retained-with-access-revoked;
- a tripwire test that fails when a new direct query to the table appears without the shared predicate, so the sweep does not have to be repeated by hand.

**Found while writing this section:** `owner.py:35` runs `SELECT id FROM salon_owners WHERE salon_id = :sid`, and `salon_owners` has no `id` column — only `(user_id, salon_id)`. The query raises `column "id" does not exist`, so the duplicate-claim guard returns a 500 instead of the intended 409 and never blocks a second claim. Verified directly against the production schema. Filed as **T-078**; not fixed here, and not folded into either ticket.

### 2.6 Crawled personal data — people who are not account holders

These people never asked to be here, so "public content, keep forever" is the weakest position in the document, not the safest. Each row below now carries a terminal event.

| Column | DB | Manual | External | Condition | Terminal event / clock |
|---|---|---|---|---|---|
| `reviews.author_name`, `text`, `text_en/ru/uk` | RETAIN | objection handling per LIA 4.1 — §4.1 | — | — | **any of**: suppression on objection; the source stops serving it and a refresh confirms that; the salon is delisted; or 24 months without re-confirmation |
| `reviews.rating`, `published_at` | RETAIN — meaningless without the text it belongs to | — | — | — | with the review row |
| `reviews.source`, `source_id`, `created_at` | RETAIN — the identity T-076 suppresses against | — | — | — | outlives the review row; kept by the suppression record |
| `crawler_sources.raw_data` | RETAIN — provenance for the current listing only | — | — | — | overwritten each crawl; **`authorAttribution.photoUri` and `.uri` stripped on write and purged retroactively by T-076** |
| `staff.name`, `bio`, `photo_url` | RETAIN — LIA 4.2 | — | — | — | the salon is delisted, or 24 months without re-confirmation |
| `staff.role`, `is_active`, `source`, `source_id` | RETAIN | — | — | — | with the staff row |
| `staff_schedules.*` | RETAIN — a named person's working schedule, via `staff_id` | — | — | — | with the staff row |
| `salons.*`, `photos`, `social_links`, `salon_hours`, `services` | business data | — | — | — | — |

"24 months without re-confirmation" is the periodic-review backstop for data with no natural end: a crawled person whose listing has not been seen for two years is being retained on the strength of a source we no longer check. The exact figure is a decision, not a derivation, and it is written here so it can be argued with.

#### 2.6.1 That clock cannot be computed today

The policy is stated; the mechanism does not exist. `reviews` has `published_at` and `created_at`, `staff` has no timestamp at all, and both writers are

```sql
ON CONFLICT (source, source_id) DO NOTHING
```

so re-seeing a row on every crawl for two years advances nothing. `crawler_sources.last_crawled_at` is source-level and proves only that the salon was fetched — not that this reviewer or this staff member was in the response. A retention job built on today's schema would delete rows that are still being served, and keep rows the source dropped long ago.

**T-048 therefore owns a clock contract, not just a job.**

*Schema.* `reviews.last_seen_at` and `staff.last_seen_at` (or one `source_observations` table keyed by `(source, source_id)` — one table is preferable if a third crawled entity ever appears), **nullable**.

*Bootstrap — the part that decides whether the first run is a cleanup or an incident.* Version 0.5 said "backfilled to `created_at`", which is a false claim: `created_at` records the first import, and the old schema never recorded a re-observation, so it is not evidence about whether the source still serves the row. Backfilling it would mark every row older than 24 months as unseen, and the first cleanup run would delete rows the crawler saw yesterday.

The column is therefore left `NULL` on migration. But "a `NULL` never age-deletes" cannot be the whole rule either, or a legacy row that the first complete baseline does *not* contain stays `NULL` for ever and becomes immortal: absent from every snapshot, never stamped, never eligible. "Absence of evidence is not evidence of absence" holds only until a complete snapshot exists — after that, absence *is* an observation, within that snapshot's scope.

Three timestamps, not one:

```text
last_seen_at         set to crawl_started_at for every item the snapshot contained
first_missing_at     set to baseline_completed_at the first time a verified complete
                     snapshot covering this item's scope did NOT contain it;
                     cleared the moment the item reappears
baseline_completed_at recorded per scope, not globally
```

Rules:

```text
observed in a verified snapshot  → last_seen_at advances, first_missing_at cleared
absent from a verified snapshot  → first_missing_at set if not already set
partial / failed / timed-out     → nothing changes, and the snapshot is not
                                   recorded as verified
age-delete eligible              → 24 months past the later of
                                   last_seen_at and first_missing_at
last_seen_at NULL and
first_missing_at NULL            → never deleted: no snapshot has covered it yet
```

*Scope.* "Verified complete" must be attached to the scope the crawl actually guarantees — this provider, for this salon, through the last page — never a vague global "source". A crawl that covered 200 of 6,400 salons says nothing about the other 6,200, and a scope defined loosely here is how a pagination cap turns into a mass deletion.

A simpler alternative remains acceptable if the baseline proves awkward: stamp existing rows with the **migration timestamp**, starting a fresh 24-month clock without asserting anything historical. It defers removal of genuinely stale rows by up to two years — the honest trade, since the wrong version of this deletes live data on day one. It is an alternative to the `NULL` bootstrap, not a variant of it: under it no row is left `NULL`, so it does not collide with the rule above.

*Writers.* `DO NOTHING` becomes `DO UPDATE SET last_seen_at = :crawl_started_at` at all four import sites. The timestamp is the crawl's start, not `now()`, so every row from one crawl carries the same instant.

*What counts as an observation.* Absence is only evidence when the snapshot was complete. The clock advances only after a crawl that finished successfully and paged to the end; a partial result, a pagination cap, a timeout or a parse failure advances **nothing**, and must not be recorded as a crawl that saw nothing. This is the part that turns a retention job into a data-loss bug if it is skipped.

*Identity.* `staff.source_id` falls back to `md5(f"{salon_id}:{name}")`, so a corrected spelling produces a new row and leaves the old one to age out silently — the same failure T-076 addresses for reviews, and it needs the same alias handling here.

*Payload.* `crawler_sources.raw_data` is overwritten wholesale each crawl, so element-level cleanup (T-076 stripping `photoUri` and `uri`) must be applied on write, not only retroactively, or the next crawl restores what was purged.

Acceptance tests for this clock:

```text
seen again inside 24 months           → retained
not seen for > 24 months              → deleted
crawl failed or returned partially    → no clock changes, baseline stays unverified
source omitted one page               → no deletion attributable to that crawl
identity alias changed                → the existing clock continues, no reset
legacy row present in the baseline    → receives last_seen_at
legacy row absent from the baseline   → survives now; eligible 24 months after
                                        baseline_completed_at, not immortal
item reappears after being missing    → first_missing_at cleared, clock restarts
no snapshot has covered it yet        → never deleted, whatever created_at says
```

**26,448 review rows, 26,156 with an author name. 6,245 of 7,481 crawler-source rows carry a review with a non-empty author display name** — and the payload holds more than the `reviews` table does: the same 6,245 rows carry a reviewer photo URI and a link to their profile on the source platform, neither of which is imported. See Appendix A.

### 2.7 Tables with no personal data today

`alembic_version`, `salon_categories`, `salon_tags`, `service_categories`, `subscription_plans`, `tags`, `crawler_sources` apart from `raw_data`.

`professional_availability` and `staff_schedules` are **not** in this list — both are a natural person's working schedule, classified `YES` in Appendix B, and both were listed here in an earlier version while being classified as personal data three sections away.

Three need a note rather than a dismissal:

- **`event_log`** — `user_id` plus a free-form `payload jsonb`, and **no foreign key at all**, so nothing at the database level marks it as referencing a person. Empty today. §4.5 defines its contract now, while that is still cheap.
- **`salon_subscriptions`** — `stripe_customer_id` and `stripe_subscription_id` identify a person at a processor. Empty; Stripe is not live. Revisit before it is.
- **`translation_cache`** — see §4.6.

## 3. T-047 is a staged, resumable workflow, not one transaction

Version 0.1 said the erasure would run "in one transaction" while also requiring manual free-text review and external object deletion. Those cannot coexist: a Postgres transaction cannot stay open while an operator reads messages, and an object delete in R2 cannot be atomic with a database commit. Nor should a crash halfway lose the work already done.

```text
1. preflight
     resolve the subject in every role
     deactivate the account and freeze new writes from it
2. structured phase          ← the only database transaction
     delete tokens and sessions
     tombstone direct identifiers
     null the FK columns the matrix names
     emit the manual-review and external-cleanup task lists
3. manual phase
     read and redact the free text the task list names
4. external phase
     delete the objects that are ours; record what is not
5. verification
     re-run the column-level query
     confirm no disallowed column holds data
6. completion
     write the completion record
```

State machine:

```text
pending → structured_complete → manual_review_required
        → external_cleanup_required → verified → completed
                                              ↘ failed
```

Re-running after a failure continues from the recorded state; it never repeats a completed phase and never loses the evidence of one. `completed` is unreachable while any manual or external task is open — the state is derived from the task list, not set by the operator.

Acceptance tests to be written with the implementation: a crash injected after each phase resumes correctly; a deactivated subject cannot create new rows; `completed` cannot be reached with an open task; a second run produces no duplicate work and no lost evidence; a fixture subject holding a row in every table of §2.1–§2.5 leaves nothing outside the allowlist.

The **completion record** is itself personal data — it names a person and what was done for them. It gets a minimal schema (subject id, request date, completion date, per-table row counts, retained categories, open-task history) with **no email address and no free text**, and its own retention clock: **24 months**. That figure is a risk-based internal choice, not a legal deadline — no rule sets a window after which a supervisory authority stops being able to ask. It is long enough to answer a follow-up or a complaint about how a request was handled, and short enough that the register of who asked for erasure does not itself become a long-lived personal-data store.

## 4. Decisions

### 4.1 Deleting a review neither removes it nor keeps it removed

LIA 4.1 is published and states: *"removal of a specific review on a legitimate objection is operationally simple (delete the `reviews` row)."*

Both halves fail:

- the author name and text also sit in `crawler_sources.raw_data` for **6,245** salons, alongside a reviewer photo URI and profile link that the `reviews` table never imported;
- re-import is guarded by `ON CONFLICT (source, source_id) DO NOTHING`, which conflicts on nothing once the row is gone, so the next enrichment run reinserts the review with the same author name.

Honouring an objection needs a **suppression record** checked before every import, plus removal of the copy in `raw_data` — not a delete. That is a separate ticket (**T-076**, filed with this document); it is not folded into T-047, whose subject is account holders, nor into T-048, which is time-driven.

**`(source, source_id)` is not a sufficient key on its own.** Only the Google path has a stable upstream identity: its `source_id` is `g_<placeId>_<review resource name>` and covers 25,332 of 26,448 rows. The other two are content-derived:

```python
# treatwell — no upstream id at all, always derived
md5(f"tw:{salon_id}:{author}:{pub}:{body[:30]}")
# fresha — upstream id when present, otherwise the same shape
rev.get("id") or md5(f"fresha:{salon_id}:{author}:{pub}:{body[:30]}")
```

Edit the display name, or the first 30 characters of the text, and the hash changes — so a suppressed review returns as a new row with a new `source_id`, and the suppression looks like it worked because the old key is still suppressed. T-076 must therefore require: the upstream immutable id wherever the source exposes one; a documented stable suppression identity for each fallback path; defined behaviour when `source_id` is null or empty; aliases retained when the id strategy changes, so old suppressions keep matching; and a suppression record that outlives the source's ability to re-serve the review. The re-import test must mutate the author name, the body and the rating, not re-import an identical payload — that would only prove the hash is deterministic.

**Shipped.** PR #103 built the durable suppression record and the `BEFORE INSERT` trigger every import path is checked against structurally; PR #162 wired the `crawler_sources.raw_data` strike into `suppress()` and stopped storing `authorAttribution.uri`/`photoUri` at all (migration `0016` scrubbed the rows already on disk). `PRIVACY_OPERATIONS.md` §5 describes the durable mechanism now in place, not the interim manual procedure this section originally required.

### 4.2 What "external delete" actually covers today

The backend has **no upload endpoint** — no `UploadFile` handler anywhere in `backend/app`. `messages.attachment_url`, `professional_portfolio.url_after`/`url_before` and `users.avatar_url` are URL strings supplied by the client and normally point at hosts we do not control.

The one thing we do host is salon photos: `media.py` migrates Google Places images into Cloudflare R2 and rewrites `photos.url` to our CDN. Those are business images, not subject media.

Two consequences, and they point in opposite directions:

- T-047 must **not** promise to delete objects behind user-supplied URLs. It records them in the completion evidence and states plainly that the object is on a third-party host.
- **`r2.py` has no delete function** — only `get_r2_client`, `upload_bytes` and `r2_key_for_photo`. The moment an upload endpoint exists, EXTERNAL DELETE becomes real and unimplemented. Whoever adds uploads adds the delete path and its confirmation in the same PR; noted here so that requirement is on record before the gap opens.

### 4.3 `email_bans` — 24 months, with the columns to enforce it

Default retention **24 months from `created_at`**; indefinite-by-omission is rejected. The table gains `created_at` (present), `expires_at`, a `reason`/`category`, and `reviewed_at`. On expiry the row is deleted. An extension is a separate documented decision on a specific case, with a basis and a new end date.

Recommended additionally: store a **normalised keyed HMAC** of the address rather than the address in clear. The table's only use is equality matching at registration, which an HMAC satisfies, and it removes a readable list of email addresses from a table that by design survives erasure. The keying follows the pattern already shipped in T-050.

### 4.4 `webhooks` — revoke, disable, delete

"Null the owner or delete the row" was not a decision, and one of its halves is unsafe: an active integration with a live `secret` and no owner is worse than either. On erasure the webhook is **disabled, its secret revoked, and the row deleted**.

### 4.5 `event_log` — define the envelope now, while it is empty

Waiting for the first writer means the contract is written after the data. The envelope:

```text
event_type       required
schema_version   required
occurred_at      required
actor_user_id    nullable
subject_type     nullable
subject_id       nullable
payload          validated against an allowlist schema per event_type
expires_at       required
```

Rules: no free text; no email addresses, phone numbers, names, message bodies, secrets or tokens; default retention 12 months; T-047 nulls `actor_user_id` and any `subject_id` naming the subject; the first writer ships a concrete payload schema and its tests in the same PR; a longer period is a decision taken before that writer merges.

### 4.6 `translation_cache` — drop it

T-048's acceptance criteria state *"no separate cache table exists."* The table exists, with `source_text` and `translated_text`. It has zero rows and no writer: nothing in `backend/app` or the crawler references it, and translations are stored in columns on the source row exactly as the criterion assumed. The conclusion holds; the premise does not.

Drop the table in T-048's migration and correct the criterion, so the next person reading the schema does not reasonably conclude that user text is cached and start writing there.

**Correction, 2026-08-07.** Earlier versions of this section stated that `_translate_query()` sends the user's search query to OpenAI. It does not. `_translate_query` is a lookup against two local dictionaries (`CITY_SYNONYMS`, `SERVICE_SYNONYMS`) and makes no network call at all; the claim came from seeing `translate_batch` imported in the same file and joining two unrelated things. `AUDIT.md`, `DATA_FLOW.md` and `API_SPECIFICATION.md` all described it correctly, and this document contradicted them.

What actually reaches OpenAI is `translate_batch`, called from exactly two places as of `24a079f` — service names and review text — which is what LIA 4.5 already covers. Both are content imported from public sources: **no text a Lookla user typed into the product** — a message, a report, a search query — reaches OpenAI.

One tripwire remains, and it is the reason this section is not simply deleted: `services/moderation.py` contains `check_text`, which posts arbitrary text to OpenAI's moderation endpoint, and **nothing calls it**. Wiring it up would begin sending user-submitted content — messages, reports, review drafts — to a processor that no assessment covers. Whoever connects it extends LIA 4.5 and the public disclosure in the same change — and `backend/tests/test_openai_call_sites.py` fails until they do, because a sentence in a document does not fail a build.

## 5. Retention clocks must not have a NULL that means "forever"

Two of the clocks proposed in version 0.1 were incomplete in the same way:

| Table | Clock | The NULL case |
|---|---|---|
| `moderation_queue` | 12 months past `reviewed_at` | a row never reviewed has `reviewed_at IS NULL` and is kept forever |
| `ip_bans` | 12 months past `expires_at` | a permanent ban has `expires_at IS NULL` and is kept forever |

Resolved:

- **`moderation_queue`** — reviewed rows: 12 months past `reviewed_at`. Pending rows: 12 months past `created_at`, escalated to the controller and then deleted. A moderation item nobody looked at for a year is not pending, it is abandoned.
- **`ip_bans`** — rows with an expiry: 12 months past `expires_at`. Rows without one: a permanent ban is a decision, so it gets a **periodic review** (annual, logged) rather than silent immortality. Absence of `expires_at` records an intent about the *ban*, never about the retention of the row.

T-048's boundary tests therefore cover four cases per clock, not three: inside the window, outside it, exactly on it, and **NULL**.

## 6. Proposed split

**T-047 — erasure.** The staged workflow of §3, walking the Action column in FK-safe order, with the completion contract of §1.1 and the completion record of §3.

**T-048 — retention.** One scheduled job per clock in the matrix, plus four schema and writer changes without which some of those clocks cannot be computed at all:

- `salon_owners.ended_at`, landing together with the single shared active-ownership predicate and the tripwire of §2.5.1;
- the `email_bans` columns of §4.3;
- the `last_seen_at` clock contract of §2.6.1 — schema, all four crawler writers, and the definition of a complete snapshot;
- the `translation_cache` drop;
- the tombstone-anchor GC of §1.2.

Per-job tests over the four boundary cases of §5, plus the observation-clock cases of §2.6.1.

Filed alongside, deliberately outside both: **T-076** review suppression (§4.1), **T-077** search-query policy review (§4.6).

The two tickets share this matrix and nothing else — no shared code path, no shared schedule, no ordering dependency.

---

## Appendix A — reproducing the audit

Schema snapshot: **2026-08-06 07:51:13 UTC**, production `beauty_db`. All queries are read-only and return counts only; no personal rows are reproduced here or were exported.

```sql
-- 38
select count(*) from information_schema.tables
 where table_schema='public' and table_type='BASE TABLE';

-- 15 foreign keys, across 13 distinct tables
select count(*), count(distinct conrelid) from pg_constraint
 where contype='f' and confrelid='users'::regclass;

-- 4 cascade
select count(*) from pg_constraint
 where contype='f' and confrelid='users'::regclass and confdeltype='c';

-- 3 that block a hard delete: NO ACTION over a NOT NULL column
select count(*) from pg_constraint c
  join unnest(c.conkey) k(attnum) on true
  join pg_attribute a on a.attrelid=c.conrelid and a.attnum=k.attnum
 where c.contype='f' and c.confrelid='users'::regclass
   and c.confdeltype='a' and a.attnotnull;

-- 7481 total; 6245 carrying at least one review with a non-empty author
-- display name. The containment operator alone only proves the key exists,
-- so the element test below is what the stated figure actually measures.
select count(*) from crawler_sources;
select count(*) from crawler_sources
 where exists (
   select 1 from jsonb_array_elements(raw_data->'reviews') r
    where nullif(r #>> '{authorAttribution,displayName}', '') is not null
 );
-- the three author fields, counted separately: 6245, 6245, 6245
select count(*) from crawler_sources
 where exists (select 1 from jsonb_array_elements(raw_data->'reviews') r
                where nullif(r #>> '{authorAttribution,photoUri}', '') is not null);
select count(*) from crawler_sources
 where exists (select 1 from jsonb_array_elements(raw_data->'reviews') r
                where nullif(r #>> '{authorAttribution,uri}', '') is not null);

-- and all three within the SAME review entry, which is the actual claim: 6245
select count(*) from crawler_sources
 where exists (
   select 1 from jsonb_array_elements(raw_data->'reviews') r
    where nullif(r #>> '{authorAttribution,displayName}', '') is not null
      and nullif(r #>> '{authorAttribution,photoUri}',    '') is not null
      and nullif(r #>> '{authorAttribution,uri}',         '') is not null
 );

-- 26448 reviews, 26156 with an author name
select count(*), count(author_name) from reviews;

-- the full FK picture behind §1 and §2.5
select c.conrelid::regclass, a.attname,
       c.confdeltype, a.attnotnull
  from pg_constraint c
  join unnest(c.conkey) with ordinality k(attnum, ord) on true
  join pg_attribute a on a.attrelid=c.conrelid and a.attnum=k.attnum
 where c.contype='f' and c.confrelid='users'::regclass
 order by 1;
```

**Corrections.** Version 0.1 reported 6,378 rows, from a substring match on `raw_data::text` that also matches unrelated occurrences. Version 0.2 reported 6,245 from a containment test that proves only that an `authorAttribution` object exists — a weaker predicate than the sentence it supported. The element test above measures the stated claim, and returns **6,245**: the two agree here because every `authorAttribution` in this data carries a non-empty `displayName`, but the query published in 0.2 could not have shown that. The same 6,245 rows carry `photoUri` and the reviewer profile `uri`.

Version 0.3 then asserted that the photo URI and the profile URI are present on the same rows while publishing a query for the photo URI alone. Each field is now counted separately, and a fourth query tests all three **within the same review entry** — which is the claim actually being made. All four return **6,245**.

Snapshots: **2026-08-06 08:14:26 UTC** for the `displayName` correction, **09:01:11 UTC** for the three-field queries.

Writer files read for this audit:

```text
backend/app/routers/chat.py            conversations, messages, availability_requests
backend/app/routers/reports.py         reports
backend/app/routers/admin.py           reports.resolved_by, moderation_queue.reviewed_by
backend/app/routers/professionals.py   professionals, portfolio, social links
backend/app/routers/owner.py           salon_owners readers and the claim guard
backend/app/routers/booking.py         salon_owners access paths
backend/app/routers/payments.py        salon_owners subscription ownership
backend/app/routers/salons.py          _owner_claimed_expr, _translate_query, photo handling
backend/app/routers/media.py           R2 migration of salon photos
backend/app/services/r2.py             upload only — no delete function
backend/app/services/translate.py      translation, no translation_cache writer
backend/app/models/user.py             users, tokens
backend/app/models/salon.py            salons, reviews, salon_owners, staff
backend/app/models/professional.py     professionals and sub-tables
crawler/beauty_crawler/spiders/enrichment.py   review import, ON CONFLICT DO NOTHING
crawler/beauty_crawler/spiders/treatwell.py    review import
```

## Appendix B — exhaustive column inventory

§2 lists the columns that need an action. This appendix lists **every column of every in-scope table**, so that "not listed" is a classification rather than an omission.

Version 0.4 used a single mutually-exclusive scale (personal / derived / technical / business), which conflated two independent questions and produced a direct contradiction: §1.1 argues that the surviving `users.id` is what keeps the result personal data, while the appendix filed it as merely technical. The two axes are separated here.

**Personal-data status** — `YES` · `NO` · `COND` (conditional: depends on what a writer puts in it, or on whether the row's subject is a natural person).
**Role** — direct identifier · pseudonymous identifier · derived · free text · credential · technical · business.

| Table | Column | Personal | Role |
|---|---|---|---|
| `users` | `email`, `phone`, `viber_phone`, `whatsapp_phone` | YES | direct identifier |
| `users` | `name` | YES | direct identifier |
| `users` | `avatar_url` | YES | direct identifier (third-party URL) |
| `users` | `google_id`, `apple_id` | YES | pseudonymous identifier (federated) |
| `users` | `password_hash` | YES | credential |
| `users` | `id` | YES | pseudonymous identifier / primary key — the anchor §1.1 is about |
| `users` | `is_email_verified` | YES | derived — asserts something about the address |
| `users` | `role`, `is_active`, `preferred_language`, `created_at` | YES | technical, but attached to a person |
| `refresh_tokens` | `token_hash` | YES | credential |
| `refresh_tokens` | `id`, `user_id`, `expires_at`, `revoked_at`, `created_at` | YES | technical / pseudonymous identifier |
| `email_verifications`, `password_resets`, `claiming_tokens` | `token` | YES | credential |
| `email_verifications`, `password_resets`, `claiming_tokens` | `user_id` | YES | pseudonymous identifier |
| `password_resets` | `channel` | YES | derived — which contact route was used |
| `email_verifications`, `password_resets`, `claiming_tokens` | `id`, `salon_id`, `expires_at`, `used_at`, `created_at` | YES | technical |
| `conversations` | `client_user_id` | YES | pseudonymous identifier |
| `conversations` | `last_message_at`, `client_unread`, `owner_unread`, `created_at` | YES | technical — activity of a specific person |
| `conversations` | `id`, `salon_id`, `professional_id` | YES | technical / business key |
| `messages` | `body` | YES | free text |
| `messages` | `attachment_url` | YES | free text / third-party URL |
| `messages` | `sender_user_id` | YES | pseudonymous identifier |
| `messages` | `proposed_slot`, `read_at`, `created_at`, `message_type`, `conversation_id`, `id` | YES | technical — attached to an identified sender |
| `availability_requests` | `client_name`, `client_phone` | YES | direct identifier |
| `availability_requests` | `service_notes`, `reply_text`, `preferred_dates` | YES | free text |
| `availability_requests` | `client_user_id` | YES | pseudonymous identifier |
| `availability_requests` | `status`, `proposed_slot`, `created_at`, `updated_at`, `id`, `salon_id`, `professional_id` | YES | technical / business key |
| `appointments` | `client_name`, `client_phone`, `client_email` | YES | direct identifier |
| `appointments` | `notes`, `cancellation_reason` | YES | free text |
| `appointments` | `client_user_id` | YES | pseudonymous identifier |
| `appointments` | `staff_id` | YES | pseudonymous identifier — names a specific worker |
| `appointments` | `starts_at`, `ends_at`, `duration_min`, `status`, `source`, `created_at`, `updated_at`, `id`, `salon_id`, `professional_id`, `service_id` | YES | technical / business key |
| `reports` | `reporter_ip` | YES | direct identifier (online identifier) |
| `reports` | `description` | YES | free text |
| `reports` | `reporter_user_id`, `resolved_by` | YES | pseudonymous identifier |
| `reports` | `reason`, `status`, `resolved_at`, `created_at`, `id`, `salon_id`, `professional_id` | YES | technical / business key |
| `moderation_queue` | `content_text` | YES | free text |
| `moderation_queue` | `content_url` | YES | free text / URL |
| `moderation_queue` | `submitter_user_id`, `reviewed_by` | YES | pseudonymous identifier |
| `moderation_queue` | `auto_flags` | YES | derived — automated assessment of a person's content |
| `moderation_queue` | `content_type`, `content_id`, `status`, `reviewed_at`, `created_at`, `id` | YES | technical |
| `ip_bans` | `ip` | YES | direct identifier (online identifier) |
| `ip_bans` | `reason`, `expires_at`, `created_at`, `id` | YES | technical |
| `email_bans` | `email` | YES | direct identifier |
| `email_bans` | `reason`, `created_at` | YES | technical |
| `blocked_email_domains` | `domain`, `added_at` | NO | business — a domain, not a person |
| `professionals` | `name`, `phone`, `email`, `instagram` | YES | direct identifier |
| `professionals` | `bio`, `bio_el`, `bio_ru`, `bio_uk` | YES | free text |
| `professionals` | `base_lat`, `base_lng`, `base_city` | YES | direct identifier — a home-service base approximates a home |
| `professionals` | `does_home_visits`, `has_home_studio`, `service_radius_km` | YES | derived — service geography of a natural person |
| `professionals` | `slug` | YES | derived — public URL built from the name |
| `professionals` | `user_id` | YES | pseudonymous identifier |
| `professionals` | `specialty` | YES | derived |
| `professionals` | `rating_avg`, `review_count`, `price_level` | YES | derived — aggregate about this person's work |
| `professionals` | `id` | YES | pseudonymous identifier / anchor |
| `professionals` | `is_verified`, `is_active`, `needs_review`, `created_at`, `updated_at` | YES | technical |
| `professional_portfolio` | `url_after`, `url_before`, `caption` | YES | free text / media of a person's work |
| `professional_portfolio` | `service_tag`, `is_featured`, `sort_order`, `created_at`, `id`, `professional_id` | YES | technical |
| `professional_social_links` | `url` | YES | direct identifier — a social profile |
| `professional_social_links` | `platform`, `id`, `professional_id` | YES | technical |
| `professional_availability` | `day_of_week`, `start_time`, `end_time`, `is_available` | YES | a natural person's working schedule |
| `professional_availability` | `id`, `professional_id` | YES | technical |
| `salon_owners` | `user_id` | YES | pseudonymous identifier |
| `salon_owners` | `salon_id` | YES | technical — links a person to a business |
| `webhooks` | `secret` | YES | credential |
| `webhooks` | `owner_user_id` | YES | pseudonymous identifier |
| `webhooks` | `url`, `events`, `is_active`, `created_at`, `id`, `salon_id` | YES | technical / business |
| `event_log` | `payload` | **COND** | free text — unconstrained today; §4.5 constrains it before the first writer |
| `event_log` | `user_id` | YES | pseudonymous identifier |
| `event_log` | `event_type`, `salon_id`, `professional_id`, `created_at`, `id` | COND | technical |
| `salon_subscriptions` | `stripe_customer_id`, `stripe_subscription_id` | YES | pseudonymous identifier at a processor |
| `salon_subscriptions` | everything else | NO | business |
| `reviews` | `author_name` | YES | direct identifier |
| `reviews` | `text`, `text_en`, `text_ru`, `text_uk` | YES | free text |
| `reviews` | `source_id` | YES | derived — for two of three sources, a hash of author name and body |
| `reviews` | `rating`, `published_at` | YES | technical — an opinion published by an identified reviewer |
| `reviews` | `source`, `created_at`, `id`, `salon_id` | YES | technical / business key |
| `crawler_sources` | `raw_data` | YES | free text — reviewer names, photo URIs, profile links |
| `crawler_sources` | everything else | NO | business / technical |
| `staff` | `name`, `photo_url` | YES | direct identifier |
| `staff` | `bio` | YES | free text |
| `staff` | `role` | YES | derived — a named person's job at a named salon |
| `staff` | `source_id` | YES | derived — falls back to a hash of salon and name |
| `staff` | `is_active`, `source`, `id`, `salon_id` | YES | technical / business key |
| `translation_cache` | `source_text`, `translated_text` | COND | free text — empty and unwritten; dropped by T-048 |
| `translation_cache` | everything else | COND | technical |
| `staff_schedules` | `staff_id` | YES | pseudonymous identifier |
| `staff_schedules` | `day_of_week`, `start_time`, `end_time`, `is_available`, `valid_from`, `valid_to` | YES | a named person's working schedule / operational |
| `staff_schedules` | `id` | YES | technical |

Tables with **no** personal data in any column: `alembic_version`, `salons`, `salon_hours`, `salon_categories`, `salon_tags`, `photos`, `social_links`, `services`, `service_categories`, `subscription_plans`, `tags`.

Version 0.5 filed `staff_schedules` as non-personal because the row carries no identifier of its own — which is exactly the reasoning this appendix's own rule rejects, and it contradicted `professional_availability`, classified `YES` for the identical structure. A working schedule reached through `staff_id` is a natural person's schedule whether the link runs through an account or not. Corrected above.

Two judgements worth stating, because they drive §2: `professionals.slug` is derived from a name and is a public URL, which is why §2.4 tombstones rather than clears it; and `reviews.source_id` is derived from the author name and body for two of three sources, which is the fact behind T-076's key requirements.

**The rule that produced this table:** a column is personal data when it is *about* an identifiable person, not only when it identifies one by itself. A timestamp on a row that names a person is that person's data; the same timestamp on a salon row is not. That is why almost every column of the account-linked tables reads `YES` with a technical role — and why the allowlist in §1.1 has to be by column, since "technical" grants no exemption.
