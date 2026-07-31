# ADR-0046 packet — verifying the extraction memo against the committed supplement

**Date:** 2026-08-01 · **Ticket:** GRS-0218 (Phase 1, item 2) · **ADR:** ADR-0046

## Why this check exists

`data/reference/7powers-math-extraction.md` was authored on 2026-07-24, **before** the source PDF
was in the repository. It was written from the supplement without the supplement being committed
alongside it, which means nobody could check it. The PDF landed on 2026-07-31 in commit `2d81f56`
under Helmer's permission grant, so the memo can now be verified against its source — and it should
be, because Helmer's permission is conditional on him reviewing the work produced under it. A packet
sent for that review should not contain claims nobody has checked.

## What the source actually is

87 pages. **Only the first four carry extractable text** — the title page, the copyright and table
of contents, and the start of the front matter. Pages 5 to 87 are page images, so this verification
is a visual check of rendered pages against the memo's transcriptions, not a text diff. That matches
what the ADR-0046 packet will need to say about reproducibility: anyone re-running this check does it
by eye.

The memo's own description of the source ("the 'Notes/Supplement' edition, 87 pp.") is correct, and
its statement that page numbers match the printed page numbers holds on every page checked.

## Formulas verified

Three spot checks, chosen to cover the fundamental equation and two Surplus Leader Margin
derivations with different shapes.

| Memo | Source | Result |
|---|---|---|
| §1 Fundamental Equation of Strategy | p.5 | **Exact** |
| Scale Economies SLM | Appendix 1.1, p.15 | **Exact** |
| Network Economies SLM | Appendix 2.1, p.19 | **Exact** |

**§1, p.5.** The memo transcribes `NPV = Σ(CF_i/(1+d)^i)` and `NPV = M_0 · g · s̄ · m̄`. Both appear
on the page as printed, and all four symbol definitions match — including the full gloss on `m̄`
("net profit margin **in excess of that needed to cover the cost of capital**"), which is the part a
careless transcription would shorten to "margin".

**Scale Economies, p.15.** The memo gives `SLM = [C/(P·_sQ)]·[_sQ/_wQ − 1]` with the decomposition
Competitive Position `[_sQ/_wQ − 1]` = relative market share beyond parity, Industry Economics
`[C/(P·_sQ)]` = the relative importance of the fixed cost. The boxed formula and both labels on the
page are identical.

**Network Economies, p.19.** The memo gives `SLM = 1 − 1/[(δ/c)·(_sN − _wN) + 1]`, Competitive
Position `[_sN − _wN]` = absolute difference in installed base, Industry Economics `δ/c`, plus the
boundary note that SLM = 0 when `_sN = _wN` and tends to 100% as `_sN >> _wN` with δ>0. All of it,
including the boundary sentence, is on the page.

The memo's left-subscript convention (`_s X` / `_w X` for the strong and weak firm) is a faithful
rendering of Helmer's printed left-subscripts, and it is declared in the memo's own source note.

## Discrepancies found

**One, and it is a provenance statement rather than a mathematical error.**

The memo's Rights paragraph reads: *"This memo is the analytical extraction; the source PDF itself
is **not** committed to the repository."* That was true when written on 2026-07-24 and became false
on 2026-07-31 when `2d81f56` committed the supplement under the permission grant. Left as-is it
would tell a reviewer — possibly Helmer — that the repository does not hold his material when it
does. **Corrected in this change**, with the commit and date named so the record shows when the
position changed rather than quietly restating it.

**No mathematical discrepancies were found in the three checks.** That is a statement about three
derivations, not about all 87 pages; the remaining Powers were not re-verified line by line, and the
packet should say so rather than implying a full audit.

## The memo's own flags still stand

The memo already raises two places where it reconstructed a reading, and both survive this check as
genuine questions for Helmer rather than transcription errors:

- **§5.1 (p.7)** — Helmer writes the growth substitution inside the sum as `K_0(1+η)^{i+1}`. The
  memo transcribes the `i+1` exponent as printed while noting that a dimensional reading would
  expect `i−1`, and that the difference is immaterial to the collapsed form `NPV = K_0·g·γ`. This is
  exactly the kind of thing the review exists to settle: it is his indexing convention to confirm,
  not ours to correct.
- **§5.2** — the source prints a coefficient as lowercase `(z−1)` where the surrounding definitions
  use `Z`. Read as `(Z−1)` and flagged.

Both belong in the review packet as questions.

## What this means for the packet

The extraction is sound enough to send. Its transcriptions are faithful where checked, its
conventions are declared, and it flags its own reconstructions instead of smoothing them over —
which is the standard the packet needs, since the whole point of the review is that Helmer can
distinguish his mathematics from our application of it.

Two things to carry into GRS-0201 when the packet is assembled:

1. Say plainly that three derivations were verified against the source and the rest were not. A
   packet claiming a full audit that was not performed is the same defect class as the provenance
   line corrected above.
2. Include the two §5 flags as explicit questions rather than footnotes.

Scheduling the review itself is **founder decision D7** (`docs/FOUNDER-DECISIONS-2026-08.md`).
