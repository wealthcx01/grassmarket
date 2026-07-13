"""The weekly quiz drafter (GRS-0024, PRD §6, non-negotiable #8).

An injectable port so the real Claude drafter plugs in behind the same call, with a deterministic
offline template drafter for CI (no live calls). Whatever drafts the quiz, it is only ever a
PROPOSAL — an advisor never sees it until a human approves it (#8). Every question links back to the
methodology it teaches (the question-bank rule).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from bcap_contracts.learning import QuizQuestion

QUIZ_DRAFTER_VERSION = "template-quiz-drafter-v1"


class QuizDrafter(Protocol):
    """Produces draft quiz questions from a set of drill topics (a power / module / anchor key)."""

    version: str

    def draft(self, topics: Sequence[str]) -> tuple[QuizQuestion, ...]: ...


class TemplateQuizDrafter:
    """Deterministic, offline drafter — one question per topic, each linked to its methodology
    reference. Stands in for the Claude drafter so CI never makes a live call."""

    version = QUIZ_DRAFTER_VERSION

    def draft(self, topics: Sequence[str]) -> tuple[QuizQuestion, ...]:
        return tuple(
            QuizQuestion(
                prompt=f"What defines the '{topic}' rating, and what evidence supports it?",
                answer=f"See the rubric anchor and methodology section for {topic}.",
                methodology_ref=topic,
            )
            for topic in topics
        )
