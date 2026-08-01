# GRS-0230 — The report editor: feedback where you can see it, figures you can actually declare

**Status:** Planned (2026-07-31, first-time-user review G2). **Priority:** HIGH. **Type:** Bug + UX.
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


**DONE.** All five scopes.

## What shipped

**1 — Feedback lands where the action happened.** Save, Download and Create-link each render their
own confirmation or refusal directly beneath the button pressed. The top-of-page strip stays too: a
long form can scroll a button off screen just as easily as it scrolled the strip away.

**2 — The refusal, rewritten, in one place.** `undeclared_figure_message()` lives in the contract
beside the rule it explains. It says what is wrong, why the rule exists, and what to do:

> What that is worth mentions £3.4m, but that number is not among the figures this assessment
> produced. Every number in a client report has to trace back to the scoring run, so the client can
> check it. Use one of the figures listed beside this section, or take the number out of the
> sentence.

No key, no class name, no bracketed repr. **`SECTION_TITLES` moved into the contract** while doing
it — the reader-facing names were already duplicated between the PDF renderer and the web page, and
this message needed a third copy. Three copies of a name is exactly the drift GRS-0228 was, red on
main for nine days. There is a test asserting the sentence leaks no internal vocabulary.

**3 — The declared figures are visible.** Each section shows the figures the run makes available as
chips (value, label, source on hover); clicking one appends it to the prose so the digits are exact,
since the gate compares strings. They come from `figures_available_to()`, which is the *same*
`_figures_for` the assembler uses — so what the editor offers and what the gate accepts cannot
disagree.

**4 — Where prices come from, stated.** A section with no quotable figures no longer sits silent: it
says any number in it will be refused, and that prices come from the value bridge on the deliverable
rather than from this editor. That is the honest answer under ADR-0002 — score-points and currency
never mix in one equation, so an advisor cannot mint a price here. **The gate is not weakened**:
prose numbers still trace to the run or they refuse.

**5 — The disabled Create-link button explains itself**, naming the empty sections by their
on-screen titles: "Write and save all six sections first — The business and Technical appendix are
still empty."

## Test fallout

Three existing tests asserted the old refusal string. The rule is unchanged; each assertion moved to
the sentence an advisor now reads, and the wiring test gained leak checks — it now asserts the detail
names a reader-facing title and contains no raw section key, checked against the contract's own map
rather than a guessed title.
