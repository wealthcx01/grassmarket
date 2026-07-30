# GRS-0220 — The client report as an interactive web page, with read tracking

**Status:** Planned (2026-07-26, staging review item 9). **Priority:** HIGH.
**Loop:** founder-feedback remediation, Wave 3. **Depends on:** GRS-0211. **Relates to:** GRS-0206.

## Why

The founder asked for the final review "as a PDF and as an interactive web page", both Bruntsfield
branded, and added: "ideally we can track interaction from clients here too."

The web version is the more valuable of the two. A PDF is a snapshot; a page can show the maturity
radar responding to what the client hovers, can hold the technical appendix behind a disclosure so
the body stays readable, and can tell the advisor what the client actually read before the follow-up
call. That last part changes how an advisor prepares for a meeting.

## Scope

1. **A signed per-client link.** One URL per deliverable per client, unguessable, revocable by the
   advisor, with an expiry the advisor sets. No login for the client. The link is the credential,
   so it is scoped to exactly one deliverable and carries no session.
2. **The same content model as the PDF** (GRS-0211). One source, two renditions. The web page must
   never say something the PDF does not, or the two artefacts start to disagree in front of a
   client.
3. **Live figures.** The maturity radar, the value build-up and the module breakdown as interactive
   visuals rather than flat images. Hovering a module explains that module. The Rive runtime from
   GRS-0206 is a candidate here if that spike lands positively; plain SVG is an acceptable answer.
4. **The appendix is disclosed, not deleted.** Technical detail sits behind a clear expander so the
   body reads as a story and nothing is hidden from a client who wants the numbers.
5. **Read tracking, disclosed.** Per-section view events and dwell time, recorded against the
   engagement, visible to the advisor on the deliverable. A visible notice on the page states that
   the sender can see which sections were opened. No covert tracking, no third-party analytics, no
   fingerprinting: it is our own endpoint or it does not happen.
6. **Branding and accessibility.** Design-system tokens, responsive to a phone, keyboard navigable,
   and readable with `prefers-reduced-motion` set.
7. **Revocation is real.** Revoking a link makes it stop working immediately, and that is tested.

## Test plan

1. Link-scoping tests: a link resolves exactly one deliverable; a tampered or expired token is
   refused; a revoked link stops working immediately.
2. Content-parity test: the web rendition and the PDF rendition of the same run produce the same
   section set and the same figures.
3. Tracking tests: events record against the right engagement, and no event is recorded for the
   advisor's own preview.
4. Watermark test: a non-production record carries the mark on the web page too.
5. Vitest per file for the report shell, figures and the appendix disclosure.
6. Standing gate: pytest, pyright, tsc, ESLint.

## Out of scope

- The PDF (GRS-0219) and the narrative content (GRS-0211).
- Client accounts or a client portal. This is a link, not a login.
- Tiering (GRS-0214).

## Acceptance

The founder sends themselves a link for the Deutsche Börse review, reads it on a phone, and can
then see from the advisor side which sections were opened.
