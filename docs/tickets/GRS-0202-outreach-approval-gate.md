# GRS-0202 — Outreach message contract, approval gate, and suppression list

**Status:** Draft — not scheduled (2026-07-25, from the GRS-0195 spike). **Priority:** TBD.
**Loop:** follow-on to the founder-feedback remediation programme. Prerequisite for GRS-0203 and
GRS-0204.

## Why

GRS-0195 recommended building a thin sequencer rather than adopting an agentic GTM platform,
because every candidate that runs treats autonomy as the product and wants to own the contact
record. This ticket builds the half of that recommendation which must exist before anything can
send: the message, its approval gate, and the suppression list.

Nothing here sends. That is deliberate. The gate ships and is tested before any send path exists,
so there is never a window in which a message can leave the building unapproved.

## Scope

1. **Contract.** `OutreachMessage`, an owned resource mirroring `AINarrative` field for field
   (ADR-0009): target id, contact id, channel, subject, body, drafter version, prompt-template
   version, status (`proposed → approved | rejected`), approver id, approved-at, and the edit diff
   of any consultant changes.
2. **An injectable `MessageDrafter` port**, with a deterministic template drafter shipped, so the
   flow is exercised offline and CI never makes a model call.
3. **Suppression.** A `contact_suppressions` table keyed on the contact's email, NOT on
   `contact_id`. The registry is re-imported by design and an idempotent upsert must never
   resurrect a suppressed contact; keying on the durable identity is what makes suppression
   survive re-import. Suppression records who suppressed, when, and why.
4. **The refusal.** A send function that refuses any message not in `approved`, and refuses any
   message to a suppressed contact, in the same runtime way an unapproved narrative is refused.
   The refusal lives in the send path, not in the UI that calls it.
5. **Audit.** Every state transition is an audit event, so "we sent this, a person approved it,
   here is who and when" is answerable.

## Test plan

- The gate: an unapproved message is refused; an approved one passes; approving records the
  approver (a message cannot be approved by nobody).
- Suppression survives a re-import of the contact under a new `contact_id`.
- Owner-scoping: an advisor sees only their own outreach messages.
- No live model call anywhere in the suite.

## Out of scope

- Sending anything at all (GRS-0203), and any Gmail scope change (GRS-0204).
- Reply parsing. Inbound reply text is attacker-controlled, and its prompt-injection boundary is
  its own design problem, not an increment here.

## Acceptance

A message cannot be sent unapproved or to a suppressed contact, both enforced at runtime and
tested. Suppression survives a registry re-import. No send capability exists yet.
