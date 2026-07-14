"""Path B ingestion unit + adapter-contract tests (GRS-0029).

Proves the encryption-at-rest cipher round-trips (and fails loud on a wrong key), the malware-scan
hook refuses by raising, and — the ticket's key swap requirement — the repository works against a
SECOND, different transcriber provider with no code change, only the injected adapter.
"""

from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from grassmarket.data.repository import Repository
from grassmarket.pathb.cipher import (
    FernetTranscriptCipher,
    TranscriptCipherError,
)
from grassmarket.pathb.scanning import AllowAllScanner, MediaThreatError
from grassmarket.pathb.transcription import EchoTranscriber, TranscriptionError
from tests.conftest import SeededConsultant

_KEY = Fernet.generate_key().decode()


# --- Encryption at rest ------------------------------------------------------------------


def test_cipher_round_trips_and_ciphertext_is_not_plaintext() -> None:
    cipher = FernetTranscriptCipher(_KEY)
    plaintext = "Meridian discovery call — confidential."
    token = cipher.encrypt(plaintext)
    assert token != plaintext.encode("utf-8")
    assert plaintext.encode("utf-8") not in token  # plaintext does not appear in the ciphertext
    assert cipher.decrypt(token) == plaintext


def test_cipher_fails_loud_on_a_wrong_key() -> None:
    token = FernetTranscriptCipher(_KEY).encrypt("secret")
    other = FernetTranscriptCipher(Fernet.generate_key().decode())
    with pytest.raises(TranscriptCipherError, match="wrong key or tampered"):
        other.decrypt(token)


def test_cipher_refuses_an_invalid_key() -> None:
    with pytest.raises(TranscriptCipherError, match="Invalid transcript encryption key"):
        FernetTranscriptCipher("not-a-valid-fernet-key")


# --- Malware-scan hook -------------------------------------------------------------------


class _RejectingScanner:
    def scan(self, media: bytes, *, filename: str) -> None:
        raise MediaThreatError(f"{filename} flagged by the scanner.")


def test_allow_all_scanner_accepts() -> None:
    AllowAllScanner().scan(b"anything", filename="x.wav")  # does not raise


def test_rejecting_scanner_refuses() -> None:
    with pytest.raises(MediaThreatError, match="flagged"):
        _RejectingScanner().scan(b"bad", filename="x.wav")


# --- Transcriber adapter contract: the swap is proven against a second provider ----------


class _ReversingTranscriber:
    """A second, different offline provider — reverses the decoded text. Only its behaviour
    differs; it satisfies the same `Transcriber` protocol, proving the path is provider-agnostic."""

    version = "reversing-transcriber-v1"

    def transcribe(self, media: bytes, *, filename: str, content_type: str) -> str:
        return media.decode("utf-8")[::-1]


@pytest.mark.parametrize(
    ("transcriber", "expected_text", "expected_ref"),
    [
        (EchoTranscriber(), "hello meeting", "echo-transcriber-v1"),
        (_ReversingTranscriber(), "gniteem olleh", "reversing-transcriber-v1"),
    ],
)
def test_ingest_media_works_against_any_transcriber(
    repo: Repository,
    alice: SeededConsultant,
    transcriber,
    expected_text,
    expected_ref,
) -> None:
    from bcap_contracts.meetings import MediaKind

    cipher = FernetTranscriptCipher(_KEY)
    stored = repo.ingest_media(
        alice.principal,
        media=b"hello meeting",
        source_filename="call.wav",
        content_type="audio/wav",
        source_kind=MediaKind.AUDIO,
        transcriber=transcriber,
        scanner=AllowAllScanner(),
        cipher=cipher,
    )
    assert stored.text == expected_text
    assert stored.transcriber_ref == expected_ref
    # Read it back through the repository (decrypts) — same plaintext.
    assert repo.get_transcript(alice.principal, stored.id, cipher=cipher).text == expected_text


def test_echo_transcriber_refuses_empty_media() -> None:
    with pytest.raises(TranscriptionError, match="empty media"):
        EchoTranscriber().transcribe(b"", filename="empty.wav", content_type="audio/wav")


def test_a_rejecting_scanner_stops_ingestion_before_anything_is_stored(
    repo: Repository, alice: SeededConsultant
) -> None:
    from bcap_contracts.meetings import MediaKind

    cipher = FernetTranscriptCipher(_KEY)
    before = len(repo.list_transcripts(alice.principal, cipher=cipher))
    with pytest.raises(MediaThreatError):
        repo.ingest_media(
            alice.principal,
            media=b"a virus",
            source_filename="bad.wav",
            content_type="audio/wav",
            source_kind=MediaKind.AUDIO,
            transcriber=EchoTranscriber(),
            scanner=_RejectingScanner(),
            cipher=cipher,
        )
    # Nothing was stored — the scan runs before transcribe/store.
    assert len(repo.list_transcripts(alice.principal, cipher=cipher)) == before


def test_ingest_media_refuses_empty_at_the_boundary(
    repo: Repository, alice: SeededConsultant
) -> None:
    from bcap_contracts.meetings import MediaKind

    # Even a provider without its own empty-guard cannot store a blank — the boundary refuses first.
    with pytest.raises(TranscriptionError, match="empty media"):
        repo.ingest_media(
            alice.principal,
            media=b"",
            source_filename="empty.wav",
            content_type="audio/wav",
            source_kind=MediaKind.AUDIO,
            transcriber=_ReversingTranscriber(),
            scanner=AllowAllScanner(),
            cipher=FernetTranscriptCipher(_KEY),
        )
