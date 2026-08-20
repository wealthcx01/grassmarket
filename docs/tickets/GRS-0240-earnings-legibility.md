# GRS-0240 — The earnings page explains how you get paid

**Status:** DONE (2026-08-19). _Previously recorded as: Planned (2026-07-31, founder: "the earnings page is so confusing")._
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

---

## Status reconciliation — 2026-08-01

**DONE** — shipped 2026-08-19, all five scopes. No rate, and no earnings maths, was touched.

## What shipped

**1 — "How you get paid" opens the page**, above every number: the two streams named in words, the
three states a commission line moves through in order, and the definitions of *Earned YTD* and
*Projected unpaid* — the latter of which existed **only in a contract docstring** an advisor will
never read. It also says a line is created by the system and never entered by the advisor, which
the page had never stated.

The states render as an ordered list rather than a diagram: the sequence *is* the explanation, it
reads on a phone, and a screen reader gets it in the right order for free.

**2 — Both streams named, and the letters KEPT.** Decision, as the ticket asks: *keep them, explain
them once.* Not a style preference — `earnings/statement.py` prints "Stream B" as a heading in the
statement an advisor downloads, so page and document have to agree or someone comparing the two is
lost. The defect was labelling one stream and not the other, which made a lone "B" read as leftover
internals. The headings are now "Selling products · Stream A" and "Delivering consulting · Stream
B", and the statement's heading was aligned to match.

**3 — One vocabulary, and a real 2×2.** Products said "yr1 · yr2" while consulting said "first year
· thereafter" for the same concept; it is now "first year / thereafter" everywhere. The four
look-alike consultancy cards became an actual grid with **delivered-by** on the rows and
**sourced-by** on the columns, each defined in the caption. Four undefined terms presented as four
unrelated products are now two questions with an answer at their intersection.

The grid is built from the carrots the API returns, never a hardcoded 2×2, so a rate change in
`commissions.yaml` reflows with no frontend edit (GRS-0187's property, now covered by a test that
renames an axis label and asserts the grid follows). A cell the schedule does not supply says **"Not
in the schedule"** rather than rendering blank — a blank box in a rate table reads as 0%.

**4 — Every stat card carries its definition**, so a £0.00 still says what it is.

**5 — Illustrative money looks illustrative.** Example figures are italic and prefixed
"Illustrative:" — the word is part of the number's presentation rather than a parenthesis after it.
On a money page an example styled like a balance invites exactly the wrong trust.

## A stale test this change exposed

`app/earnings/page.test.tsx` asserted the literal heading `"Consulting (Stream B)"` and went red the
moment the copy changed. That is the same failure as GRS-0228 — an assertion pinned to a sentence
rather than to a behaviour, which stays green until a copy edit and then reads as a regression.

It is rewritten against **structure**: a heading matching `/Delivering consulting/`, a row header,
and a rate cell, queried by role inside the matrix. And it asserts "Stream B" appears **exactly
twice** — once where the explainer defines it, once where the heading uses it — so losing either
fails rather than passing quietly.

## Not done

- **No screenshots** (test-plan item 3). The zero-state and seeded-state comparison needs a running
  app with a signed-in advisor; the assertions cover the zero state directly instead, which is the
  state the founder actually walked.
- Rates and the v7 audit remain **GRS-0067 / D2**, untouched and still gated.
