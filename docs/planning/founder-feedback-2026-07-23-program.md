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

## Program inputs — in the repo under `data/`

By founder decision (2026-07-23), the program's data inputs are committed to this private repo
so the workbench VM can execute with **only git access** (no OneDrive/Downloads). See
`data/README.md` for the full layout and provenance.

| Input | In-repo path | Needed by |
|---|---|---|
| 7 Powers mathematics extraction memo | `data/reference/7powers-math-extraction.md` | GRS-0180 → GRS-0201 |
| LSEG analyst dataset (1,754 rows) + contributor map | `data/gtm/lseg/` | GRS-0193, GRS-0194 |
| Exchange Supplier List, Bank list, Barclays workbook/brief | `data/gtm/sources/` | GRS-0193 |
| Benzinga catalog, OpenBB strategy | `data/gtm/sources/` | GRS-0191 |

**Not committed:** the raw `7Powers.pdf` (Helmer's grant covers adapting the *mathematics* — the
extraction memo — not redistributing his copyrighted file). The `data/gtm/` files carry named
business-contact PII; this repo must stay private. See `data/README.md` for the PII notice.

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

## Second review — 2026-07-26

The founder reviewed staging on 2026-07-26 and found much of the 23/07 list still open, plus
fourteen new points. The honest tally at that date was 9 of 27 items closed. Three things this
program had reported as shipped were not visible to the founder at all, because the code existed
and the environment did not: the staging duplicates were never cleaned, the GTM registry was
imported into a throwaway local database rather than staging, and Google sign-in was never
provisioned. **"Shipped" in this program now means the founder can see it working on staging.**

New tickets from that review:

| Review item | Ticket |
|---|---|
| 1, 2, 3 — all copy still reads as AI | GRS-0205 (supersedes the sweep half of GRS-0174) |
| 4 — Rive CLI for wizard and pipeline | GRS-0206 (ADR-0049) |
| 5 — email, CRM, AI prospecting platform | GRS-0207 (ADR-0048; reopens GRS-0195) |
| 6 — demo account + founder admin acting-as | GRS-0208 |
| 7 — Operating Model dropdown still misaligned | GRS-0209 (bug, follows GRS-0178) |
| 8 — smart search knows too few firms | GRS-0210 |
| 9, 10 — deliverable is terrible; PDF + interactive, Acquired-style | GRS-0211 (extends GRS-0189) |
| 11 — Customer Proposition for exchanges | GRS-0212 |
| 12 — scenario tool must be interactive, with a narrative assistant | GRS-0213 (absorbs GRS-0184) |
| 13 — free vs engaged tiers, downstream reports | GRS-0214 |
| 14 — courses are paragraphs, not courses | GRS-0215 (replaces the content half of GRS-0191) |

Also from that review, handled without a ticket:

- **Staging cleanup (Grassmarket item 4): DONE 2026-07-29.** Four duplicate demo/sandbox records
  removed from staging; the advisor portfolio went from 8 rows to 4. Required ADR-0047, because
  `delete_assessment` refused any record carrying a scoring run and every duplicate was finalised.
  Two production strays remain on that account and need a founder decision, because ADR-0047 keeps
  production records undeletable: `Revolut` (draft, 0% coverage) and `Meridian Securities`
  (finalised, 2% coverage).
- **Permission layer (Grassmarket item 1).** `.claude/settings.json` now allowlists the commands
  the workbench needs. This does **not** fix `git push origin main` or `gh pr merge`: those are
  refused by the harness safety classifier, not by the permission allowlist, which already
  permitted `Bash(git *)`. See `merge-and-deploy-blocked-by-classifier`.

### Wave 6 — the 2026-07-26 review

Order, by the founder's stated priority plus what unblocks what:

1. GRS-0188 + ADR-0041 (remove peer rating, committee, calibration; route approvals to the
   founder). Items 23 and 24, still open from 23/07, and the founder's own first pick.
2. GRS-0215 courses. The item raised twice and the one they are angriest about.
3. GRS-0211 client deliverable. The only artefact a client ever sees.
4. GRS-0213 scenarios.
5. GRS-0208 demo tenancy, GRS-0205 copy, GRS-0209 dropdown, GRS-0210 search: the four that make a
   walkthrough survivable.
6. GRS-0207 outreach platform, GRS-0212 exchange C, GRS-0214 tiers, GRS-0206 Rive.

## Item → ticket map

1→0173 · 2→0174 · 3→0176 · 4→0177 · 5→0178 · 6→0179/0175 · 7→0180/0201/ADR-0046 · 8→0179 ·
9→0181 · 10→0182 · 11→0183 · 12→0184 · 13→0185 · 14→0186 · 15→0186/0197 ·
16→0200/0193/0194/0195 · 17→ADR-0042/0189 · 18→0197 · 19→0198 · 20→ADR-0043/0190/0191/0192 ·
21→ADR-0043 · 22→0196 · 23→ADR-0041 · 24→ADR-0041/0188 · 25→0199 · 26→0187 · 27→0175
