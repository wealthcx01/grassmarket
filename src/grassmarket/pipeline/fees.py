"""Recovery-fee logic — eligibility + the immutability seal (GRS-0012, PRD §4).

Pure, deterministic helpers over the recovery-fee attribution: is a contract within the window, and
the content hash that makes an attribution record tamper-evident. The £ amount is `Money`
throughout; nothing here is a Score (ADR-0002 — this module sits in the AST-scanned pipeline tree).
"""

from __future__ import annotations

import hashlib
from datetime import date
from uuid import UUID

from bcap_contracts.money import Money


def is_within_attribution_window(delivered_on: date, contracted_on: date, window_days: int) -> bool:
    """Eligible iff the prospect contracted on/after delivery and within ``window_days`` of it.

    The boundary is inclusive: contracting exactly ``window_days`` days after delivery is eligible;
    one day later is not. Contracting before delivery is never eligible.
    """
    if contracted_on < delivered_on:
        return False
    return (contracted_on - delivered_on).days <= window_days


def attribution_content_hash(
    *,
    workshop_id: UUID,
    prospect_id: UUID,
    delivered_on: date,
    contracted_on: date,
    window_days: int,
    rate_ref: str,
    fee: Money,
) -> str:
    """SHA-256 over the canonical attribution fields — the immutability seal (scoring-run pattern).
    Deterministic: the same attribution always hashes the same, so a stored hash can be recomputed
    to prove the row was not altered. Cites the rate/window it used and the exact fee."""
    canonical = "|".join(
        [
            str(workshop_id),
            str(prospect_id),
            delivered_on.isoformat(),
            contracted_on.isoformat(),
            str(window_days),
            rate_ref,
            str(fee.amount_minor),
            fee.currency.value,
        ]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
