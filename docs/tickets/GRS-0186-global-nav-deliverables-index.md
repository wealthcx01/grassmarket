# GRS-0186 — Global navigation + Deliverables reachability

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: In review (2026-07-25) — PrimaryNav + mobile drawer, /deliverables index (owner-scoped), RecordBreadcrumb + po._
**Loop:** founder-feedback remediation, Wave 1.

## Why

Verified: the header has no primary navigation (wordmark, Workbench, Guide, account only), there
is no deliverables list anywhere (the dashboard card named "Deliverables" opens the engagements
index), and Workshops/Engagements/Stage History are reachable only via Kanban card → slide-over
→ "Open full record". The founder could not find the path from Portfolio to Deliverables, nor to
the per-client record — and the per-client record is the useful surface.

## Scope

1. **Primary navigation component.** `frontend/app/layout.tsx` is a server component (it wires the
   font CSS variables and `metadata`) and must stay one, so the active-state logic that needs
   `usePathname()` goes in a new client component `frontend/components/PrimaryNav.tsx`
   (`"use client"`). It renders five links — Pipeline (`/pipeline`), Portfolio (`/assessments`),
   Engagements (`/engagements`), Workbench (`/workbench`), Earnings (`/earnings`) — each with an
   active state (accent underline + `aria-current="page"`) computed by
   `pathname === href || pathname.startsWith(href + "/")`. `layout.tsx` (~98–128) drops the
   standalone Workbench pill (it folds into the nav), keeps the Guide (`/help`) pill and
   `<AccountMenu />` in the right cluster, and mounts `<PrimaryNav />` between the wordmark
   `<Link>` (~60–96) and the right cluster. Decision: extract a client child rather than convert
   the layout to a client component, so `metadata` and the font-variable wiring stay server-side.
2. **Mobile drawer.** `PrimaryNav.tsx` holds an `open` state. At the existing mobile breakpoint
   the inline link row is hidden and a hamburger button (`aria-expanded`, `aria-controls`)
   toggles a drawer panel that drops under the sticky header (`position: absolute`, full-width,
   `background: var(--color-paper)`, hairline `border-bottom`). Selecting a link, pressing
   Escape, or clicking the scrim closes it. Media handling uses a `matchMedia("(max-width: 767px)")`
   listener (not CSS-only) so the hamburger and the row never both render. Decision: 768px matches
   the one breakpoint already used across the app; no new token is introduced.
3. **Deliverables index contract.** New Pydantic model `DeliverableIndexRow` in
   `packages/bcap_contracts/src/bcap_contracts/deliverables.py`: `id: UUID`,
   `type: DeliverableType`, `title: str`, `mode: DeliverableMode`, `generated_at: datetime | None`,
   `engagement_id: UUID`, `engagement_title: str`, `prospect_id: UUID`,
   `prospect_company_name: str`. It is a read projection, not a stored resource (no `OwnedResource`
   base needed; it is only ever returned owner-scoped). Regenerate the JSON schema into
   `packages/bcap_contracts/.../json_schema/` and add the `DeliverableIndexRow` interface to
   `frontend/lib/types.ts` beside `Deliverable`.
4. **Repository query (single, owner-scoped).** New method
   `list_deliverables_for_consultant(principal) -> list[DeliverableIndexRow]` in
   `src/grassmarket/data/repository.py`, next to `list_deliverables` (~2316). One query over
   `DeliverableORM` joined to `EngagementORM` (title, prospect_id) and `ProspectORM`
   (company_name), filtered strictly by `owner_consultant_id == principal.consultant_id`, ordered
   `generated_at DESC NULLS LAST, created_at DESC`. Decision: a dedicated single query, **not**
   iterate `list_engagements` then `list_deliverables` per engagement — that is an N+1 and would
   fold the whole org's deliverables into an admin's view; this mirrors the self-only
   `_own_prospects` rule (ADR-0016), so even an admin sees only their own deliverables here.
5. **Index endpoint.** `GET /deliverables` in `src/grassmarket/web/routers/deliverables.py`
   (the router has no prefix; add beside `GET /engagements/{id}/deliverables` at ~194) →
   200 `list[DeliverableIndexRow]`. Owner-scoped; an advisor with none gets `[]` (never 404).
   No new admin surface.
6. **Deliverables index page.** New route `frontend/app/deliverables/page.tsx` (`"use client"`):
   redirect to `/login` when unauthenticated (the `getToken()` pattern from the earnings page),
   fetch `api.listAllDeliverables(signal)` (new client method `GET /deliverables`), and render a
   table — columns Subject/Engagement, Type, Audience, Generated, Download. The Subject cell links
   to `/engagements/{engagement_id}`; a second line links the company name to
   `/prospects/{prospect_id}`. Audience reuses the `Client`/`Draft` badge idea from
   `DeliverablesPanel`; Download reuses `api.downloadDeliverable(id, { clientFacing: mode === "client" })`.
   The `TYPE_LABEL` map moves to `frontend/lib/deliverableLabels.ts` and is imported by both this
   page and `DeliverablesPanel.tsx` (decision: share the one map rather than duplicate the
   seven-entry record). Empty state: "No deliverables generated yet."
7. **Paths to the client record.** Portfolio rows (`frontend/app/assessments/page.tsx`) link the
   subject to `/prospects/{prospect_id}` **only when linked**: the portfolio row contract gains
   `linked_prospect_id: UUID | None`, computed in the repository's portfolio builder by the
   existing reverse chain (an assessment whose id appears in some engagement's `assessment_ids`
   yields that engagement's `prospect_id`); rendered as a link when present, never fabricated when
   absent (fail-loud: no guessed link). Engagement detail (`frontend/app/engagements/[id]/page.tsx`)
   and prospect detail (`frontend/app/prospects/[id]/page.tsx`) gain a shared
   `frontend/components/RecordBreadcrumb.tsx` header (Pipeline › {Company} › {this record}) so the
   prospect page — workshops, engagements, stage history — is one click from any surface naming the
   client. `DealDetailPanel.tsx` already links "Open full record" (~357); it is unchanged.

## Test plan

Backend (pytest, offline):
- `tests/test_deliverables.py` additions:
  - `list_deliverables_for_consultant` returns only the caller's rows — seed advisor A and advisor
    B each with an engagement + deliverable; A's call returns A's row only, B's absent (scoping).
  - Ordering: two deliverables, one with a later `generated_at`, returned newest-first; a
    null-`generated_at` row sorts last.
  - Enriched fields (`engagement_title`, `prospect_id`, `prospect_company_name`) resolve from the
    joined rows.
  - `GET /deliverables` → 200 self-scoped list; advisor A's token never returns advisor B's row
    (explicit cross-advisor negative); a brand-new advisor → `200 []`.
  - Portfolio row `linked_prospect_id` is set when the assessment is linked to an engagement and
    `None` when it is not.

Frontend (vitest, per-file):
- `bunx vitest run frontend/components/PrimaryNav.test.tsx`: all five links render with correct
  hrefs; the active link carries `aria-current="page"` for a matching pathname; the hamburger
  toggles the drawer (`aria-expanded` flips, links appear) and Escape closes it.
- `bunx vitest run frontend/app/deliverables/page.test.tsx`: rows render with Subject→engagement
  and company→prospect links, the download button calls `api.downloadDeliverable`, and the empty
  state shows when the list is `[]`.
- `bunx vitest run frontend/components/RecordBreadcrumb.test.tsx`: breadcrumb renders the prospect
  link on both the engagement and prospect pages.

## Out of scope

- Milestone chips / stage-advance prompts on the pipeline (GRS-0198).
- Any change to how deliverables are generated or gated (GRS-0188 rewires the release gate).
- A cross-advisor or admin "all deliverables" view — this index is deliberately self-only.
- One ticket = one branch = one PR; the contract regeneration ships in this PR.

## Acceptance

From the portfolio, a generated deliverable is reachable in at most two clicks (Deliverables nav →
row), and the client's workshops/engagements/stage history in one (portfolio/engagement → prospect
record); no cross-section movement routes through the dashboard; the `/deliverables` index is
owner-scoped with a passing cross-advisor negative test; every nav link shows an active state on
its section.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `d1c0abc` (GRS-0186 followup: remove the /deliverables→/engagements redirect), `429740b` (GRS-0186: global navigation + deliverables reachability).

This ticket carried no *What shipped* record; the commits above are that record.
