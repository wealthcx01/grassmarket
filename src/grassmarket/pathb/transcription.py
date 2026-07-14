"""Transcription adapter (GRS-0029, PRD §3.3).

A `Transcriber` port turns uploaded audio/video bytes into a transcript. The provider is a
choice swappable by config, never a code change elsewhere — the production default is local Whisper
(`WhisperTranscriber`, wired outside CI so no model download runs in tests). CI + contract tests use
deterministic offline fakes. A pasted transcript needs no transcriber (the text is already text).
"""

from __future__ import annotations

from typing import Protocol

# The production default recorded per the ticket: local Whisper (openai-whisper / faster-whisper),
# selected by config. It is NOT imported here so CI never pulls the model; the real adapter is wired
# at the composition root behind this same protocol.
WHISPER_PROVIDER_REF = "whisper-local-v1"


class TranscriptionError(Exception):
    """Transcription failed — surfaced, never silently producing an empty transcript."""


class Transcriber(Protocol):
    """Turns media bytes into a transcript. `version` identifies the provider on the stored record
    so a re-transcription is traceable."""

    @property
    def version(self) -> str: ...

    def transcribe(self, media: bytes, *, filename: str, content_type: str) -> str: ...


class EchoTranscriber:
    """A deterministic offline transcriber for CI/contract tests — decodes the bytes as UTF-8 text
    (a text fixture masquerading as 'audio'), so a fixture round-trips without any model."""

    version = "echo-transcriber-v1"

    def transcribe(self, media: bytes, *, filename: str, content_type: str) -> str:
        if not media:
            raise TranscriptionError(f"Refusing to transcribe empty media ({filename}).")
        return media.decode("utf-8", errors="replace").strip()
