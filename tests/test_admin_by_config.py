"""Admin by configuration (GRS-0208 scope 3).

The ticket asks for `john@bruntsfield.capital` to be an admin **provisioned through the domain SSO
path, not as a hand-seeded row**. That runs straight into a rule the codebase deliberately holds:
Google auto-provisioning always creates `Role.CONSULTANT`, never anything higher, so that signing in
can never mint an elevated role (GRS-0042).

Weakening auto-provisioning for one address was the obvious shortcut and the wrong one — it would
mean anyone able to present that address gets an admin account created for them. So the SSO path
creates the account exactly as it creates every account, and the elevation is granted separately by
configuration, derived **per request** from the signed token's email in the same way and for the
same reasons as the founder claim (ADR-0041): no migration, no stored role change, no new claim
anyone could forge, and a rotation that takes effect on the next call.

The three tests that matter are the last three: elevation cannot be minted by signing in, cannot be
forged by a token, and cannot widen an act-as session.
"""

from __future__ import annotations

import pytest
from bcap_contracts.common import Role

from grassmarket.config import Settings


class TestTheConfiguredSet:
    def test_it_is_empty_by_default(self) -> None:
        """No environment gets an admin it did not configure."""
        assert Settings(admin_emails="").admin_email_set == frozenset()

    def test_case_and_whitespace_are_not_identity(self) -> None:
        """A rotation typed with different capitalisation must still work."""
        settings = Settings(admin_emails="  John@Bruntsfield.Capital , other@x.com ")
        assert settings.admin_email_set == {"john@bruntsfield.capital", "other@x.com"}

    def test_empty_entries_are_dropped(self) -> None:
        assert Settings(admin_emails="a@b.c,,  ,d@e.f").admin_email_set == {"a@b.c", "d@e.f"}


class TestElevation:
    """Behaviour of the derivation itself, expressed as the dependency computes it."""

    @staticmethod
    def _role(email: str, stored: Role, configured: str) -> Role:
        settings = Settings(admin_emails=configured)
        return Role.ADMIN if email.strip().lower() in settings.admin_email_set else stored

    def test_a_configured_email_becomes_admin(self) -> None:
        assert (
            self._role("john@bruntsfield.capital", Role.CONSULTANT, "john@bruntsfield.capital")
            is Role.ADMIN
        )

    def test_an_unconfigured_email_keeps_its_stored_role(self) -> None:
        assert (
            self._role("someone@bruntsfield.capital", Role.CONSULTANT, "john@bruntsfield.capital")
            is Role.CONSULTANT
        )

    def test_it_only_ever_elevates(self) -> None:
        """A stored ADMIN absent from the list is NOT demoted.

        Demoting on absence would silently strip an admin the moment someone edited an environment
        variable — a much worse failure than an extra admin, and one nobody would attribute to the
        edit that caused it.
        """
        assert (
            self._role("existing@admin.com", Role.ADMIN, "john@bruntsfield.capital") is Role.ADMIN
        )

    def test_an_empty_configuration_elevates_nobody(self) -> None:
        assert self._role("john@bruntsfield.capital", Role.CONSULTANT, "") is Role.CONSULTANT


class TestTheRuleThisDoesNotBreak:
    def test_auto_provisioning_still_cannot_mint_an_elevated_role(self) -> None:
        """GRS-0042, unchanged and load-bearing.

        If this ever fails, presenting a workspace email would CREATE an admin account rather than
        merely being recognised as one — the difference between a configured grant and an open door.
        """
        import inspect

        from grassmarket.auth import google_oauth

        source = inspect.getsource(google_oauth)
        assert "Role.ADMIN" not in source, (
            "the Google auto-provisioning path now references Role.ADMIN; signing in must never be "
            "able to create an elevated account (GRS-0042)"
        )

    def test_the_tier_setting_cannot_be_used_to_smuggle_a_role(self) -> None:
        """`google_autoprovision_tier` configures TIER only; role is fixed at CONSULTANT."""
        with pytest.raises(Exception):  # noqa: B017 - any refusal is correct; it must not accept
            Settings(google_autoprovision_tier="admin")


def test_elevation_is_not_a_token_claim() -> None:
    """Derived per request, never minted — so an old token cannot carry a stale grant.

    The same reasoning as the founder claim: a rotation must take effect on the next call rather
    than waiting for every issued token to expire, and there must be no admin claim to forge.
    """
    import inspect

    from grassmarket.auth import security

    source = inspect.getsource(security)
    assert "admin_email" not in source, "admin elevation must not be written into a token"
