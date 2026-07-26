# Style and voice

This guide is normative for all user-facing copy in Grassmarket: screen text, button labels,
tooltips, error messages, empty states, and the Guide and Help pages. Write to it. When a review
finds copy that breaks a rule here, the copy changes, not the rule.

## The register, in one paragraph

Write like a capable advisory colleague explaining the product to someone using it for the first
time. Use full sentences and plain connectives (and, so, because, which means, but). Explain what
a thing is and why it matters before you rely on the reader already knowing. The goal is that a
newcomer understands; it is not to sound clever or to compress a point into something quotable. An
advisor who reads a screen should come away knowing more than they did, not admiring the prose.

## Rules

Each rule has a real before-and-after from the codebase.

### 1. The em dash is rare, and never the default joiner

Let commas, colons, and full stops carry the sentence. Reserve the em dash for a genuine aside,
and use it at most once in a passage. An em dash between every clause is the single clearest sign
of the register we are leaving.

- Before: "is the current weakest link at 65 — but at only 40% coverage this is provisional: a
  module can rank weakest simply because it hasn't been assessed yet."
- After: "is the current weakest link at 65. At only 40% coverage this is still provisional,
  because a module can rank weakest simply because it has not been assessed yet."

### 2. No aphorism in place of an explanation

A maxim can summarise a point you have already made. It cannot do the explaining. If a line would
fit on a poster, it is probably standing in for the sentence that should be there.

- Before: "Words rate; numbers rank. The module bands are what you defend in the boardroom; the
  continuous scores decide what to fix first."
- After: "The module band (Basic to Frontier) is the rating you put in front of a client. The
  underlying score, which is more precise, is what decides which weakness to fix first. Use the
  band to communicate and the score to prioritise."

### 3. Define a term before you trade on it

The first time a screen uses V, C, q_m, P10/P50/P90, coverage, or provenance, say what it means in
plain words. After that, the short form is fine on that surface.

- Before: "V 67.4 (P10–P90 61.2–72.0)"
- After: "Platform Value 67.4. The likely range, from the tenth to the ninetieth percentile, is
  61.2 to 72.0." (Later mentions on the same screen may read "V 67.4".)

### 4. Size an explanation to inform a newcomer, not to impress a colleague

Say enough that someone new follows the point, and then stop. Do not add a second clever clause
once the first has done the work. Length is not the measure; a long sentence that teaches is fine,
a short one that only performs is not.

- Before: "honest by design."
- After: "The score never fills a gap with a guess. A subcomponent you have not assessed is left
  out of the calculation rather than counted as a zero."

### 5. Sentence case for headings and buttons

Capitalise the first word and any proper nouns. Not title case, not all caps for emphasis.

- Before: "Finalise & Lock Inputs", "RECOMMENDED TO SELL"
- After: "Finalise and lock inputs", "Recommended to sell"

### 6. Write numbers and units so a cold reader cannot misread them

Spell out a range or a percentile the first time rather than leaning on punctuation a screen
reader will skip. Use "to" for a range in prose. Keep the compact form (61.2–72.0) for dense
tables where the label has already been explained.

- Before: "V 67.4 (61.2–72.0) P50 · P10–P90"
- After, in prose: "Platform Value is 67.4, with a likely range of 61.2 to 72.0."

## Banned patterns

- Em-dash chains: more than one em dash in a sentence, or an em dash used where a comma or full
  stop would do.
- Tweet couplets: two short phrases joined by a semicolon for rhythm ("Words rate; numbers rank",
  "AI proposes; a human approves"). Write the sentence instead.
- Unexplained notation: q_m, P90, δ, θ, or a bare "V" shown before the surface has said what it
  is.
- Mantra repetition: the same slogan appearing on more than one surface. Each recurring line
  survives at most once, in the Guide, expanded into a real explanation.

## The mantras, once

Several slogans currently repeat across surfaces: "Words rate; numbers rank", "Read the range,
not the point", "honest by design", "AI proposes; a human approves". Each says something true. Keep
the idea, drop the slogan form, and let the full explanation live once in the Guide (that expansion
is GRS-0175's work). Elsewhere, state the point in plain sentences sized to the surface.
