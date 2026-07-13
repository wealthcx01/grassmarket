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


def currency_symbol(currency: Currency) -> str:
    """The display symbol for a currency. The one place other modules ask for it — no reaching
    into the private ``_SYMBOL`` table."""
    return _SYMBOL[currency]


def major_units(money: Money) -> float:
    """The amount in major units (e.g. pounds) as a float — for DISPLAY / charting only. The one
    audited spot where money crosses from exact minor units into a float; never used for arithmetic
    on money (that stays in integer minor units, ADR-0002)."""
    return money.amount_minor / 100


def format_money(money: Money) -> str:
    """Render a `Money` as e.g. ``£1,234,567``. Negative amounts print a leading minus.

    The sign is taken from the ROUNDED whole-pound value, so a sub-pound amount that rounds to
    zero prints ``£0`` and never a misleading ``-£0``.
    """
    whole = round(major_units(money))  # whole major units — an estimate earns no pretend pence
    sign = "-" if whole < 0 else ""
    return f"{sign}{currency_symbol(money.currency)}{abs(whole):,}"
