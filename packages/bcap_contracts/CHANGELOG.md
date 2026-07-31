# Changelog — bcap-contracts

All notable changes to the shared contracts package. This package is the type system where the
Bruntsfield studios meet Holy Corner; keep it additive so consumers (grassmarket, fountainbridge)
never break on an upgrade.

## [0.1.0] — 2026-07-20

### Added (FB-002 — Foundry Studio entities, consumed by fountainbridge)
- `foundry` module with six entities the Foundry Studio renders:
  - **Venture** — the root config object (venture-as-config): `vps` binding (D1), `founder`
    identity (GitHub + venture-domain Google Workspace `workspace_email`, D3/D6), D7
    `approval_matrix` (change class → founder | bruntsfield | dual), plus repos/lanes/
    departments/connectors.
  - **Lane** — a workshop lane bound to a venture repo (tmux, standing order, status).
  - **Ticket** — a `docs/tickets/` work item (id/phase/depends_on/status/branch/pr_url/body_md);
    status `todo | in-progress | pr-open | done`.
  - **Approval** — an attention-queue item; `kind` extensible (`pr` today, external gates post-FB-012).
  - **Department** — a venture department with its own repo/queue and gate (`pr | activegraph | tbd-fb012`).
  - **RunReport** — the record a lane writes back after a run; `no-useful-work` is a first-class outcome.
- JSON Schemas for all six committed under `json_schema/` (parity-checked, as for every model).
- Supporting enums (`VentureStatus`, `LaneStatus`, `TicketStatus`, `ApprovalKind`, `ApprovalState`,
  `DepartmentGate`, `RunTrigger`, `RunOutcome`, `ChangeClass`, `Approver`) and sub-models
  (`VpsBinding`, `FounderIdentity`, `ApprovalRule`), all re-exported from the package root.
- `FounderIdentity.workspace_email` refuses personal consumer mailboxes (`gmail.com` /
  `googlemail.com`) — a misconfigured manifest fails loud instead of leaking the founder's
  personal identity into the auth/send path (D3, `docs/research-gtm.md` §1).

### Notes
- **No breaking changes.** Only new files were added; no existing model or schema changed
  (grassmarket's contract-consumption tests stay green — CI proves it).
- **TypeScript types:** this package has no TS generator today (the frontend hand-writes types and
  CI runs `tsc --noEmit`). fountainbridge (the TS consumer) will generate/consume TS types from
  these committed JSON Schemas in FB-005 — tracked there, not here.

## [0.0.1]
- Loop 0 scaffold: initial contract surface consumed by grassmarket (ATLAS, pipeline, workbench,
  earnings, auth, audit). Version history for those additions lives in the `GRS-*` commit log.
