# ADR-0036 — Finish & trust: solo-path discoverability, account security, cert teeth, and commission disclosure

- **Status:** Accepted (2026-07-19). Founder-directed stress-test remediation (raise advisor trust from a mean 57/100 toward ≥95).
- **Date:** 2026-07-19
- **Deciders:** Founder + engineering
- **Normative source:** `docs/tickets/GRS-0148`; stress-test synthesis `reports/mock-advisor-stress-test-2026-07-19.md`.
- **Implements:** GRS-0148 (+ GRS-0149 shipped). **Couples with:** ADR-0009 (AI-proposes/humans-approve gate), ADR-0029 (sandbox records), ADR-0017 (commission governance).

## Context

Four "finish & trust" gaps dragged confidence down independently of the scoring engine. They are a mix
of buildable wins and genuine governance decisions:

1. **"No solo path to a finished deliverable" (4/5 personas).** Production finalise needs a co-rater +
   committee; the sandbox self-approve path existed but was undiscoverable. *(Already shipped as
   GRS-0149 — a "Preview in sandbox" affordance in the wizard.)*
2. **Unfinished account surfaces (3 personas).** `/profile` and `/settings` are "coming soon"; there is
   no change-password endpoint, no data-protection/consent surface. On a live, invite-only product this
   reads as unfinished and, for the compliance persona, unsafe.
3. **"Certified" attests coverage, not skill (governance).** Course completion is self-reported clicks;
   the comprehension check is never verified server-side. Certification = coverage + a senior co-sign,
   not demonstrated skill — yet the demonstrated-skill data (SM-2 drill `repetitions`, arena
   `completeness`) already exists per-consultant.
4. **Commission-for-product-sales with no disclosure (2 personas).** The advisor both assesses a client
   and earns commission selling them third-party products (Benzinga/OpenBB/Brandfetch), and the Academy
   coaches the commission "carrot" — but nothing records that the advisor **told the client**. An
   independence hole a skeptical advisor or regulator flags first.

## Decision

1. **Solo-path discoverability — DONE (GRS-0149).** A "Preview in sandbox" affordance in the wizard's
   Summary step clones a production assessment into a self-approvable sandbox copy (composing shipped
   endpoints), so a solo advisor sees the real watermarked deliverable. No backend change.

2. **Change-password + real Profile — BUILD NOW (M).** Add a self-scoped `POST /auth/change-password`
   (verify current password via `verify_password`, enforce the existing min-12 rule, hash with
   `hash_password`, refuse cleanly for OAuth-only accounts, record an `AUTH_PASSWORD_CHANGED` audit
   event), a repository `set_consultant_password` mirroring `bind_google_sub`, an `api.changePassword`,
   and a real change-password form on `/profile`. Five thin layers, each templated by existing auth
   code; no new tables. Persistence stays in the repository layer (#5); the change is recorded, never
   silent (#3). Data-protection/consent copy is a fast follow.

3. **Cert teeth — BUILD MECHANISM NOW, threshold founder-set.** Tie the senior sign-off (the existing
   cert chokepoint) to a demonstrated-skill precondition computed from data already on hand: every
   auto-enrolled drill card for the backing course's topics at `repetitions >= 1` (a lapse resets
   repetitions to 0, so this is a clean "passed the recall at least once" signal), optionally an arena
   session at `completeness >= T`. The mechanism ships behind a config constant; **the numbers are a
   §9 certification-standard decision the founder sets** (default: every backing-course drill passed
   once, arena optional). Keeps the pure-function blocker boundary and fail-loud (a missing
   demonstration returns a reason, never a silent pass).

4. **Commission disclosure — ADOPT the artifact, founder confirms the gate.** Add a
   `CommissionDisclosure` record (`engagement_id`, `product_id`, `disclosed_by`, `disclosed_at`,
   `method`, `note`) written through the repository and emitting a `COMMISSION_DISCLOSED` audit event.
   **Recommended default (founder to confirm): a hard gate** — a commission-bearing deliverable/line
   cannot be recorded without a disclosure on file, mirroring the existing fail-loud governance gates.
   This turns "AI proposes, humans approve" (#8) into "advisor earns, client is told."

5. **Doctrine branding — founder call, default keep-internal.** The "Sales Egoist / weapons / zero-sum"
   framing is training-only and never client-facing; keep the doctrine intensity, but **rename the
   learner-visible certification title** (it can appear on a profile) to something neutral (e.g.
   "Consultative Sales"). Pure content edit if the founder agrees.

## Consequences

- Ships now: GRS-0149 (done), change-password + Profile (#2), cert-teeth mechanism behind a constant
  (#3).
- Founder-gated numbers/decisions: the cert threshold (#3), the commission-disclosure hard-gate (#4),
  the doctrine cert-title rename (#5).
- New: `ChangePasswordRequest` contract, `set_consultant_password` repo method, `/auth/change-password`
  router, `AUTH_PASSWORD_CHANGED` + `COMMISSION_DISCLOSED` audit types, a `CommissionDisclosure` record,
  and a `demonstrated` blocker in the cert sign-off path.

## Alternatives considered

- **Hide `/profile` and `/settings` until fully built.** Rejected — the identity view is useful and
  change-password is the one security control every live product owes; ship the real form, don't remove
  the page.
- **Make "Certified" require the demonstration unconditionally now.** Deferred — the *how much* is a
  certification-standard decision (§9) that belongs to the founder; ship the mechanism behind a tunable
  default rather than hard-code a bar.
- **Leave commission disclosure to training/manual process.** Rejected — the platform actively coaches
  the commission carrot, so the absence of a recorded disclosure is a real independence gap; a
  first-class artifact + gate is the honest fix.
