"""Bootstrap the 5 mock-advisor persona accounts on the CONFIGURED database (staging).

Idempotent on email — mirrors scripts/seed_dev.py's _ensure_consultant. Run via:
  railway run --service Postgres --environment staging -- bash -lc \
    'GM_DATABASE_URL="$DATABASE_PUBLIC_URL" GM_JWT_SECRET=x... uv run python scratch/stage/create_mock_advisors.py'
"""

from __future__ import annotations

import os

os.environ.setdefault("GM_JWT_SECRET", "local-dev-secret-that-is-more-than-thirty-two-chars-xxxxx")

from bcap_contracts.common import AssessorLevel, ConsultantTier, Role  # noqa: E402

from grassmarket.auth.security import hash_password  # noqa: E402
from grassmarket.config import get_settings  # noqa: E402
from grassmarket.data.database import make_engine, make_session_factory, run_migrations  # noqa: E402
from grassmarket.data.repository import Repository  # noqa: E402

PASSWORD = "mockadvisor-2026"  # pragma: allowlist secret  (throwaway staging personas)
PERSONAS = [
    ("priya.nair@bruntsfieldcapital.com", "Priya Nair"),
    ("tom.fielding@bruntsfieldcapital.com", "Tom Fielding"),
    ("marcus.bell@bruntsfieldcapital.com", "Marcus Bell"),
    ("elena.rossi@bruntsfieldcapital.com", "Elena Rossi"),
    ("james.okafor@bruntsfieldcapital.com", "James Okafor"),
]


def main() -> None:
    settings = get_settings()
    engine = make_engine(settings.database_url)
    run_migrations(engine)
    session = make_session_factory(engine)()
    try:
        repo = Repository(session)
        for email, name in PERSONAS:
            if repo.get_consultant_by_email(email) is not None:
                print(f"  {email:44} exists")
                continue
            repo.create_consultant(
                email=email,
                full_name=name,
                hashed_password=hash_password(PASSWORD),
                role=Role.CONSULTANT,
                tier=ConsultantTier.CONSULTANT,
                assessor_level=AssessorLevel.CERTIFIED_LEAD,
            )
            session.commit()
            print(f"  {email:44} created")
    finally:
        session.close()


if __name__ == "__main__":
    main()
