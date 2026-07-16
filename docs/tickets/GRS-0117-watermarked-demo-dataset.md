# GRS-0117 — Watermarked end-to-end DEMO dataset (Revolut)

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** ADR-0029 (demo/illustrative records)

## Why

A solo beta tester cannot reach the payoff of the platform. Finalisation is gated on a co-reviewer plus
committee approval (dual-rating/governance, ADR-0009), so a lone tester can never complete an assessment
and therefore **never sees** what an AI-generated deliverable looks like — nor how an internal draft
differs from the client-facing version. The fix is a complete, clearly-labelled worked example seeded from
the **Revolut** briefing (the founder's pick — the richer neobank/wealth showcase) that runs prospect →
finalised assessment → every deliverable type, so anyone can walk the whole platform end-to-end. Crucially
the founder wants to see the **real AI-generated** draft, so the demo must run the actual
deliverable-generation against a seeded finalised assessment (not hand-pasted placeholders) and then
watermark every surface. This is the symptom-fix that unblocks the demo now; the root-cause sandbox
follow-up is GRS-0119.

## What to build

**Demo seed (a seed/fixture module under `src/grassmarket/`)**
- Seed one prospect → one assessment from the Revolut briefing, **finalised past the dual-rating/committee
  gate for the demo record only** — via the demo-record concept in ADR-0029, **not** by weakening the real
  gate. The demo record is flagged and segregated so production governance is untouched.
- Seed through **scoped storage**: the Revolut source is reference-only and **must not be committed** as
  client data. No client artifact enters the repo.

**Deliverable generation (`deliverables/` generators, `DeliverablesPanel.tsx` + deliverable views)**
- Run the **actual** AI deliverable-generation against the seeded finalised assessment for **all** types,
  in **both** internal-draft and client-facing forms: Platform Power report, exec summary, infrastructure
  heat map, technical appendix, and workshop output.
- Watermark every generated surface with a clear **"DEMO — illustrative only"** badge/watermark so it can
  never be mistaken for a real client artifact (governance/ADR-0009 hygiene).

**Demo badge on the record views (assessment + engagement views)**
- Carry the same "DEMO — illustrative only" badge on the assessment and engagement detail surfaces so the
  demo status is visible everywhere the record appears, not only on the deliverables.

## Acceptance / verification

- A solo tester with no co-rater can walk prospect → finalised assessment → every deliverable type in both
  internal-draft and client-facing forms.
- Every demo surface (assessment, engagement, each deliverable) shows the "DEMO — illustrative only"
  watermark/badge.
- The deliverables are produced by the real generators against the seeded finalised assessment, not
  hand-pasted placeholders.
- The production dual-rating/committee gate is unchanged; no Revolut client data is committed (seeded
  through scoped storage only).

## Not in scope

- The sandbox self-approve mode that lets a tester finalise their **own** assessment — GRS-0119
  (sequenced after this).
- Weakening or altering the real governance gate for non-demo records.
- Engagement↔assessment link legibility — GRS-0116; cross-screen backlinks — GRS-0118.
