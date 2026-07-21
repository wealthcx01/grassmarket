# Product confidence deep-dive on a fresh staging environment (2026-07-20)

Prepared for founder review. You asked me to (1) retry the Railway staging environment, (2) deep-dive
the product and be confident of it — pipeline, assessment wizard, deliverables — and (3) explain why the
Workbench had no accessible course content. This is what I found. The end-to-end brokerage run
(pipeline → earnings) is teed up and waiting on your go.

---

## 0. Staging environment — up, isolated, and safe

- New Railway environment **`staging`** (duplicate of production). URLs:
  - Web: https://grassmarket-web-staging.up.railway.app
  - API: https://grassmarket-api-staging.up.railway.app
- **Two cross-environment leaks found and fixed before any test touched data** (this is exactly the kind
  of thing that makes a naive "duplicate prod" dangerous):
  1. Staging web's `NEXT_PUBLIC_API_BASE_URL` pointed at the **production** API — left alone, my testing
     would have written to prod. Repointed to the staging API (needs a rebuild; Next bakes it in).
  2. Staging API's `GM_FRONTEND_ORIGIN` (CORS) pointed at the production web origin. Repointed to staging.
- Verified isolation empirically: the app's captured API calls go **only** to `…-api-staging`, never prod.
- Bootstrapped a fresh DB with `scripts/seed_dev.py` → login `advisor@bruntsfieldcapital.com` /
  `grassmarket-demo`, an admin, **the Academy catalog**, and a demo prospect→assessment→engagement chain.

*Why this matters:* the crash last time was on this step. It's now a repeatable, isolated testbed —
change freely, throw it away, never risk production.

---

## 1. Why the Workbench was empty — root-caused and proven

**The course content is not missing — it was never seeded into the deployed database.** ~2,171 lines of
authored courses exist in code (`src/grassmarket/workbench/content/`): Sales Egoist (8 lessons), the Sales
Operations Playbook (4), and full product courses for OpenBB (22), Benzinga (18), Brandfetch (19).

The only thing that publishes them is `seed_academy_content()`, and its **only caller is the dev-only
`scripts/seed_dev.py`**, which targets a local SQLite file. The production boot path (`web/app.py`) runs
**only** migrations; migration `0026` creates the empty `course` tables and inserts **zero rows**. So a
fresh Railway DB → empty catalogue → the Academy page correctly renders *"No courses published yet."* It
"works locally" only because someone once ran the seed against `local.db`.

**Proven both directions:** after I ran the seed against the staging DB, the Academy immediately showed
the full, rich catalogue (screenshots in `scratch/stage/03-academy.png`). Nothing needs re-authoring.

**The fix (small, ready to build on your go):** an idempotent `scripts/seed_academy.py` (ensure an admin
principal → `seed_academy_content`) wired into the Railway **release phase**, kept separate from the demo
prospect/assessment data. Then run it once against production. One ticket.

---

## 2. The three core flows — do they work, and are they clunky?

| Flow | Works? | Verdict |
|---|---|---|
| **Pipeline** | ✅ | Kanban stages, weighted "expected wins" forecast, time-in-stage/stale flags. Renders clean, no errors. |
| **Assessment wizard** | ✅ | 7 legible steps; a clear live-score gate ("rate 7 Powers + 1 metric + 1 core-module subcomponent"); coverage counter; a "Preview in sandbox" escape hatch to finalise solo. |
| **Deliverables** | ✅ | Generated Executive Summary + Platform Power Report drafts; **Download returns a real, valid 59 KB `.docx`** with structured content (V score, triad, module risks, DRAFT watermark). |

**So the product genuinely works** — no console errors, no API 4xx/5xx, no backend flakes on any flow.

**Where the "clunky / hard to use" comes from — and it's real:** it is *not* the content or the design
system. The microcopy is excellent and the Business Metrics step is a clean set of well-labelled cards.
The friction is concentrated in the **dense rating steps**, and it's an interaction-model problem:

- **Infrastructure Deep Dive is a single ~5,100px-tall page** — 51 subcomponents across 9 modules, each a
  native dropdown (`— unrated —`) + a *Guidance* button, stacked vertically with no way to collapse a
  finished module.
- **Customer Proposition** repeats the pattern for a 93-widget checklist; **Powers** is 7 cards, each with
  benefit + barrier + two evidence grades.
- To complete one assessment you make **hundreds of individual dropdown selections down a very long scroll**,
  with **no bulk-fill, no "N/A this whole module", no import**, and the **live-score rail sits only at the
  top** so you lose sight of the score and the checklist as you scroll.

That density — lots of mechanical clicking with the score out of view — is what makes it *feel* like work,
even though every field is well-explained. It's fixable UX (sticky score rail + per-module
collapse/progress + a faster rating control + bulk "N/A"), not a rebuild.

---

## 3. My confidence verdict

**The product is real and it works** — pipeline, a rich and methodologically-serious assessment wizard,
and genuine downloadable deliverables, all clean on a fresh stack. The two things that made it *feel*
broken/clunky to you are both explained and both fixable:
1. **Empty Workbench** = a one-line deploy gap (never ran the seed in prod), not missing content. ← ship the seed step
2. **Wizard clunk** = the dense rating steps' interaction model, not the content. ← a focused UX pass

Neither is a methodology or correctness problem; the engine, scoring, and document generation are sound.

---

## 4. Next: the brokerage end-to-end run (ready, awaiting go)

Everything is staged to run Revolut/HL/WeBull through **pipeline → assessment → deliverable → earnings**:
- The staging testbed is live and isolated; the browser-driving harness is repointed to it
  (`scratch/stage_drive.mjs`).
- The brokerage reviews *are* the C-index dataset — the `_COMPLETED_Claude.md` checklists map directly to
  the 93-widget Customer Proposition, and their strengths/weaknesses feed the 7 Powers and business metrics.
- I'll add each as a pipeline prospect, populate a full assessment from the review data, finalise (sandbox),
  generate the deliverable, and follow it through to earnings — documenting every point of friction.

**On your go, I'll run it.**
