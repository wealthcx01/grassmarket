# GRS-0085 — C deliverable sections

**Status:** Planned
**Loop:** Loop 7 — C-index (Customer Proposition)
**Depends on:** ADR-0023 (Accepted), ATLAS-Methodology-v1.3

## Why

C only earns its keep when it reaches the client deliverable. With the index computed (GRS-0082),
captured (GRS-0083) and benchmarked (GRS-0084), the deliverable builder needs sections that present
the customer proposition legibly: where the subject is strong/weak across the 10 modules, and how
its widget coverage differentiates against peers once rarity is accounted for (a Rare widget the
subject has and peers lack is a differentiation asset; a Common one it lacks is a gap). This ticket
adds those two sections to the deliverable builder.

## What to build

Files:
- `src/grassmarket/deliverables/` — two new deliverable sections:
  1. **Proposition heatmap** — the 10 C modules × maturity, subject vs. peer benchmark set, driven
     by the C result and the GRS-0084 benchmark rows.
  2. **Differentiation-vs-rarity map** — widgets plotted by rarity (Common/Uncommon/Rare) against
     present/absent, highlighting Rare-present (differentiators) and Common-absent (table-stakes gaps).
- Chart/template code following the existing deliverable section pattern (python-docx templates +
  charts), and a methods-appendix note describing the C section provenance.

Refs / reuse:
- The existing deliverable builder section + chart machinery (heatmap/matrix patterns already used
  for B/P/L diagnostics).
- The C `CustomerResult` / `c_index` from GRS-0082 and the benchmark rows from GRS-0084.
- The AI-drafted → consultant-approved gating already applied to deliverable first drafts (nothing
  AI-generated reaches a client without sign-off).

New:
- The two section templates and their chart renderers; rarity-aware differentiation plotting.

## Acceptance / verification

- Both sections render into a generated deliverable for an assessment that has a C result and peer
  benchmarks; missing C data omits the sections cleanly rather than emitting blanks or zeros.
- The heatmap reflects the reported C values (Stage 1: reported alongside V, not a four-index V).
- The differentiation map correctly classifies Rare-present vs. Common-absent widgets.
- Deliverable drafts remain approval-gated; methods appendix documents the C sections.
- Golden master unchanged.

## Not in scope

- The engine/contract changes — GRS-0082; benchmark ingestion — GRS-0084 (prerequisites).
- Folding C into the headline V — GRS-0086.
