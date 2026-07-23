# GRS-0171 — Two-step finalise confirmation

**Status:** Done (2026-07-23). Staging-rerun finding (4/5 personas). **Loop:** rerun remediation.

## Why

"Finalise & lock inputs" executed an irreversible, input-locking action in ONE un-confirmed click,
and nothing at the moment of locking told a solo advisor what the sandbox path skips vs production.

## Fix (frontend only)

The button now opens an inline confirm (`role="alertdialog"`): states that the immutable run is
created and inputs lock permanently, quotes the exact score that will lock (the ADR-0040 point —
"the same number showing above"), and explains the current path (sandbox: self-approved,
watermarked, no second rater/committee, never client-facing · production: dual-rating + committee,
client-usability gates). Confirm / Cancel.
