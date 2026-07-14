# ADR-0021 — Append-only audit log, GDPR anonymisation-not-deletion, and the hardening posture

- **Status:** Accepted
- **Loop:** 6 (GRS-0032)
- **Normative source:** PRD §2; Viewforth PRD §3 (inherited data-protection standards); CLAUDE.md #6
  (immutable runs), #9 (scoping).
- **Builds on:** every prior feature ticket (this is the final compliance pass).

## Context

Before launch the platform needs a compliance posture: an audit trail of security-relevant actions,
and GDPR subject rights (export + erasure). Erasure collides head-on with the non-negotiable that
scoring runs are immutable (#6) — you cannot both "delete everything about a person" and "never
mutate a run." That collision is the decision this ADR settles.

## Decision

### 1. The audit log is append-only and admin-only

Every security-relevant action writes an `AuditEvent` (actor, event type, target resource, time):
auth login, assessment finalisation, deliverable generation, committee decision, certification
override, commission recording (and GDPR export/erasure themselves). Events are **inserted, never
updated or deleted** — there is no repository method that mutates one. The log is **admin-only** to
read (compliance). `detail` carries no secret (no token, password, or plaintext transcript).

### 2. Erasure is anonymisation-not-deletion for immutable runs

GDPR erasure (`delete_personal_data`, self-or-admin):

- **Deletes** every owned row that holds personal or client data — found by **reflection over the
  ORM registry** (every table with `owner_consultant_id`), so a new owned table is covered
  automatically with no hand-maintained list to drift. Deletion runs **children-before-parents**
  (via `metadata.sorted_tables` reversed) so foreign keys never break.
- **Anonymises the consultant** in place: email → a `@anonymised.invalid` sentinel, name →
  `[deleted]`, password → unusable, `is_active` → false. The row's **id is kept** so anything that
  legitimately references it stays FK-valid and becomes an opaque, PII-free key.
- **Does NOT delete scoring runs.** They are immutable (#6); instead they are **de-identified at the
  owner** — the run's now-anonymised owner id carries no PII. The run **retains its full
  `inputs_json`/`result_json`**, which includes advisor-authored free-text evidence (subcomponent
  `notes`, power `benefit_evidence`/`barrier_evidence`) that *may* describe the client. This residual
  PII-inside-a-run is an **accepted risk**: the `content_hash` is computed over exactly those inputs
  (the immutability seal), so scrubbing the text would break the seal — there is no path to erase
  embedded evidence without destroying the run's tamper-evidence. This is the exact reconciliation
  the ticket names: "no personal data outside anonymised immutable runs" — inside a run, under the
  immutability exception, retained evidence is permitted and documented. The GRS-0031 benchmark rows
  are already ownerless — untouched. The audit log survives as a de-identified compliance record
  (its actor id is now an opaque key; `detail` carries no secret and, by discipline, no PII).

Export (`export_personal_data`) uses the same reflection to bundle **every** owned table plus the
consultant record; the password hash and raw transcript ciphertext are redacted, not dumped.

### 3. The launch hardening posture — what ships, what is an accepted risk

**Shipped now:** the audit log, GDPR export/erasure, encryption-at-rest for transcripts (GRS-0029),
absolute repository scoping tested from day one (#9), fail-loud everywhere (#3), bcrypt password
hashing, a production config that refuses placeholder secrets/keys and SQLite.

**Accepted risks, to close as a fast-follow before the advisor cohort scales (documented per the
exit criterion "risks explicitly accepted in writing"):**

- **MFA (TOTP)** is not yet enforced. Accepted because launch is **invitation-only** to a small,
  known cohort over JWT + bcrypt; TOTP enrolment (required for Certified Leads and committee members
  per PRD) is a scoped fast-follow, not a launch blocker for the initial trusted group.
- **Application-level rate limiting** is not yet added. Accepted because the Railway edge provides
  network-level rate limiting and the cohort is small; per-endpoint app limits on auth/generation
  are a fast-follow.

## Consequences

- Compliance is now demonstrable: an audit trail of every listed action class, a complete subject
  export, and an erasure that leaves no personal data outside anonymised immutable runs — all tested.
- The immutability guarantee and GDPR erasure coexist by construction, not by exception.
- **Accepted scope boundaries:** MFA and app-level rate limiting are scoped fast-follows (above). The
  audit log is written at the repository layer for the wired flows; a deliverable **download** event
  and further flows reuse the same `record_audit` helper. Retention-driven auto-deletion of old
  transcripts (the GRS-0029 `retention_until` field) is a scheduled job, not built here.
