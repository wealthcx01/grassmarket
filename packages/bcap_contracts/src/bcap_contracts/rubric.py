"""The rubric anchor library — the assessor guidance content (Methodology §4).

One anchor per subcomponent × maturity level: 51 × 4 = **204** anchors. Each anchor follows the §4
template — a behavioural (BARS-style) statement, 2–4 required-evidence artifacts, 1–2 differentiator
questions, and misgrading notes. This module is the contract-typed **storage + loader**; the content
itself is John's to author and ratify (it ships `draft-pending-ratification`).

Fail-loud the ADR-0001 way. Every (subcomponent, level) pair is **either present or EXPLICITLY
marked TODO** — a silently missing anchor is a load-time refusal, never an empty string masquerading
as content. An unknown subcomponent key is a refusal. An "authored" anchor with an empty statement
is a refusal. Nothing is fabricated or defaulted around.
"""

from __future__ import annotations

import functools
from enum import StrEnum
from importlib import resources
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, model_validator

from bcap_contracts.common import MaturityLevel
from bcap_contracts.registry import Registry, UnknownKeyError, load_registry


class RubricError(Exception):
    """Base class for rubric-library failures. Never swallowed."""


class MissingAnchorError(RubricError):
    """A (subcomponent, level) pair has no anchor and was not explicitly marked TODO. Refusal."""

    def __init__(self, missing: set[tuple[str, str]]) -> None:
        self.missing = missing
        shown = ", ".join(f"{s}/{lvl}" for s, lvl in sorted(missing))
        super().__init__(
            f"The rubric library is incomplete — {len(missing)} (subcomponent, level) pair(s) have "
            f"neither an anchor nor an explicit TODO: {shown}. Every pair must be present or "
            f"explicitly absent (ADR-0001)."
        )


class DuplicateAnchorError(RubricError):
    """The same (subcomponent, level) pair is defined more than once. Refusal, never last-wins."""


class AnchorStatus(StrEnum):
    """The authoring state of an anchor — so 'not yet written' is a first-class, explicit state,
    never a silent gap or a fabricated-looking placeholder."""

    AUTHORED = "authored"  # full §4 anchor, ratified-quality content
    DRAFT = "draft"  # drafted (first pass / from the subcomponent label), not ratified
    TODO = "todo"  # explicitly not yet authored — content empty on purpose


class RubricAnchor(BaseModel):
    """One subcomponent × level anchor (§4 template)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subcomponent_key: str
    level: MaturityLevel
    status: AnchorStatus
    # behavioural, BARS-style; REQUIRED for authored/draft, empty for todo
    statement: str = ""
    required_evidence: tuple[str, ...] = ()  # 2–4 artifacts that must exist to award the level
    # 1–2 questions separating this level from its neighbours
    differentiator_questions: tuple[str, ...] = ()
    misgrading_notes: str | None = None  # known over/under-rating traps (updated after calibration)

    @model_validator(mode="after")
    def _content_matches_status(self) -> RubricAnchor:
        where = f"{self.subcomponent_key}/{self.level.value}"
        if (
            self.status in (AnchorStatus.AUTHORED, AnchorStatus.DRAFT)
            and not self.statement.strip()
        ):
            raise RubricError(
                f"A {self.status.value} anchor ({where}) must carry a non-empty statement — a "
                f"silently empty anchor is a refusal (ADR-0001)."
            )
        if self.status is AnchorStatus.AUTHORED and not (
            self.required_evidence and self.differentiator_questions and self.misgrading_notes
        ):
            raise RubricError(
                f"An authored anchor ({where}) must carry the full §4 template: required evidence, "
                f"differentiator question(s), and misgrading notes."
            )
        if self.status is AnchorStatus.TODO and (
            self.statement.strip() or self.required_evidence or self.differentiator_questions
        ):
            raise RubricError(
                f"A todo anchor ({where}) is an explicit placeholder and must carry no content — "
                f"draft or authored content must declare its real status, never hide behind todo."
            )
        return self


class RubricLibrary(BaseModel):
    """The whole 204-anchor library. Construction checks each anchor is well-formed;
    :meth:`validate_against` checks completeness against the registry (all 204 present, keys legal,
    no duplicates) — the ADR-0001 load-time gate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: str
    anchors: tuple[RubricAnchor, ...]

    def get(self, subcomponent_key: str, level: MaturityLevel) -> RubricAnchor:
        for a in self.anchors:
            if a.subcomponent_key == subcomponent_key and a.level is level:
                return a
        raise MissingAnchorError({(subcomponent_key, level.value)})

    def for_subcomponent(self, subcomponent_key: str) -> tuple[RubricAnchor, ...]:
        return tuple(
            sorted(
                (a for a in self.anchors if a.subcomponent_key == subcomponent_key),
                key=lambda a: a.level.rank,
            )
        )

    def authored_count(self) -> int:
        return sum(1 for a in self.anchors if a.status is AnchorStatus.AUTHORED)

    def validate_against(self, registry: Registry) -> None:
        legal = registry.all_subcomponent_keys()
        present: set[tuple[str, str]] = set()
        for a in self.anchors:
            if a.subcomponent_key not in legal:
                raise UnknownKeyError("subcomponent", a.subcomponent_key, legal)
            key = (a.subcomponent_key, a.level.value)
            if key in present:
                raise DuplicateAnchorError(
                    f"Duplicate anchor for {a.subcomponent_key}/{a.level.value}."
                )
            present.add(key)
        required = {(s, lvl.value) for s in legal for lvl in MaturityLevel}
        missing = required - present
        if missing:
            raise MissingAnchorError(missing)


# --- Canonical loader -------------------------------------------------------------------


def _load_yaml(filename: str) -> Any:
    data_pkg = resources.files("bcap_contracts").joinpath("registry_data")
    with resources.as_file(data_pkg.joinpath(filename)) as path:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)


@functools.lru_cache(maxsize=1)
def load_rubric_library() -> RubricLibrary:
    """Load and validate the canonical rubric library, once, cached.

    The YAML lists ``anchors`` (authored/draft entries in full) and, compactly, the pairs that are
    explicitly not yet written: ``todo_all_levels`` (subcomponents where all four levels are TODO)
    and an optional ``todo`` list of individual {subcomponent, level} pairs. The loader expands
    those into real TODO anchors, then validates completeness against the registry — fail-loud."""
    raw = _load_yaml("rubric_anchors.yaml") or {}
    registry = load_registry()

    anchors: list[RubricAnchor] = [
        RubricAnchor(
            subcomponent_key=a["subcomponent_key"],
            level=MaturityLevel(a["level"]),
            status=AnchorStatus(a["status"]),
            statement=a.get("statement", ""),
            required_evidence=tuple(a.get("required_evidence", ())),
            differentiator_questions=tuple(a.get("differentiator_questions", ())),
            misgrading_notes=a.get("misgrading_notes"),
        )
        for a in raw.get("anchors", [])
    ]
    for sub_key in raw.get("todo_all_levels", []):
        anchors.extend(
            RubricAnchor(subcomponent_key=sub_key, level=lvl, status=AnchorStatus.TODO)
            for lvl in MaturityLevel
        )
    for pair in raw.get("todo", []):
        anchors.append(
            RubricAnchor(
                subcomponent_key=pair["subcomponent_key"],
                level=MaturityLevel(pair["level"]),
                status=AnchorStatus.TODO,
            )
        )

    library = RubricLibrary(status=_require_status(raw), anchors=tuple(anchors))
    library.validate_against(registry)
    return library


def _require_status(raw: dict[str, Any]) -> str:
    if not isinstance(raw, dict) or "status" not in raw:
        raise RubricError("rubric_anchors.yaml must declare a `status` (no default — ADR-0001).")
    return raw["status"]
