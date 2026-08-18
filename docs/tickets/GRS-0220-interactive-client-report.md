# GRS-0220 — The client report as an interactive web page, with read tracking

**Status:** DONE (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-26, staging review item 9). **Priority:** HIGH._
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

## What shipped

The link, the public page, and disclosed read tracking. Stacked on GRS-0219.

**Scope items 1, 2, 4, 5, 6, 7 are in.** Signed per-client links (`/r/<token>`), the same content
model as the PDF, the appendix behind a native `<details>`, per-section read tracking with a visible
notice, design-system styling that is responsive and keyboard-navigable, and immediate revocation.

**The link is the credential, so it is treated like one.** Only the token's SHA-256 is stored; the
plaintext is returned once at creation and is unrecoverable. Unknown, expired and revoked tokens all
return the *same* 404 body, so the endpoint cannot be used to discover which links exist or to learn
that one was withdrawn. Expiry is capped at 180 days and an over-long request is **refused, not
silently clamped** — an advisor who asked for a year and got six months without being told would
believe the wrong thing about their client's access.

**A design decision the ticket did not specify: the shared page serves a SNAPSHOT.** The assembled
report is stored on the link at issue. Re-rendering from live data would silently change a document
a client has already read and may have quoted back — the same immutability discipline scoring runs
carry (non-negotiable #6).

**A bug worth recording:** SQLite returns naive datetimes and Postgres returns aware ones, so the
expiry comparison raised `TypeError` under the test suite. A security control that "works" by
crashing the request is not a control, so timestamps are normalised to UTC before comparison.

**Tracking is narrow by construction.** Section and dwell only — no IP, no user agent, no
fingerprint, no third party. Dwell is batched on section exit (an interval would count time spent on
another tab) and capped at six hours, so a tab left open overnight cannot tell an advisor the client
studied the appendix all night. A failed event never surfaces to the reader.

**Scope item 3 is partially done.** Figures are live SVG with per-bar text values and an aria-label
carrying every number — but they are bar charts, not the interactive radar with hover-to-explain the
ticket describes. The Rive path (GRS-0206) is unbuilt, and plain SVG is named in the ticket as an
acceptable answer; richer interaction is a follow-up.

**Not yet wired to the advisor's UI.** The API to issue, list and revoke links and to read the
per-section summary all exist and are tested, but no button in the app calls them, so the founder
cannot yet send themselves a link from the Deliverables page. That is the remaining last mile for
the acceptance test, and it is the same gap GRS-0219 has.

Gate: 24 backend tests, 7 vitest, ruff/pyright/tsc/ESLint clean.


## Correction, 2026-07-31 — the first link sent for review arrived broken

Tokens were `secrets.token_urlsafe`, whose alphabet includes `-` and `_`. A link is something a
human pastes, and a renderer that treats `_word_` as emphasis eats the underscores; the recipient
gets a URL that resolves to "this report is not available" — which the public endpoint makes
deliberately indistinguishable from a revoked link, so it is unbudgeable from the outside.

Tokens are now 48 hex characters: 192 bits of entropy, no punctuation for a formatter to eat,
survives a double-click select, and can be read down a phone line. Existing links keep working —
resolution is a hash lookup and does not care about the alphabet.

Also corrected: the client-facing routes never called `assert_client_ready`. Every section is
consultant-written today, so the gate passed trivially — which is precisely why it needed wiring
before GRS-0222 starts drafting. Non-negotiable #8 is now enforced on the path that reaches a
client, with a test that fails if the call is removed.

---

## Status reconciliation — 2026-08-01

**DONE.** Landed on main in `6a892cb` (GRS-0220: tell a client WHY the report did not load), `2eae954` (GRS-0220: the client report as a shared web page, with disclosed read tracking).
