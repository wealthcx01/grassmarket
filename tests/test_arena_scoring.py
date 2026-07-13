"""Golden-master + property tests for the Practice Arena scorer (GRS-0025, PRD §6).

The fixture and its expected score are hand-computed in the comments so the scorer is pinned to an
independently-derived answer — the same discipline as the ATLAS/SM-2/kappa golden masters.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from uuid import uuid4

from bcap_contracts.arena import (
    ArenaModuleTarget,
    ArenaPowerTarget,
    ArenaScenario,
    ArenaSpeaker,
    ArenaTurn,
)

from grassmarket.workbench.arena import score_transcript


def _scenario() -> ArenaScenario:
    now = datetime.now(UTC)
    return ArenaScenario(
        id=uuid4(),
        owner_consultant_id=uuid4(),
        created_at=now,
        updated_at=now,
        title="Meridian discovery",
        brief="A mid-market broker exploring its moat.",
        client_persona="A guarded CFO who answers narrowly.",
        target_powers=(
            ArenaPowerTarget(
                power_key="SCALE_ECONOMIES",
                benefit_cues=("fixed cost", "unit cost"),
                barrier_cues=("scale advantage", "hard to replicate"),
            ),
            ArenaPowerTarget(
                power_key="NETWORK_ECONOMIES",
                benefit_cues=("network effect", "more users"),
                barrier_cues=("lock-in", "switching"),
            ),
        ),
        target_modules=(
            ArenaModuleTarget(module_key="APP_SERVER", cues=("hosting", "uptime")),
            ArenaModuleTarget(module_key="OEMS", cues=("order management", "execution")),
        ),
        evidence_cues=("can you show", "do you have data", "what evidence"),
    )


def _turn(speaker: ArenaSpeaker, text: str) -> ArenaTurn:
    return ArenaTurn(speaker=speaker, text=text)


# --- Golden master ----------------------------------------------------------------------
#
# Advisor turns cover: SCALE benefit ("fixed cost") + barrier ("scale advantage", "hard to
# replicate") → FULLY probed (1.0). NETWORK benefit ("network effects" ⊃ "network effect",
# "more users") but NO barrier → half (0.5). APP_SERVER evidenced ("uptime", "hosting") → 1.
# OEMS never mentioned → 0. One evidence cue ("can you show").
#   achieved = 1.0 + 0.5 + 1 (APP_SERVER) + 0 (OEMS) = 2.5 ; possible = 2 powers + 2 modules = 4
#   completeness = 2.5 / 4 = 0.625
def test_arena_scoring_golden() -> None:
    transcript = (
        _turn(ArenaSpeaker.CLIENT, "We run a lean broker."),
        _turn(ArenaSpeaker.ADVISOR, "How does your fixed cost behave as volume grows?"),
        _turn(ArenaSpeaker.ADVISOR, "Is that scale advantage hard to replicate for a rival?"),
        _turn(ArenaSpeaker.ADVISOR, "Do you see network effects as more users join the venue?"),
        _turn(ArenaSpeaker.ADVISOR, "Can you show me the uptime data for your hosting?"),
        _turn(ArenaSpeaker.CLIENT, "Our uptime is strong."),
    )
    score = score_transcript(_scenario(), transcript)

    assert math.isclose(score.completeness, 0.625, abs_tol=1e-9)
    probes = {p.power_key: p for p in score.powers}
    assert probes["SCALE_ECONOMIES"].fully_probed is True
    assert probes["NETWORK_ECONOMIES"].benefit_probed is True
    assert probes["NETWORK_ECONOMIES"].barrier_probed is False
    assert set(score.modules_evidenced) == {"APP_SERVER"}
    assert score.evidence_questions == 1
    assert score.powers_fully_probed == ("SCALE_ECONOMIES",)


# --- Properties -------------------------------------------------------------------------


def test_only_advisor_turns_count_as_probing() -> None:
    # The client (role-play) saying every cue must NOT count — only the advisor probes.
    scenario = _scenario()
    client_says_everything = (
        _turn(
            ArenaSpeaker.CLIENT,
            "fixed cost scale advantage hard to replicate network effect more users "
            "lock-in uptime hosting order management execution",
        ),
    )
    score = score_transcript(scenario, client_says_everything)
    assert score.completeness == 0.0
    assert score.modules_evidenced == ()


def test_a_full_extraction_scores_one() -> None:
    scenario = _scenario()
    perfect = (
        _turn(
            ArenaSpeaker.ADVISOR,
            "fixed cost. scale advantage. network effect. lock-in. hosting. execution.",
        ),
    )
    score = score_transcript(scenario, perfect)
    assert score.completeness == 1.0
    assert len(score.powers_fully_probed) == 2


def test_matching_is_case_insensitive() -> None:
    scenario = _scenario()
    shouted = (_turn(ArenaSpeaker.ADVISOR, "FIXED COST and SCALE ADVANTAGE"),)
    probe = score_transcript(scenario, shouted).powers[0]
    assert probe.fully_probed is True


def test_a_cue_does_not_match_across_a_turn_boundary() -> None:
    # "fixed cost" split so each word ends/starts a separate advisor turn must NOT count as probed:
    # turns are newline-joined, so the phrase never appears contiguously.
    scenario = _scenario()
    split = (
        _turn(ArenaSpeaker.ADVISOR, "tell me about your fixed"),
        _turn(ArenaSpeaker.ADVISOR, "cost of goods sold"),
    )
    probe = {p.power_key: p for p in score_transcript(scenario, split).powers}["SCALE_ECONOMIES"]
    assert probe.benefit_probed is False


def test_probing_nothing_scores_zero() -> None:
    now = datetime.now(UTC)
    scenario = ArenaScenario(
        id=uuid4(),
        owner_consultant_id=uuid4(),
        created_at=now,
        updated_at=now,
        title="one power",
        brief="b",
        client_persona="p",
        target_powers=(
            ArenaPowerTarget(power_key="X", benefit_cues=("alpha",), barrier_cues=("omega",)),
        ),
    )
    # One power, no modules; the advisor raises neither cue → achieved 0 / possible 1 → 0.0.
    score = score_transcript(scenario, (_turn(ArenaSpeaker.ADVISOR, "small talk only"),))
    assert score.completeness == 0.0
