"""Regression guards for the golden-master rating gate (GRS-0003 review defects A2, A6).

The gate lives in the fixture generator (a script), so it is loaded by file path. Its logic is
the draft interpretation of Methodology §5.2 that ADR-0003 formalises; GRS-0004 will re-implement
and re-test it in the engine, but these guards stop the two fixed defects from silently returning.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_golden_master.py"
_spec = importlib.util.spec_from_file_location("_gm_gate", _SCRIPT)
assert _spec and _spec.loader
_bgm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bgm)


def test_basic_band_is_reachable() -> None:
    # A2: an all-Basic module must be rated Basic, not floored at Developing.
    band, blocked, _ = _bgm._rating_gate([("Basic", "E2")], [1, 1, 1])
    assert band == "Basic"
    assert blocked is False


def test_single_basic_caps_at_developing() -> None:
    band, _, _ = _bgm._rating_gate([("Basic", "E2"), ("Advanced", "E3")], [1, 2, 3])
    assert band == "Developing"


def test_all_advanced_e3_criticals_can_be_frontier() -> None:
    band, _, _ = _bgm._rating_gate([("Advanced", "E3")], [3, 3, 4])
    assert band == "Frontier"


def test_not_assessed_critical_blocks_at_developing() -> None:
    band, blocked, _ = _bgm._rating_gate([("NOT_ASSESSED", None)], [3, 3])
    assert band == "Developing"
    assert blocked is True


def test_missing_evidence_fails_loud() -> None:
    # A6: no `ev or "E1"` default — an assessed critical without evidence must raise.
    with pytest.raises(ValueError):
        _bgm._rating_gate([("Advanced", None)], [3])
