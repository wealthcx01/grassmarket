# GRS-0038 — UI audit: back-arrow "←" renders as tofu (VERIFY before fixing)

- **Loop:** UI retro-audit (grs-ui-retro-audit)
- **Status:** RESOLVED — verified as a local-environment artifact, not a product bug. No code change. See "Resolution" below.
- **Severity:** Low.
- **Found by:** Visual audit on the dev VPS's freshly-repaired browser. Repro screenshot:
  `assets/ui-audit-prospect-detail.desktop.png` (top-left "▯ Pipeline").

## Observation

Every "back" link uses a raw `←` (U+2190) character — "← Pipeline", "← Dashboard", "← Prospect".
In the audit screenshots the arrow renders as **tofu (▯)** — a missing-glyph box.

## Why this needs verifying, not blind-fixing

The audit browser is the dev VPS's Playwright chromium, whose system fonts were installed
**non-root by hand** (Ubuntu 26.04 has no supported Playwright font package set — see
`reports/ui-gate-2026-07-14.md`). A missing `←` glyph is exactly the kind of thing that font gap
causes, and it would **not** reproduce in the CI gallery (which runs `npx playwright install
--with-deps` on ubuntu-24.04, installing the full font set) or in a real user's browser.

**Action for the fix ticket:** first check whether `←` renders correctly in the CI `ui-gallery`
artifact (from the E2E UI-gate workflow) and in a normal desktop browser. If it renders fine there,
this is an environment artifact — close it. If it genuinely tofus for real users, replace the raw
Unicode arrow with an inline SVG / icon that doesn't depend on font coverage.

## Exit criteria (for the fix ticket, later)

- Confirmed reproduction (or not) in the CI gallery + a real browser.
- If real: back-affordances no longer depend on a font glyph that can be missing.

## Resolution (2026-07-14) — environment artifact, closed with no code change

Verified directly. The tofu is caused **solely** by the dev VPS's minimal, hand-installed font set
(it had no font covering U+2190). Proof: installed a normal font that covers the Arrows block
(`fonts-dejavu-core`, extracted to `~/.local/share/fonts`) and re-rendered the same page in the same
local browser — the back-link then renders **"← Pipeline"** correctly (evidence:
`assets/ui-audit-back-arrow-with-font.png`), versus **"▯ Pipeline"** before
(`assets/ui-audit-prospect-detail.desktop.png`).

Conclusion: real users (whose browsers have standard fonts) and CI (which runs
`npx playwright install --with-deps`, installing the full font set) render `←` correctly. This is
not a product defect. **No code change** — closing per this ticket's own "verify first" directive.
(A defensive inline-SVG for back-affordances remains possible if we ever want belt-and-braces
independence from font coverage, but it is not warranted for a non-bug.)
