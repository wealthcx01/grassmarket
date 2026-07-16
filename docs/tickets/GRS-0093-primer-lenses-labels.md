# GRS-0093 — Primer: the lenses (B/P/L/V) + label clarity

**Status:** Planned
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** GRS-0097 (refine the P & L labels product-wide)

## Why

The primer's treatment of the four lenses is too thin, and two of the labels read as arbitrary. Each lens
needs more explanation: what "Platform" and "Platform Power" actually mean, Helmer's 7 Powers, and the
**added Platform Power layer** (the Economic / Perceived / Defence triad). The mappings that don't land:
**P = "Strategic Power" doesn't work** ("just call it P" — P is for *Power*), and **L = "Infrastructure"
is unexplained** (the letter and the word mismatch — "no idea where L comes from"). The founder's
decision (2026-07-16) is to **refine the labels and keep the b/p/l/v letters**. This ticket explains each
lens properly and applies the refined labels in the primer.

## What to build

**Primer (`frontend/app/guide/page.tsx`)**
- Explain each lens (B / P / L / V) in depth: what "Platform" and "Platform Power" mean, Helmer's 7
  Powers, and the added Platform Power layer (the Economic / Perceived / Defence triad).
- Make the letter↔word mapping legible: explain the derivation so P and L no longer read as arbitrary.
- Apply the refined labels from GRS-0097 in the primer — **P: "Power"** (Helmer's Powers, matches the
  letter) and **L captioned so the letter reads** (e.g. "Infrastructure · the technology Layer"). GRS-0097
  owns the product-wide wording; this ticket applies the same wording in the primer.

## Acceptance / verification

- Each of B/P/L/V has a substantive explanation, including the added Economic/Perceived/Defence triad.
- The P and L labels match the refined wording from GRS-0097; the letter↔word mapping is explained, not
  arbitrary.
- The letters b/p/l/v are kept; no engine identifiers change.

## Not in scope

- The product-wide label refinement itself (GRS-0097 — wizard, panels, dashboard, public site).
- The 7 Powers deep content (GRS-0094).
