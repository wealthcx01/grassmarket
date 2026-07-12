# GRS-0015 — Deliverable core + the client-usable gate

- **Loop:** 4 (see PRD §9) — first Loop 4 ticket.
- **Branch:** `grs-0015-deliverable-core`
- **Status:** In review
- **Normative source:** PRD §5 (Deliverable Builder); `docs/ATLAS-Methodology-v1.2.md` §6–§7;
  ADR-0001 (fail loud), ADR-0002 (score/currency separation), ADR-0008 (honest uncertainty),
  CLAUDE.md #8 (AI proposes / humans approve — the approver field is present now).
- **Depends on:** GRS-0006 (value layer / provenance), GRS-0009 (finalised scoring runs),
  GRS-0013 (engagements + `DeliverableSlot`).

## Goal

The python-docx deliverable engine and **the controlling gate**: a client-facing pack may not be
generated from a coefficient set with `client_usable=False`.

## What shipped

1. **The client-usable gate** (`deliverables/gate.py`) — the controlling non-negotiable, a **runtime
   refusal**: `resolve_mode(coefficients, client_facing=True)` on a `client_usable=False` set raises
   `ClientUsabilityError`. `client_facing=False` returns `DRAFT_INTERNAL` (allowed on any set,
   always watermarked). The draft v1 set (`v1-draft-pending-elicitation`, `client_usable=False`) can
   therefore emit only watermarked "DRAFT — not client-usable" internal documents — never a client
   pack. The gate is enforced *before* anything is rendered.
2. **The python-docx builder** (`deliverables/builder.py`, SD3 report-stack pattern) — the first
   sections of the Diagnostic pack from a finalised scoring run:
   - **Platform Power Report**: B/P/L/V with honest uncertainty statements + the triad **ordinals**
     with rationale (the ordinal is what a client sees; the audit-only score is noted, ADR-0002).
   - **Methods Appendix**: engine / methodology / coefficient / uncertainty versions; "weights
     expert-elicited [date] ([method]), review due [date]" from the provenance records; and the
     weight-stability summary (recorded dispersion per coefficient family).
   - A `DRAFT_INTERNAL` document carries the watermark in the page header on every page.
3. **Honest uncertainty** (`deliverables/uncertainty_text.py`, ADR-0008): a modelled index prints
   `V = 51.1 (range 48.4–53.9)`; an **unmodelled** index prints a labelled point,
   `B = 67.9 (uncertainty not modelled)` — never a false-tight band.
4. **Service + persistence**: `deliverables/service.py` re-derives the uncertainty bands by
   re-running the Monte Carlo from the run's stored inputs (fixed seed → reproducible), using the
   run's **immutable stored** AtlasResult for the point scores. `DeliverableORM` + repository
   (scoped) persist the deliverable's metadata (mode, scoring-run link, coefficient version, content
   hash); the `Deliverable` contract gained `mode`/`scoring_run_id`/`coefficient_version`/
   `content_hash`/`generated_at`. The .docx is **regenerated on download** (no bytes stored).
5. **API** (`deliverables` router): `POST /engagements/{id}/deliverables` (generate; `client_facing`
   flag), `GET /engagements/{id}/deliverables` (list), `GET /deliverables/{id}/download` (stream the
   regenerated .docx). Scoped; cross-owner → 404; the gate refusal and "no finalised assessment" →
   409. **Alembic migration 0006**.
6. **ADR-0002 guard extended**: `_SCAN_DIRS` now includes `src/grassmarket/deliverables` — the
   builder renders scores now and will render Money (the value bridge) from GRS-0016; the doc may
   show both side by side but no function mixes them. Guard green with the new surface.

## Tests

The gate refuses a client pack on the draft set (unit + service + HTTP 409) and allows an internal
draft / a client pack on a client-usable set; a draft document is watermarked; a modelled index
prints a range while an **unmodelled B/P prints a labelled point, not a range**; the methods appendix
carries the versions + elicitation/review dates; generation ties to the engagement's finalised run;
download regenerates a real .docx (PK zip); every route is scoped (cross-owner → 404); an engagement
without a finalised assessment refuses. **225 backend tests pass** (+13).

## Non-negotiables honoured

The client-usable gate is a runtime refusal (tested); Methodology v1.2 normative; fail loud;
repository-only persistence; data scoping absolute + tested; ADR-0002 with the AST guard extended to
`deliverables`; the approval fields carry non-negotiable #8 (AI drafts are GRS-0017); one ticket =
one branch = one PR.
