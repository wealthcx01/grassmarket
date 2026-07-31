# GRS-0240 — The earnings page explains how you get paid

**Status:** Planned (2026-07-31, founder: "the earnings page is so confusing").
**Priority:** MED-HIGH. **Loop:** first-time-user coherence. **Extends GRS-0187.**
**Relates to:** GRS-0067, ADR-0026.

## Why

Walked as a zero-earnings first-time user, 31/07/2026. The page is six stacked modules with no
orienting sentence about how payment actually works:

- Five £0.00 cards — Earned YTD / Pending / Invoiced / Paid / **Projected unpaid** — with no
  definition of any state or how money moves between them. ("Projected unpaid" is defined only in a
  contract docstring.)
- "Stream B" appears as a section heading ("Consulting (Stream B)") with no "Stream A" anywhere —
  the products section is never labelled, so the letters read as leftover internal naming. The
  split-bar that would explain them only renders once earnings exist.
- The Stream B matrix ("Bruntsfield-led · Self-sourced — 65% first year · 55% thereafter") uses
  four undefined terms, and its neighbours mix "yr1/yr2" with "first year / thereafter" for the
  same concept.
- "Next milestone · 0 reached — 0% of the way to £5,000.00 earned" and "CLOSE THIS NEXT — Sell
  Benzinga and earn £15,000.00 (illustrative deal)" arrive before the page has said what a
  commission line even is. An illustrative number styled like a real one, on a money page, invites
  exactly the wrong trust.

The rates themselves are right and config-driven (commissions-v7, ADR-0026) — the failure is
narrative order and vocabulary, and this page has already needed one legibility patch (the
"Consultancy £0.00" fix), which is the tell that it needs a structural pass, not another patch.

## Scope

1. **Open with how payment works.** A short "How you get paid" block at the top: two streams named
   in words (selling represented products; delivering consulting), the life of a commission line in
   four states (pending → invoiced → paid, with projected-unpaid defined as pending+invoiced), and
   where lines come from. One paragraph and a small diagram, not a wall.
2. **Name both streams or neither.** "Product commissions (Stream A)" / "Consulting (Stream B)",
   with the letters explained at first use — or drop the letters from the page entirely. Decide and
   state which; today's half-labelling is the worst of both.
3. **One vocabulary.** "First year / thereafter" everywhere (or yr1/yr2 everywhere); the Stream B
   matrix rendered as an actual 2×2 (delivered-by × sourced-by) with each axis term defined in a
   caption, replacing four look-alike cards.
4. **State definitions on the cards themselves** — each stat card carries its one-line meaning;
   empty state shows the definition rather than a bare £0.00.
5. **Illustrative numbers look illustrative.** The milestone ladder and "close this next" carrots
   are visually distinct from real earnings (muted style + "illustrative" as part of the number's
   presentation, not a parenthesis after it), and appear *below* the real-money modules, not beside
   the zeros.

## Test plan

1. Vitest: zero-state renders definitions on every card; both stream headings labelled
   consistently; matrix renders as 2×2 with axis captions; no "yr1" string when "first year" is the
   chosen form (assert one vocabulary).
2. Copy from the config mapping, not hardcoded — rate changes in commissions.yaml reflow with no
   frontend edit (existing GRS-0187 property, preserved by test).
3. Manual: zero-earnings screenshot and with-earnings screenshot (seeded), before/after, in the PR.
4. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- Rates and the v7 schedule audit (GRS-0067, gated).
- New earnings features (statements, projections math — unchanged).

## Acceptance

A brand-new advisor with £0 earned reads the page top to bottom once and can explain to someone
else how they will get paid, in which currency of effort, and what each of the five numbers will
mean when it stops being zero.
