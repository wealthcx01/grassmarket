# ADR-0029 — Demo and sandbox records (seeing deliverables without weakening the gate)

- **Status:** Accepted (2026-07-16). Founder-directed in the Part-2 UI/UX review: a solo tester cannot reach
  the payoff because finalisation needs a co-reviewer + committee, so they never see what a generated
  deliverable looks like. Founder chose **"Both, demo first."**
- **Date:** 2026-07-16
- **Deciders:** Founder + engineering
- **Normative source:** `docs/planning/PART2-uiux-review.md` §5.
- **Implements:** GRS-0117 (watermarked-demo-dataset — now), GRS-0119 (sandbox-self-approve — follow-up).
- **Couples with:** ADR-0009 (AI-approval gating); the CLAUDE.md non-negotiables (#6 immutable/versioned
  runs, #8 AI proposes/humans approve, #9 data scoping).

## Context

Deliverable generation is gated: an assessment cannot be finalised (and its Platform Power Report, exec
summary, infrastructure heat map, technical appendix, workshop output cannot be produced as client artefacts)
until it clears **dual-rating + committee** review. This gate is correct and load-bearing — but it means a
lone beta tester, or a salesperson demoing the platform, can never walk the flow end-to-end and see the
outputs. The founder wants two things without touching the production gate: (1) a polished, watermarked
**demo** anyone can view, and (2) a **sandbox** in which a solo tester can finalise their *own* test
assessment to see real generated drafts.

The risk to manage is that a demo/sandbox artefact must **never** be mistaken for, or promoted into, a real
client deliverable, and must never dilute the AI-approval non-negotiable.

## Decision

Introduce a first-class **record provenance** flag with two non-production values — `demo` and `sandbox` —
alongside the default `production`. The flag is set at creation, immutable, carried on the assessment /
engagement / deliverable, and enforced at the repository + generation layers:

1. **A non-production record bypasses the human governance gate but is permanently marked.** A `demo` or
   `sandbox` record may finalise and run the *real* deliverable generation (not hand-pasted placeholders), so
   the outputs are genuine AI drafts. Every surface it touches renders a **"DEMO — illustrative only"** (or
   "SANDBOX") watermark/badge.
2. **Non-production records are segregated and non-promotable.** They are never counted as ratified, never
   enter benchmark populations or the prediction register, and there is **no path** to convert a demo/sandbox
   record into a production one. The AI-approval gate for *client-facing* output is untouched — these outputs
   are never client-facing by construction.
3. **GRS-0117 (demo) first.** Seed one complete worked example from the **Revolut** briefing: prospect →
   finalised `demo` assessment → all deliverables in both internal-draft and client-facing *presentation*
   forms, watermarked. Reference source only; seeded through scoped storage; no client data committed.
4. **GRS-0119 (sandbox) as the follow-up.** A clearly-labelled non-production mode lets a solo tester
   self-approve and finalise their *own* assessment to see real drafts. Sandbox records are per-owner scoped,
   flagged, and disposable.

## Consequences

- A `provenance` (or equivalent) field on the assessment/engagement/deliverable contracts + ORM + migration;
  repository-layer enforcement (segregation, non-promotion, benchmark/prediction exclusion); a watermark
  component across deliverable + assessment + engagement views; a demo seed module under
  `src/grassmarket/`; a sandbox mode toggle in the wizard finalisation path.
- The golden master and scoring math are untouched — this is a provenance/gating concern, not a scoring one.
- Immutability (#6) is preserved: provenance is fixed at creation and sealed with the record.

## Alternatives considered

- **Weaken the real gate for solo testers.** Rejected — the dual-rating/committee gate is a system
  non-negotiable; a tester's convenience must not erode it.
- **Hand-paste static placeholder deliverables.** Rejected — the founder specifically wants to see the *real*
  AI-generated draft; placeholders don't show how generation behaves or how internal vs client-facing differ.
- **A separate demo deployment/database.** Rejected — heavier to maintain and it divorces the demo from the
  live product; an immutable in-band provenance flag is simpler and keeps one code path.
