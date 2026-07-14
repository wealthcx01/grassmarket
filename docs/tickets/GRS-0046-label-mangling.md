# GRS-0046 — humanizeKeysInText must not mangle ordinary text (and must redact UUIDs)

- **Loop:** 3 (pipeline / shared UI)
- **Status:** Fixed — found in the 2026-07-14 adversarial frontend review.
- **Severity:** Medium — legitimate free text is corrupted before the advisor sees it.
- **Normative source:** CLAUDE.md #3/#9 (no raw internal identifier reaches a client).

## Problem

`humanizeKeysInText` treated **any** slash- or underscore-joined uppercase run as a registry key:

```
'EUR/USD exposure is unhedged' -> 'Eur · Usd exposure is unhedged'
'Run an A/B test'              -> 'Run an A · B test'
'TCP/IP latency'              -> 'Tcp · Ip latency'
'Q1/Q2 revenue dip'           -> 'Q1 · Q2 revenue dip'
```

In a wealth/advisory product, currency pairs like `EUR/USD` are highly plausible in a blocking or
finalise reason, and were being corrupted. Secondarily, a raw lowercase UUID passed straight
through (the matcher was upper-case-anchored), so an id embedded in a message would leak verbatim.

## Change

- The key matcher now requires **at least one underscore** (a lookahead) in addition to a
  separator — the real shape of `BACK_OFFICE` / `FRONTEND_PERFORMANCE` /
  `FRONTEND/FRONTEND_PERFORMANCE`. Ordinary uppercase text without an underscore (`EUR/USD`, `A/B`,
  `TCP/IP`, `Q1/Q2`) is left verbatim.
- A UUID is redacted (`…`) before key substitution, so no raw id reaches the screen even if the
  backend ever embeds one.

## Exit criteria

- Real keys still humanize; `EUR/USD`, `A/B`, `TCP/IP`, `Q1/Q2` render unchanged; a raw UUID is
  redacted — all pinned by `labels.test.ts`.
