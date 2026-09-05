"""One level, one derivation, so Bench and the Certification ladder cannot disagree.

GRS-0242 scope 3.

Walked as a first-time user on 2026-07-31, the Workbench said two things at once: Bench's "My
performance" reported **Level: certified lead**, while the Certification tab beside it showed
coursework outstanding, the exam not taken, zero shadow assessments and no promotions recorded.

Both were true. The level lives on the consultant record (and the JWT), where an invite, a seed or
an administrator can set it directly; the evidence lives on the certification record and is only
ever written by the ladder. Nothing reconciled the two, so a level granted outside the ladder
rendered exactly like one earned through it.

The fix is not to hide the level or to force it down to the evidence — an administrator may
legitimately grant one. It is to derive what the evidence *does* support, carry that everywhere the
level appears, and let both surfaces say the same thing about the same person.
"""

from __future__ import annotations

import pytest
from bcap_contracts.certification import SHADOW_ASSESSMENTS_REQUIRED, CertificationRecord
from bcap_contracts.common import AssessorLevel
from sqlalchemy.orm import Session, sessionmaker

from grassmarket.data.models import ConsultantORM
from grassmarket.workbench.certification import (
    earned_level,
    evidence_blockers,
    level_is_evidenced,
    promotion_blockers,
)
from tests.conftest import SeededConsultant, auth_header


def _record(level: AssessorLevel = AssessorLevel.TRAINED, **evidence) -> CertificationRecord:
    from datetime import UTC, datetime
    from uuid import uuid4

    now = datetime.now(UTC)
    return CertificationRecord(
        id=uuid4(),
        owner_consultant_id=uuid4(),
        level=level,
        created_at=now,
        updated_at=now,
        **evidence,
    )


_FULL_SHADOW_EVIDENCE = {
    "coursework_complete": True,
    "exam_score": 0.95,
    "shadow_count": SHADOW_ASSESSMENTS_REQUIRED,
}


class TestWhatTheEvidenceActuallySupports:
    def test_no_evidence_earns_trained_and_nothing_more(self) -> None:
        """Trained is the floor — the rung an advisor starts on, needing no evidence to hold."""
        assert earned_level(_record()) is AssessorLevel.TRAINED

    def test_coursework_alone_does_not_earn_shadow(self) -> None:
        assert earned_level(_record(coursework_complete=True)) is AssessorLevel.TRAINED

    def test_the_full_trained_credentials_earn_shadow(self) -> None:
        assert earned_level(_record(**_FULL_SHADOW_EVIDENCE)) is AssessorLevel.SHADOW

    def test_an_observed_lead_on_top_earns_observed_lead(self) -> None:
        assert (
            earned_level(_record(**_FULL_SHADOW_EVIDENCE, observed_lead_logged=True))
            is AssessorLevel.OBSERVED_LEAD
        )

    def test_a_signoff_on_top_earns_certified_lead(self) -> None:
        from uuid import uuid4

        assert (
            earned_level(
                _record(
                    **_FULL_SHADOW_EVIDENCE,
                    observed_lead_logged=True,
                    observed_lead_signoff_by=uuid4(),
                )
            )
            is AssessorLevel.CERTIFIED_LEAD
        )

    def test_the_ladder_is_cumulative_so_a_gap_low_down_stops_the_walk(self) -> None:
        """A sign-off does not carry someone past a missing exam. Skipping a rung is exactly what
        the ladder exists to prevent, so the derivation must not permit it either."""
        from uuid import uuid4

        record = _record(
            coursework_complete=True,
            exam_score=None,  # the gap
            shadow_count=SHADOW_ASSESSMENTS_REQUIRED,
            observed_lead_logged=True,
            observed_lead_signoff_by=uuid4(),
        )
        assert earned_level(record) is AssessorLevel.TRAINED


class TestALevelAboveItsEvidenceIsFlagged:
    def test_a_granted_certified_lead_is_not_evidenced(self) -> None:
        """The exact case the founder met: marked Certified Lead, ladder empty."""
        record = _record(level=AssessorLevel.CERTIFIED_LEAD)
        assert earned_level(record) is AssessorLevel.TRAINED
        assert level_is_evidenced(record) is False

    def test_an_earned_level_is_evidenced(self) -> None:
        record = _record(level=AssessorLevel.SHADOW, **_FULL_SHADOW_EVIDENCE)
        assert level_is_evidenced(record) is True

    def test_a_level_below_the_evidence_is_still_evidenced(self) -> None:
        """Evidence beyond the current rung is not a contradiction — it is somebody due a
        promotion. Only a level ABOVE its evidence is the problem."""
        record = _record(level=AssessorLevel.TRAINED, **_FULL_SHADOW_EVIDENCE)
        assert earned_level(record) is AssessorLevel.SHADOW
        assert level_is_evidenced(record) is True


class TestTheGateAndTheDisplayShareOneImplementation:
    @pytest.mark.parametrize(
        "target",
        [AssessorLevel.SHADOW, AssessorLevel.OBSERVED_LEAD, AssessorLevel.CERTIFIED_LEAD],
    )
    def test_promotion_blockers_delegates_to_the_same_rung_rules(
        self, target: AssessorLevel
    ) -> None:
        """`promotion_blockers` adds the one-rung-at-a-time rule on top of `evidence_blockers`.
        If the two ever list different requirements, the gate and the ladder display drift apart —
        which is the class of bug this ticket is about."""
        from grassmarket.workbench.certification import _LADDER, _RANK

        below = _LADDER[_RANK[target] - 1]
        record = _record(level=below)
        assert promotion_blockers(record, target) == evidence_blockers(record, target)


class TestBothTabsDescribeThePersonTheSameWay:
    def test_bench_and_the_certification_record_agree_over_http(
        self,
        client,
        alice: SeededConsultant,
        session_factory: sessionmaker[Session],
    ) -> None:
        """The whole point, end to end. Alice is marked Certified Lead with an empty ladder — the
        seeded state the founder actually met."""
        with session_factory() as session:
            row = session.get(ConsultantORM, alice.stored.id)
            assert row is not None
            row.assessor_level = AssessorLevel.CERTIFIED_LEAD.value
            session.add(row)
            session.commit()

        performance = client.get(
            f"/bench/performance/{alice.stored.id}", headers=auth_header(alice)
        ).json()
        certification = client.get(
            f"/certification/{alice.stored.id}", headers=auth_header(alice)
        ).json()

        assert performance["level"] == certification["level"] == "certified_lead"
        # Both now carry the same derivation, so neither can present it as earned.
        assert performance["earned_level"] == certification["earned_level"] == "trained"
        assert performance["level_is_evidenced"] is False
        assert certification["level_is_evidenced"] is False

    def test_an_advisor_whose_level_matches_their_evidence_reads_as_earned(
        self, client, alice: SeededConsultant
    ) -> None:
        performance = client.get(
            f"/bench/performance/{alice.stored.id}", headers=auth_header(alice)
        ).json()
        certification = client.get(
            f"/certification/{alice.stored.id}", headers=auth_header(alice)
        ).json()
        assert performance["level"] == certification["level"]
        assert performance["level_is_evidenced"] == certification["level_is_evidenced"]
