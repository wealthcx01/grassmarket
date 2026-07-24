# GRS-0195 — Agentic GTM research spike

**Status:** Planned (2026-07-23, founder feedback item 16c). **Priority:** MED. Time-boxed.
**Loop:** founder-feedback remediation, Wave 5. Research output, no adoption in this ticket.

## Why

The founder wants "whatever best in class git repo there is for enabling agentic GTM" to help
advisors run cold outreach. That is a selection problem before it is a build problem, and any
candidate must fit two hard constraints: every outbound touch is human-approved through the
ActiveGraph gate (non-negotiable #8 applied to outreach), and outreach to sell-side/regulated
contacts is compliance-sensitive (the Barclays brief's own caveat).

## Scope

Docs-only. Time-box: two working days. Output file:
`docs/planning/agentic-gtm-spike.md`. No code, no dependency, no config change anywhere in the
repo.

1. **Candidate survey.** Enumerate current open-source agentic GTM / outbound frameworks and
   the adjacent categories they blur into (agentic SDR platforms, outreach sequencers with
   agent layers, general agent frameworks with GTM templates). Minimum five candidates
   evaluated in full; candidates discovered but screened out are listed with a one-line
   reason. For each surviving candidate record: repo URL, licence, stars/last-commit/release
   cadence, language/stack, hosting model.
2. **Evaluation matrix.** Score every candidate 0–2 on six fixed criteria, in a table:
   1. Approval-gating fit — can every outbound send be forced through a human-approval
      checkpoint (ActiveGraph policy) without forking the send path?
   2. Self-hosting fit on Railway — Postgres-compatible, no mandatory third-party SaaS in the
      send loop.
   3. Data-model fit with the ADR-0045 registry — can targets/contacts be the system of
      record, with provenance preserved, rather than a parallel contact store?
   4. Licence compatibility for commercial use.
   5. Maintenance health — bus factor, issue responsiveness, release history.
   6. Security posture — dependency surface, credential handling, prompt-injection exposure
      for any inbound-reply parsing.
3. **Constraint analysis.** One section each on: (a) how the human-approval gate attaches for
   the recommended path (concretely: which seam the ActiveGraph policy wraps); (b) compliance
   posture for regulated/sell-side contacts (unsubscribe handling, records of consent, the
   Barclays caveat); (c) Gmail sending implications given GRS-0197's scopes (note:
   `gmail.readonly` deliberately excludes send — any send capability is a separate,
   explicitly-approved scope escalation, not an increment).
4. **Supply-chain rule (hard).** Nothing is downloaded and executed during the spike beyond
   reading source in an isolated checkout outside `C:\dev\Grassmarket`; no candidate is
   installed into any environment that holds Grassmarket credentials or data; a security
   review precedes any future adoption. State in the memo that this rule was followed.
5. **Recommendation.** Exactly one of: **adopt X** (with the integration seam named),
   **build thin** (a minimal in-house sequencer over the ADR-0045 registry with the approval
   gate native), or **defer** (with the trigger condition that reopens the question). No
   option lists in the conclusion — one recommendation with evidence.
6. **Follow-on tickets.** Draft the follow-on ticket files for the chosen path (numbered in
   the GRS-02xx range, `docs/tickets/`, Status: Draft — not scheduled), each with scope and
   acceptance stubs, committed in the same PR as the memo.

## Test plan

None — this ticket changes only `docs/`. CI must show no dependency, lockfile, or source
change; the PR diff is `docs/planning/agentic-gtm-spike.md` plus drafted ticket files only.

## Out of scope

- Adopting, vendoring, or installing any candidate.
- Any outbound sending capability, Gmail scope change, or ActiveGraph policy implementation.
- Building the thin sequencer (its own ticket if recommended).
- Importing the GTM registries (GRS-0193) or influencer maps (GRS-0194).

## Acceptance

- `docs/planning/agentic-gtm-spike.md` exists with: ≥ 5 fully-evaluated candidates, the 6 × N
  scoring table, all three constraint analyses, the supply-chain attestation, and exactly one
  recommendation with reasoning.
- Follow-on ticket drafts for the chosen path exist in `docs/tickets/`.
- `git diff` for the PR touches only `docs/` — no dependency has been added to the repo.
- Spike closed within the two-day box (noted in the memo header).
