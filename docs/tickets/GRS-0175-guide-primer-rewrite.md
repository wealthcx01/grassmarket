# GRS-0175 — Guide & Primer rewrite

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: In review (2026-07-25) — /help merged into /guide, page rewritten in the STYLE-VOICE._
register, PR open. (2026-07-23, founder feedback items 27 and 6-partial.) **Priority:** HIGH.
**Loop:** founder-feedback remediation, Wave 1. Depends on GRS-0174 (style guide) and GRS-0179
(the maths explainer it summarises).

## Why

The Guide and Primer share the same compressed register the founder rejected, and the
"Reading the Outputs" section references P50/P10/P90 without ever defining them — the founder's
direct words: "I have no idea what these mean". There are also two similarly-named guides with
different entry points (header "Guide" opens `/help`; the dashboard primer strip opens `/guide`),
which confuses first-time readers.

## Scope

1. **One entry point.** Decision: `/guide` is the single canonical Guide, because the header
   label already says "Guide" and the concepts content lives there. Merge the how-to content of
   `frontend/app/help/page.tsx` (its `SECTIONS` walkthroughs and `PRINCIPLES` cards) into
   `frontend/app/guide/page.tsx` as a second half, so the page reads: "Concepts" (the primer)
   then "Working the app" (the walkthroughs) then "Principles". Structure:
   - Delete `frontend/app/help/page.tsx` and add a redirect in `frontend/next.config.mjs`
     (`{ source: "/help", destination: "/guide", permanent: true }`), preserving old links and
     the in-app anchors that matter (`/help#...` anchors map to the same ids under `/guide`;
     keep the section `id` values unchanged when content moves).
   - `frontend/app/layout.tsx` line 115: the header link changes `href="/help"` to
     `href="/guide"`; the label stays "Guide".
   - Update every internal link that targets `/help` (find with `rg '"/help' frontend`).
   - `frontend/components/GuideNav.tsx` gains the merged section list (concepts, how-to,
     principles) so in-page navigation covers the whole document.
2. **Rewrite the content** of the merged page in the STYLE-VOICE register (GRS-0174), with real
   depth: every term defined before first use, worked examples in place of slogans, and no
   sentence that trades on notation the reader has not yet been given. The existing section ids
   (`why`, `provenance`, `how-it-works`, `lenses`, `letters`, `maturity`, `evidence-grades`,
   `scoring-powers`, `seven-powers`, `reading-outputs`, `calibration`, `mistakes`) survive so
   deep links keep working.
3. **"Reading the Outputs" defines the notation before using it.** New order inside that
   section: what a modelled range is (many recalculations of the same assessment under input
   uncertainty); then P10/P50/P90 in words (the value that 10%, 50%, and 90% of those
   recalculations fall below); then why the quoted headline is the deterministic point and the
   range is the honesty band around it (ADR-0040); then one worked picture, an inline SVG strip
   showing a P10-P90 bar with the point marked, built with the design tokens (no chart library).
4. **Cross-link the maths explainer.** Add a "Scoring, explained in full" subsection at the end
   of the concepts half that summarises the GRS-0179 composite (V = θ_B·B + θ_P·P + θ_L·L, the
   per-segment weights in one table read from the shipped values, and the words-vs-numbers rule
   as an explained paragraph, not a mantra) and names `docs/ATLAS-Scoring-Explained.md` as the
   full reviewable account. Decision: the Guide paraphrases at reader depth rather than
   embedding the document, because the docs file is the founder-review artifact and the Guide is
   the advisor-facing summary; the numbers quoted in the Guide must match the live coefficient
   sets exactly (`src/grassmarket/atlas/draft_coefficients.py` retail θ 0.30/0.30/0.40;
   `elicited_coefficients.py` wealth 0.45/0.30/0.25, exchange 0.30/0.37/0.33).
5. Each mantra retired by GRS-0174 appears here exactly once, expanded into its real
   explanation (for example "Words rate; numbers rank" becomes a paragraph on why rating gates
   produce boardroom words while continuous scores order the fix list).

## Test plan

1. Create `frontend/app/guide/page.test.tsx`; run `bunx vitest run frontend/app/guide/page.test.tsx`.
   Asserts: the page renders the three-part structure; the reading-outputs section defines
   "P10", "P50", and "P90" in words before any bare use (assert the definition strings render);
   the section ids listed in Scope item 2 are all present; no occurrence of "P50" before the
   definitions block (order assertion via DOM position).
2. Delete or migrate any `/help` page test; assert in the guide test that `GuideNav` lists the
   merged sections.
3. Manual check recorded in the PR: `/help` returns a 308 to `/guide` in `next start`, and the
   dashboard primer card and header both land on `/guide`.
4. Standing gate: tsc, ESLint; `rg '"/help' frontend` returns nothing.

## Out of scope

- Any scoring, engine, or backend change (this is copy and routing only).
- The Summary step repair (GRS-0182) and the component copy sweep (GRS-0174).
- Authoring `docs/ATLAS-Scoring-Explained.md` itself (GRS-0179).
- Academy or Workbench content.

## Acceptance

A reader who has never seen the product can explain V, C, the range, and P10/P50/P90 after the
Guide alone. No unexplained notation anywhere on the page. One "Guide" entry point: the header,
dashboard, and all internal links resolve to `/guide`, and `/help` permanently redirects there
with anchors preserved. The θ values quoted match the shipped coefficient sets exactly.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `b4d585b` (GRS-0175: merge /help into /guide and rewrite the Guide).

This ticket carried no *What shipped* record; the commits above are that record.
