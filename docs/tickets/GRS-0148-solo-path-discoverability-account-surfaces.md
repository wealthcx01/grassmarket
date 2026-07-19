# GRS-0148 — Solo-path discoverability + unfinished account surfaces

**Status:** Surfaced — part discoverability (buildable), part founder-call
**Loop:** Part 2 — mock-advisor stress test / trust & finish

## Findings

**1. "No solo path to a finished score/deliverable" — actually a discoverability failure (4/5).**
Four personas concluded finalisation is impossible solo (needs a second independent rater + resolved
consensus), so they never saw a finished score or the client deliverable — the single artefact they
most wanted to judge. **But a "Sandbox (self-approve, non-production)" checkbox already exists** on the
assessment-create page (GRS-0119, `app/assessments/page.tsx:199-203`): it finalises solo and produces a
real, watermarked deliverable draft. None of the four found it. → surface the sandbox path far more
prominently (e.g. on the finalise gate, when a solo user is blocked, offer "preview in sandbox").

**2. Cert = demonstrated skill (founder-call, carried from the earlier critical review).** The
comprehension gate is UX-level self-assessed recall, not a server-enforced quiz pass; "Certified"
should be tied to a minimum drill/arena record. Needs MC auto-grading design.

**3. Unfinished account surfaces (Marcus, James, Tom — MED).** `/profile` and `/settings` are both
"coming soon" placeholders on a live, invite-only product; there is no change-password, no
notification/data-retention/consent controls, and no visible data-protection statement when a real
company name is entered. Known gap (a change-password endpoint does not exist yet). → ship real
name/credential editing + change-password + basic preferences, or hide the pages until ready.

**4. Reputational / independence calls (James, Tom — founder decisions, not bugs).**
- The mandatory "Sales Egoist" doctrine's "own the zero-sum pipeline / Relationship-Challenger-Demo
  *weapons*" branding clashes with fiduciary wealth culture — keep the (strong) content, retire the
  mercenary naming.
- The advisor both assesses a client and earns commission selling them third-party products
  (Benzinga/OpenBB/Brandfetch) with no client-facing conflict/independence disclosure record.

## Buildable now vs founder-gated
- **Buildable:** sandbox discoverability hint (#1); change-password + real Profile/Settings (#3, needs
  a backend auth endpoint — moderate).
- **Founder-gated:** cert-teeth design (#2), doctrine branding + commission-disclosure (#4).

See the synthesis report `reports/mock-advisor-stress-test-2026-07-19.md` for the full ranking.
