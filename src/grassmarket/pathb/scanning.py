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


class ContentTypeScanner:
    """Refuses bytes that are not what they claim to be (GRS-0251 follow-up).

    **Not antivirus, and it does not pretend to be.** It is the control that was missing entirely:
    `POST /transcripts/media` accepts up to 25 MB of arbitrary bytes from a browser, and until now
    nothing looked at them at all.

    What it stops: an executable, a script or an HTML page renamed to something harmless, and any
    file whose bytes disagree with its declared content type. That covers the realistic accident
    (the wrong file) and the cheap attack (a mislabelled payload someone opens later). A
    genuinely malicious PDF is out of scope — that needs ClamAV or a cloud scanner, which is a
    separate provider behind this same port.

    Deliberately an allowlist. An unrecognised type is refused, because "I have never seen this,
    so it is probably fine" is exactly the reasoning non-negotiable #3 forbids.
    """

    version = "content-type-scanner-v1"

    #: declared-type prefix -> byte signatures a file of that type must start with.
    #: ``None`` means the format legitimately has no signature to check.
    _SIGNATURES: dict[str, tuple[bytes, ...] | None] = {
        "application/pdf": (b"%PDF-",),
        # ZIP containers: docx, xlsx, pptx — PK\x03\x04 plus the empty-archive variant.
        "application/vnd.openxmlformats-officedocument": (b"PK\x03\x04", b"PK\x05\x06"),
        "application/zip": (b"PK\x03\x04", b"PK\x05\x06"),
        "image/png": (b"\x89PNG\r\n\x1a\n",),
        "image/jpeg": (b"\xff\xd8\xff",),
        "image/gif": (b"GIF87a", b"GIF89a"),
        "audio/mpeg": (b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"),
        "audio/wav": (b"RIFF",),
        "audio/x-wav": (b"RIFF",),
        "audio/webm": (b"\x1a\x45\xdf\xa3",),
        "video/webm": (b"\x1a\x45\xdf\xa3",),
        "audio/ogg": (b"OggS",),
        "text/csv": None,
        "text/plain": None,
        "text/markdown": None,
    }

    #: Refused whatever the declared type says.
    _NEVER: tuple[tuple[bytes, str], ...] = (
        (b"mz", "a Windows executable"),
        (b"\x7felf", "a Linux executable"),
        (b"#!", "a script"),
        (b"<!doctype html", "an HTML document"),
        (b"<html", "an HTML document"),
    )

    def scan(self, media: bytes, *, filename: str) -> None:
        lowered = media[:16].lower()
        for signature, description in self._NEVER:
            if lowered.startswith(signature):
                raise MediaThreatError(
                    f"{filename} begins as {description}. Refusing to store it, whatever it is "
                    f"named."
                )

    def scan_declared(self, media: bytes, *, filename: str, content_type: str) -> None:
        """`scan`, plus a check that the bytes match the declared content type."""
        self.scan(media, filename=filename)
        declared = (content_type or "").split(";")[0].strip().lower()
        for prefix, signatures in self._SIGNATURES.items():
            if not declared.startswith(prefix):
                continue
            if signatures is None or media.startswith(signatures):
                return
            raise MediaThreatError(
                f"{filename} is declared as {declared} but does not begin like one. Refusing to "
                f"store a file that is not what it says it is."
            )
        raise MediaThreatError(
            f"{filename} declares the unsupported type {declared!r}. Supported: "
            f"{', '.join(sorted(self._SIGNATURES))}."
        )


PROVIDER_ALLOW_ALL = "allow-all"
PROVIDER_CONTENT_TYPE = "content-type"
#: Scanners that must never serve production — they inspect nothing.
NO_OP_SCANNERS = frozenset({PROVIDER_ALLOW_ALL})

_SCANNERS = {
    PROVIDER_ALLOW_ALL: lambda _settings: AllowAllScanner(),
    PROVIDER_CONTENT_TYPE: lambda _settings: ContentTypeScanner(),
}


def build_scanner(settings) -> MediaScanner:  # noqa: ANN001 - Settings, imported lazily
    """Resolve the configured media scanner, or refuse.

    Fails loud on an unknown key, and on a no-op scanner in production. `content-type` is the
    provider production should use: a real control, though not antivirus.
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
