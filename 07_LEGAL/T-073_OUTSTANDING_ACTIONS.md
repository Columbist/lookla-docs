# T-073 — actions requiring account access

Everything below needs credentials, a contact channel or a decision that the server cannot supply. The text is ready to use as-is.

---

## 1. Barracuda delisting — **attempted, blocked on one field**

**Status: not submitted.** The form was completed and rejected server-side:

```text
Please correct the following errors:
Please enter a phone number we can contact you at.
```

The phone field is not marked `required` in the HTML, but the server enforces it. **No number was invented.** Barracuda states that requests with invalid information are ignored and that multiple requests are also ignored — a fabricated number would have guaranteed rejection while consuming the one attempt that gets read.

Listing at the time of writing: still `127.0.0.2` (listed). Nothing was recorded on their side.

**To complete:** open <https://www.barracudacentral.org/rbl/removal-request> and submit once with a real, reachable number.

| Field | Value |
|---|---|
| IP address | the origin address (not written here) |
| Email | `hello@lookla.gr` |
| Name | `Zhuykov Andrey` |
| Contact email | `hello@lookla.gr` |
| Phone | **required — a real, reachable number** |
| Reason | the text below |

```text
An unintended unauthenticated proxy service was discovered on this IP address.

The service had been exposed due to an incorrect access configuration. It was
fully contained on 4 August 2026:

- external access to the proxy ports was blocked at the host firewall;
- the alternate empty-SNI route to the proxy was removed;
- the proxy service was stopped, disabled and masked;
- obsolete directly exposed application processes were stopped;
- persistent firewall and nginx controls were installed and verified;
- external tests confirm that the IP no longer operates as an open proxy.

We have reviewed the remaining public listeners and confirmed that the
affected relay is no longer reachable. Please review the IP reputation and
remove the listing if appropriate.
```

Do **not** include client addresses, CONNECT destinations, log volumes, internal topology, VPN SNI values, secrets or firewall rules.

After submitting, record privately: submission timestamp (Europe/Athens), the listing state beforehand (`LISTED`), and any reference number. Re-check after 12–24 hours. **Do not submit again** merely because the listing has not cleared yet.

---

## 2. Spamhaus — official web checker

The DNS path from this host is unusable: Spamhaus returned `NXDOMAIN` for both the origin address **and** its own self-test entry, which means the list is not answering through this resolver. Its silence is not a clean result.

Check manually at <https://check.spamhaus.org>. If a listing exists, the checker shows the reason and the removal route.

Do not run the check or a removal request through a VPN or proxy — Spamhaus expects the request to come from a network connected to the address, or from the range owner. For a leased address the provider may have to submit it.

If a removal is needed:

```text
Cause:      Unintended unauthenticated proxy exposure.
Resolved:   2026-08-04 10:25:23 Europe/Athens.
Actions:    Public paths blocked, proxy stopped/disabled/masked,
            obsolete listeners removed, persistent controls verified.
Prevention: Reviewed listener inventory, dedicated firewall chains,
            SNI routing controls, persistence and external verification.
```

---

## 3. SORBS / Proofpoint — official web check

The three SORBS zones tested — including the proxy-specific `socks.` and `http.` ones — failed the same self-test, so their result is **inconclusive, not clean**. That matters more here than the lists that did answer, since they are the ones that track open proxies.

Check at Proofpoint's IP Check, which is where Proofpoint directs anyone affected by its reputation services or SORBS. Delisting can be requested through the same form; processing may take up to 72 hours and may not be acknowledged.

---

## 4. Provider portal and registered mailbox

Nothing is visible from the server: the host has no mail spool at all, so any notice went to the account's registered address.

Check for abuse complaints, security notices, automated suspension warnings, outbound-traffic restrictions, unresolved tickets, **and the Spam/Junk folder**, plus any Acceptable Use Policy warning.

**Do not contact the provider first** if there are no complaints, no restrictions, the service is running and the address does not need rotating. Volunteering an incident report against no open ticket invites a restriction rather than avoiding one.

If a ticket does exist, answer with facts and do not minimise — the logs confirm the relay was used:

```text
Incident identified:      Unintended open proxy.
Containment completed:    2026-08-04 10:25:23 Europe/Athens.

Current state:            Proxy stopped, disabled and masked.
                          External access blocked.
                          Alternative ingress route removed.
                          Obsolete public listeners removed.
                          Persistent controls verified.

Recurrence prevention:    Listener inventory, firewall persistence,
                          SNI routing policy, external verification.
```

---

## 5. Re-checks

- **12–24 hours** after the Barracuda submission — listing state only, no second request.
- **3–7 days** — full reputation re-check. Lists update on a lag in both directions: a listing can still appear after the behaviour stopped, and Barracuda may clear on its own.
