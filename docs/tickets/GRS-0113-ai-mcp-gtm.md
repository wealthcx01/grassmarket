# GRS-0113 — AI / MCP GTM enablement surface

**Status:** Planned
**Loop:** Part 2 — Pipeline / GTM engine (one program)
**Depends on:** ADR-0027 (Pipeline / GTM engine)

## Why

A real GTM engine should let advisers do AI-assisted prospecting, enrichment, and outreach from inside
the Advisory app, not stitch tools together by hand. This ticket adds an enablement surface where an
adviser links their Gmail/Calendar (via GRS-0112) and runs best-in-class GTM/prospecting MCP skills —
the candidate set from the founder review is the Claude sales/GTM plugins (knowledge-work-plugins
`sales`, Salesably, La Growth Machine). This is new and large; it is the AI-assisted layer on top of
the rebuilt CRM.

## What to build

- A GTM/prospecting workspace in the pipeline area where an adviser can invoke registered GTM MCP
  skills (Claude sales plugins et al.) for prospecting, enrichment, and outreach drafting.
- AI-generated outreach and enrichment are **approval-gated** per the AI-proposes-humans-approve
  non-negotiable (ADR-0009): nothing AI-drafted leaves the app to a prospect without adviser sign-off.
- Results write back onto the prospect/deal via `CommsLogEntry` so drafted outreach and enrichment
  land on the activity timeline (GRS-0111).
- Keep owner-scoping and config-not-code: which skills are available is configuration, not hardcoded.

## Acceptance / verification

- An adviser links Gmail/Calendar and runs at least one GTM MCP skill from within the pipeline
  surface, with the result attached to the prospect.
- AI-drafted outreach carries a recorded approval gate before it can be sent (ADR-0009).
- The available-skills list is configuration-driven, not hardcoded.

## Not in scope

- The Google OAuth/scope plumbing itself (GRS-0112).
- LSEG influencer mapping (GRS-0114) and the target-universe seed (GRS-0115).
