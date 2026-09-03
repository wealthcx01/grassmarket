# ADR-0041 — Founder review gate: a single named reviewer replaces peer governance

- **Status:** Accepted (2026-07-23). Founder-directed (feedback 23/07/2026, items 23–24);
  ratifies with GRS-0188.
- **Deciders:** Founder (governance model), Engineering (implementation).
- **Normative source:** Methodology §8/§9 (amended by v1.6 with this ADR), ADR-0010
  (dual rating), ADR-0011 (committee), ADR-0012 (calibration), ADR-0013 (certification
  enforcement), ADR-0029 (sandbox/demo self-approval), non-negotiable #8 (AI proposes, humans
  approve — unchanged).

## Context

The governance stack was designed for a network of peer assessors: blind dual rating with lead
consensus, a rating committee for high-stakes ratings, and calibration sessions measuring
inter-rater agreement. The network today is one founder plus early advisors. In practice the
peer machinery cannot be exercised (no committee members exist outside the founder), it blocks
the core loop, and it confused the founder's own review of the product. The founder's decision:
every client draft routes to john@bruntsfield.capital, who signs and approves everything that
goes out.

## Decision

1. **Production finalisation and client-deliverable release require one recorded approval by
   the configured founder-reviewer account.** The approval records approver, timestamp, and the
   document content hash; re-editing re-opens review (an approval at a stale hash never counts —
   the same freshness rule the committee gate used).
2. **Dual rating, committee, and calibration are retired from product flows** — UI, routes, and
   finalise-chain blockers removed. Chosen depth is **disable, not delete**: history tables,
   contracts, and the agreement-statistics engine (weighted kappa, AC1) remain in the codebase,
   dormant with their tests, so peer governance can return when the network's size justifies it.
3. **Certification evidence** (shadow / observed-lead) switches from co-rating auto-credit to
   founder-recorded events via the existing admin-recorded paths and OVERRIDE-with-reason
   machinery. The certified-lead finalisation requirement (ADR-0013) is unchanged.
4. **Unchanged:** sandbox/demo self-approval (ADR-0029); the AI-narrative approval gate
   (ADR-0009), whose approver for client packs is now the founder; scoring, uncertainty, and
   the golden master, byte-identical.

## Consequences

- The approval chain matches the real organisation: one accountable reviewer, one audit trail.
- Methodology v1.6 amends §8/§9 to describe the founder gate as the current governance mode and
  the peer machinery as the scale-up mode it reverts to.
- The Bench queue loses its two governance priorities (re-prioritised in GRS-0199).
- Single-reviewer risk (availability, self-review of founder-led work) is accepted explicitly
  by the founder; the dormant machinery is the mitigation path.

## Reaffirmed 2026-09-03

The Advisor Studio redesign's frontend cut (GRS-0271) listed **blind rating** among the Workbench
surfaces, which would have required un-retiring the peer machinery. The founder confirmed the
opposite: **it stays off.** There is no blind/peer rating surface, no committee queue and no
calibration session to design or build.

Two consequences recorded so this does not have to be rediscovered:

- `GET /queue` (GRS-0253) reports `rate` as a **dormant kind, in words**, rather than showing an
  empty category. An empty queue and a queue whose source is switched off look identical on
  screen, and only one of them means the advisor can stop looking.
- `docs/API-SURFACE.md` now names every retired route at the top and marks each one inline. The
  15 retired routes still appear in the OpenAPI spec, so a designer or a generated client would
  otherwise find them and assume they work. The marking is derived from the app's own dependency
  graph, so it cannot go stale in either direction.
