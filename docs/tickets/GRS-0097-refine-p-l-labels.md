# GRS-0097 — Refine the P & L labels product-wide (UI copy)

**Status:** Shipped
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** ADR-0030 (ATLAS → Platform Power rename)
**Branch:** `grs-0097-refine-p-l-labels`

## What shipped

Refined the two arbitrary-reading lens labels, keeping the **B/P/L/V letters** and leaving the engine
untouched (ADR-0030):

- **P: "Strategic Power" → "Power"** (Helmer's Powers — matches the letter).
- **L captioned so the letter reads: "Infrastructure · the technology Layer"** (L = Layer).

Applied where the labels appear:
- **Live-score / summary panel** (`components/LiveScorePanel.tsx`) — band labels now `P — POWER` and
  `L — INFRASTRUCTURE · THE TECHNOLOGY LAYER`.
- **Wizard** (`components/steps.tsx`) — the step title `Strategic Powers → Powers`.
- **Primer lens labels** (`app/guide/page.tsx`) — `Power` and `Infrastructure · the technology Layer`
  (the primer's explanatory prose is GRS-0093's).
- **Advisor guide** (`app/help/page.tsx`) — `P (Power)`, `L (Infrastructure · the technology Layer)`,
  and the step name `Strategic Powers → Powers`.
- **Diagnostics waterfall** (`lib/diagnostics.ts`) — `P → "Power (P)"`; the compact SVG axis keeps the
  terse `Infrastructure (L)` (the fuller caption rides the live-score band label + the primer, where
  there is room — a chart axis stays terse by design).

**Engine identifiers unchanged** — `b_index`/`p_index`/`l_index`, `theta_*`, and the golden master are
untouched (user-facing copy only). The **public-site coordination note** is recorded in ADR-0030.

## Acceptance / verification

`grep`-clean of "Strategic Power" across `frontend/`. P reads as "Power" and L is captioned in the
live-score/summary panel, wizard step title, primer, and guide; the B/P/L/V letters are retained;
engine + golden master unchanged; frontend type-check · lint · vitest green.

## Why

Two of the four lens labels read as arbitrary to the founder: **P = "Strategic Power"** doesn't land ("P
is for *Power*"), and **L = "Infrastructure"** leaves the letter unexplained ("no idea where L comes
from"). The founder's decision (2026-07-16) is to **refine the labels while keeping the b/p/l/v letters**
— the engine and code are untouched. This is a cross-cutting copy change so the labels read consistently
everywhere they appear, plus a coordination note for the public BC site. GRS-0093 applies the same
wording inside the primer.

## What to build

**Product-wide label copy (keep letters B/P/L/V)**
- Relabel **P: "Strategic Power" → "Power"** (Helmer's Powers — matches the letter).
- **Caption L so the letter reads**, e.g. **"Infrastructure · the technology Layer"** (or similar), so
  the L↔word mapping is legible.
- Apply everywhere the labels appear: the primer, the wizard (`frontend/components/steps.tsx` step titles
  and `frontend/app/assessments/[id]/WizardClient.tsx`), the summary / live-score panel, and dashboard
  blurbs.
- Add a **coordination note for the public BC site** so its labels match.

**Engine identifiers — unchanged**
- `b_index` / `p_index` / `l_index`, `theta_*`, and the golden master are **not touched**. This is
  user-facing copy only.

## Acceptance / verification

- P reads as "Power" and L is captioned so the letter reads, in the primer, wizard step titles, live-score/
  summary panel, and dashboard blurbs.
- The letters B/P/L/V are retained everywhere.
- Engine identifiers (`b_index`/`p_index`/`l_index`, `theta_*`) and the golden master are unchanged; tests
  stay green.
- The public-site coordination note is recorded.

## Not in scope

- The primer's explanatory lens content (GRS-0093 applies this wording there).
- Renaming ATLAS → Platform Power (GRS-0090) — a separate, parallel copy change.
