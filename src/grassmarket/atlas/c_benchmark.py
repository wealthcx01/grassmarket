"""C benchmark ingestion + peer comparison (ADR-0023 / GRS-0084).

The C (Customer-Proposition) benchmark is a NAMED peer set — public brokerage apps scored against
the C rubric — so a subject's C index ships with peer context on day one. Two honest boundaries:

- **No client data committed.** The seven scored reviews are the founder's IP (read reference-only,
  never committed). This module is the *ingestion machinery*: the operator feeds each review's C
  ratings in, they are scored + validated against the C registry (fail-loud, ADR-0001), and the
  result is proposed as an UNAPPROVED benchmark row. The real scores never live in the repo.
- **AI proposes, humans approve (ADR-0009 / CLAUDE.md #8).** Ingestion only ever *proposes* a row;
  a consultant records the approval that makes it live (the repository enforces this).
"""

from __future__ import annotations

from dataclasses import dataclass

from bcap_contracts.assessments import CoefficientSet, SubcomponentRating
from bcap_contracts.registry import Registry

from grassmarket.atlas.engine import score_customer

# The seven public-app peers already scored against the C rubric (GRS-0084). Names are public
# products, not client data. The nine currently-unscored apps (Capital, Charles Schwab, EFG Hermes,
# EasyEquities, Futu, Hapi, Robinhood, Trii, eToro) are the documented NEXT content batch, not here.
C_BENCHMARK_PEER_ROSTER: tuple[str, ...] = (
    "Saxo",
    "Interactive Brokers",
    "Lightyear",
    "Revolut",
    "Trading 212",
    "WeBull",
    "Hargreaves Lansdown",
)


@dataclass(frozen=True)
class CBenchmarkProposal:
    """A scored-but-unapproved C benchmark row, ready to hand to the repository's approval gate.
    Carries the deterministic C index and per-C-module q_m — nothing that is not derivable from the
    validated ratings, and no review content."""

    peer_name: str
    profile_key: str
    c_index: float
    module_scores: dict[str, float]
    methodology_version: str
    coefficient_version: str
    source_ref: str | None


def c_benchmark_proposal(
    peer_name: str,
    profile_key: str,
    c_subcomponents: tuple[SubcomponentRating, ...],
    coefficients: CoefficientSet,
    registry: Registry,
    *,
    source_ref: str | None = None,
) -> CBenchmarkProposal:
    """Score one peer's C ratings into a benchmark proposal (UNAPPROVED — the repository gates it).

    Fail-loud: `score_customer` requires a C-scoring coefficient set and EXACT C coverage, so an
    unknown or missing C key aborts here — never a silent drop (ADR-0001). `module_scores` are the
    per-module q_m; a fully-unassessed module contributes no key (excluded, never zero-filled — D9).
    """
    customer = score_customer(c_subcomponents, coefficients, registry)
    module_scores = {m.key: m.q_m for m in customer.modules if m.q_m is not None}
    return CBenchmarkProposal(
        peer_name=peer_name,
        profile_key=profile_key,
        c_index=customer.value,
        module_scores=module_scores,
        methodology_version=coefficients.methodology_version,
        coefficient_version=coefficients.version,
        source_ref=source_ref,
    )


@dataclass(frozen=True)
class CPeerComparison:
    """Where a subject's C index sits among its (approved, same-profile) peers."""

    subject_c: float
    peer_count: int
    ahead_of: int  # peers the subject beats
    percentile: float | None  # ahead_of / peer_count; None when there are no peers


def c_peer_comparison(subject_c: float, peer_c_indices: list[float]) -> CPeerComparison:
    """Position a subject's C index against a list of peer C indices. Percentile is the share of
    peers the subject beats (None when the peer set is empty: first-class, never a fabricated 0)."""
    n = len(peer_c_indices)
    ahead = sum(1 for p in peer_c_indices if p < subject_c)
    return CPeerComparison(
        subject_c=subject_c,
        peer_count=n,
        ahead_of=ahead,
        percentile=(ahead / n) if n else None,
    )
