# ADR-0030 — Rename "ATLAS" → "Platform Power" (user/client-facing only)

- **Status:** Accepted (2026-07-16). Founder decision in the Part-2 UI/UX review: "ATLAS" is a meaningless
  placeholder; rename it product-wide to **Platform Power**.
- **Date:** 2026-07-16
- **Deciders:** Founder + engineering
- **Normative source:** `docs/planning/PART2-uiux-review.md` §1 (GRS-0090) + §2 (GRS-0097).
- **Implements:** GRS-0090 (rename-atlas-platform-power), GRS-0097 (refine-p-l-labels).

## Context

"ATLAS" was a working name for the assessment engine and methodology. The founder finds it meaningless to
advisers and clients. The deliverable is already "the Platform Power Report" and the headline score is
"Platform Value (V)", so the product vocabulary is converging on **Platform Power** already — the rename
makes it consistent everywhere a human reads it.

Two constraints shape the decision: (1) the golden master and the entire scoring surface are pinned to
internal identifiers (`atlas/` package, `b_index`/`p_index`/`l_index`, `theta_*`, `V = 0.478565`) — churning
those risks the load-bearing no-regression gate for zero user value; (2) two of the lens labels read as
arbitrary — **P = "Strategic Power"** doesn't match its letter and **L = "Infrastructure"** has no visible
letter link.

## Decision

1. **Rename user- and client-facing text only.** Everywhere an advisor or client sees "ATLAS", it becomes
   **Platform Power**: advisor UI (`app/page.tsx`, `app/guide/page.tsx`, `components/steps.tsx`, section
   blurbs), the methodology/docs (`docs/ATLAS-Methodology-*`, "ATLAS Assessment — How It Works"), and the
   public BC Advisory page (coordination note to the public-site design). Grep `ATLAS`/`atlas` across the repo
   + BC design to find every surface.
2. **Keep engine identifiers internal and unchanged.** The `atlas/` package, the `b/p/l/v` index names, the
   `theta_*` coefficients, and the golden master stay as-is. Internal code identifiers may remain `atlas` to
   avoid churn; this is a copy change, not a refactor.
3. **Naming nuance (avoid recursion).** Use **"the Platform Power assessment/method"** for the *process* and
   **"the Platform Power Report"** for the *deliverable*. Never write "the Platform Power methodology produces
   the Platform Power Report."
4. **Refine the lens labels, keep the letters (GRS-0097).** Keep B/P/L/V. Relabel **P: "Strategic Power" →
   "Power"** (Helmer's Powers — matches the letter) and **caption L so the letter reads**, e.g.
   "Infrastructure · the technology Layer", everywhere the lenses appear (primer, wizard, summary/live-score,
   dashboard). Engine identifiers unchanged.

## Consequences

- A UI-copy sweep (GRS-0090a), a docs/methodology-doc sweep (GRS-0090b), an explicit "leave internal `atlas/`
  identifiers alone" note (GRS-0090c), and a public-site coordination note (GRS-0090d); plus the label
  refinement (GRS-0097). No scoring, contract, or golden-master change.
- The methodology documents are re-titled but their normative content and version lineage are unchanged
  (a Platform Power methodology vN supersedes ATLAS-Methodology vN by title only at first).

## Alternatives considered

- **Rename internal identifiers too (`atlas/` → `platform_power/`, `b/p/l/v` unchanged).** Deferred — high
  churn, touches the golden-master-pinned surface, zero user value; can be a later cosmetic refactor if ever
  wanted.
- **Invent new letters to match the words.** Rejected — B/P/L/V are embedded in the engine and golden master;
  the founder chose to keep the letters and fix the words.
