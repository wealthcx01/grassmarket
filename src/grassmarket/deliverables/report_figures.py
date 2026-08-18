"""The data behind the client report's three figures (GRS-0211/0219/0220).

Deliberately *data*, not pictures. The PDF (GRS-0219) rasterises these at print resolution; the web
page (GRS-0220) draws the same numbers as interactive SVG. One derivation means the two renditions
cannot show a client different charts of the same run — the parity GRS-0220's test asserts.

Everything here is read off a finalised run. A module with no assessed subcomponent is omitted, not
plotted at zero: an unmeasured module is not a weak one (defect D9).
"""

from __future__ import annotations

from dataclasses import dataclass

from grassmarket.deliverables.builder import DeliverableContext
from grassmarket.deliverables.uncertainty_text import to_display


@dataclass(frozen=True)
class Series:
    """One labelled series. Parallel lists so it serialises to JSON unchanged for the web."""

    labels: tuple[str, ...]
    values: tuple[float, ...]
    #: One line explaining what each entry MEANS, for the web page's hover (GRS-0233 scope 4). The
    #: cheap version of hover-to-explain, without waiting on GRS-0206's motion system. Empty when
    #: the series has no per-entry meaning to give — a composition figure's parts are explained by
    #: the caption, not one at a time.
    notes: tuple[str, ...] = ()
    #: Whether this series' ORDER carries meaning (GRS-0233 scope 2). A composition figure must
    #: render as given — sorting Business/Powers/Infrastructure/Platform Value by value destroys
    #: the build-up its caption promises. A ranked figure may be sorted weakest-first, because
    #: weakest-first is what its caption says it is.
    ordered: bool = False

    def __post_init__(self) -> None:
        if len(self.labels) != len(self.values):
            raise ValueError("labels and values must be the same length.")
        if self.notes and len(self.notes) != len(self.labels):
            raise ValueError("notes, when present, must be one per label.")


@dataclass(frozen=True)
class ReportFigureData:
    """The three figures the founder asked to keep and make more visual."""

    #: Module maturity, for the radar. Assessed modules only.
    maturity: Series
    #: How Platform Value builds up: B → P → L → V.
    value_buildup: Series
    #: Every assessed module, for the ranked breakdown.
    module_breakdown: Series


def figure_data_from_context(context: DeliverableContext) -> ReportFigureData:
    """Derive all three figures from one finalised run."""
    result = context.result

    scored = [
        (m.name, to_display(m.q_m), _module_note(m)) for m in result.modules if m.q_m is not None
    ]
    module_labels = tuple(name for name, _, _ in scored)
    module_values = tuple(value for _, value, _ in scored)
    module_notes = tuple(note for _, _, note in scored)

    composite = result.composite
    return ReportFigureData(
        maturity=Series(labels=module_labels, values=module_values, notes=module_notes),
        value_buildup=Series(
            labels=("Business", "Powers", "Infrastructure", "Platform Value"),
            values=(
                to_display(composite.b_index),
                to_display(composite.p_index),
                to_display(composite.l_index),
                to_display(composite.v_index),
            ),
            # The build-up IS the order. Rendering it by value would show four numbers and no
            # composition, which is the opposite of what its caption claims.
            ordered=True,
        ),
        module_breakdown=Series(labels=module_labels, values=module_values, notes=module_notes),
    )


def _module_note(module) -> str:  # noqa: ANN001 - ModuleResult, imported for typing only in callers
    """One line about what a module's score means, for the web page's hover.

    Coverage rather than a registry lookup: the score alone does not tell a reader how much of the
    module was actually assessed, and that is the question a client asks first when a number looks
    low. A module scored on two subcomponents of nine is a different claim from one scored on all
    nine, and the bar looks identical either way.
    """
    return (
        f"{module.name}: scored on {module.n_assessed} of {module.n_applicable} applicable "
        f"subcomponents."
    )
