# Mock-advisor cold stress test — synthesis & action plan (2026-07-19)

Five persona agents drove the **live production build** cold (no source access), each modelled on a
real customer across exchange / retail / wealth, via `scratch/agent_drive.mjs`. This consolidates
their findings, ranks by **severity × cross-persona consensus**, and records what was fixed vs. what
is surfaced for a founder/methodology decision.

Personas & confidence scores:
- **Priya Nair** — ex-Goldman, data-driven → **LSEG** (exchange) — **48/100**
- **Tom Fielding** — compliance-anxious IFA → **St. James's Place** (wealth) — **55/100**
- **Marcus Bell** — fintech BDR, breaks things → **Robinhood** (retail) — **68/100**
- **Elena Rossi** — quant, methodology-obsessed → **Deutsche Börse** (exchange) — **46/100**
- **James Okafor** — senior partner, credibility → **Brewin Dolphin** (wealth) — **68/100**

Mean confidence **≈ 57/100**. The consistent message: **the method is trusted, the fit and finish are
not.** Every persona independently praised the rigor (Helmer 7 Powers, E1–E4 evidence grades,
weaker-side-wins, honest uncertainty language, dual-rater governance, fail-loud pipeline, honestly-
labelled win-probability, AI-drafted labels). The confidence is dragged down by segment mis-fit,
unfinished surfaces, and — most seriously — a scoring-integrity inconsistency the quant found.

---

## Ranked findings (severity × consensus)

### TIER 1 — HIGH severity

**1. Uncertainty layer imputes ~50 for unassessed subcomponents → phantom module bands + a phantom
"likely constraint" that names a module nobody assessed.** (Elena, HIGH; verified in source.)
The deterministic engine correctly excludes Not Assessed (D9). But the Monte Carlo layer
(`atlas/montecarlo.py:285-298`) imputes a *uniform-over-four-levels* prior for every Not Assessed
subcomponent and includes it in each draw, manufacturing a ~49–52 `q_m` band for **zero-coverage**
modules. The frontend "likely constraint" callout (`LiveScorePanel.tsx:77-97`, `steps.tsx:831-833`)
picks the lowest-`p50` module with **no coverage check**, so at 14% coverage it confidently told the
advisor to "fix EMS Gateway" — the one system nobody had assessed. Bands are also too tight for the
coverage (LLN concentrates the imputed draws). **This contradicts ADR-0001's D9 rule and is not
ratified in the methodology docs — only in a code comment justified by ADR-0008 §3.**
→ **Split fix:** the model change is *methodology-gated* (see GRS-0146, needs an ADR). The *display*
half — never present a confident bottleneck at low coverage — is shipped as **GRS-0145** (uses the
existing top-level `coverage`, changes no scoring).

**2. No sanity validation on scoring inputs.** (Marcus, HIGH.) A negative −£999,999 "Assets Under
Administration" saved cleanly and satisfied the "enter a metric" gate — garbage feeds B and V. A
visible fail-loud violation (non-negotiable #3). → **GRS-0144.**

**3. Segment mis-fit: no wealth operating model; exchange/retail metrics are retail-framed and
GBP-locked; non-retail profiles self-flag "not client-usable."** (All 5, in different words: Priya &
Elena exchange, Tom & James wealth, Marcus retail.) The wizard offers only *Retail brokerage* /
*Exchange*; a wealth firm must be mislabelled as retail while the Academy treats "wealth" as
first-class. Metrics (AUA/ARPU/GBP) don't describe an exchange or a neobroker. → **Methodology-gated**
(weight/critical elicitation + metric taxonomy). Surfaced, not silently built (GRS-0147).

### TIER 2 — MED severity, high consensus, safely fixable

**4. Dead routes referenced by the product.** (4/5 — Priya, Tom, Marcus, James.) `/deliverables` and
`/academy` hard-404; the **Help page copy itself lists "Deliverables"** as a section, and the real
Academy lives at `/workbench/academy`. No global not-found with a way back. → **GRS-0143.**

**5. Disabled buttons with no hint + raw error leakage.** (Priya HIGH, Marcus MED.) "Add prospect" and
"Open engagement" sit disabled until a required field is typed, with no hint — read as dead by fast
users. Bad/missing IDs (`/prospects/<junk>`) surface a raw "Request failed (422)" instead of a
friendly not-found. → folded into **GRS-0143** (routing/not-found) + a hint pass.

**6. "No solo path to a finished score/deliverable."** (4/5.) All four who tried concluded finalise is
impossible solo — **but a "Sandbox (self-approve, non-production)" checkbox already exists** on the
assessment-create page (GRS-0119) and finalises solo with a watermarked draft. This is a
**discoverability** failure, not a missing capability. → surface + a discoverability hint (GRS-0148).

**7. Profile & Settings are "coming soon"; no change-password.** (Marcus, James, Tom.) Empty account
surfaces read as unfinished on a live, invite-only product. Known gap. → surfaced as a recommended
build (needs a backend change-password endpoint).

### TIER 3 — polish / reputational / founder-call

**8. Power-name key casing** — the Summary tab shows `BRANDING` / `CORNERED_RESOURCE` (raw keys) beside
Title-Case names, two representations of one list on one screen. (Marcus, James.) → **GRS-0145.**
**9. "Sales Egoist / weapons / zero-sum" doctrine branding** clashes with fiduciary culture; keep the
content, retire the naming. (James MED-HIGH reputational, Tom.) → founder/content call.
**10. Commission-for-product-sales conflict with no client-facing disclosure.** (Tom, James.) The
advisor assesses a client and earns commission selling them Benzinga/OpenBB — an independence conflict
with no disclosure record. → founder call.
**11. Silent duplicate prospects; workshop "date TBD" one-click; "50% conversion" with 0 engagements;
"Closed" 0% with no Won/Lost split.** (Marcus, low.) → backlog.

---

## What ships autonomously (one PR per fix, self-merge on green)
- **GRS-0142** — pipeline board load resilience (kills the stuck "Loading…"; the original stress-test
  bug) + repaired two stale CRM E2E assertions GRS-0137 had left red on main. *(PR #153)*
- **GRS-0143** — dead routes → redirects + a global not-found with a way back; friendly not-found for
  bad record IDs.
- **GRS-0144** — metric input validation (reject negative / out-of-range; refuse-to-score, fail-loud).
- **GRS-0145** — low-coverage honesty caveat on the "likely constraint" callout (display-only) +
  power-name casing normalisation.

## Surfaced for founder / methodology decision (NOT silently edited — per non-negotiables #2/#3)
- **GRS-0146** — reconcile the Monte-Carlo unassessed-imputation with ADR-0001 D9 (needs an ADR + a
  methodology-version bump; likely: exclude zero-coverage modules from `module_qm`/bottleneck, or make
  coverage widen the band). *The single most important integrity item.*
- **GRS-0147** — wealth operating model + segment-native metric taxonomies + finish non-retail weight
  elicitation so non-retail stops self-flagging "not client-usable."
- **GRS-0148** — surface the existing sandbox self-approve path (discoverability) and tie "Certified"
  to a demonstrated drill/arena record.
- Founder calls: Sales-doctrine branding tone; commission/independence disclosure; ship real
  Profile/Settings + change-password.
