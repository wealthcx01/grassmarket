# Pending — needs John's review or input

_Living tracker of everything blocked on the founder. Last updated 2026-07-16 after Track A shipped
(GRS-0066–0073, PRs #75–#82, all on `main`). Decisions also live in `NEXT-STEPS-2026-07.md` §4; this
adds the data inputs and the ops items, and tracks status._

## 0. Review the deploy

Track A is live for review. **Backend auto-deployed** from `main` (Railway GitHub integration).
**Frontend deployed manually** (the GitHub-Actions auto-deploy is down — see Ops item O1).

- Advisor portal: https://grassmarket-web-production.up.railway.app
- API: https://grassmarket-api-production.up.railway.app (`/health` → 200)

What's new to look at (all in the wizard + portfolio):
- **Your Brokerages** portfolio home (segment · last score · status) — the assessments page.
- Wizard **Step 1**: structured business profile (country/segment/asset classes/regions/licensing).
- **Strategic Powers** step: Helmer definitions, per-power brokerage examples, benefit/barrier evidence.
- **Summary** step: diagnostic visuals — maturity radar, B→P→L→V waterfall, weighted module table,
  scenario impact bars.

## 1. Decisions that gate remaining builds

| # | Decision | Unblocks | Recommendation | Status |
|---|---|---|---|---|
| D-4 | Confirm **Commission Schedule v7** as the earnings config source | GRS-0067 earnings build | Confirm (placeholder is known-wrong) | ⏳ awaiting |
| D-5 | Approve harvesting **ASX/NSI pack structure** (anonymised) as deliverable templates | GRS-0072/0073 house deliverables | Approve | ⏳ awaiting |
| D-1 | Ratify the **C-index Phase-E 10-module set** (vs 6-module synthesis) | ADR-0023 → v1.3 normative → Loop 7 | Phase-E 10 | ⏳ awaiting |
| D-2 | Confirm **staged C entry** (v1.3 report-alongside → v1.4 into V) vs straight to a 4th θ | ADR-0023 | Staged | ⏳ awaiting |
| D-3 | Sequence: **exchange operating-model profile** vs C-index first | Loop 7 / profile ADR scope | Exchange profile first or in parallel | ⏳ awaiting |
| D-6 | Commission the **Power Primers** (Foundation Package strand 1, unwritten) | GRS-0024 Power Drills quiz depth | Commission | ⏳ awaiting |
| D-7 | Share the **θ_C re-elicitation** session with the v1 annual re-elicitation? | v1.4 (θ_C) | Share | ⏳ awaiting |

## 2. Content / data only John can provide (not decisions — inputs)

Per the standing rule, **no client data is committed to this repo** — these are ingested as
config/seed through the app's scoped storage, or read reference-only. I need them made available:

| # | Input | Needed for | Status |
|---|---|---|---|
| I-1 | **Commission Schedule v7** template (OneDrive) | Build the earnings v7 config (after D-4) | ⏳ awaiting |
| I-2 | **ASX / NSI deliverable packs** (OneDrive) | House deliverable templates (after D-5) | ⏳ awaiting |
| I-3 | **Brokerage-App-Reviews corpus** — 16 apps, 7 scored, 93 widgets (OneDrive) | C-index benchmark seed (Loop 7, after D-1/D-2) | ⏳ awaiting |
| I-4 | **θ / λ / δ weight elicitation** (4–8 experts) | Client-usable coefficients — the **launch bottleneck** (GRS-0033) | ⏳ awaiting |

## 3. Ops / platform items for John

| # | Item | Impact | Status |
|---|---|---|---|
| O1 | **GitHub Actions halted account-wide (billing)** since 2026-07-15 | CI can't run; frontend auto-deploy (rides on Actions) is down — frontend now needs manual `railway up`. Merges are on **local green** by your authorisation. | 🔴 needs billing fix |
| O2 | **No change-password endpoint** exists | Needed for launch + to rotate the password that was echoed to chat at cutover | ⏳ open (build candidate) |
| O3 | Custom domain `advisors.bruntsfieldcapital.com` not pointed | Prod runs on the `*.up.railway.app` URL | ⏳ awaiting DNS |
| O4 | `nixpacks.toml` uv pin still a manual service var (`NIXPACKS_UV_VERSION`) | Build fragility on the API service | ⏳ open (build candidate) |

## Notes

- Everything shippable **without** the above is done — the advisor workflow is complete end-to-end
  (pipeline → assessment → dual-rating + committee → finalise → deliverable → earnings) and every
  button works. The gated items above are the only remaining scope.
- O2 and O4 I can build without a decision if you want them — say the word.
