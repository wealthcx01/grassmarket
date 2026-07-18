# GRS-0140 — Comprehension checks for the product courses

**Status:** In progress
**Loop:** Part 2 — critical review / trust hardening
**Follows:** GRS-0139 (Academy learning loop)

## Why

GRS-0139 gave every lesson a completion gate + auto-enrolled drill, but only the mandatory Sales
Egoist course carried **authored** comprehension Q&A — the product courses fell back to a recall
prompt derived from each lesson's `measurement`. This authors real checks for the product courses, so
completing a product lesson (and its spaced-repetition drill) is retrieval practice grounded in the
actual product knowledge, not a generic "how do you know you applied it".

## What was authored

- **OpenBB** — 22 checks (4 shared "sell it" lessons + 18 deep: pivot / Workspace / Platform /
  Copilot-MCP, five use cases, the white-label & build angle, and the conviction/objections set).
- **Benzinga** — 18 checks (4 template + 14 deep: the two arms, WIIM/news, signals & ratings,
  calendars/delivery, four use cases, redistribution/attribution, positioning, origin, conviction,
  objections).
- **Brandfetch** — 18 checks (4 template + 14 deep: directory+API, Brand API keys, Logo Link,
  Transaction API, four use cases, the two-tier commercial model, trademark, pricing motion, origin,
  conviction, objections). The one separately-built "two commission tiers" lesson keeps its
  measurement-derived check.

Every answer is grounded in the lesson's own body + measurement and the accuracy guardrails already in
each course (e.g. options-flow is *signal, not alpha*; OpenBB does NOT claim Bloomberg parity;
Brandfetch does not own the logos). The four shared template lessons — which had **no** measurement
(the weakest fallback) — now carry per-product checks.

## Implementation
- `product_course.build_product_course` takes an optional `checks` map for its four template lessons.
- Each course adds a `_DEEP_CHECKS` dict (keyed by lesson key) + a `_TEMPLATE_CHECKS` dict, and its
  `_lessons` helper applies them. No contract/schema change — `Lesson.check_question/check_answer`
  already exist (GRS-0139). No frontend change — the reader already renders the check.

## Flagged (still open)
- The two doctrine/process courses (Sales Ops Playbook) and any future courses still use the
  measurement fallback; deepen the doctrine course *bodies* remains a separate content task.

## Acceptance
- Every product-course lesson (bar the bespoke Brandfetch tiers lesson) has an authored
  check_question + check_answer; the courses build and all course tests pass. Golden master untouched.
