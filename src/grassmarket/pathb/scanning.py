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


class AllowAllScanner:
    """The default hook — accepts everything. Replace by config with a real AV scanner in prod."""

    def scan(self, media: bytes, *, filename: str) -> None:  # noqa: D102 - trivial no-op hook
        return None
