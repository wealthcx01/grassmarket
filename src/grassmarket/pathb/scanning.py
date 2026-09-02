"""Malware-scan hook for uploaded media (GRS-0029, PRD §3.3).

A `MediaScanner` port runs before any uploaded bytes are transcribed or stored. The shipped default
is a permissive no-op (the hook is present so a real scanner — ClamAV, a cloud AV API — plugs in by
config without touching the ingestion path). A scanner refuses by RAISING; ingestion never proceeds
on a refusal.
"""

from __future__ import annotations

from typing import Protocol


class MediaThreatError(Exception):
    """The scanner flagged the media. Ingestion is refused — never stored, never transcribed."""


class MediaScanner(Protocol):
    """Inspects uploaded media before ingestion. Raises `MediaThreatError` to refuse."""

    def scan(self, media: bytes, *, filename: str) -> None: ...


class ScannerNotConfiguredError(Exception):
    """The configured scanner cannot be built (unknown key), or is a no-op in production."""


class AllowAllScanner:
    """The default hook — accepts everything.

    **Not usable in production**; `build_scanner` refuses it there (GRS-0251). It is honest about
    what it does, but a permissive default on a route that accepts arbitrary uploaded bytes is a
    missing control, and nothing was replacing it.
    """

    version = "allow-all-v1"

    def scan(self, media: bytes, *, filename: str) -> None:  # noqa: D102 - trivial no-op hook
        return None


PROVIDER_ALLOW_ALL = "allow-all"
#: Scanners that must never serve production — they inspect nothing.
NO_OP_SCANNERS = frozenset({PROVIDER_ALLOW_ALL})

_SCANNERS = {PROVIDER_ALLOW_ALL: lambda _settings: AllowAllScanner()}


def build_scanner(settings) -> MediaScanner:  # noqa: ANN001 - Settings, imported lazily
    """Resolve the configured media scanner, or refuse.

    Fails loud on an unknown key and on a no-op scanner in production. There is no real scanner
    implementation yet: production must therefore configure one before media ingestion is enabled
    there, which is the honest position rather than scanning nothing and implying otherwise.
    """
    provider = (settings.media_scanner_provider or "").strip().lower()
    if provider not in _SCANNERS:
        known = ", ".join(sorted(_SCANNERS))
        raise ScannerNotConfiguredError(
            f"Unknown media scanner {provider!r}. Known scanners: {known}."
        )
    if settings.is_production and provider in NO_OP_SCANNERS:
        raise ScannerNotConfiguredError(
            f"Refusing to serve production with the {provider!r} media scanner — it inspects "
            "nothing. Configure a real scanner before enabling media ingestion in production."
        )
    return _SCANNERS[provider](settings)
