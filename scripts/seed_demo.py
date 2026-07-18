"""Seed the watermarked Revolut DEMO worked example (GRS-0117) into the configured database.

Run AFTER scripts/seed_dev.py (or against any environment that has the dev advisor):

    uv run python scripts/seed_demo.py

It creates a DEMO-provenance prospect → finalised assessment → real generated deliverables in the
dev advisor's portfolio, so a solo tester can walk the whole platform. Every surface is watermarked
"DEMO — illustrative only" (ADR-0029). The production dual-rating/committee gate is untouched.
"""

from __future__ import annotations

import os

os.environ.setdefault("GM_JWT_SECRET", "local-dev-secret-that-is-more-than-thirty-two-chars-xxxxx")
os.environ.setdefault("GM_DATABASE_URL", "sqlite+pysqlite:///./local.db")

from grassmarket.demo.revolut_demo import seed_revolut_demo_from_env  # noqa: E402


def main() -> None:
    ids = seed_revolut_demo_from_env()
    print("Seeded the Revolut DEMO worked example.")
    for k, v in ids.items():
        print(f"  {k:14} {v}")


if __name__ == "__main__":
    main()
