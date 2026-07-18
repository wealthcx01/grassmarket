"""Product-course template (GRS-0123) — the reusable spine every signed-product course fills in.

A product course always answers the same four questions, in order: **why it is relevant** to a
retail broker / wealth manager / exchange, **what white-labelling is**, the **sell/introduction
motion**, and — prominently — **how much commission the advisor earns**. The commission lesson is
GENERATED from a live `ProductCommissionCarrot` (Earnings v7, ADR-0026), never a re-typed number, so
it can't drift from the real schedule.

GRS-0124/0125/0126 instantiate this with per-product `ProductCourseSpec`s (Benzinga / Brandfetch /
OpenBB) without inventing bespoke structure. IDs are derived (uuid5) so re-seeding is idempotent.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import NAMESPACE_URL, UUID, uuid5

from bcap_contracts.commissions import ProductCommissionCarrot
from bcap_contracts.learning import (
    CertificationCredit,
    CourseModule,
    CourseTree,
    Lesson,
    LessonAuthor,
)

_NS = "grassmarket:academy:product-course"


@dataclass(frozen=True)
class ProductCourseSpec:
    """The per-product content the template needs; the commission section is resolved live, not
    here. `product_id` must match the Earnings v7 catalogue so the carrot resolves."""

    product_id: str
    slug: str
    display_name: str
    relevance: str
    white_label: str
    sell_motion: str


def _id(slug: str, kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{_NS}:{slug}:{kind}:{key}")


def _bps_pct(bps: int) -> str:
    """A basis-point rate as a human percentage (1500 → '15%', 375 → '3.75%')."""
    return f"{bps / 100:g}%"


def _commission_body(carrot: ProductCommissionCarrot) -> str:
    """The commission section, generated from the LIVE carrot — the £ carrot that motivates."""
    ex = carrot.example_deal.amount_minor // 100
    y1 = carrot.yr1_commission.amount_minor // 100
    y2 = carrot.yr2_commission.amount_minor // 100
    return (
        f"You earn **{_bps_pct(carrot.yr1_bps)}** on {carrot.name} in Year 1 and "
        f"**{_bps_pct(carrot.yr2_bps)}** in Year 2, for {carrot.window_months} months from sale "
        f"(the attribution window). Worked example on an illustrative £{ex:,} first-year deal: "
        f"£{y1:,} in Year 1, then £{y2:,} in Year 2. These figures are read live from the Earnings "
        f"v7 schedule ({carrot.schedule_version}) — never a typed-in number, so the carrot always "
        f"matches the real rate. Sold as a fix for an assessment-identified gap, or as a "
        f"commission product in its own right."
    )


def build_product_course(
    spec: ProductCourseSpec,
    carrot: ProductCommissionCarrot,
    checks: dict[str, tuple[str, str]] | None = None,
) -> CourseTree:
    """Assemble a product course from its spec + the live commission carrot. The `carrot.product_id`
    must match the spec (the caller resolves the carrot for this product) — the four sections come
    out in a fixed order every time, so the template is reusable across products. `checks` maps a
    lesson key → (comprehension question, model answer) for the active-recall gate (GRS-0140)."""
    if carrot.product_id != spec.product_id:
        raise ValueError(
            f"carrot is for {carrot.product_id!r}, not this course's product {spec.product_id!r}."
        )

    checks = checks or {}
    sections = (
        ("relevance", "Why it's relevant", spec.relevance),
        ("white-label", "What white-labelling is", spec.white_label),
        ("sell-motion", "The sell motion", spec.sell_motion),
        ("commission", "How much you earn", _commission_body(carrot)),
    )
    lessons = tuple(
        Lesson(
            id=_id(spec.slug, "lesson", key),
            title=title,
            body=body,
            order=order,
            author=LessonAuthor.HUMAN,
            drill_topics=(f"product:{spec.product_id}:{key}",),
            measurement=None,
            check_question=checks.get(key, (None, None))[0],
            check_answer=checks.get(key, (None, None))[1],
        )
        for order, (key, title, body) in enumerate(sections)
    )
    module = CourseModule(
        id=_id(spec.slug, "module", "core"),
        title=f"{spec.display_name} — sell it",
        order=0,
        lessons=lessons,
    )
    return CourseTree(
        title=f"{spec.display_name} — product course",
        summary=(
            f"Sell {spec.display_name}: why it's relevant across retail brokerage, wealth, and "
            f"exchange; what white-labelling is; the sell motion; and how much commission you earn "
            f"(live from the Earnings v7 schedule)."
        ),
        certification_credit=CertificationCredit.NONE,
        modules=(module,),
    )
