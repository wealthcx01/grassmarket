# GRS-0021 — Rating Committee queue

- **Loop:** 5
- **Branch:** `grs-0021-rating-committee`
- **Status:** In review — PR #23
- **Normative source:** Methodology v1.2 §8 (committee sign-off); ADR-0007; Morningstar moat-committee pattern.
- **Depends on:** GRS-0020.

## Goal

High-stakes ratings require peer sign-off — enforced at runtime.

## Scope

1. Committee-approval requirement computed from results: any power rated Established or above; any triad rating above None; any module whose rating gate = Frontier.
2. Queue API + minimal admin UI: approve / reject-with-rationale; dissent recorded on split decisions; every decision carries member identity + timestamp.
3. Finalisation and client-pack gates extended: committee-pending items → refuse (409), same pattern as the GRS-0015 client-usable gate.
4. Committee membership as a role claim (JWT shape preserved for Holy Corner SSO).
5. Approved rationale paragraphs feed the deliverable (the triad rationale in the Platform Power Report is the committee-approved text).

## Exit criteria

- A Frontier module or Established+ power without committee approval blocks finalisation AND client packs (tested both paths).
- Rationale + dissent render into the methods appendix.
- Founder-track note: registry critical flags should be ratified before this ships, else the Frontier gate protects draft criticals.
- Full gate green; CI green.
