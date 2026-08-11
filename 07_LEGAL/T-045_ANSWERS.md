# Lookla — answers received on the legal questions

**Received:** 2026-08-11 · **Questions:** `T-045_REMAINING_QUESTIONS.md` and `TERMS_LEGAL_EXTRACT.md`
**Status of the publication gate:** still closed. See §4.

Recorded verbatim, then read for what each one requires. Where an answer cannot
be turned into work as written, it says so rather than being interpreted into
something convenient.

---

## 1. Answered, and closing the question

| Question | Answer |
|---|---|
| §12 — is the remaining limitation enforceable against a Greek consumer? | **Yes** |
| §14 — compatible with Rome I and Brussels I recast for consumers? | **Yes** |
| Should a specific Greek ADR body be named? | **No** |
| Is 16 appropriate as a product minimum? | **Yes** |
| What does contractual capacity require, separately from the data-protection threshold? | **Nothing** |
| Does messaging change the answer on age? | **No** |
| Is age verification or parental authorisation required in practice? | **No** — and no account can be created in this release |

No code changes follow from these. §12 and §14 stand as drafted; the age rule
stays at 16 with its existing wording, which already separates the product rule
from the data-protection threshold of Article 21 of Law 4624/2019.

---

## 2. Answered, and creating work

| Question | Answer |
|---|---|
| Does Lookla fall within the DSA, and under which category? | **Yes — providing information** |
| Does any exemption apply at this size? | **No** |
| Does the present description satisfy Article 14? | **No** |
| Must a formal notice-and-action and internal complaint-handling procedure be built? | *"It is"* — read as **yes**; see §3 |

**This is the largest single consequence of the whole review.** With the DSA
applying and no size exemption, the obligations are not limited to describing
moderation accurately in the Terms. Article 16 requires a notice-and-action
mechanism, Article 17 a statement of reasons to the person whose content is
affected, and Article 20 an internal complaint-handling system. Article 14 —
answered "not satisfied" — requires the Terms to set out the moderation
policies, procedures, measures and tools, including any algorithmic
decision-making and human review, **and the rules of procedure of that
complaint-handling system**. The system has to exist before the Terms can
describe it.

What exists today: a report button that records a report and can flag a listing
for a person to look at. It does not acknowledge receipt, give reasons, or offer
a way to disagree.

Filed as **T-084**.

---

## 3. Answers that could not be implemented as written — now settled by DEC-019

All three were closed on 2026-08-11 by adopting what comparable services do: no acceptance
control and no acceptance record; DSA procedure in its own document; "it is" read as *must be
built*. Kept below as the record of what was ambiguous and how it was resolved.


Recorded as open rather than guessed at. Each is a sentence away from being
actionable.

1. **"It is"**, on whether notice-and-action and internal complaint-handling
   must be built. Read as *"it is required"*, which is consistent with the
   Article 14 answer immediately above. If it meant *"it is already built"*,
   that is not the case in the product and the reading changes nothing about
   the work — but it changes who is expected to do it.
2. **"Standard privacy"**, on where assent is required and what it must cover,
   and **"the same as in standard privacy"** on whether a version-stamped
   acceptance record must be stored. The drafted Terms deliberately have **no**
   acceptance checkbox, and a test fails if one appears without a version
   reference and an evidence-storage contract. Whether "standard privacy" means
   *the privacy policy needs no assent and neither do the Terms*, or *assent is
   required on the same terms as for privacy*, decides whether a control and a
   storage contract get built. The two readings produce opposite products.
3. **"We don't provide salon publicity in this release."** Taken as a statement
   of scope rather than an answer to a question that was asked. Its consequence
   depends on what "publicity" covers: no paid promotion or ranking (already
   true — payments are off and there is no promoted placement), or no
   salon-supplied promotional content (also true — owner editing is off), or
   something narrower about how listings are presented. Recorded so it is not
   read later as a claim the product does not support.

---

## 4. These are operator decisions, not advice

Recorded by instruction on 2026-08-11 as **DEC-018**: the positions in §1 and §2
are the operator's own, taken without an opinion from a Greek lawyer.

The distinction is kept rather than smoothed over, because the two are not
interchangeable. An opinion moves a judgement to someone qualified to make it;
a decision keeps it with the person who made it. Nothing in this document says
the positions are wrong — several are the readings a lawyer would likely give.
What changes is who is answerable for them, and that is worth being able to
find later.

## 5. Why the publication gate is still closed

**The gate asks for a recorded Greek legal review, and this is not one.**
`TERMS_PUBLICATION_ENABLED` stays `false`; a test fails if it is set true while
the backlog records no review. Publishing on the operator's own reading instead
is a legitimate choice, but it is a change to the gate's *condition* rather than
to a value, and it needs its own decision entry. It has not been made.

**And question 1 is still not answered here.** Whether the geographic address
must be published is the item blocking the first release. The operator's
position — that it need not be — is now recorded as a decision, which resolves
what the product does but not what the file contains: the address is absent from
the frontend, and the reasoning is not on record.
