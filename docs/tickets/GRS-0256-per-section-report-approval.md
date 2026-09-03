# GRS-0256 — Report editor: per-section approval on report prose

**Status:** OPEN (2026-09-03). **Priority:** MED-HIGH. **Type:** Feature. **Source:** R4. New gap **G14**.

## Why

Two section models exist and they disagree. `ai_narratives` has 3 sections, each approvable.
`client_report_prose` has 6 `ReportSectionKind` sections, saved and approved **whole**. The report
editor in the design is built on the 6, and approves section by section — so today an advisor who
changes one sentence in §3 re-approves all six.

## Build

- Section-level approval on report prose: `approved_at`, `approved_by`, **voided by a later edit of
  that section**. An approval that survives an edit is the exact dishonesty non-negotiable #8
  exists to prevent.
- Retire or fold in the narratives endpoints. Two approval models over the same document is how the
  gate gets bypassed by accident.
- The editor shows "changed since your read" per section.

## Done when

Approving §3 leaves §4 unapproved, editing §3 afterwards voids its approval, and there is exactly
one approval model for report content.
