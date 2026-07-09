"""ADR-0002 tests — score and currency never mix; the category error is unrepresentable.

The prototype computed `LV = κ·Δq/(1+r) − cost`, subtracting pounds from score-points. Here that
is structurally impossible: `Money` needs an assumption register to exist, currency arithmetic is
same-currency-only, triad outputs are ordinal enums, and — the key guarantee — no function in the
contracts or the (Loop 1) engine takes both a `Score` and a `Money`.
"""

from __future__ import annotations

import ast
import re
from enum import Enum
from pathlib import Path

import pytest
from bcap_contracts.assessments import TriadResult
from bcap_contracts.common import StrengthRating
from bcap_contracts.money import Currency, Money
from pydantic import ValidationError

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCAN_DIRS = [
    _REPO_ROOT / "packages" / "bcap_contracts" / "src" / "bcap_contracts",
    _REPO_ROOT / "src" / "grassmarket" / "atlas",
    # The value layer is exactly where prototype D2 mixed pounds and score-points — scan it hardest.
    _REPO_ROOT / "src" / "grassmarket" / "value",
    # The assessment services orchestrate scoring + scenario ΔV; keep them Money-free too.
    _REPO_ROOT / "src" / "grassmarket" / "assessments",
    # The pipeline tree is where Money entered (GRS-0012 recovery fees) alongside the score-free
    # forecast — the boundary must hold across both, so scan the whole subtree.
    _REPO_ROOT / "src" / "grassmarket" / "pipeline",
]
_SCORE = re.compile(r"\bScore\b")
_MONEY = re.compile(r"\bMoney\b")


def test_money_requires_assumption_register() -> None:
    with pytest.raises(ValidationError):
        Money(amount_minor=1000, currency=Currency.GBP)  # type: ignore[call-arg]


def test_money_rejects_empty_assumption_ref() -> None:
    with pytest.raises(ValidationError):
        Money(amount_minor=1000, currency=Currency.GBP, assumption_register_ref="")


def test_money_same_currency_add() -> None:
    a = Money(amount_minor=1000, currency=Currency.GBP, assumption_register_ref="AR-1")
    b = Money(amount_minor=500, currency=Currency.GBP, assumption_register_ref="AR-2")
    assert a.add(b).amount_minor == 1500


def test_money_cross_currency_add_refused() -> None:
    a = Money(amount_minor=1000, currency=Currency.GBP, assumption_register_ref="AR-1")
    b = Money(amount_minor=500, currency=Currency.USD, assumption_register_ref="AR-2")
    with pytest.raises(ValueError):
        a.add(b)


def test_triad_rating_is_ordinal_enum_not_float() -> None:
    assert issubclass(StrengthRating, Enum)
    assert not issubclass(StrengthRating, float)
    result = TriadResult(
        dimension=__import__(
            "bcap_contracts.common", fromlist=["TriadDimension"]
        ).TriadDimension.DEFENCE_VALUE,
        rating=StrengthRating.ESTABLISHED,
        rationale="Barrier evidence across all seven powers.",
    )
    assert result.rating is StrengthRating.ESTABLISHED


def test_no_function_takes_both_score_and_money() -> None:
    """Structural guarantee: scan every function signature in the contracts and the engine; none
    may name both a Score and a Money. This is the ADR-0002 boundary enforced in code, not prose."""
    offenders: list[str] = []
    for base in _SCAN_DIRS:
        for path in base.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                annotations: list[str] = []
                for arg in [*node.args.args, *node.args.kwonlyargs, *node.args.posonlyargs]:
                    if arg.annotation is not None:
                        annotations.append(ast.get_source_segment(source, arg.annotation) or "")
                if node.returns is not None:
                    annotations.append(ast.get_source_segment(source, node.returns) or "")
                blob = " ".join(annotations)
                if _SCORE.search(blob) and _MONEY.search(blob):
                    offenders.append(f"{path.name}::{node.name}")
    assert offenders == [], f"ADR-0002 violation — signatures mix Score and Money: {offenders}"
