# Execution plan — Part 2: Advisor Studio UI/UX & product review

**For the execution VM.** A section-by-section founder review of the deployed Advisor Studio, turned into
**48 tickets (GRS-0087–0134)** + **4 ADRs**. This is the entry point: read the ADR(s) for a program, then the
tickets, in order. (Part 1 — OAuth · Earnings v7 · Profiles · C-index, GRS-0073–0086 — is already on `main`;
`PART1-oauth-earnings-profiles-cindex.md`.)

The full narrative review (what the founder said, per section, with the reasoning) is preserved in the plan
file the tickets were distilled from; this index is the buildable summary.

## Sections → tickets

| § | Area | Tickets | Program / shape |
|---|---|---|---|
| 0 | Session sign-out bug | GRS-0120 | fold into ADR-0024 (auth) — **quick win, do first** |
| 1 | Home / Dashboard | GRS-0087–0091 | discrete UI tickets (0090 rename → ADR-0030) |
| 2 | Primer / `/guide` depth | GRS-0092–0097 | discrete content tickets (0097 labels → ADR-0030) |
| 3 | Portfolio + Assessment Wizard | GRS-0098–0110 | **Phase A now** / Phase B flagged (0100, 0101, 0109) |
| 4 | Pipeline / GTM | GRS-0111–0115 | **one program** → ADR-0027 |
| 5 | Deliverables / Engagements | GRS-0116–0119 | 0117 demo now, 0119 sandbox follow-up → ADR-0029 |
| 6 | Workbench / Academy | GRS-0121–0132 | **one program** → ADR-0028 |
| 7 | My Earnings | GRS-0133 | small / near-term |
| 8 | Guide navigation | GRS-0134 | sequence **last** |

## ADRs authored with this plan

| ADR | Decision |
|---|---|
| **ADR-0027** | Pipeline / GTM engine — EliteVault-grade CRM + Gmail/Calendar + LSEG influencer maps + AI/MCP GTM + 150-bank seed, as one program. |
| **ADR-0028** | Bruntsfield Academy / Workbench — content CMS, Sales Egoist core, product courses (Benzinga/Brandfetch/OpenBB), certification, ops playbook, practice/calibration, cert-evidence auto-link; admin oversight deferred to Holy Corner. |
| **ADR-0029** | Demo & sandbox records — a watermarked demo (Revolut) and a sandbox self-approve mode let testers see deliverables without weakening the dual-rating/committee gate. |
| **ADR-0030** | ATLAS → Platform Power rename (user/client-facing copy only) + refine the P/L lens labels; engine identifiers + golden master unchanged. |

## Suggested order for the VM

1. **GRS-0120** session fix — unblocks all testing (30-min token, no refresh).
2. **§1 Home + §2 Primer + the rename** (GRS-0087–0097, ADR-0030) — the first-impression surface.
3. **§5 Deliverables incl. the Revolut demo** (GRS-0116–0118, ADR-0029) — makes solo testing show the payoff.
4. **§3 Wizard Phase A** (rigor/depth) — the strongest single critique of the review.
5. **ADR-0027 — Pipeline / GTM program** (GRS-0111–0115).
6. **ADR-0028 — Academy program** (GRS-0121–0132); the three product courses are the biggest research lift,
   OpenBB last.
7. **§7 earnings gamify** (GRS-0133) → **§8 guide nav** (GRS-0134, last).
8. **Phase-B flags** (GRS-0100, 0101, 0109, 0119) — scope as their own follow-ups after the above.

## Hard invariants (do not break)

- **Golden master** `V = 0.478565` byte-identical (`tests/test_atlas_engine_golden_master.py`). The rename,
  the profiles work, and every Academy/Pipeline change are copy / UI / data — never scoring math.
- **Fail-loud / ADR-0001** (registry key uniqueness, no silent defaults); **currency-free scoring / ADR-0002**
  (earnings gamification stays behind the Money boundary); **AI-approval gating / ADR-0009** (lesson drafts,
  demo-record generation, video/widget AI, GTM enrichment/outreach).
- **No client/partner data committed** — the Revolut demo, EliteVault, the OneDrive contracts/decks, the
  150-bank list, and product docs are reference-only; ingestion is config/seed through scoped storage,
  watermarked where it is a demo.
- **Owner-scoping** (non-negotiable #9) preserved throughout.

## Overlaps with already-planned/built work (so the VM doesn't rebuild)

- **§3 broaden-scope** = the profiles program (ADR-0025 / GRS-0077–0079); **widgets + C-index** = GRS-0080–
  0085; **meeting upload** = Path B (GRS-0029/0030). The genuinely new §3 asks: entity/company linking (0100),
  screen-recording → AI-video → widget auto-population (0109), merging the two infra pages (0106), the
  completeness metric (0099), the evidence-rigor uplift (0107).
- **§6**: committee / rating-requests / dual-rating **already link to assessments and work** — GRS-0131
  targets the real gap (cert evidence isn't auto-computed from participation). The **admin role already
  exists** (`Role.ADMIN`) — only HC oversight dashboards are deferred (GRS-0132). The **bench already
  aggregates** next-actions (GRS-0128 extends it). The **AI-approval gate already exists** (quiz flow, reused
  for lessons in GRS-0121).

## Needs a human / operator (not blocking the buildable parts)

- **GRS-0112 / ADR-0027:** operator provisions Google Gmail + Calendar OAuth scopes (extends ADR-0024).
- **GRS-0114/0115:** the `bcap-lseg` MCP connector must be reachable in the build environment.
- **GRS-0124/0125/0126:** VM research agents need web access to the product docs / blogs / YouTube.
- **GRS-0117:** the Revolut briefing (reference-only) as demo source content.
