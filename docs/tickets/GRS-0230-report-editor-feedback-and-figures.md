# GRS-0230 — The report editor: feedback where you can see it, figures you can actually declare

**Status:** OPEN (reconciled 2026-08-01). _Previously recorded as: Planned (2026-07-31, first-time-user review G2). **Priority:** HIGH. **Type:** Bug + UX._
**Loop:** client-report hardening. **Extends GRS-0211.** **Relates to:** GRS-0222, GRS-0163.

## Why

Reviewed live on staging 31/07/2026, writing a real report end to end on
`/deliverables/f6312cfe…/report`:

- Clicking **Save** (mid-page) and **Download the PDF** (bottom of page) both appear to do nothing.
  The "Saved." confirmation and the refusal both render in a strip at the very top of the page,
  off-screen from every button that triggers them. The tester clicked Download, saw no response,
  checked the filesystem, found nothing, and only discovered the refusal by scrolling back up.
- The refusal reads: *"section 'value' states ['£3.4m'] without declaring it. Every number in prose
  must be a DeclaredFigure so it can be traced to the run."* — an internal section key and an
  internal class name, at an advisor. This is the exact failure GRS-0163 existed to stop
  ("stop leaking internal flag names at a human").
- There is no way out. The editor never shows which figures the run declares, and there is no
  affordance to declare one, so the section titled **"What that is worth"** cannot state what
  anything is worth in pounds. The gate's principle is right (non-negotiable #3; GRS-0211 scope 4);
  the workflow around it is a dead end that will make an advisor abandon the editor the first time
  they try to price a lever.

## Scope

1. **Feedback lands where the action happened.** Save/refusal messages render adjacent to the
   button that triggered them (and inline on the offending section), not only in a top-of-page
   strip. A refusal names the section by its on-screen label ("What that is worth"), never its key.
2. **Rewrite the refusal in the product voice.** Say what happened and what to do: which number, in
   which section, and that numbers in the report must come from the assessment so a client can trace
   them. No `DeclaredFigure`, no quoted key, no bracketed repr. The sentence lives in one place both
   API and frontend use (the GRS-0228 lesson: a message asserted in two places and authored in a
   third will drift).
3. **Show the declared figures.** The editor lists, per section, the figures the run makes available
   (label, value, source field — the same set the PDF appendix table prints), so an advisor knows
   the vocabulary before the gate teaches it to them by refusal. An insert action places the
   figure's display form into the prose at the caret.
4. **Decide how an advisor declares a new figure — or state plainly that they cannot.** If the
   value-bridge NPVs are the only priceable numbers (ADR-0002), the editor must say where prices
   come from and link there. What is forbidden is today's silence. Whatever is decided must not
   weaken the gate: prose numbers still trace to the run or they refuse.
5. **The disabled Create-link button explains itself.** It sits inert with no reason until sections
   are written; a one-line hint ("write and save all six sections first — Business and Appendix are
   still empty") replaces the mystery.

## Test plan

1. Vitest: a 422 renders adjacent to the triggering control and inline on the named section, with
   the human label; no internal key or class name appears in any user-visible string (assert on the
   rendered text, not the fixture).
2. Vitest: the declared-figures panel lists the run's figures per section; insert places text.
3. Backend: refusal payload carries section key + human label + offending tokens, and the shared
   copy constant.
4. Manual: repeat the £3.4m walk on staging; screenshot the refusal beside the button, in the PR.
5. Standing gate: pytest, pyright, tsc, ESLint, per-file vitest.

## Out of scope

- AI drafting of prose (GRS-0222).
- The appendix's own gate coverage (GRS-0232).
- Naming the client on the editor (GRS-0231).

## Acceptance

The founder writes a value section that cites a run figure without leaving the page or meeting a
class name, and when they get something wrong the page tells them, next to the button they pressed,
in a sentence they could read aloud to a client.

---

## Status reconciliation — 2026-08-01

**OPEN.** Scheduled in the GRS-0229–0245 wave (see docs/BACKLOG.md for the build order).
