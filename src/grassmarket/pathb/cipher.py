"""Encryption at rest for transcripts (GRS-0029, PRD §3.3; Viewforth data-protection standards).

A `TranscriptCipher` port encrypts a transcript on write and decrypts on read, so plaintext never
touches the database. The shipped implementation is authenticated symmetric encryption (Fernet =
AES-128-CBC + HMAC), keyed from configuration — the key is never hard-coded and a placeholder key is
refused in production (the `jwt_secret` pattern). The port lets a KMS-backed cipher swap in later
without touching feature code.
"""

from __future__ import annotations

from typing import Protocol

from cryptography.fernet import Fernet, InvalidToken


class TranscriptCipherError(Exception):
    """Encryption/decryption failed — never swallowed (a corrupt or wrong-key record fails loud)."""


class TranscriptCipher(Protocol):
    """Encrypts plaintext for storage and decrypts it for its owner.

    The text methods are the original pair (GRS-0029). The byte methods were added for uploaded
    documents (GRS-0247), which are arbitrary binary — a PDF is not UTF-8, and routing it through
    the text methods would mean an encoding round-trip that either corrupts it or relies on a
    lossless-but-obscure trick like latin-1. Encrypting bytes as bytes says what it means.
    """

    def encrypt(self, plaintext: str) -> bytes: ...

    def decrypt(self, token: bytes) -> str: ...

    def encrypt_bytes(self, plaintext: bytes) -> bytes: ...

    def decrypt_bytes(self, token: bytes) -> bytes: ...


class FernetTranscriptCipher:
    """Fernet symmetric encryption keyed from config. The key is a 32-byte url-safe base64 string
    (`Fernet.generate_key()` output). A wrong key or tampered ciphertext raises, never returns
    garbage."""

    def __init__(self, key: str) -> None:
        try:
            self._fernet = Fernet(key.encode("utf-8"))
        except (ValueError, TypeError) as exc:
            raise TranscriptCipherError(
                "Invalid transcript encryption key — expected a 32-byte url-safe base64 key "
                "(Fernet.generate_key())."
            ) from exc

    def encrypt(self, plaintext: str) -> bytes:
        return self._fernet.encrypt(plaintext.encode("utf-8"))

    def decrypt(self, token: bytes) -> str:
        try:
            return self._fernet.decrypt(token).decode("utf-8")
        except InvalidToken as exc:
            raise TranscriptCipherError(
                "Could not decrypt a stored transcript — wrong key or tampered ciphertext."
            ) from exc

    def encrypt_bytes(self, plaintext: bytes) -> bytes:
        return self._fernet.encrypt(plaintext)

    def decrypt_bytes(self, token: bytes) -> bytes:
        try:
            return self._fernet.decrypt(token)
        except InvalidToken as exc:
            raise TranscriptCipherError(
                "Could not decrypt a stored document — wrong key or tampered ciphertext."
            ) from exc
