# GRS-0049 — 2026-07-14 audit follow-up backlog

Tracked, deferred findings from the 2026-07-14 adversarial review (scoring, auth/scoping,
AI-gating/API, frontend). The CRITICAL and HIGH items were fixed under GRS-0042…GRS-0047; this
ticket keeps the remaining LOW / systemic items visible so nothing is silently dropped. Each should
become its own `GRS-nnnn` ticket + branch + PR when picked up.

## Medium

- **Pagination is absent on every list endpoint** (`repository.py` uses `.all()` throughout; ~27
  `response_model=list[...]` routes). Highest exposure: `GET /benchmark` and `GET /compliance/audit`
  are org-wide and uncapped. Append-only + no cap = latency/memory growth. Add `limit`/`offset` (or
  cursor) with a capped default at the repository layer.
- **`LinkAssessmentControl` collapses loading / empty / error into a silent no-op** (on the
  `grs-0039` link-assessment branch, PR #48). A non-network refresh error is swallowed with no
  `setError`, leaving `available = []` → the control renders nothing, indistinguishable from "no
  finalisable assessments". Track a `loaded`/`error` state and show a retry affordance; don't hide
  the section purely on empty. **Fix in PR #48 before it merges.**

## Low

- **Committee decisions accept arbitrary `(item_type, item_key, rating)`** (`repository.py`
  `decide_committee_item`) — a member can pre-approve a speculative rating not currently required.
  Reject a decision whose triple is not in `required_committee_items(current result)`.
- **Transcript `engagement_id` stored without ownership validation** (`routers/transcripts.py`
  `ingest_text`/`ingest_media` → `_store_transcript`). No cross-tenant *read* results, but it allows
  a dangling/foreign reference. Resolve the id through `get_engagement(principal, …)` first (404 on
  cross-owner).
- **No global exception handler; transcript decrypt can 500** (`web/app.py`; `transcripts.py`
  decrypt path). Register handlers mapping `RepositoryError` subclasses to their HTTP codes as a
  safety net, and translate `InvalidToken` (key rotation / corrupt ciphertext) to a controlled 5xx.
  (Not a detail leak today — FastAPI's default 500 body is generic.)
- **Arena feedback is gated by label + self-scoping, not an approval record** (`workbench/arena.py`,
  the weakest of the four AI gates). It satisfies non-negotiable #8 (never reaches a *client*), but
  the inconsistency should be documented in CLAUDE.md, or an approval step added for parity.
- **Monte Carlo docstring vs iteration order** (`montecarlo.py`): the "fixed registry order"
  reproducibility claim isn't literally true for metrics/powers (iterated in input order).
  Determinism holds for a fixed input ordering; either sort by registry order or correct the
  docstring.
- **A11y: bare single-token registry keys aren't humanized** (`labels.ts`) — a key with no
  separator (e.g. `FRONTEND`) renders raw. Low impact; extend the matcher or map known bare keys.

## Verified clean (recorded for the reviewer)

- AI-proposes-humans-approve is genuinely enforced at runtime (deliverable client packs gated at
  generate *and* download; extraction/quiz/narrative gates hold).
- JWT verification is sound (single-alg allow-list, exp/aud/iss required, no default secret).
- Repository ownership enforcement: no IDOR found across prospects/engagements/assessments/earnings/
  scoring-runs/transcripts/predictions.
- Scoring core: no silent coefficient fallback; monotonicity/bottleneck/renormalisation correct;
  score-points and currency never mix.
