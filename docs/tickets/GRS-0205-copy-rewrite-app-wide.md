# GRS-0205 — Rewrite every string in the app, not just the screens we reviewed

**Status:** Planned (2026-07-26, staging review items 1, 2, 3). **Priority:** HIGH.
**Loop:** founder-feedback remediation, Wave 1. **Supersedes the sweep half of GRS-0174.**

## Why

GRS-0174 wrote a voice guide and rewrote the screens it listed. The founder then opened staging
and found the same problem on the first thing they read:

> "Your home for the Bruntsfield Advisory Network — manage your pipeline, run Platform Power
> assessments, generate client deliverables, and grow in the Workbench."

and on the primer call to action, and on the buttons, and on all four Getting Started messages.
Their words: "All copy actually sounds too much like AI."

The pattern is the same every time. A dash splices two clauses that should have been two
sentences. A list of four gerunds stands in for a reason to care. The sentence is short because
short reads as confident, not because the advisor needed less. That register is fine in a product
tour and wrong in a tool an advisor uses for hours.

GRS-0174 failed because it treated copy as a set of screens. It is a set of strings, and the ones
nobody listed are still in the old voice.

## Scope

1. **Inventory first, rewrite second.** Extract every user-visible string in `frontend/` (JSX
   text nodes, `title`/`label`/`placeholder`/`aria-label`, button labels, empty states, toasts,
   error messages, tooltips) and every string the backend sends to a screen. Commit the inventory
   as `docs/copy/inventory-2026-07-26.md` with a file:line for each. This is the checklist the
   ticket is measured against, and the reason the last sweep missed things.
2. **Rewrite in the register defined by GRS-0174**, with these additions the founder's feedback
   makes explicit:
   - No em dash used as a clause splice. Two sentences, or a comma, or a colon. The em dash is
     allowed in an aside inside a sentence, and that should be rare.
   - No three-or-four item gerund list standing in for an explanation.
   - Say what the thing does and who it is for. Length is not the enemy. "Too brief" was the
     complaint, twice.
   - Address the advisor as a colleague who knows their trade, not a new user being onboarded.
3. **Named rewrites the founder called out**, each reviewed individually rather than swept:
   the home page hero, "New to Platform Power? Start with the primer", the four Getting Started
   messages, and every button label in the wizard, pipeline, portfolio and Workbench.
4. **A lint that keeps it fixed.** `tests/test_copy_register.py` walks the inventory paths and
   fails on: an em dash between two independent clauses, a sentence under five words used as a
   standalone description, and the specific banned constructions listed in the style guide. New
   copy has to pass it, so the next sweep is not needed.
5. **Style guide updated** at `docs/STYLE-VOICE.md` with the em dash rule and a before/after table
   drawn from the strings the founder actually quoted.

## Test plan

1. `uv run pytest tests/test_copy_register.py`, which must fail on the pre-rewrite strings
   (commit the failing run in the PR description) and pass after.
2. Per-file vitest loop over every changed frontend test file.
3. Manual: screenshot the home page, primer CTA and Getting Started sequence before and after,
   both in the PR.
4. Standing gate: pytest, pyright, tsc, ESLint.

## Out of scope

- The Guide and Primer long-form documents (GRS-0175, already merged; this ticket only fixes
  strings inside the app shell).
- Report and deliverable prose (GRS-0189, GRS-0211).
- Course content prose (GRS-0215).

## Acceptance

The founder reads the home page, the primer prompt, the Getting Started messages and ten buttons
picked at random, and does not flag the voice. The inventory shows zero unreviewed strings.
