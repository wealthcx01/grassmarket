"""GRS-0251 — a test double must never serve production, and must never invent a transcript.

Before this ticket, `_transcriber()` returned `EchoTranscriber()` unconditionally in every
environment. It decodes media as UTF-8 with `errors="replace"`, so a real MP3 became a string of
replacement characters that was encrypted and stored as that meeting's transcript, with a 201 and
no error anywhere — a silent fallback that fabricated data (non-negotiable #3).

These are the tests that would have caught it.
"""

from __future__ import annotations

import pytest

from grassmarket.config import Settings
from grassmarket.pathb.scanning import (
    AllowAllScanner,
    ScannerNotConfiguredError,
    build_scanner,
)
from grassmarket.pathb.transcription import (
    EchoTranscriber,
    OpenAIWhisperTranscriber,
    TranscriberNotConfiguredError,
    TranscriptionError,
    build_transcriber,
)

_SECRET = "test-secret-that-is-more-than-thirty-two-characters-long-xxxxx"
# A valid Fernet key that is NOT the placeholder — the production guard rejects that one
# first, which would mask the transcriber guard these tests are actually about.
_REAL_KEY = "OCvmNU9cP2th7k3VdTYcEquwC9ox889a7hsaIQe8Be8="  # pragma: allowlist secret


def _settings(**over) -> Settings:
    base = dict(
        _env_file=None,
        env="ci",
        jwt_secret=_SECRET,
        database_url="sqlite+pysqlite:///:memory:",
    )
    base.update(over)
    return Settings(**base)


# --- the echo transcriber refuses rather than inventing ------------------------------------------


def test_echo_transcriber_refuses_bytes_that_are_not_text() -> None:
    """The actual defect: MP3 bytes used to come back as replacement characters."""
    mp3ish = b"\xff\xfb\x90\x64\x00\x00\x00\x00\x00\x00"
    with pytest.raises(TranscriptionError) as exc:
        EchoTranscriber().transcribe(mp3ish, filename="meeting.mp3", content_type="audio/mpeg")
    assert "not UTF-8" in str(exc.value)


def test_echo_transcriber_refuses_empty_and_whitespace_only() -> None:
    for media in (b"", b"   \n\t "):
        with pytest.raises(TranscriptionError):
            EchoTranscriber().transcribe(media, filename="x.txt", content_type="text/plain")


def test_echo_transcriber_still_round_trips_a_text_fixture() -> None:
    """The reason it exists at all must keep working."""
    out = EchoTranscriber().transcribe(
        b"  Anna: we are behind on the migration.  ", filename="f.txt", content_type="text/plain"
    )
    assert out == "Anna: we are behind on the migration."


# --- production refuses the doubles --------------------------------------------------------------


def test_production_still_boots_with_the_default_providers() -> None:
    """Deliberate: the guard is NOT at boot.

    Refusing to construct Settings would take all 173 endpoints down over one feature with no UI —
    and would have crashed the running production service on the deploy that added these settings.
    Enforcement belongs where the harm is, so booting stays fine and the endpoint refuses."""
    settings = _settings(
        env="production",
        database_url="postgresql+psycopg://u:p@h/db",
        transcript_encryption_key=_REAL_KEY,
    )
    assert settings.is_production
    assert settings.transcriber_provider == "echo"


def test_production_refuses_the_test_doubles_where_the_harm_is() -> None:
    """The guarantee: in production nothing is transcribed or scanned by a stand-in."""
    prod = _settings(
        env="production",
        database_url="postgresql+psycopg://u:p@h/db",
        transcript_encryption_key=_REAL_KEY,
    )
    with pytest.raises(TranscriberNotConfiguredError, match="test double"):
        build_transcriber(prod)
    with pytest.raises(ScannerNotConfiguredError, match="inspects nothing"):
        build_scanner(prod)


# --- the registry fails loud on nonsense ---------------------------------------------------------


def test_unknown_provider_is_refused_at_build_time() -> None:
    with pytest.raises(TranscriberNotConfiguredError, match="Unknown transcription provider"):
        build_transcriber(_settings(transcriber_provider="whisper-ultra"))
    with pytest.raises(ScannerNotConfiguredError, match="Unknown media scanner"):
        build_scanner(_settings(media_scanner_provider="clamav-9000"))


def test_openai_provider_needs_a_key() -> None:
    with pytest.raises(TranscriberNotConfiguredError, match="GM_OPENAI_API_KEY"):
        build_transcriber(_settings(transcriber_provider="openai-whisper", openai_api_key=""))


def test_openai_transcriber_carries_its_version_for_traceability() -> None:
    assert OpenAIWhisperTranscriber("sk-test").version == "openai-whisper-1"


# --- non-production keeps working ----------------------------------------------------------------


def test_ci_default_is_the_offline_double() -> None:
    assert isinstance(build_transcriber(_settings()), EchoTranscriber)
    assert isinstance(build_scanner(_settings()), AllowAllScanner)


# --- the real scanner ---------------------------------------------------------------------------


class TestContentTypeScanner:
    """The control that was missing entirely: nothing looked at uploaded bytes at all."""

    def _scanner(self):
        from grassmarket.pathb.scanning import ContentTypeScanner

        return ContentTypeScanner()

    def test_it_refuses_an_executable_however_it_is_named(self) -> None:
        from grassmarket.pathb.scanning import MediaThreatError

        with pytest.raises(MediaThreatError, match="Windows executable"):
            self._scanner().scan(b"MZ\x90\x00\x03", filename="quarterly-report.pdf")

    def test_it_refuses_a_script_and_an_elf_binary(self) -> None:
        from grassmarket.pathb.scanning import MediaThreatError

        with pytest.raises(MediaThreatError, match="script"):
            self._scanner().scan(b"#!/bin/sh\nrm -rf /", filename="notes.txt")
        with pytest.raises(MediaThreatError, match="Linux executable"):
            self._scanner().scan(b"\x7fELF\x02\x01", filename="deck.pdf")

    def test_it_refuses_html_renamed_as_a_pdf(self) -> None:
        """The phishing-page-in-a-report case."""
        from grassmarket.pathb.scanning import MediaThreatError

        with pytest.raises(MediaThreatError, match="HTML"):
            self._scanner().scan(b"<!DOCTYPE HTML><html>", filename="board-pack.pdf")

    def test_it_refuses_bytes_that_contradict_the_declared_type(self) -> None:
        from grassmarket.pathb.scanning import MediaThreatError

        with pytest.raises(MediaThreatError, match="does not begin like one"):
            self._scanner().scan_declared(
                b"just some text", filename="x.pdf", content_type="application/pdf"
            )

    def test_it_refuses_an_unrecognised_type_rather_than_waving_it_through(self) -> None:
        """An allowlist. 'Never seen this, probably fine' is the reasoning #3 forbids."""
        from grassmarket.pathb.scanning import MediaThreatError

        with pytest.raises(MediaThreatError, match="unsupported type"):
            self._scanner().scan_declared(
                b"\x00\x01\x02", filename="x.bin", content_type="application/x-mystery"
            )

    def test_it_accepts_the_real_thing(self) -> None:
        scanner = self._scanner()
        scanner.scan_declared(
            b"%PDF-1.7\n%\xe2\xe3", filename="deck.pdf", content_type="application/pdf"
        )
        scanner.scan_declared(b"ID3\x03\x00", filename="m.mp3", content_type="audio/mpeg")
        scanner.scan_declared(b"RIFF....WAVE", filename="m.wav", content_type="audio/wav")
        # A text format with no signature to check.
        scanner.scan_declared(b"a,b,c\n1,2,3", filename="d.csv", content_type="text/csv")

    def test_it_is_selectable_by_config_and_allowed_in_production(self) -> None:
        from grassmarket.pathb.scanning import ContentTypeScanner

        prod = _settings(
            env="production",
            database_url="postgresql+psycopg://u:p@h/db",
            transcript_encryption_key=_REAL_KEY,
            media_scanner_provider="content-type",
        )
        assert isinstance(build_scanner(prod), ContentTypeScanner)
