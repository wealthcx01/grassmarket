"""Deterministic wizard-input suggester (GRS-0101, ADR-0032).

Proposals over an injectable port. `HeuristicWizardSuggester` derives suggestions from the current
`AssessmentDocument` + the registry — offline, testable, and the seam a Claude Agent SDK adapter
drops into later behind the same `WizardSuggester` Protocol. It proposes INPUTS, never scores (the
engine is untouched, CLAUDE.md #2), references only registry-valid keys (fail-loud, #3), and only
ever targets UNSET fields — it never overwrites an advisor's rating. Nothing here commits anything;
the advisor's explicit accept/edit in the UI is the gate (ADR-0032), and an accepted value still
flows through the §9 dual-rating and §8 committee gates before any client-facing output.
"""

from __future__ import annotations

from typing import Protocol

from bcap_contracts.assessments import AssessmentDocument
from bcap_contracts.common import StrengthRating
from bcap_contracts.registry import Registry
from bcap_contracts.wizard import WizardSuggestion, WizardSuggestionKind

from grassmarket.assessments.service import scoreability_blockers

SUGGESTER_VERSION = "heuristic-v1"

# A "strong" advantage — worth checking that something defends it.
_STRONG_BENEFIT = frozenset({StrengthRating.ESTABLISHED, StrengthRating.WIDE})

# Keep the panel calm: cap each kind so suggestions read as help, not noise.
_MAX_CONSISTENCY = 3
_MAX_UNRATED = 3


class WizardSuggester(Protocol):
    """The port the suggestion service depends on — never a concrete SDK (ADR-0032)."""

    version: str

    def suggest(
        self, document: AssessmentDocument, registry: Registry
    ) -> list[WizardSuggestion]: ...


class HeuristicWizardSuggester:
    """The shipped deterministic suggester."""

    version = SUGGESTER_VERSION

    def suggest(self, document: AssessmentDocument, registry: Registry) -> list[WizardSuggestion]:
        out: list[WizardSuggestion] = []
        out.extend(self._coverage(document, registry))
        out.extend(self._power_consistency(document, registry))
        out.extend(self._unrated_nudge(document, registry))
        return out

    # --- guidance: what stands between the advisor and a live score --------------------
    def _coverage(self, document: AssessmentDocument, registry: Registry) -> list[WizardSuggestion]:
        blockers = scoreability_blockers(document, registry)
        if not blockers:
            return []
        return [
            WizardSuggestion(
                id="coverage:scoreable",
                kind=WizardSuggestionKind.GUIDANCE,
                step="summary",
                title="A few inputs stand between you and a live score",
                rationale=" ".join(blockers),
            )
        ]

    # --- guidance: a strong benefit with no barrier is worth a re-check ----------------
    def _power_consistency(
        self, document: AssessmentDocument, registry: Registry
    ) -> list[WizardSuggestion]:
        names = {p.key: p.name for p in registry.powers}
        out: list[WizardSuggestion] = []
        for p in document.powers:
            if p.benefit in _STRONG_BENEFIT and p.barrier is StrengthRating.NONE:
                name = names.get(p.power_key, p.power_key)
                out.append(
                    WizardSuggestion(
                        id=f"consistency:power:{p.power_key}",
                        kind=WizardSuggestionKind.GUIDANCE,
                        step="powers",
                        power_key=p.power_key,
                        title=f"Re-check the barrier on {name}",
                        rationale=(
                            f"You rated the benefit {p.benefit.value} but the barrier None — a "
                            "durable advantage usually has something defending it. Worth a look."
                        ),
                    )
                )
            if len(out) >= _MAX_CONSISTENCY:
                break
        return out

    # --- guidance: finish a partly-rated module — WITHOUT anchoring a level ------------
    def _unrated_nudge(
        self, document: AssessmentDocument, registry: Registry
    ) -> list[WizardSuggestion]:
        """When a module is partly rated, nudge the advisor to finish it — but propose NO value.
        Pre-planting the module's modal level would anchor an unrated subcomponent toward the herd,
        and ATLAS is bottleneck-sensitive (the weakest subcomponent drives the module score), so an
        anchor would inflate the score and mask the binding constraint the methodology exists to
        surface. Guidance only: rate each on its own evidence (GRS-0136, ADR-0032 amendment)."""
        present: dict[str, set[str]] = {}
        rated: dict[str, int] = {}
        for s in document.subcomponents:
            present.setdefault(s.module_key, set()).add(s.subcomponent_key)
            if s.level is not None:  # a rated (not N/A, not blank) subcomponent
                rated[s.module_key] = rated.get(s.module_key, 0) + 1

        out: list[WizardSuggestion] = []
        for module in registry.modules:
            if rated.get(module.key, 0) < 2:  # only once a real rating pattern exists
                continue
            here = present.get(module.key, set())
            unrated = [sc for sc in module.subcomponents if sc.key not in here]
            if not unrated:
                continue
            n = len(unrated)
            out.append(
                WizardSuggestion(
                    id=f"unrated:{module.key}",
                    kind=WizardSuggestionKind.GUIDANCE,
                    step="infrastructure",
                    module_key=module.key,
                    title=f"{n} subcomponent{'s' if n != 1 else ''} still unrated in {module.name}",
                    rationale=(
                        "Assess each on its own evidence — don't copy the module's pattern. The "
                        "weakest subcomponent drives the module score, so a real weak point is the "
                        "signal that matters most."
                    ),
                )
            )
            if len(out) >= _MAX_UNRATED:
                break
        return out


def suggest_for(
    document: AssessmentDocument,
    registry: Registry,
    suggester: WizardSuggester | None = None,
) -> list[WizardSuggestion]:
    """Run the (injectable) suggester over a document. Defaults to the deterministic heuristic."""
    return (suggester or HeuristicWizardSuggester()).suggest(document, registry)
