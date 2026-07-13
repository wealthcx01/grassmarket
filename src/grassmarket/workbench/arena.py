"""The Practice Arena scorer (GRS-0025, PRD §6) — deterministic extraction-completeness scoring.

Pure and deterministic: given a scenario's targets and a discovery transcript, it reports which
powers the advisor probed on both sides, which modules they evidenced, and how many evidence-raising
questions they asked, plus a single completeness fraction. Only the ADVISOR's turns count as probing
(the role-played client's words are the case, not the advisor's discovery). Cue matching is
case-insensitive substring — simple, explainable, and pinned by a golden master.

A fully-probed power (benefit AND barrier) scores 1; a one-sided probe 0.5; a module 1 if evidenced.
completeness = achieved / (powers + modules). A scenario always targets at least one power (the
contract enforces it), so the denominator is never zero; the `else 0.0` guard is defensive only.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from bcap_contracts.arena import (
    AI_DRAFTED_LABEL,
    ArenaScenario,
    ArenaScore,
    ArenaSpeaker,
    ArenaTurn,
    PowerProbeResult,
)

_FULL_POWER = 1.0
_HALF_POWER = 0.5

ARENA_FEEDBACK_DRAFTER_VERSION = "template-arena-feedback-v1"


def _advisor_text(transcript: Sequence[ArenaTurn]) -> str:
    """The advisor's turns, lower-cased and newline-joined — the only text that counts as probing.

    Turns are joined on a newline (not a space) so a multi-word cue can never match across a turn
    boundary — "...fixed" then "cost..." in separate turns must not satisfy the cue "fixed cost".
    """
    return "\n".join(t.text.lower() for t in transcript if t.speaker is ArenaSpeaker.ADVISOR)


def _matches_any(haystack: str, cues: Sequence[str]) -> bool:
    return any(cue.lower() in haystack for cue in cues)


def score_transcript(scenario: ArenaScenario, transcript: Sequence[ArenaTurn]) -> ArenaScore:
    """Score a discovery transcript against a scenario's extraction targets (deterministic)."""
    text = _advisor_text(transcript)

    powers = tuple(
        PowerProbeResult(
            power_key=pt.power_key,
            benefit_probed=_matches_any(text, pt.benefit_cues),
            barrier_probed=_matches_any(text, pt.barrier_cues),
        )
        for pt in scenario.target_powers
    )
    modules_evidenced = tuple(
        mt.module_key for mt in scenario.target_modules if _matches_any(text, mt.cues)
    )
    evidence_questions = sum(text.count(cue.lower()) for cue in scenario.evidence_cues)

    achieved = sum(
        _FULL_POWER
        if p.fully_probed
        else _HALF_POWER
        if (p.benefit_probed or p.barrier_probed)
        else 0.0
        for p in powers
    ) + float(len(modules_evidenced))
    possible = len(scenario.target_powers) + len(scenario.target_modules)
    completeness = round(achieved / possible, 6) if possible else 0.0

    return ArenaScore(
        powers=powers,
        modules_evidenced=modules_evidenced,
        evidence_questions=evidence_questions,
        completeness=completeness,
    )


class ArenaFeedbackDrafter(Protocol):
    """Drafts coaching feedback from a scored session. The real Claude drafter plugs in behind this
    same call; feedback is always a labelled PROPOSAL (#8), never authoritative."""

    version: str

    def draft(self, scenario: ArenaScenario, score: ArenaScore) -> str: ...


class TemplateArenaFeedbackDrafter:
    """Deterministic offline drafter — coaching feedback derived from the score, so CI makes no live
    call. Every message is prefixed with the AI-DRAFTED label (#8)."""

    version = ARENA_FEEDBACK_DRAFTER_VERSION

    def draft(self, scenario: ArenaScenario, score: ArenaScore) -> str:
        fully = set(score.powers_fully_probed)
        missed_barrier = [
            p.power_key for p in score.powers if p.benefit_probed and not p.barrier_probed
        ]
        missed_entirely = [
            p.power_key for p in score.powers if not p.benefit_probed and not p.barrier_probed
        ]
        evidenced = set(score.modules_evidenced)
        missed_modules = [
            m.module_key for m in scenario.target_modules if m.module_key not in evidenced
        ]

        lines = [
            f"{AI_DRAFTED_LABEL}: extraction completeness {score.completeness:.0%}.",
            f"Fully probed (benefit + barrier): {', '.join(sorted(fully)) or 'none'}.",
        ]
        if missed_barrier:
            lines.append(
                "You raised the benefit but not the barrier for: "
                + ", ".join(missed_barrier)
                + " — a power is only as strong as its weaker side (§8), so probe both."
            )
        if missed_entirely:
            lines.append("Not probed at all: " + ", ".join(missed_entirely) + ".")
        if missed_modules:
            lines.append("Modules left unevidenced: " + ", ".join(missed_modules) + ".")
        if score.evidence_questions == 0:
            lines.append("Ask evidence-raising questions to lift the evidence grade (E1→E3+).")
        return "\n".join(lines)
