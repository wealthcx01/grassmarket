# GRS-0097 — Refine the P & L labels product-wide (UI copy)

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** ADR (ATLAS → Platform Power rename)

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
