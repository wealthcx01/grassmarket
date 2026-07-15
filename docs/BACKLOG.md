# Grassmarket Backlog — index

All tickets exist as files in `docs/tickets/` (detail lives there, not here). GRS-0001–0015 shipped or in review; GRS-0016–0034 are `Status: Planned`. The builder updates a ticket's status and appends "What shipped" when its PR lands.

## Loop 4 — Deliverable Builder (remaining)

| Ticket | Title |
|---|---|
| GRS-0016 | Value-bridge rendering + Modernisation Roadmap |
| GRS-0017 | AI first-draft narratives (gated) |
| GRS-0018 | Complete the Diagnostic pack + charts |
| GRS-0019 | Deliverables frontend |

## Loop 5 — Workbench + Governance

| Ticket | Title |
|---|---|
| GRS-0020 | Dual-rating + consensus (governance data model) |
| GRS-0021 | Rating Committee queue |
| GRS-0022 | Calibration module |
| GRS-0023 | Certification ladder (enforced) |
| GRS-0024 | Learning content + Power Drills |
| GRS-0025 | Practice Arena v1 |
| GRS-0026 | Bench-time queue + performance view |
| GRS-0027 | Workbench frontend |

## Loop 6 — Earnings, Path B, Validation, Hardening, Launch

| Ticket | Title |
|---|---|
| GRS-0028 | My Earnings |
| GRS-0029 | Path B: ingestion + transcription |
| GRS-0030 | Path B: extraction → review → identical scoring |
| GRS-0031 | Prediction register + validation loop + benchmark ingestion |
| GRS-0032 | Hardening + compliance |
| GRS-0033 | Elicited coefficients: ingestion + client-usable flip — **launch bottleneck** |
| GRS-0034 | Launch readiness |

## Parallel founder/content track (dependencies, not tickets)

| Item | Blocks |
|---|---|
| Ratify registry criticals + subcomponents | GRS-0021 (honest Frontier gate), GRS-0033 |
| Rubric anchors (204, GRS-0008 content track) | wizard guidance depth; arena scoring |
| Calibration vignettes (3–5 cases) | GRS-0022, GRS-0025 |
| Certification coursework + exam content | GRS-0023, GRS-0024 |
| Commission rates decision | GRS-0028 (builds with placeholder config) |
| **Weight-elicitation panel (4–8 experts)** | **GRS-0033 → launch** |
| Transcription provider decision | GRS-0029 (defaults local Whisper) |

## Sequencing notes

- Loop 4 remainder (0016–0019) and GRS-0020 can interleave; 0020 has no Loop-4 dependency.
- GRS-0033 is the launch bottleneck; everything about it except the panel itself is buildable earlier — schedule the panel now.
- After GRS-0034: phase 2 = Holy Corner (Elite Vault adaptation, new ticket prefix), phase 3 = Viewforth. Both consume `bcap-contracts` as-is.
