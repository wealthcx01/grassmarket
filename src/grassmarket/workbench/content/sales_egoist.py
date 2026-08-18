"""Sales Egoist course assembly — the Academy's mandatory doctrine course (GRS-0122, ADR-0028).

**This module is now assembly only.** The course content lives in `sales_egoist_slides.py` — eight
sections rebuilt to the GRS-0215 depth standard (GRS-0218), 177 slides, one section test each, every
lesson citing the committed source under `data/reference/sales-egoist/`.

The eight paragraph-lessons that used to live here were **deleted on 2026-08-01**, the same decision
OpenBB's and Benzinga's superseded modules got on 2026-07-30. They were written in July 2026 from a
paraphrase of material that was not in the repository, and they are exactly what the founder was
describing:

    "You have done nothing but generically summarize some of the content I gave you. I am beyond
    disappointed."

Keeping them alongside the rebuild would have meant that sentence still shipped. What they contained
that the rebuild does NOT simply inherit is recorded here rather than lost: their strongest idea was
that *the assessment is the demo* — a live Platform Power read that lets the client watch their own
moat get measured — and that survives, developed, as section 8's treatment of the assessment's three
jobs in a campaign. Their weakest was treating "Total Account Awareness" as a closing technique; the
curriculum has it as conviction VIII, a continuous reading of the whole account, and section 7 now
teaches it that way.

`mandatory_first` stays True, and that is now the right answer rather than an embarrassment.
GRS-0239
scope 5 proposed moving the flag to the strongest rebuilt course because "Start here" pointed at the
worst content we had; rebuilding this course fixes the cause instead, so the flag can stay where the
Academy's design always wanted it.

IDs are derived (uuid5) from a stable namespace so re-seeding is idempotent — the same lesson keeps
the same id across every publish.
"""

from __future__ import annotations

from bcap_contracts.learning import CertificationCredit, CourseTree

from grassmarket.workbench.content.sales_egoist_slides import rebuilt_sections

SALES_EGOIST_SLUG = "sales-egoist"


def sales_egoist_course() -> CourseTree:
    """Build the Sales Egoist course: eight sections rebuilt to the GRS-0215 depth standard, each
    one lesson of 20 to 40 slides with a section test the advisor passes before the next opens.

    No certification credit by itself — the certification sits on top in GRS-0127.
    """
    return CourseTree(
        title="The Sales Egoist",
        summary=(
            "The Bruntsfield sales doctrine, from the Master Curriculum: eight convictions for "
            "capital-markets technology selling, the armoury they draw on, the dated catalysts "
            "they "
            "ride, and the campaign that runs all eight against a single account — with the "
            "Platform Power assessment placed inside it."
        ),
        certification_credit=CertificationCredit.NONE,
        mandatory_first=True,
        modules=rebuilt_sections(),
    )
