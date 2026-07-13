# ADR-0009 — AI narrative proposal/approval: minimal in-repo model + injectable drafter port

- **Status:** Accepted
- **Loop:** 4 (GRS-0017)
- **Context sources:** PRD §5; CLAUDE.md non-negotiable #8 (AI proposes, humans approve — a runtime
  guarantee); GRS-0015 (`Deliverable` approver fields, the client-usable gate).

## Context

GRS-0017 requires AI to draft the interpretation/commentary/recommendation sections of deliverables,
with a human approving every word before it can reach a client. Two open questions:

1. **Where does the approval state machine live?** ActiveGraph (event-sourced, approval policies) is
   the eventual home, but it is not built yet.
2. **How does drafting run in CI?** The Claude Agent SDK is not a repo dependency, and CLAUDE.md
   forbids live model calls in tests.

## Decision

**A minimal, in-repo proposal/approval model now; an ActiveGraph adapter later.** The ticket
authorises this fallback explicitly.

1. **`AINarrative` contract + `ai_narratives` table.** A per-section owned resource bound to a
   deliverable and its finalised scoring run, carrying the proposal text, the approval trail
   (approver id, timestamp, and an edit-diff of consultant changes), and a status
   (`proposed → approved | rejected`). Scoped by `owner_consultant_id` like every owned resource.

2. **An injectable `NarrativeDrafter` port.** The drafting service depends on a `NarrativeDrafter`
   Protocol, never on a concrete SDK. The shipped implementation is `TemplateNarrativeDrafter` — a
   **deterministic, offline** drafter that renders versioned in-repo templates against facts derived
   from the scoring run. It is a real, testable proposer today and the seam a Claude Agent SDK
   adapter drops into later without touching feature code or tests.

3. **No live AI in CI.** Because the port is injectable and the default drafter is deterministic,
   the whole flow is exercised offline. The SDK adapter is deferred; when added it must still route
   every output through the same proposal/approval gate.

4. **Prompt templates are versioned in-repo.** `PROMPT_TEMPLATE_VERSION` and `DRAFTER_VERSION` are
   persisted on every proposal, so a narrative is always attributable to the template + drafter that
   produced it (auditability, mirroring the engine/coefficient versioning on scoring runs).

5. **The gate extends GRS-0015.** A client-facing pack containing **any** narrative not `APPROVED`
   is refused at runtime (`UnapprovedNarrativeError` → HTTP 409), exactly as a non-client-usable
   coefficient set is refused. Watermarked internal documents may render unapproved drafts, each
   clearly labelled `AI-DRAFTED`.

6. **Seniority gate (PRD §5 quality review).** Narratives authored under a **Venture Associate** or
   **Advisor** tier require **senior (Consultant-tier)** approval before finalisation; a
   Consultant-tier author may self-approve. Seniority ordering adopted here:
   `VENTURE_ASSOCIATE < ADVISOR < CONSULTANT`. This is the one judgement call not fixed by an
   existing contract; if the PRD later distinguishes "early-tier" from "senior" Advisors, refine the
   rank here and in `assert_senior_approval`.

   **How a junior's narrative actually gets approved under absolute data scoping (#9).** A narrative
   is owned by its author, so a *peer* consultant cannot see it — and a junior may not self-approve.
   The reachable senior path is the existing **governance-visibility** seam: a reviewer with a
   governance role (`Role.ADMIN`, later `COMMITTEE_MEMBER`) sees resources across owners in the
   repository layer, and if that reviewer is Consultant-tier, `assert_senior_approval` passes and
   they sign off the junior's draft. So senior approval crosses ownership only through governance
   visibility, never by widening peer scoping. A general senior-to-junior **delegation/reassignment**
   workflow (granting a specific senior access to a specific junior's draft without a governance
   role) is deferred to the Loop 5 governance work; it is additive to this seam, not a change to it.

## Consequences

- The runtime guarantee (#8) holds today with no external dependency and no live calls.
- The contract surface (`AINarrative`) and the port (`NarrativeDrafter`) are the stable seams; the
  ActiveGraph state machine and the SDK adapter are additive, not rewrites.
- The seniority ordering is an explicit, revisitable assumption, not a silent default.
