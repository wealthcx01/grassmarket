# GRS-0093 — Primer: the lenses (B/P/L/V) + label clarity

**Status:** Shipped
**Loop:** Part 2 — Advisor Studio UI/UX review
**Depends on:** GRS-0097 (refine the P & L labels product-wide)
**Branch:** `grs-0093-primer-lenses-labels`

## What shipped

A new **"What the letters mean"** section in the primer (`app/guide/page.tsx`), below the lens cards,
that explains each lens in depth and makes the **letter↔word mapping legible** so P and L no longer
read as arbitrary:

- Opens by defining **"platform"** (the whole operating system of a brokerage/fintech — economics,
  strategy, technology) and **"Platform Power"** (how much durable value that whole creates → the V,
  Platform Value, headline).
- A definition list per lens: **B — Business** (the economic reality, normalised so a £2bn and a £50m
  platform compare fairly); **P — Power** (the letter *is* Power — Helmer's Powers, benefit protected
  by a barrier, weaker side wins); **L — Infrastructure · the technology Layer** (the letter is *Layer*
  — the tech layer under the business; asset or constraint?); **V — Platform Value** (the composite,
  but the number a client remembers is the bottleneck).
- Closes on the **triad** re-reading the same evidence as three plain words — Economic / Perceived /
  Defence value.

Applies the GRS-0097 refined labels in the primer (P: "Power"; L: "Infrastructure · the technology
Layer"). GRS-0097 owns the product-wide wording; this ticket applies it in the primer + explains the
derivation.

## Acceptance / verification

Each lens is explained in depth with its letter derivation (P = Power, L = Layer), "platform" /
"Platform Power" are defined, and the triad is covered. Refined labels applied. Frontend type-check ·
lint · vitest green.

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
