# GRS-0032 — Hardening + compliance

- **Loop:** 6
- **Branch:** `grs-0032-hardening-compliance`
- **Status:** Planned
- **Normative source:** PRD §2; Viewforth PRD §3 (inherited data-protection standards); CLAUDE.md #6, #9.
- **Depends on:** all prior feature tickets (final-pass ticket before launch).

## Goal

Production-grade security and compliance posture.

## Scope

1. MFA (TOTP), policy: recommended for all, required for Certified Leads and committee members.
2. Comprehensive append-only audit logging: auth events, scoring finalisations, deliverable generations + downloads, committee decisions, certification overrides, commission-config changes.
3. Rate limiting on auth and generation endpoints; session/inactivity policies.
4. GDPR export (complete scoped bundle per person) and deletion workflow. Deletion vs scoring-run immutability is reconciled by **anonymisation-not-deletion** of immutable runs — document as an ADR.
5. Dependency audit + secret-scan review; run `/security-review`; findings fixed or ticketed with accepted-risk rationale.

## Exit criteria

- Security review clean or risks explicitly accepted in writing.
- Audit log covers every listed event class (tested).
- GDPR export produces a complete scoped bundle; deletion request leaves no personal data outside anonymised immutable runs (tested).
- Full gate green; CI green.
