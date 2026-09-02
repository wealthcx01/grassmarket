"""Transcription adapter (GRS-0029, GRS-0251, PRD §3.3).

A `Transcriber` port turns uploaded audio/video bytes into a transcript. The provider is a config
choice, never a code change elsewhere — `build_transcriber(settings)` is the single resolution
point, and an unknown provider key is refused at load time (the ADR-0001 registry pattern).

**GRS-0251.** The offline `EchoTranscriber` was previously the unconditional return of the route's
dependency, in every environment. It decodes bytes as UTF-8, so a real MP3 became replacement
characters that were stored and served as that meeting's transcript — a silent fallback that
fabricated data (non-negotiable #3). Two things stop that recurring: the echo transcriber now
REFUSES rather than replacing undecodable bytes, and `build_transcriber` refuses to hand a
test double to production.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:  # pragma: no cover - typing only
    from grassmarket.config import Settings

# Provider keys. `openai-whisper` is the production default (founder direction, 2026-09-02):
# the hosted whisper-1 endpoint, keyed by GM_OPENAI_API_KEY.
PROVIDER_ECHO = "echo"
PROVIDER_OPENAI_WHISPER = "openai-whisper"
#: Providers that must never serve production — they are test doubles, not implementations.
TEST_DOUBLE_PROVIDERS = frozenset({PROVIDER_ECHO})

_OPENAI_TRANSCRIBE_URL = "https://api.openai.com/v1/audio/transcriptions"
_OPENAI_MODEL = "whisper-1"


class TranscriptionError(Exception):
    """Transcription failed — surfaced, never silently producing an empty or invented transcript."""


class TranscriberNotConfiguredError(Exception):
    """The configured provider cannot be built (unknown key, or a missing credential)."""


class Transcriber(Protocol):
    """Turns media bytes into a transcript. `version` identifies the provider on the stored record
    so a re-transcription is traceable."""

    @property
    def version(self) -> str: ...

    def transcribe(self, media: bytes, *, filename: str, content_type: str) -> str: ...


class EchoTranscriber:
    """A deterministic offline transcriber for CI/contract tests — decodes the bytes as UTF-8 text
    (a text fixture masquerading as 'audio'), so a fixture round-trips without any model.

    **Not usable in production**; `build_transcriber` refuses it there. It raises on bytes that are
    not valid UTF-8 rather than substituting replacement characters, because returning plausible
    nonsense is exactly the failure GRS-0251 exists to prevent.
    """

    version = "echo-transcriber-v1"

    def transcribe(self, media: bytes, *, filename: str, content_type: str) -> str:
        if not media:
            raise TranscriptionError(f"Refusing to transcribe empty media ({filename}).")
        try:
            text = media.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise TranscriptionError(
                f"The offline echo transcriber cannot read {filename!r}: it is not UTF-8 text. "
                "This provider exists for text fixtures only — configure a real transcription "
                "provider (GM_TRANSCRIBER_PROVIDER) to transcribe audio."
            ) from exc
        stripped = text.strip()
        if not stripped:
            raise TranscriptionError(f"Refusing to store an empty transcript for {filename}.")
        return stripped


class OpenAIWhisperTranscriber:
    """The hosted OpenAI Whisper (`whisper-1`) adapter.

    Client speech leaves our infrastructure when this is used — that is a deliberate, recorded
    trade (GRS-0251 scope 4) and the advisor-facing UI says so. Every failure path raises
    `TranscriptionError`: there is no fallback to another provider, because a quiet downgrade is
    the bug this class was written to fix.
    """

    version = f"openai-{_OPENAI_MODEL}"

    def __init__(self, api_key: str, *, timeout_seconds: float = 120.0) -> None:
        if not api_key:
            raise TranscriberNotConfiguredError(
                "The openai-whisper transcriber needs GM_OPENAI_API_KEY."
            )
        self._api_key = api_key
        self._timeout = timeout_seconds

    def transcribe(self, media: bytes, *, filename: str, content_type: str) -> str:
        if not media:
            raise TranscriptionError(f"Refusing to transcribe empty media ({filename}).")
        import httpx

        try:
            response = httpx.post(
                _OPENAI_TRANSCRIBE_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                files={
                    "file": (
                        filename,
                        io.BytesIO(media),
                        content_type or "application/octet-stream",
                    )
                },
                data={"model": _OPENAI_MODEL, "response_format": "text"},
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            raise TranscriptionError(f"Transcription request failed for {filename}: {exc}") from exc

        if response.status_code != 200:
            # The provider's body can echo request content; report the status and a short reason
            # only, never the whole payload.
            raise TranscriptionError(
                f"Transcription provider refused {filename} with HTTP {response.status_code}."
            )
        text = response.text.strip()
        if not text:
            raise TranscriptionError(
                f"Transcription provider returned nothing for {filename}. Refusing to store an "
                "empty transcript."
            )
        return text


def build_transcriber(settings: Settings) -> Transcriber:
    """Resolve the configured transcription provider, or refuse.

    Fails loud on an unknown key, on a missing credential, and on a test double in production.
    """
    provider = (settings.transcriber_provider or "").strip().lower()
    if provider not in _BUILDERS:
        known = ", ".join(sorted(_BUILDERS))
        raise TranscriberNotConfiguredError(
            f"Unknown transcription provider {provider!r}. Known providers: {known}."
        )
    if settings.is_production and provider in TEST_DOUBLE_PROVIDERS:
        raise TranscriberNotConfiguredError(
            f"Refusing to serve production with the {provider!r} transcriber — it is a test "
            "double, not a transcription implementation. Set GM_TRANSCRIBER_PROVIDER to a real "
            f"provider ({PROVIDER_OPENAI_WHISPER})."
        )
    return _BUILDERS[provider](settings)


_BUILDERS = {
    PROVIDER_ECHO: lambda _settings: EchoTranscriber(),
    PROVIDER_OPENAI_WHISPER: lambda settings: OpenAIWhisperTranscriber(settings.openai_api_key),
}
