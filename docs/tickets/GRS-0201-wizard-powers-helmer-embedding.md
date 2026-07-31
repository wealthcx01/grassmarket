# GRS-0201 — Wizard Powers step: embed the Helmer adaptation + review packet

**Status:** BLOCKED (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-23, founder feedback item 7 follow-through). **Priority:** HIGH —._
this is the surface Hamilton Helmer will actually see. **Loop:** founder-feedback remediation,
Wave 1 (after GRS-0180). Under ADR-0046.

## Why

The founder: "update the wizard accordingly so we do not let him down, he will be reviewing our
work." Today the Powers step rates benefit/barrier against summary guidance in
`frontend/lib/powerGuidance.ts`. With the adaptation document (GRS-0180) as the sanctioned
source, the wizard's Powers content is rebuilt from it, per power and per segment.

## Scope

1. **`frontend/lib/powerGuidance.ts` rebuilt from `docs/ATLAS-7Powers-Adaptation.md`:** per
   power — the definition, the Benefit and Barrier stated in Helmer's terms, the intensity
   determinants rendered as "what to look for" anchors for each rating level, and one
   segment-correct worked example per segment (retail brokerage / wealth advisory / exchange).
   The data shape gains a `segments` keyed field so the wizard shows the example matching the
   assessment's operating-model profile (`document.profile`), not a generic one.
2. **Powers step UI (`frontend/components/steps.tsx` Powers section + `GuidancePanel.tsx`):**
   the guidance drawer shows the adapted content with the attribution line ("Adapted from
   Hamilton Helmer, 7 Powers: The Foundations of Business Strategy, with the author's
   permission") rendered once per drawer, footer position. The one-click StrengthControl
   interaction from GRS-0170 is unchanged.
3. **Guide (`frontend/app/guide/page.tsx` seven-powers section):** re-sourced from the same
   adaptation document (it already shares `powerGuidance.ts`, so most of this falls out of §1);
   the section gains the Fundamental Equation in its wealth-platform reading, with attribution.
4. **Review packet** (`docs/planning/helmer-review-packet.md` + assets): the adaptation
   document, current screenshots of the Powers step and guidance drawer for each segment, and
   the Methodology §4/§5.4 extract showing where the mathematics sits in scoring — assembled so
   the founder can send one artifact. A recorded slot for Helmer's feedback; ADR-0046 moves to
   Accepted when the founder records the review outcome.

## Test plan

- `frontend/lib/powerGuidance.test.ts` (new): every power has all seven fields populated for
  all three segments; the attribution string is present exactly once in the drawer render.
- Per-file vitest on the Powers step: rating interactions unchanged (existing
  StrengthControl.test.tsx and RatingControl.test.tsx untouched and passing); guidance shows
  the segment matching the document profile, with a fail-loud error state if the profile is
  missing (no silent fallback to retail).
- Backend untouched; golden master suite passes unchanged.

## Out of scope

- Any change to the P computation or rating scale. Academy Powers content (Wave 4 authors it
  from the same adaptation document). Report narrative use of the equations (GRS-0189 may cite
  the adaptation document; scoped there).

## Acceptance

An advisor rating Powers for an exchange sees exchange-specific Helmer-grounded guidance with
attribution; the same for retail and wealth; the review packet is assembled and handed to the
founder; no score or stored run changes anywhere.

---

## Status reconciliation — 2026-08-01

**BLOCKED.** Blocked on founder decision **D7** (docs/FOUNDER-DECISIONS-2026-08.md). Embedding the Helmer adaptation in the wizard waits on the ADR-0046 review Helmer's permission is conditional on.
