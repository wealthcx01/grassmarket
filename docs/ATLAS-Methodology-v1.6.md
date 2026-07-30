# ATLAS Methodology v1.6

**Bruntsfield Capital — CONFIDENTIAL — July 2026**

The Bruntsfield Platform Power assessment method. This document is **normative** for the Grassmarket
scoring engine and **supersedes v1.5** for the governance sections only. It is a focused successor:
it amends **§8 and §9 only** — who signs off an assessment — and restates the amended rules in full
below. **All other sections are unchanged** and are incorporated by reference: §7 uncertainty and
§5.1 critical-control cap (v1.5), §5.1 four-index composition (v1.4), §3.3 evidence scales (v1.2),
and §1–§6/§10–§12 (v1.1).

**No coefficient value changes. Nothing computational changes at all: the deterministic scores (§5)
remain byte-identical to v1.1 (golden master V = 0.478565), and the uncertainty machinery (§7) is
untouched.** v1.6 changes only *who is required to approve a result before it may be used*.

---

## 1.1 Changelog: v1.5 → v1.6

The methodology described governance built for a network of assessors: independent dual rating so
that no solo rating became a deliverable, a Rating Committee signing off the high-stakes calls, and
calibration sessions keeping assessors aligned on what a rubric level means.

The Bruntsfield Advisory Network is not that network yet. It is one founder and a small group of
advisors. Requiring a second independent rater and a peer committee in a group that size does not
produce peer challenge; it produces a queue with the same few names in it, and the discipline
degrades into a formality. The founder has therefore taken the sign-off responsibility directly.

| Amendment | Section | ADR |
|---|---|---|
| **A single named reviewer approves, in place of peer sign-off.** No production assessment may be finalised, and no client-facing deliverable may be produced, without a recorded approval from the configured founder reviewer at the assessment document's **current version**. | §8, §9 | ADR-0041 |
| **Dual rating, Rating Committee sign-off and calibration sessions are DORMANT.** They remain specified here and implemented in the codebase, and are the intended mode when the network is large enough for genuine peer challenge. They are not part of the current gate. | §8, §9 | ADR-0041 |
| **Certification evidence must be asserted by a person.** Participation in a finalised assessment no longer derives certification credit automatically, because the peer participation it derived from no longer exists. | §9 | ADR-0041 |

### Version-stamping convention (v1.6)

`methodology_version` on a scoring run continues to record the version the engine computed under.
Because v1.6 changes no computation, a run stamped v1.6 is numerically identical to the same
document scored under v1.1 through v1.5. **The version tells you which approval regime applied, not
which arithmetic did.**

---

## §8 Sign-off on high-stakes ratings (restated)

**Current mode — founder review.** An assessment intended for a client is approved by the
configured founder reviewer before it is finalised. The approval is recorded against the **sha256
of the assessment document as it stood when it was approved**. It clears the gate only while that
hash still matches the document's current hash.

The consequence is the point of the design: **any edit after approval withdraws the approval**, not
by a state transition but by arithmetic. There is no path by which a document can be finalised or
released in a state the reviewer did not read. The reviewer's queue distinguishes a first reading
from a re-reading after an edit, so a small change is not presented as fresh work.

Two properties are enforced at the repository layer rather than by convention:

1. **Only the reviewer approves.** Not the advisor who owns the assessment, and not an
   administrator. An administrative bypass would reintroduce self-approval, which is the exact
   failure the gate exists to prevent (non-negotiable #8).
2. **The hash is computed server-side** from the stored document. A caller cannot state which
   version it is approving.

**Dormant mode — Rating Committee.** The v1.1 §8 rule stands unamended as the intended mode at
scale: any power rated Established or above, any triad dimension above None, and any module whose
rating gate is Frontier requires committee approval with recorded rationale and dissent, and a
decision clears only while the rating it reviewed still matches. The derivation of high-stakes
items and the decision-matching rule are implemented and unit tested. Re-adopting this mode is a
routing decision, not a rebuild.

## §9 Independence of rating and assessor certification (restated)

**Current mode.** A production assessment is rated by its lead and approved by the founder
reviewer. The v1.1 principle that "solo ratings are drafts, never deliverables" is preserved in
substance: a rating by one person is still not a deliverable, because it does not become one until
a second person — the reviewer — has read and signed it.

The certification floor is unchanged: a Frontier module or a Wide power still requires a Certified
Lead to lead the assessment, and an administrative override still requires a recorded reason and is
audited.

**Certification evidence.** Credit is no longer derived automatically from finalisation. Under the
peer mode, finalising credited each co-rater with a shadow assessment and the lead with an observed
lead. With no co-raters there is nothing to derive, and crediting an *observed* lead with nobody
observing would record evidence for something that did not happen. Evidence is now recorded through
the explicit routes, each of which requires a person to assert that the thing occurred.

**Non-production records are unchanged.** A demo or sandbox record self-approves, is permanently
watermarked, is excluded from the benchmark population, and never reaches a client (ADR-0029). It
requires no approval under either mode, because there is no client on the other side of it.

**Dormant mode — dual rating and calibration.** The v1.1 §9 rules for blind independent rating,
consensus resolution with a mandatory dissent note, and calibration sessions with measured
inter-rater agreement stand unamended as the intended mode at scale. The agreement statistics
(Cohen's κ, Gwet's AC1) remain implemented and unit tested.

---

## 1.2 What did not change

- **§5 deterministic scoring.** Byte-identical. The golden master is unchanged.
- **§7 uncertainty.** Unchanged from v1.5, including the D9 Not-Assessed rule and the
  critical-control cap.
- **§3.3 evidence grades**, §4 weights, §6 rating gates, §10–§12: unchanged.
- **The client-usability gate.** A client-facing pack still requires a ratified coefficient set and
  a client-usable uncertainty model. Founder approval is an additional gate, not a replacement for
  those.
