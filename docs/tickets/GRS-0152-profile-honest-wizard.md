# GRS-0152 — Profile-honest wizard: C-dimension degrade, dynamic module counts, provisional banner on score views

**Status:** Done (2026-07-20). From the mock-advisor re-measure (Elena + Tom, HIGH) + the frontend UX audit.
**Loop:** Part 2 — segment fit / trust. **Related:** ADR-0023 (C dimension), ADR-0025/0035 (profiles).

## Why

Three profile-honesty defects, all flagged by the persona re-measure and the code audit:

1. **The Customer-Proposition (C) tab shows retail neobroker widgets on a wealth/exchange assessment**
   — "time-to-first-trade, KYC friction, first-deposit ease." The C taxonomy is a retail-brokerage
   customer-experience model; `for_profile` passed it through unchanged for every profile. Elena
   (Deutsche Börse) + Tom (SJP): *"instantly signals not built for us."* HIGH.
2. **Hardcoded "work each of the nine modules" / "ten Phase-E modules"** over a profile-driven render —
   a wealth/exchange view shows a different count, so the prose lies. James flagged the module count.
3. **The "indicative, not client-usable" banner rendered only on the Overview step** — an advisor could
   quote a finalised non-retail V on the score rail / Summary with no provisional flag. HIGH (audit #1).

## What shipped

- **C-dimension is profile-aware (fail-loud).** `ProfileDef.c_module_keys` (None ⇒ inherit the full
  retail C taxonomy, retail byte-identical; a tuple selects exactly those C modules; `[]` ⇒ none).
  `for_profile` filters `c_modules` accordingly; an unknown C-module key refuses to load. Wealth &
  exchange set `c_modules: []`, so their views carry no retail customer widgets.
- **C step degrades honestly.** When the view has no C modules, the wizard shows a clear "Customer
  Proposition — not yet modelled for the {profile} operating model … this step is skipped for this
  segment, it does not affect your V" panel, instead of retail onboarding questions. A per-segment C
  taxonomy is a founder-scoped content build (logged as outstanding), never an engineering guess.
- **Dynamic module counts.** Wizard copy interpolates `registry.modules.length` /
  `registry.c_modules.length` — no hardcoded "nine"/"ten".
- **Provisional banner travels with the number.** A reusable `ProvisionalScoreBanner` renders on the
  live rail (`LiveSummary`) and the Summary panel (`LiveScorePanel`) whenever the profile is non-retail
  — so a draft-weighted V is never shown without its "indicative, not client-usable" caveat. Also
  fixed the mislabeled live-score error heading ("Can't finalise yet" → "Score unavailable").

## Tests
`tests/test_profiles.py`: retail keeps the full C taxonomy; wealth/exchange carry zero C modules/subs;
C-module selection is fail-loud on an unknown key; None inherits / empty selects none. Golden master
untouched (C never enters V). Frontend type-check + lint + LiveSummary vitest green.

## NOT in scope (founder-gated, logged as outstanding)
A real per-segment C taxonomy (member/ISV/data/issuer proposition for an exchange; advice-relationship
/ planning / reporting for wealth) — a content + methodology build like the L/B taxonomy was (ADR-0025).
