# Tom Fielding (SJP/wealth) — RE-MEASURE after GRS-0147d. Confidence 58/100 (was 46 metrics-only, 55 original). **+12 recovery**

**GRS-0147d WORKED.** "Infrastructure Deep Dive modules read as wealth: Client Portal & Planning, Platform & AUM Economics, Investment Data & Research, Advice Workflow & Investment Governance, Client Management & Suitability… client portal, digital onboarding, financial-planning tools, accessibility/vulnerable-client support. Big improvement." "The core assessment has genuinely been re-skinned to a wealth manager and reads credibly." Scored V=73.9. Praised uncertainty honesty + AI/sandbox labelling.

Remaining caps at 58:
1. **Engagement page crash (HIGH) — STALE-BUILD ARTIFACT** (chunk 913 failed / 400): I rebuilt .next on the 0143b branch while the prod server ran → chunk hash mismatch. NOT a product bug. Fix: rebuild+restart frontend clean.
2. **C-index / Customer Proposition tab still retail (HIGH)** — "time-to-first-trade, first-deposit ease". The C dimension (ADR-0023) wasn't touched by 0147d. Real follow-up (parallel dimension).
3. **Scoreability gate copy names retail modules** ("rate a core module: App Server, Back Office, or OEMS") — MED. `scoreability_blockers` message is retail-hardcoded; make profile-aware/generic. Clean fix.
4. Account/security empty (0148 Item 2 unbuilt); "not client-usable" banner (Phase 4).
