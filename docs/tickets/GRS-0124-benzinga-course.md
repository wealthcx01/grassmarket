# GRS-0124 — Benzinga course (VM research)

**Status:** Shipped
**Loop:** Part 2 — Bruntsfield Academy / Workbench (one program)

## Delivered

A deep, use-case-aligned **Benzinga product course** (`workbench/content/benzinga_course.py`, slug
`product-benzinga`) on the GRS-0123 template — 5 modules, ~19 lessons, from three parallel research
agents over Benzinga's public product/API pages, docs, partner press, and reviews. Modules: the
template spine (live commission); **What Benzinga actually is** (the media + data-licensing arms, the
news feeds incl. the signature WIIM, the analyst-ratings/options-signals data, the calendar +
reference suite + delivery); **Use cases you can sell for** (powering a retail brokerage, wealth/
advisor platforms, algo/quant signals, fintech engagement) tied to buyer segments + assessment
findings; **The reseller & commercial angle** (redistribution is the core model; licensing/attribution
scoped per-contract; the honest competitive frame — not a terminal/fundamentals/tick source); and
**Conviction & the company** (Raznick, Detroit ~2009–2010, "level the playing field", Beringer-backed).

**Commission:** the advisor's **15% share** (Benzinga pays the Bruntsfield reseller 30% over up to 36
months; Bruntsfield shares half) was added to `commissions.yaml` (ADR-0026 config) and the course's
commission section resolves it **live**. Only public facts — the confidential reseller agreement is
**not** committed; company scale/client claims are attributed; redistribution/attribution terms flagged
to confirm per deal. Backend content only — no contract/schema/frontend change. Golden master untouched.
**Depends on:** ADR-0028 (Bruntsfield Academy / Workbench), GRS-0121 (content CMS), GRS-0123 (product-course framework)

## Why

Benzinga is a **signed** product and one of Bruntsfield's commission earners, so advisers need a real
course to learn how to introduce and white-label it. No content exists yet; this is a **VM-research
ticket** — the VM builds our own catalog from Benzinga's own public and developer material rather than
hand-waving, then authors it through the CMS.

## What to build

- The VM **spawns a research agent** over **Benzinga's public + developer docs / APIs** to gather the
  raw material for the course.
- Build our **own course catalog** framed by GRS-0123's template: relevance to retail broker / wealth
  manager / exchange, what white-labelling Benzinga looks like, the sell/introduction motion, and the
  commission the advisor earns (via Earnings v7).
- Author the course **through GRS-0121's CMS**; any **AI-authored lesson drafts stay approval-gated**
  (ADR-0009) before publication.

## Acceptance / verification

- A Benzinga course exists in the CMS with all GRS-0123 sections filled from researched Benzinga
  material (not placeholder text).
- AI-drafted lessons are published only after passing the approval gate (ADR-0009).
- The commission section resolves from Earnings v7 rates, consistent with GRS-0123.

## Not in scope

- The product-course template itself (GRS-0123) and the CMS (GRS-0121).
- Brandfetch (GRS-0125) and OpenBB (GRS-0126) courses.
