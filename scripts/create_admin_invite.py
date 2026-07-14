"""One-off production bootstrap: mint an ADMIN invitation for the very first account.

Signup is invitation-only and the invite flow needs an existing consultant as the inviter — a
chicken-and-egg for account #1. This creates an admin-role invitation using a system sentinel as
the inviter (``invited_by_consultant_id`` carries no FK), then prints the raw token. The first admin
then accepts it through the normal ``/auth/accept-invitation`` flow, choosing their own password —
so no password is ever set or transmitted by this script.

Run inside the deployed container (which has the internal DATABASE_URL + secrets):

    railway ssh --service grassmarket-api -- bash -lc \\
      "cd /app && ADMIN_INVITE_EMAIL=you@example.com uv run python scripts/create_admin_invite.py"
"""

from __future__ import annotations

import os
from uuid import UUID

from bcap_contracts.common import ConsultantTier, Role

from grassmarket.auth.service import AuthService
from grassmarket.config import get_settings
from grassmarket.data.database import make_engine, make_session_factory
from grassmarket.data.repository import Repository

# The very first invitation has no real inviter; invited_by_consultant_id has no FK, so a sentinel
# is safe and self-documenting (matches the system-actor pattern used for audit events).
_SYSTEM_ACTOR = UUID(int=0)


def main() -> None:
    email = os.environ.get("ADMIN_INVITE_EMAIL")
    if not email:
        raise SystemExit("Set ADMIN_INVITE_EMAIL to the admin's email address.")

    settings = get_settings()
    engine = make_engine(settings.database_url)
    session_factory = make_session_factory(engine)
    session = session_factory()
    try:
        repo = Repository(session)
        if repo.get_consultant_by_email(email) is not None:
            raise SystemExit(f"A consultant already exists for {email}; nothing to do.")
        token = AuthService(repo, settings).create_invitation(
            inviter_id=_SYSTEM_ACTOR,
            email=email,
            role=Role.ADMIN,
            tier=ConsultantTier.CONSULTANT,
        )
        session.commit()
    finally:
        session.close()

    print(f"ADMIN_INVITE_EMAIL: {email}")
    print(f"ADMIN_INVITE_TOKEN: {token}")
    print(
        "Accept it (within the invite TTL) via POST /auth/accept-invitation with your own password."
    )


if __name__ == "__main__":
    main()
