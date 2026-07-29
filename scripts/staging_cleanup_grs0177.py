"""Clean the duplicate and stray records the founder found on staging (GRS-0177).

This does NOT run automatically anywhere. It prints what it would delete and exits; deleting
needs an explicit `--execute`. That asymmetry is deliberate: the fix for a confusing demo must not
itself be capable of quietly removing an advisor's real work.

    uv run python scripts/staging_cleanup_grs0177.py --owner advisor@bruntsfield.capital
    uv run python scripts/staging_cleanup_grs0177.py --owner advisor@bruntsfield.capital --execute

Every lookup and deletion goes through `Repository`, so owner-scoping is enforced the same way it
is for a request. Nothing is matched by a wildcard; each rule below names its criteria.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from uuid import UUID

from bcap_contracts.assessments import AssessmentState, RecordProvenance

from grassmarket.config import get_settings
from grassmarket.data.database import make_engine, make_session_factory
from grassmarket.data.repository import Principal, Repository

# The stray record the founder found: finalised at 2% coverage, which is not a usable assessment
# of anything. Anything at or below this is a mis-click rather than work.
STRAY_COVERAGE = 0.05


@dataclass(frozen=True)
class Candidate:
    assessment_id: UUID
    subject: str
    provenance: str
    state: str
    coverage: float | None
    reason: str

    def describe(self) -> str:
        cov = "—" if self.coverage is None else f"{self.coverage * 100:.0f}%"
        return (
            f"  {self.subject:<28} {self.provenance:<11} {self.state:<10} "
            f"coverage {cov:<5} {self.assessment_id}\n      → {self.reason}"
        )


def find_candidates(repo: Repository, principal: Principal) -> list[Candidate]:
    """The three conditions, each stated explicitly rather than inferred from a pattern."""
    entries = repo.list_brokerage_portfolio(principal)
    candidates: list[Candidate] = []

    # 1. Drafts that were never really started. A 0%-coverage draft is a mis-click.
    for entry in entries:
        if entry.state is not AssessmentState.FINALISED and (entry.coverage or 0) <= 0.0:
            candidates.append(
                Candidate(
                    assessment_id=entry.assessment_id,
                    subject=entry.subject,
                    provenance=entry.provenance.value,
                    state=entry.state.value,
                    coverage=entry.coverage,
                    reason="draft with nothing assessed",
                )
            )

    # 2. Records finalised on almost no evidence. A locked score at 2% coverage is not a score.
    for entry in entries:
        if (
            entry.state is AssessmentState.FINALISED
            and entry.coverage is not None
            and entry.coverage <= STRAY_COVERAGE
        ):
            candidates.append(
                Candidate(
                    assessment_id=entry.assessment_id,
                    subject=entry.subject,
                    provenance=entry.provenance.value,
                    state=entry.state.value,
                    coverage=entry.coverage,
                    reason=f"finalised at or below {STRAY_COVERAGE:.0%} coverage",
                )
            )

    # 3. Duplicate non-production records for a subject that ALSO has a better one. The most real
    # record is kept; only the redundant copies of the same company go. Production records are
    # never candidates, whatever else exists.
    by_subject: dict[str, list] = {}
    for entry in entries:
        by_subject.setdefault(entry.subject.strip().lower(), []).append(entry)
    rank = {RecordProvenance.PRODUCTION: 0, RecordProvenance.SANDBOX: 1, RecordProvenance.DEMO: 2}
    already = {c.assessment_id for c in candidates}
    for rows in by_subject.values():
        if len(rows) < 2:
            continue
        ordered = sorted(rows, key=lambda e: (rank.get(e.provenance, 9), -_ts(e.updated_at)))
        for entry in ordered[1:]:
            if entry.provenance is RecordProvenance.PRODUCTION or entry.assessment_id in already:
                continue
            candidates.append(
                Candidate(
                    assessment_id=entry.assessment_id,
                    subject=entry.subject,
                    provenance=entry.provenance.value,
                    state=entry.state.value,
                    coverage=entry.coverage,
                    reason=(
                        f"duplicate of the {ordered[0].provenance.value} record for this subject"
                    ),
                )
            )
    return candidates


def _ts(value) -> float:
    return value.timestamp() if hasattr(value, "timestamp") else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--owner", required=True, help="Email of the consultant whose records to clean."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete. Without this the script only reports.",
    )
    parser.add_argument(
        "--discard-scoring-runs",
        action="store_true",
        help=(
            "Also remove FINALISED demo/sandbox records together with their scoring runs. "
            "Production records are never touched, with or without this flag (ADR-0047)."
        ),
    )
    args = parser.parse_args()

    if not os.environ.get("GM_DATABASE_URL"):
        raise SystemExit("Set GM_DATABASE_URL to the environment you intend to clean.")

    factory = make_session_factory(make_engine(get_settings().database_url))
    session = factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(args.owner)
        if owner is None:
            raise SystemExit(f"No consultant found for {args.owner}.")
        principal = Principal(consultant_id=owner.id, role=owner.role)
        candidates = find_candidates(repo, principal)

        if not candidates:
            print(f"Nothing to clean for {args.owner}.")
            return 0

        print(f"{len(candidates)} record(s) matched for {args.owner}:\n")
        for candidate in candidates:
            print(candidate.describe())

        # Two things this script will not decide for you, so the list is split rather than acted
        # on wholesale. A PRODUCTION record is never deletable, whatever it looks like — retiring
        # real client work is a founder decision. A FINALISED record carries a scoring run, and
        # runs are append-only (#6); discarding one needs the operator to say so explicitly with
        # --discard-scoring-runs, which ADR-0047 confines to demo and sandbox records.
        deletable: list[Candidate] = []
        needs_decision: list[tuple[Candidate, str]] = []
        for candidate in candidates:
            if candidate.provenance == RecordProvenance.PRODUCTION.value:
                needs_decision.append((candidate, "production record — never deleted here"))
            elif candidate.state == "finalised" and not args.discard_scoring_runs:
                needs_decision.append(
                    (candidate, "finalised — re-run with --discard-scoring-runs to remove it")
                )
            else:
                deletable.append(candidate)

        if needs_decision:
            print(f"\n{len(needs_decision)} record(s) this script will NOT delete:")
            for candidate, why in needs_decision:
                print(f"  {candidate.subject:<28} {candidate.assessment_id}  → {why}")

        if not args.execute:
            print(f"\nReport only. Re-run with --execute to delete the {len(deletable)} record(s).")
            return 0

        for candidate in deletable:
            repo.delete_assessment(
                principal,
                candidate.assessment_id,
                discard_scoring_runs=args.discard_scoring_runs,
            )
        session.commit()
        print(f"\nDeleted {len(deletable)} record(s); left {len(needs_decision)} for a decision.")
        return 0
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
