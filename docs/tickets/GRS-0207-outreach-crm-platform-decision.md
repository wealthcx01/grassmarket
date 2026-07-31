# GRS-0207 — Outreach and CRM platform: decide, then build the thin layer

**Status:** OPEN (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-26, staging review item 5). **Priority:** HIGH._
**Loop:** founder-feedback remediation, Wave 5. **ADR:** ADR-0048.
**Reopens the conclusion of GRS-0195.**

## Why

The founder's words: there is no email client integration, nowhere to draft an email, and no CRM
holding the contacts we imported from the exchange list and the LSEG pull. They named four
candidate directions and asked which is right: Odoo, whatever Google Workspace provides, a
self-hosted Mautic, or lemlist even at higher cost.

GRS-0195 already ran a spike and concluded "build thin", largely because every candidate wanted to
own the contact record and we already have one. That conclusion was reached without the founder's
stated preference in front of it, and the founder has now said explicitly that they expect us to
use the best available technology rather than hand-roll. So the comparison gets re-run against the
real requirement, and this time it produces a decision the founder signs rather than a memo.

## The actual requirement, stated once

An advisor working a target from the registry needs to: see the contacts we hold for that target,
draft a first-touch email with the assessment context filled in, have it reviewed under the
founder gate (ADR-0041), send it from their own @bruntsfield.capital mailbox, and have the reply
land back against the contact record. Sequences and open-tracking are useful. Marketing automation,
landing pages and lead scoring are not what this is.

## Scope

1. **Comparison, written up in ADR-0048**, scoring each option against: who owns the contact
   record, whether sending is from the advisor's own mailbox, per-advisor cost at 10 and at 50
   advisors, self-hosting burden, data residency for named business-contact PII, and how much of
   the requirement above is met out of the box.
   - **Mautic** self-hosted. Note the operational cost honestly: it is a PHP application with its
     own database and cron requirements.
   - **lemlist**, priced per seat. The founder has said cost is acceptable if it is the right tool.
   - **Odoo** CRM, and what adopting it implies for Holy Corner.
   - **Google Workspace** native: Gmail API plus the contacts and tasks surfaces we can already
     reach with the scopes GRS-0197 provisions.
   - **Build thin on our own registry**, which is what GRS-0195 recommended. Kept in the
     comparison so the recommendation is a choice rather than a default.
2. **A recommendation with a number attached**, not a shortlist. Say which one, what it costs,
   what we give up, and what the migration path is if we are wrong.
3. **Build the layer the decision implies**, behind the existing `EntityRegistry` port so the
   contact record stays ours whichever platform we adopt:
   - a contacts CRM surface listing registry contacts by target, with the assessment and pipeline
     context we already hold,
   - a draft-email composer that pre-fills from the assessment,
   - the founder review gate on anything client-facing before it can send (ADR-0041),
   - send and reply threading through whichever transport the ADR picks.
4. **Nothing sends without a recorded approval.** Non-negotiable #8 applies to outreach exactly as
   it applies to deliverables. See GRS-0202 and GRS-0204, which this ticket now supersedes as the
   decision point.

## Test plan

1. Repository tests: contacts are owner-scoped and target-scoped, and an advisor cannot list
   another advisor's outreach.
2. Approval-gate tests: an unapproved draft cannot reach the send path, asserted at the repository
   layer rather than in the UI.
3. Vitest per file for the composer and the contacts list.
4. Standing gate: pytest, pyright, tsc, ESLint.

## Out of scope

- Provisioning the Google OAuth scopes (GRS-0197).
- The GTM registry import itself (GRS-0193, done).
- Cold-outreach sequencing beyond a first touch and one follow-up; sequences come after the
  platform decision lands.

## Acceptance

The founder reads ADR-0048 and agrees with the pick, or overrules it with the trade-offs visible.
An advisor can open a target, see its contacts, draft an email with real assessment context, and
send it after the founder approves.

---

## Status reconciliation — 2026-08-01

**OPEN.** No implementing commit on main; genuinely unbuilt.
