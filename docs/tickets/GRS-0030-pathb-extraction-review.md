# GRS-0030 — Path B: extraction → review → identical scoring

- **Loop:** 6
- **Branch:** `grs-0030-pathb-extraction-review`
- **Status:** In review
- **Normative source:** PRD §3.3 — including its acceptance criterion verbatim: "confirmed Path B data produces identical scores to manual entry of the same data." CLAUDE.md #8.
- **Depends on:** GRS-0029, GRS-0010 (wizard).

## Goal

AI maps conversation content to the assessment schema; the consultant confirms every field; confirmed data is indistinguishable from manual entry downstream.

## Scope

1. Extraction service: transcript → intermediate assessment schema with per-field confidence (high/medium/low) and explicit gap flags for unfilled fields.
2. Every extraction is a gated proposal (ActiveGraph pattern from GRS-0017): nothing enters the assessment unconfirmed; acceptance logged per field with provenance (which transcript, which span).
3. Review UI: wizard pre-populated with extractions marked by confidence; accept / correct / reject per field.
4. Evidence-grade discipline: extracted fields default to E1 (or E2 where the transcript shows the accountable owner confirming) — never higher without an artifact; the UI cannot raise E-grade without an evidence link.
5. THE test: a full fixture transcript, confirmed unchanged, produces a byte-identical scoring run to the same data entered manually through Path A.

## Exit criteria

- Identical-scores test passes (the PRD acceptance criterion as an executable test).
- Unconfirmed extractions provably never reach the engine.
- Field-level provenance persisted (transcript + span + confidence + acceptance).
- Full gate green; CI green.
