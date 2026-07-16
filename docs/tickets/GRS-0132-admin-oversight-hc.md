# GRS-0132 — Admin/oversight — DEFERRED to Holy Corner (record only)

**Status:** Planned
**Loop:** Part 2 — Bruntsfield Academy / Workbench (one program)
**Depends on:** ADR-0028 (Bruntsfield Academy / Workbench)

## Why

The founder wants john@bruntsfield.capital as admin with backdoor visibility (committee, per-consultant
assessment + learning progress), and others as child accounts. **The admin role already exists** in
Grassmarket — `Role.ADMIN` (`bcap_contracts/common.py:163`), carried in the JWT `role` claim, with
`principal.is_admin` bypasses and admin-gated actions throughout `repository.py`. So the *role plumbing*
is done; what's **deferred to Holy Corner** is the **oversight dashboards / backdoor views**
(cross-consultant committee + learning + assessment progress). Grassmarket stays flat-consultant per the
founder decision — the backdoor is HC's job.

## What to build

- **Record only — nothing to build in GM now beyond noting this.** The Academy ADR (ADR-0028) records
  cross-consultant oversight (committee + learning + assessment progress dashboards) as a **Holy Corner
  capability** that consumes the existing `Role.ADMIN` claim (`common.py:163`).
- Confirm the existing admin plumbing is sufficient as the HC consumption surface: `Role.ADMIN`, the
  `role` JWT claim, `principal.is_admin` bypasses, and admin-gated actions in `repository.py`.

## Acceptance / verification

- ADR-0028 documents oversight dashboards as a deferred Holy Corner capability consuming the existing
  admin claim — no new GM feature code.
- The existing `Role.ADMIN` plumbing (`common.py:163`, JWT `role` claim, `principal.is_admin`) is
  confirmed as the intended HC consumption point.

## Not in scope

- Building any oversight/backdoor dashboard in Grassmarket — deferred to Holy Corner.
- Any change to the flat-consultant model or the existing admin role plumbing.
