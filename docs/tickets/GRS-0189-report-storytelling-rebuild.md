# GRS-0189 — Rebuild the deliverables to the story architecture

**Status:** SUPERSEDED (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-23, founder feedback item 17). **Priority:** HIGH._
**Loop:** founder-feedback remediation, Wave 3. Carries ADR-0042.

## Why

Founder verdict on the current reports: formatting and context "abysmal" relative to the data
collected and the design system available. The report should tell a story — generally good news,
with the one thing the client can do to improve their standing — and the technical material
belongs in an appendix. Today builder.py/reports.py compose a data-ordered document with default
matplotlib charts and no narrative arc.

## Scope

Per ADR-0042 (report narrative architecture):

1. **Brand tokens in one module.** New `src/grassmarket/deliverables/brand.py`: colour
   constants (PAPER `#F7F5F0`, INK `#1C1C1A`, INK_MUTED, BOTTLE_GREEN `#1A3B26`, ALERT_RED
   `#8A2020` — matching `frontend/app/globals.css`), font names (Source Serif 4 for headings,
   Inter for body, IBM Plex Mono for figures), and shared table/callout style helpers.
   `charts.py` imports its palette from here (its local `BOTTLE_GREEN`/`ALERT_RED` constants
   move); `docx_base.py` and `builder.py` consume the same tokens. Decision: fonts are set by
   name in docx styles (the reader substitutes if not installed); no font files are committed.

2. **Styled document base.** `src/grassmarket/deliverables/docx_base.py` is extended so
   `start_document` produces: a cover page (subject, deliverable title, date, Bruntsfield
   wordmark as text, Bottle Green rule), styled Heading 1–3 (Source Serif 4, ink/green),
   body style (Inter, 10.5pt, 1.35 line spacing), a shared table style (green header row,
   paper banding), and a callout paragraph helper. The DRAFT watermark behaviour
   (`DRAFT_WATERMARK` header on every page plus banner) is preserved exactly for
   DRAFT_INTERNAL mode.

3. **Five-part story structure.** New `src/grassmarket/deliverables/story.py` holds pure
   section-derivation functions plus the section renderers; `build_platform_power_report` in
   `builder.py` is rewritten to compose, in order:
   1. *Executive letter* — where the client stands (V with its honest band via
      `format_index_statement`, C alongside where present), led by strengths (modules at
      Advanced/Frontier, powers at Established+), headline in words.
   2. *The one thing* — the bottleneck: the minimum of B/P/L names the binding constraint
      (the same "lowest is binding" logic the narrative template already states); within L,
      the lowest-q_m or gate-blocked module names the concrete target. ΔV is stated from the
      stored composite, in plain language.
   3. *The path* — prioritised upgrades. Score-domain ΔV ordering always renders; value-bridge
      pricing (cost £ / lever NPV £ / strategic ordinal) renders only when a `ValueBridge` is
      supplied by the caller, in separate labelled columns. Decision: the Platform Power
      Report's path section renders priorities and points readers to the Modernisation Roadmap
      for pricing when no bridge is passed — score-points and currency never share an equation
      or a column (ADR-0002), and the report never fabricates prices.
   4. *Evidence highlights* — at most three charts: module radar, index tornado, and (when a
      bridge is present) the priority-vs-cost scatter, each titled and captioned.
   5. *Technical appendix* — everything currently in the body relocates here unchanged in
      substance: the full index statements, the C heatmap and differentiation/rarity sections,
      `_methods_appendix` (versions, weight provenance, stability table), the committee/founder
      approval trail, and `append_narrative_appendix`. Nothing technical is deleted.

4. **Chart restyle.** `charts.py`: all four functions (`priority_cost_scatter`,
   `module_radar`, `evolution_lines`, `index_tornado`) restyled to the brand tokens — titled,
   axis-labelled, annotated, paper background, no default matplotlib look. Signatures are
   unchanged (plain floats only, AST guard stays green); `_render_png` determinism note and
   metadata stripping unchanged.

5. **Narrative sections.** `narrative.py`: the three existing `NarrativeSection` values are
   re-purposed 1:1 — INTERPRETATION drafts the executive letter, COMMENTARY drafts the one
   thing, RECOMMENDATION drafts the path. Decision: reuse the existing enum rather than extend
   it, so the approval machinery, repository rows, and gate (`assert_narratives_approved`)
   need no contract or migration change. Template texts are rewritten to the story voice;
   `DRAFTER_VERSION` bumps to `template-drafter-v2` and `PROMPT_TEMPLATE_VERSION` to
   `narrative-templates-v2`. The deterministic template drafter remains the offline/CI path;
   a Claude drafter still plugs in behind the same Protocol later. Approved narratives render
   INTO sections 1–3 (replacing the deterministic paragraph for that section); unapproved or
   absent narratives fall back to the deterministic text, and the appendix trail renders as
   today.

6. **Boardroom pptx variant.** New `src/grassmarket/deliverables/pptx_summary.py` with
   `build_executive_summary_pptx(context, mode) -> bytes` (python-pptx added to
   `pyproject.toml`): 5 slides — cover, headline (V band + C), the one thing, the path, and an
   honesty slide (uncertainty + versions). Same brand tokens; DRAFT_INTERNAL mode stamps
   `DRAFT_WATERMARK` on every slide. Contract: `DeliverableType.EXECUTIVE_SUMMARY_PPTX =
   "executive_summary_pptx"` added in `bcap_contracts/deliverables.py`, JSON schema
   regenerated, TS union in `frontend/lib/types.ts` extended, label added to
   `DeliverablesPanel`. Service: `RenderedDeliverable` gains `media_type: str` and
   `file_extension: str` (docx renderers fill the docx values; the field `docx_bytes` is
   renamed `file_bytes` across the deliverables package and router in this PR). The pptx type
   joins the single-run dispatcher in `service.py` and passes the same gates
   (`resolve_mode`, uncertainty client-usable, founder approval per GRS-0188); the download
   route serves the stored type's media type and extension.

7. **Honesty invariants.** Every figure quoted in sections 1–3 is taken from the stored
   run/context objects (never re-derived arithmetic in prose) so it recomputes exactly
   (ADR-0040 one-number rule); bands accompany points per `format_index_statement`; the
   good-news ordering never drops a gate, caveat, or uncertainty statement (the appendix always
   carries them); watermark and gate machinery unchanged.

## Test plan

Backend (pytest, offline; python-docx/python-pptx read-back — no golden image diffing):
- New `tests/test_report_story.py`:
  - Generated Platform Power Report headings appear in the five-part order; the executive
    letter section precedes any table; the strings "Methods Appendix", weight-provenance
    table, and version block appear only after the "Technical appendix" heading.
  - The one-thing section names the argmin of (B, P, L) and, when L is binding, the
    lowest-q_m/gate-blocked module — asserted against a fixture whose bottleneck is known.
  - Every numeric token in sections 1–3 equals the corresponding stored-result value formatted
    by the shared helpers (one-number rule).
  - The path section contains no "£" when no bridge is passed; with a bridge, ΔV and £ appear
    in separate cells and never in one expression.
  - Approved narrative replaces the deterministic paragraph for its section; unapproved falls
    back and still renders in the appendix with its status.
  - DRAFT_INTERNAL docx carries the watermark header; CLIENT does not.
- New `tests/test_pptx_summary.py`: pptx generates for a finalised run; slide count and titles;
  DRAFT watermark on every slide in draft mode; client-facing pptx on draft coefficients →
  `ClientUsabilityError` (router: 409); byte-deterministic for a fixed context.
- `tests/test_deliverables.py` / `test_diagnostic_pack.py`: updated for `file_bytes` /
  `media_type`; new type generates via `POST /engagements/{id}/deliverables` (201), downloads
  with the pptx media type; unknown/roadmap types still 422; owner-scoping 404 cases unchanged.
- `tests/test_atlas_engine_golden_master*.py`: untouched and green — no scoring code changes.
- Chart smoke tests: signatures unchanged; each returns non-empty PNG bytes.

Frontend (vitest):
- `frontend/components/DeliverablesPanel.test.tsx`: the pptx type is offered, labelled
  "Executive Summary (slides)", and downloads with the right filename extension.

## Out of scope

- The founder review gate wiring itself (GRS-0188; this ticket assumes its gate function
  exists and calls it).
- Modernisation Roadmap and Score Evolution document redesigns (follow-up ticket if wanted;
  they keep the new docx_base styling for free but their section structure is unchanged).
- A live Claude narrative drafter (the Protocol seam is unchanged).
- Any scoring, uncertainty, or value-bridge computation change.

## Acceptance

- A generated Platform Power Report opens with the executive letter and reads as the five-part
  story; all formulas, module tables, uncertainty method, and version block sit in the
  technical appendix (verified by read-back test).
- The pptx variant generates behind the same gates and watermark rules as the docx set.
- Every quoted number reconciles exactly to the stored run (test-enforced).
- Charts render in the Bruntsfield palette with titles and annotations; no default-styled
  chart remains in any deliverable.
- ATLAS golden masters byte-identical; contract schema + TS mirror regenerated in the same PR.

---

## Status reconciliation — 2026-08-01

**SUPERSEDED.** Superseded by GRS-0211. GRS-0211 says so in terms: 'GRS-0189 was written for this and has not been started. This ticket replaces it.'
