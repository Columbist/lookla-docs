# What comparable services actually publish — first pass

**Prepared:** 2026-08-11 · **Method:** their own live legal pages, read directly. Where a site refused automated reading, that is stated rather than filled in from memory.

Benchmarking answers *what a working service publishes* and *how it is structured*. It does not answer whether their template fits our facts, and on one point below it points away from a decision already taken.

---

## 1. Who was read

| Service | Why it is comparable | Read? |
|---|---|---|
| **Yelp** | The closest shape: a directory of businesses that never signed up, with claimable listings and third-party reviews | ✅ Terms of Service |
| **Trustpilot** | Third-party reviews about named businesses, EU-facing, DSA-exposed | ✅ Terms of use for consumers |
| **Vrisko.gr** | The closest *market* analogue — a Greek business directory, and one of our own crawl sources | ❌ **403 to automated reading.** Operator confirmed from search as a named SA company; corrections by email to `info@vrisko.gr`. The legal pages need opening by hand |

---

## 2. What they publish

### Operator identity

**Every one of them publishes a full postal address.**

- Yelp: *"Yelp Inc., 350 Mission Street, 10th Floor, San Francisco, CA 94105, U.S.A."*, plus Yelp Ireland Ltd for EU users.
- Trustpilot: *"Trustpilot A/S, Pilestræde 58, 5th floor, 1112 Copenhagen K, Denmark, CVR no. 30 27 65 82"*, and a London address for the operating company.
- Vrisko: a named Greek SA (`NEWSPHONE HELLAS SA`).

**This is the one place the benchmark contradicts a decision already taken.** DEC-018 records the operator's position that the geographic address need not be published. No comparable does that.

The caveat matters and cuts the other way too: all three are **companies**, publishing a *registered office*. None of them faced our actual problem, which is a natural person with no registered activity, for whom the only address is a home. So the comparables do not show that skipping the address is normal — they show that nobody in this business skips it, while none of them had to weigh publishing a home.

### Acceptance

**Both readable services accept by use, with no mandatory checkbox.**

- Yelp: *"your continued access to or use of the Service … represents your acceptance"*. No checkbox.
- Trustpilot: *"by … browsing, accessing, searching, writing a review, or otherwise using our platform; **or** clicking a box or button"* — the box is one route among several, not a requirement.

This supports the drafted Terms as they stand, which have no checkbox and say why. It is also the more useful reading of the "standard privacy" answer, which was recorded as ambiguous: no acceptance control, no version-stamped record.

### DSA

**Both keep it in a separate document, not in the Terms.** Trustpilot's Terms carry no DSA discussion and link out to a transparency report; Yelp's Terms direct EU residents to information "consistent with the Digital Services Act" held elsewhere.

That is a structural lesson for **T-084**: build a standalone notice-and-action page and reference it from §9, rather than inflating the Terms with procedure. It also means their Terms are a poor place to copy the procedure *from* — the substance lives on pages that were not part of this pass.

---

## 3. What this changes

| Open item | What the benchmark says |
|---|---|
| Acceptance checkbox and version-stamped record | **Not needed.** Two comparables accept by use. Resolves the "standard privacy" ambiguity in the direction the product already implements |
| Structure of the DSA work (T-084) | A separate notice-and-action page, linked from the Terms — not procedure inside §9 |
| Publishing the geographic address | **Points against DEC-018.** Every comparable publishes one; none is a natural person |

## 4. What it cannot settle

Copying a comparable copies its assumptions. All three are companies that took on the obligations of being companies. Ours is a natural person with no registered activity, publishing a crawled directory — and the questions that actually block us are exactly the ones their documents never had to answer.

The text itself is also theirs. What transfers is structure, coverage and the shape of a procedure; the wording does not.

**Next, if this is worth continuing:** open `vrisko.gr/TermsAndConditions/` and its privacy page by hand — a Greek directory operating in the same market under the same regulator is worth more than two American-and-Danish comparables — and read Trustpilot's and Yelp's separate DSA pages, which is where the procedure T-084 has to build actually lives.
