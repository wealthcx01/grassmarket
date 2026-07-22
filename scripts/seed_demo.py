"""Seed a demo instance: the full brokerage showcase (GRS-0159) into the configured database.

One command populates a clean environment with the showcase brokerages (Revolut, Hargreaves
Lansdown, WeBull) as complete, finalised DEMO assessments — pipeline chain, real generated
deliverables, engagements, and the illustrative Year-1 product commissions, so /earnings shows a
populated statement. Idempotent: re-running skips any brokerage already seeded.

Run AFTER scripts/seed_dev.py (or standalone — it bootstraps the demo advisor + admin if absent):

    uv run python scripts/seed_demo.py

Every record is DEMO-provenanced (ADR-0029): watermarked, self-approvable, excluded from
benchmarks. The production dual-rating/committee gate is untouched. The original thin Revolut
worked example (GRS-0117) remains available as `grassmarket.demo.revolut_demo`.
"""

from __future__ import annotations

import os

os.environ.setdefault("GM_JWT_SECRET", "local-dev-secret-that-is-more-than-thirty-two-chars-xxxxx")
os.environ.setdefault("GM_DATABASE_URL", "sqlite+pysqlite:///./local.db")

from grassmarket.config import get_settings  # noqa: E402
from grassmarket.data.database import (  # noqa: E402
    make_engine,
    make_session_factory,
    run_migrations,
)
from grassmarket.demo.brokerage_showcase import seed_brokerage_showcase  # noqa: E402


def main() -> None:
    settings = get_settings()
    engine = make_engine(settings.database_url)
    run_migrations(engine)
    session_factory = make_session_factory(engine)

    results = seed_brokerage_showcase(
        session_factory, engine, settings, owner_email="advisor@bruntsfieldcapital.com"
    )
    print("Brokerage showcase demo seed:")
    for r in results:
        line = f"  {r['subject']:22} {r['status']}"
        if "assessment_id" in r:
            line += f"  assessment={r['assessment_id']}  sold={r['product_sold']}"
        print(line)


if __name__ == "__main__":
    main()
