# Business-Estate Reconciliation — July 2026 sweep

A full sweep of the three OneDrive business folders (Advisory, Briefing, Elite-Vault-System) against the build. **Rule: no client data is copied into this repo** — this note references OneDrive paths; ingestion happens as config/seed data through the app's own scoped storage, never as committed files.

## Findings → actions (ranked)

### 1. My Earnings must encode Commission Schedule v7 — the placeholder assumption is wrong
`Advisory\Resources\Bruntsfield_Consultant_CommissionSchedule_TEMPLATE_v7.docx` is the decided model, not an open item:
- **Stream A — product commission:** per product, Yr1/Yr2 rates, commission window (ConnectTrade 15%/10% 24mo; OpenBB 15%/10% 24mo; Brandfetch distribution 7.5%/5% 24mo, redistribution 3.75%/3.75% 36mo). Rates amendable by notice.
- **Stream B — consultancy commission:** split by sourcing (self vs firm) AND by delivery type — "Bruntsfield-led (Power Platform Assessment / Bruntsfield-methodology)" carries a different rate than "consultant-led bespoke". Pay-when-paid; share of outcome; uncapped.
- **Action (amend GRS-0028 follow-up):** earnings config schema must support two streams, per-product Yr1/Yr2 tiers, commission windows (dated), sourcing × delivery-type matrix for consultancy, and pay-when-paid status. Verify shipped schema covers this; if not, ticket the delta. Seed config from v7; filled instances (Consultants\Byoung, \Randy) validate against real records.

### 2. Deliverable types: PRD ≠ practice
Real house output (Engagements\Active\ASX, \NSI): **Outside Read Deck, Note, Primer, Strategic Assessment / 7 Powers Brief** — polished, client-named, exchange-focused. The PRD's seven deliverable types don't include these.
- **Action (new ticket, Loop 4 follow-up):** add the house deliverable types to the builder as templates; harvest structure/house style from the ASX and NSI packs (reference material, not committed). The "Workshop Output" template should be checked against the real Outside Read pattern.
- These packs are also the best **case-study and vignette source** in the estate (calibration vignettes, Practice Arena scenarios) — anonymise before use per the vignette pipeline.

### 3. Exchange profile priority is settled by revenue reality
Active engagements are exchange-side (ASX, NSE Data & Analytics). The METHODOLOGY-V2-SCOPE question "which profile ships second (exchange vs wealth)?" is answered: **exchange first** — arguably promoted from v2-nice-to-have to early-v2 priority, since the methodology is already being applied to exchanges manually.

### 4. Pipeline/CRM stage model should mirror the real lifecycle
Real flow observed: Proposal (versioned GTM decks + internal strategy + critique) → MSA + Engagement Schedule (versioned to executed) → Active engagement → Deliverables. Clients: OpenBB (executed v6), Brandfetch, ConnectTrade, Benzinga (reseller), ASX, NSE.
- **Action:** verify GRS-0011–0013's stage model accommodates contract documents (MSA/ES versions, executed dates) and the internal-strategy + adversarial-critique pattern (OpenBB's InternalStrategy.md + GTM_Critique.md is the exemplar). Seed the pipeline with the real book at cutover (operator task — real client data enters production only, never fixtures).

### 5. Workbench content: the seed set exists, the library doesn't
- Onboarding kit: Consultant Agreement v7, Overview Decks, PreSale Proposal template, NDA, Invitation template (Resources\) → certification/onboarding content seeds.
- Sales training: Challenger Sales summary (Training\) — the only training doc; fits the "old school" sales journey slot.
- **Power Primers (Power Drills quiz source) are NOT yet written** — the Foundation Package v3 SOW (Briefing\Content-Bank\Projects) specifies them (7 Powers applied to brokerage). This is a content-authoring dependency for GRS-0024's quiz bank, alongside rubric anchors and vignettes on the founder track.

### 6. Datasets for benchmarks / reference
- Widget checklists (Brokerage-App-Reviews, 7 brokers) → C-index benchmark corpus (already in METHODOLOGY-V2-SCOPE).
- Regulatory Filing Database v3 (Briefing\Projects\Regulatory-Filings-Database\Development) → candidate reference dataset for the knowledge base / entity context.

### 7. Confirmed absences (useful negatives)
- CPI / Customer Proposition Index, Holy Corner, Viewforth: no textual presence anywhere in the business folders — build-internal concepts only (provenance for CPI is GRS-0003 + METHODOLOGY-V2-SCOPE).
- Empty scaffolds: Advisory\{Deliverables, Completed, Invoicing, _reference}, Briefing\{Analytics, Distribution, Drafts, Published, _reference}. The build defines these schemas from first principles; nothing to harvest.
- Elite-Vault-System outside Development\ is LSEG-engagement business data — Holy Corner-phase reference only.

## Founder-track additions

| Item | Feeds |
|---|---|
| Confirm v7 commission schedule as the earnings config source (or supersede it) | GRS-0028 config |
| Approve harvesting ASX/NSI pack structure as deliverable templates (anonymised) | new deliverable-types ticket |
| Commission the Power Primers (Foundation Package strand 1 — currently unwritten) | GRS-0024 quiz bank, knowledge base |
| Decide exchange-profile promotion into early v2 | METHODOLOGY-V2-SCOPE |
