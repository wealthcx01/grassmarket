"""Publish the authored Academy catalog into the configured database (GRS-0158).

Idempotent and PRODUCTION-safe: it ensures a dedicated non-login system admin (authoring is
admin-gated, ADR-0028) and publishes every seeded course + practice scenario via
``seed_academy_content``. It contains NO demo prospect/assessment data (that is
``scripts/seed_dev.py``), so it is safe to run against prod.

The app also runs this at boot when ``GM_SEED_ACADEMY_ON_BOOT`` is set; this script is the
manual/one-off equivalent (e.g. to backfill an already-running environment).

Run:  GM_DATABASE_URL=... uv run python scripts/seed_academy.py
"""

from __future__ import annotations

from grassmarket.config import get_settings
from grassmarket.data.database import make_engine, make_session_factory, run_migrations
from grassmarket.workbench.content.seed import seed_academy


def main() -> None:
    settings = get_settings()
    engine = make_engine(settings.database_url)
    run_migrations(engine)
    seed_academy(make_session_factory(engine))
    print("Academy catalog seeded (courses + practice scenarios).")


if __name__ == "__main__":
    main()
