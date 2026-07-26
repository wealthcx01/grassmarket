# Tom Fielding (SJP/wealth) — FULL RE-MEASURE. Confidence 63/100 (was 55 orig, 46 last, **+17 vs last**)

Confirmed fixed: wealth metrics native (AUM/bps margin/Consumer-Duty ceiling — "SJP now sees its own language"); wealth infra (Client Portal & Planning, Platform & AUM Economics, Custody/Settlement/CASS, Portfolio Mgmt & Dealing — no retail App Server/OEMS/watchlist); score gate names WEALTH modules; Guidance graceful; change-password works (updated + reverted, verified); client-facing deliverable correctly refused (fail-loud gate, "REVIEW BEFORE IT GOES TO CLIENT").

Scored lower than James (72) due to a REAL NEW BUG:
1. **Internal-draft deliverable generation FAILS (HIGH)** — POST /engagements/.../deliverables (Internal draft, Platform Power Report + Exec Summary) → net::ERR_FAILED / "Cannot reach API at http://localhost:8000"; no document produced. Client-facing branch returns a clean 409 (endpoint IS up) → the internal-draft/docx generation for a WEALTH assessment specifically breaks (likely deliverable builder assumes retail module/subcomponent keys → 500 without CORS, or hangs). INVESTIGATE + FIX.
2. Wealth §4 rubric anchors unauthored (med).
3. "not client-usable" (med — Phase 4).
4. Opaque error copy leaks host:port (low-med).
5. No explicit Suitability module; portfolio rows not clickable (low).
