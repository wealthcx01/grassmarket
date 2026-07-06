"""Assessment lifecycle services (GRS-0009) — the glue between the intermediate document and the
engine. The document is partial-friendly; the live-score service completes it to engine inputs
(missing subcomponents/metrics → Not Assessed, first-class, never zero-filled) and scores what it
can, labelling B/P honestly (ADR-0008)."""

from __future__ import annotations

from grassmarket.assessments.service import (
    LIVE_DRAWS,
    ScoreArtifacts,
    compute_score,
    live_score,
    scoreability_blockers,
)

__all__ = [
    "LIVE_DRAWS",
    "ScoreArtifacts",
    "compute_score",
    "live_score",
    "scoreability_blockers",
]
