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

## 1. Decisions that gate remaining builds — **RESOLVED 2026-07-16**

| # | Decision | Resolution | Now planned as |
|---|---|---|---|
| D-4 | Commission Schedule v7 as earnings config source | ✅ **Confirmed.** Encode the two-stream v7 model; model independent-consultant contracts (Byoung = first hire) | ADR-0026 · GRS-0075/0076 |
| D-5 | Harvest ASX/NSI packs as deliverable templates | ✅ **Approved** — as *exchange* templates; elevated to a **profiles program of work** (wealth, exchange, …) | ADR-0025 · GRS-0078 |
| D-1 | C-index Phase-E 10-module set | ✅ **Phase-E 10 ratified** | ADR-0023 Accepted |
| D-2 | Staged C entry | ✅ **Staged** (v1.3 report-alongside → v1.4 into V) | ADR-0023 · v1.3 normative |
| D-3 | Exchange profile vs C-index first | ✅ **Exchange profile ahead / in parallel** | ADR-0025 |
| D-6 | Power Primers (unwritten) | ✅ Proceed — content dependency; scaffold in the quiz bank | founder content track |
| D-7 | θ_C re-elicitation session | ✅ **Share** the v1 annual re-elicitation | GRS-0086 (Stage 2) |

## 2. Content / data only John can provide (not decisions — inputs)

Per the standing rule, **no client data is committed to this repo** — these are ingested as
config/seed through the app's scoped storage, or read reference-only. I need them made available:

| # | Input | Needed for | Status |
|---|---|---|---|
| I-1 | **Commission Schedule v7** template + `Resources/` contracts (OneDrive) | Earnings v7 config | ✅ **provided** (path given; read for ADR-0026/GRS-0075) |
| I-2 | **ASX / NSI deliverable packs** (`Engagements/Active`) | Exchange deliverable templates | ✅ **provided** |
| I-3 | **Brokerage-App-Reviews corpus** — 16 apps, 7 scored, 93 widgets | C-index benchmark seed | ✅ **provided** |
| I-4 | **θ / λ / δ weight elicitation** (4–8 experts) | Client-usable coefficients | ⚙️ **proceed on the existing elicited set** as launch default; a real panel = post-launch validation |

## 3. Ops / platform items for John

| # | Item | Impact | Status |
|---|---|---|---|
| O1 (3.01) | GitHub Actions / billing | CI + frontend auto-deploy | ✅ **completed** (restored) |
| O2 (3.02) | Login / password | Not change-password — **Google OAuth sign-in** (all consultants have Gmail); this *is* the public-site → app login→redirect mechanism | 🔁 **superseded** → ADR-0024 · GRS-0073/0074 |
| O3 (3.03) | Custom domain `advisors.bruntsfieldcapital.com` | Prod on `*.up.railway.app` | ⏳ **do last, pre-release** |
| O4 (3.04) | `nixpacks.toml` uv pin (manual `NIXPACKS_UV_VERSION`) | API build fragility | ⚙️ **proceed** — just fix it |

## Notes

- Everything shippable **without** the above is done — the advisor workflow is complete end-to-end
  (pipeline → assessment → dual-rating + committee → finalise → deliverable → earnings) and every
  button works. The gated items above are the only remaining scope.
- O2 and O4 I can build without a decision if you want them — say the word.
