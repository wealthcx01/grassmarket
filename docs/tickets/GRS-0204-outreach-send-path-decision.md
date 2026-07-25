# GRS-0204 — The outreach send path: Gmail scope escalation or own-domain SMTP

**Status:** Draft — not scheduled (2026-07-25, from the GRS-0195 spike). **Priority:** TBD.
**Loop:** follow-on. **This is a founder decision before it is an implementation**, and it needs an
ADR.

## Why

GRS-0197 requests `gmail.readonly` and deliberately excludes any send scope: the Studio reads mail
and never sends. Adding a send capability is therefore a scope escalation, not an increment, and
adding a send scope to an OAuth app advisors have already authorised silently widens what that
existing grant permits. GRS-0195 §3c flagged it for exactly that reason.

## The decision

**Option A — escalate to `gmail.send`.** Messages come from the advisor's own address, which is
what makes a warm introduction read as warm. Costs: a new consent flow for every already-connected
advisor, a changed Google verification posture for the Workspace app, and a wider blast radius on
any token compromise.

**Option B — a dedicated own-domain SMTP mailbox.** No scope escalation, no re-consent, and the
send path is fully under our control. Costs: mail arrives from a different address than the
advisor's, which weakens the referral framing that GRS-0194's compliance caveat says is the
effective route.

The two are not equally reversible. Option B can be adopted now and escalated later; Option A
cannot easily be walked back once advisors have granted the scope.

## Sequencing (non-negotiable)

The approval gate and suppression model (GRS-0202) ship and are tested **first**. The scope
escalation is requested **second**. A send capability must never precede the gate that constrains
it.

## Scope

1. An ADR recording the decision and its reasoning.
2. The chosen transport behind an injectable port, so the other option remains reachable without
   touching the sequencer.
3. Compliance plumbing: unsubscribe honoured across every campaign and recorded against the
   contact; the lawful basis recorded per contact, given these are imported business contacts
   rather than opted-in leads; per-message audit.

## Out of scope

- The sequencer (GRS-0203) and the gate (GRS-0202).

## Acceptance

An ADR records the decision. The transport sits behind a port. No send exists until GRS-0202 has
landed.
