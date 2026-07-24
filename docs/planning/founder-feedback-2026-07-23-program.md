# Founder-feedback remediation program — 2026-07-23

The execution manifest for the 27-item founder review of 2026-07-23. This is the single entry
point: read this, then each ticket. Tickets are `docs/tickets/GRS-nnnn-*.md`; cross-cutting
decisions are `docs/adr/ADR-00nn-*.md`. One ticket = one branch = one PR.

## Standing rules (every ticket)

- **No `--no-verify`.** Pre-commit hooks (ruff, format, schema-validate, secret-scan) never
  bypassed.
- **Merge gate (CI is billing-halted):** `uv run pytest` + `uv run pyright` + `bunx tsc
  --noEmit` + ESLint + the **per-file** vitest loop (`bunx vitest run <file>` — never a bare
  `bunx vitest run`, which silently runs one file).
- **Golden master byte-identical.** No ticket in this program changes ATLAS scoring. Any change
  that would is a new ADR + Methodology version first (non-negotiable #2).
- **Fail loud, repository-layer persistence, owner-scoping tested, contracts regenerate schemas
  + TS mirror.** Standing non-negotiables from CLAUDE.md.
- Write all new copy in the STYLE-VOICE register defined by GRS-0174.

## Inputs that are NOT in this repo (deliberate — do not look for them in git)

| Input | Location | Needed by |
|---|---|---|
| LSEG analyst dataset (1,754 rows) + contributor map | OneDrive `Business/Advisory/GTM Data/lseg-influencer-pull-2026-07-23/` | GRS-0193, GRS-0194 |
| 7 Powers extraction memo (667 lines) | OneDrive `Strategy/7Powers-Adaptation-Working/7powers-math-extraction-2026-07-23.md` | GRS-0180 |
| 7 Powers source PDF | `Downloads/7Powers.pdf` | GRS-0180 (verification) |
| Benzinga catalog, Exchange Supplier List, Bank list, Barclays workbook, OpenBB strategy | OneDrive Advisory / Downloads | GRS-0191, GRS-0193 |

A worker executing this program needs **git plus access to this machine's OneDrive and
Downloads**. PII and partner material are never committed (ESTATE-RECONCILIATION policy). The
7 Powers PDF is used under Hamilton Helmer's personal permission (ADR-0046) and is likewise
never committed.

## Waves and order

Execute in wave order. Within a wave, tickets are independent unless a dependency is noted.

### Wave 1 — Demo credibility (start here)
GRS-0174 (voice/style guide + copy sweep) lands **first** — later frontend tickets write in its
register. Then, independently mergeable:
- GRS-0173 domain SSO · GRS-0175 guide/primer rewrite (after 0174) · GRS-0176 vertical Kanban ·
  GRS-0177 portfolio dedupe/clarity · GRS-0178 new-assessment form · GRS-0179 scoring-explained
  doc (cross-refs 0180) · GRS-0180 7 Powers adaptation doc → GRS-0201 wizard embedding +
  Helmer review packet · GRS-0181 wizard pagination · GRS-0182 Summary repair · GRS-0183 remove
  ConnectTrade · GRS-0184 scenario workspace v2 · GRS-0185 Brandfetch segment scoping ·
  GRS-0186 global nav + deliverables index · GRS-0187 consulting commissions on earnings.

### Wave 2 — Governance
GRS-0188 (founder review gate; ADR-0041). Retires dual-rating/committee/calibration to dormant,
gates production release on john@bruntsfield.capital. GRS-0182's governance-panel fix ships
first as the interim; GRS-0188 then removes the panels. GRS-0199 depends on this.

### Wave 3 — Reports
GRS-0189 (story-first deliverables + technical appendix + pptx variant; ADR-0042).

### Wave 4 — Academy & Workbench
GRS-0190 rich lesson renderer (prerequisite) → GRS-0191 content depth (per-course PRs, uses the
OneDrive sources) → GRS-0192 freshness watcher. GRS-0196 practice arena v2. GRS-0199 bench
honesty (Wave-4 honesty part; Wave-5 wiring part depends on GRS-0193).

### Wave 5 — GTM data & integrations
GRS-0200 (DONE — dataset pulled). GRS-0193 contact registry import (behind the EntityRegistry
port) → GRS-0194 LSEG influencer-map generator. GRS-0195 agentic-GTM spike (docs-only). GRS-0197
Gmail/Calendar. GRS-0198 pipeline linkage surfaces.

## ADRs

| ADR | Decision |
|---|---|
| ADR-0041 | Founder review gate; peer governance retired to dormant |
| ADR-0042 | Report narrative architecture (story first, technical appendix, pptx) |
| ADR-0043 | Academy content architecture (in-house rich content, no external LMS) |
| ADR-0044 | Workspace domain SSO auto-provisioning (amends ADR-0024) |
| ADR-0045 | GTM target & contact registry (extends ADR-0027) |
| ADR-0046 | 7 Powers mathematics embedding under Helmer's permission grant (Helmer reviews) |

## Migration-number caution

GRS-0184, 0188, 0193, 0197, and 0198 each add an Alembic migration. The head at authoring time
is `0031_drill_card_prompt_answer`. Whichever lands first takes `0032`; the rest rebase onto the
new head. Do not pin `0032` in more than one PR — the tickets say "next free number after
rebasing" for this reason.

## Item → ticket map

1→0173 · 2→0174 · 3→0176 · 4→0177 · 5→0178 · 6→0179/0175 · 7→0180/0201/ADR-0046 · 8→0179 ·
9→0181 · 10→0182 · 11→0183 · 12→0184 · 13→0185 · 14→0186 · 15→0186/0197 ·
16→0200/0193/0194/0195 · 17→ADR-0042/0189 · 18→0197 · 19→0198 · 20→ADR-0043/0190/0191/0192 ·
21→ADR-0043 · 22→0196 · 23→ADR-0041 · 24→ADR-0041/0188 · 25→0199 · 26→0187 · 27→0175
