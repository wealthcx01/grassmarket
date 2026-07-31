# GRS-0234 — PDF furniture: the filename, the subtitle, the footer, the precision

**Status:** Planned (2026-07-31, first-time-user review G6). **Priority:** MED.
**Loop:** client-report hardening. **Extends GRS-0219.** **Relates to:** ADR-0040, GRS-0150.

## Why

The report body is now something Bruntsfield could put its name on; the furniture around it is not.
Observed on the staging WeBull and Hargreaves Lansdown PDFs, 31/07/2026:

- **The downloaded file is named `f6312cfe-4310-4dba-8a25-0c2c3bd77a57.pdf`.** An advisor will
  forward a database UUID to a CFO, or waste a minute renaming every export.
- **The cover subtitle reads "WeBull — delivery"** — the engagement's internal title, which reads as
  a system key, under an otherwise good cover.
- **Every page's footer prints `coefficients v1-draft-pending-elicitation`.** Provenance honesty is
  right (GRS-0219 scope 6) and stays; the wording is an internal config identifier. A client-facing
  sentence carrying the same fact reads: "Draft weighting — pending expert panel ratification."
  The identifier can live in the appendix's version table, where identifiers belong.
- **Page 4 of the WeBull sample is one chart and ~90% white space** — the figure placement strands
  the value build-up on its own page when the preceding section runs short.
- **The portfolio quotes V as 54.7 where the PDF appendix quotes 55** (`v_display_0_100` rounded).
  Same number, two precisions; an advisor saying "54.7" to a client holding a page saying "55" is
  friction the one-number rule (ADR-0040) exists to prevent. Pick one display precision for V and
  apply it on every surface and both renditions.

## Scope

1. **Filename:** `Bruntsfield — Platform assessment — <Client> — <YYYY-MM>.pdf` (sanitised for
   filesystem), set via Content-Disposition; the web download honours it.
2. **Cover subtitle:** derived from deliverable type + client ("Platform Power assessment", already
   line 1) with the engagement title dropped or humanised; no internal keys on the cover.
3. **Footer wording:** plain-English coefficient status sentence from a single mapping owned by
   contracts (draft / elicited / ratified → sentence), identifier retained in the appendix table
   only. The mapping is data, so GRS-0150's eventual ratification changes the sentence without a
   code edit.
4. **Figure flow:** allow the build-up figure to share a page with the section that references it
   (keep-with heuristics), and add a regression check that no interior page of the golden-master
   sample is >80% empty.
5. **Precision:** one display rule for V (recommend one decimal, matching the wizard), applied in
   the PDF figures table, web appendix, portfolio, stage 6 and engagement header. State the rule in
   ADR-0040's terms in the PR.

## Test plan

1. Backend: Content-Disposition filename asserted for a demo record; UUID absent.
2. Golden-master render re-baselined once, with the diff reviewed line by line in the PR (the text
   fixture changes here by design; scoring does not — golden master engine values byte-identical).
3. Footer mapping unit tests: three statuses, three sentences, identifier only in the appendix.
4. Page-fill check on the sample PDFs.
5. Standing gate: pytest, pyright, ruff.

## Out of scope

- What the report says (GRS-0211) and the web page (GRS-0220/0229/0233).
- Actually ratifying coefficients (GRS-0150).

## Acceptance

The founder downloads a report and could attach it to a client email unedited: the filename says
what it is, the cover carries no keys, and the footer's caveat reads as a sentence a client can
understand.
