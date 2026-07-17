# GRS-0126 — OpenBB course (dedicated research agent — the biggest)

**Status:** Shipped
**Loop:** Part 2 — Bruntsfield Academy / Workbench (one program)
**Depends on:** ADR-0028 (Bruntsfield Academy / Workbench), GRS-0121 (content CMS), GRS-0123 (product-course framework)

## Delivered

A deep, use-case-aligned **OpenBB product course** (`workbench/content/openbb_course.py`, slug
`product-openbb`), authored through the GRS-0121 CMS on the GRS-0123 template — 5 modules, ~19
lessons. Built from real research: five parallel research agents over OpenBB's site, docs, blog, and
founder **Didier Rodrigues Lopes**'s writing, **plus a hands-on run of the open-source Platform**
(`pip install openbb`; `obb.equity.price.historical('AAPL', provider='yfinance')` returned live data;
17 providers, the full equity/crypto/economy/fixedincome router surface). Modules: the template spine
(relevance / white-label / sell-motion / **live commission carrot**); **What OpenBB actually is**
(the Terminal→Platform→Workspace pivot, Workspace, the Open Data Platform, Copilot+MCP); **Use cases
you can sell for** (buy-side research, portfolio/risk, branded client reporting, governed AI over the
firm's own data, quant/consolidation, honest vs-Bloomberg) each tied to an assessment finding + buyer
segment; **The white-label & build angle** (AGPLv3→commercial license, Workspace branding, the
custom-backend `widgets.json` deliverable, enterprise/Snowflake, the real dev experience); and
**Conviction & founder thesis** (Gamestonk origin, the governed-AI bet, objection handling). The
commission section resolves **live** from the Earnings v7 schedule (not hardcoded). Seeded
idempotently; completing it counts toward the `product:openbb` certification (GRS-0127). Only public
product facts — no partner-confidential data; versioned so the founder can deepen it. Backend content
only — no contract/schema/frontend change. Golden master untouched.

## Why

OpenBB is a **signed** product, a commission earner, and the **largest and most technical** of the
three — especially relevant to wealth managers. It warrants a **dedicated** research agent, not the
lighter treatment of Benzinga/Brandfetch. The founder's brief: "leave no stone uncovered." No content
exists yet; this is a **VM-research ticket** built through the CMS.

## What to build

- The VM **spawns a dedicated research agent** over **OpenBB docs, Didier Lopez's blogs, the OpenBB blog
  + YouTube** to gather comprehensive source material.
- Build our **own structured course catalog** (framed by GRS-0123's template) covering: **set up your
  own OpenBB account**, **build your own dashboards**, the **use cases**, **how to introduce/sell +
  white-label**, **likely pricing**, and **likely earnings** (especially to wealth managers). Link out
  to OpenBB YouTube/blogs but build our own catalog rather than deferring to theirs.
- Author the course **through GRS-0121's CMS**; any **AI-authored lesson drafts stay approval-gated**
  (ADR-0009).

## Acceptance / verification

- An OpenBB course exists in the CMS covering all six briefed areas (account setup, dashboards, use
  cases, sell/white-label, pricing, earnings) plus the GRS-0123 spine, sourced from the researched
  material.
- Out-links to OpenBB YouTube/blogs are present alongside our own structured lessons.
- AI-drafted lessons are published only after passing the approval gate (ADR-0009); commission/earnings
  resolve from Earnings v7.

## Not in scope

- The product-course template (GRS-0123) and the CMS (GRS-0121).
- Benzinga (GRS-0124) and Brandfetch (GRS-0125) courses.
