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

    def __post_init__(self) -> None:
        if len(self.labels) != len(self.values):
            raise ValueError("labels and values must be the same length.")


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

    scored = [(m.name, to_display(m.q_m)) for m in result.modules if m.q_m is not None]
    module_labels = tuple(name for name, _ in scored)
    module_values = tuple(value for _, value in scored)

    composite = result.composite
    return ReportFigureData(
        maturity=Series(labels=module_labels, values=module_values),
        value_buildup=Series(
            labels=("Business", "Powers", "Infrastructure", "Platform Value"),
            values=(
                to_display(composite.b_index),
                to_display(composite.p_index),
                to_display(composite.l_index),
                to_display(composite.v_index),
            ),
        ),
        module_breakdown=Series(labels=module_labels, values=module_values),
    )
