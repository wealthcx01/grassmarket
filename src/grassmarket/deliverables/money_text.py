"""Currency display for the deliverable layer (GRS-0016, ADR-0002).

Formats a `Money` for the page. Lives beside `uncertainty_text` (the score-domain display helper)
but is kept in its own module so the boundary is visible: nothing here takes a `Score`, and the
value bridge's figures are the only thing it renders. Amounts are exact integer minor units; we
display whole major units with a thousands separator — an NPV estimate does not earn a pretend
pence of precision.
"""

from __future__ import annotations

from bcap_contracts.money import Currency, Money

_SYMBOL = {Currency.GBP: "£", Currency.USD: "$", Currency.EUR: "€"}


def format_money(money: Money) -> str:
    """Render a `Money` as e.g. ``£1,234,567``. Negative amounts print a leading minus.

    The sign is taken from the ROUNDED whole-pound value, so a sub-pound amount that rounds to
    zero prints ``£0`` and never a misleading ``-£0``.
    """
    symbol = _SYMBOL[money.currency]
    whole = round(
        money.amount_minor / 100
    )  # whole major units — an estimate earns no pretend pence
    sign = "-" if whole < 0 else ""
    return f"{sign}{symbol}{abs(whole):,}"
