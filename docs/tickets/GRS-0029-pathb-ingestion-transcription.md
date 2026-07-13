# GRS-0029 — Path B: ingestion + transcription

- **Loop:** 6
- **Branch:** `grs-0029-pathb-ingestion-transcription`
- **Status:** Planned
- **Normative source:** PRD §3.3 (Path B); Viewforth-inherited data-protection standards.
- **Depends on:** GRS-0009 (assessment lifecycle).

## Goal

Meeting recordings and transcripts enter the system safely, behind a swappable transcription adapter.

## Scope

1. Upload: audio/video/transcript paste; size + type limits; malware-scan hook.
2. `Transcriber` adapter interface; default implementation decided at build time (local Whisper acceptable default; provider swap is config + adapter, not code change elsewhere) — record the choice in the ticket.
3. Transcripts stored scoped to the owning consultant, encrypted at rest.
4. Retention-policy fields on stored media/transcripts (GDPR groundwork for GRS-0032).
5. No AI extraction in this ticket — storage and transcription only (extraction is GRS-0030).

## Exit criteria

- A pasted transcript and an uploaded audio fixture both yield stored, scoped transcripts.
- Adapter contract tests pass against a fake second provider (swap proven).
- Cross-owner access → 404.
- Full gate green; CI green.
