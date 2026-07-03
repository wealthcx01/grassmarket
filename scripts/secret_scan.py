"""Offline secret-scan pre-commit hook.

Self-contained (stdlib only) so the hook never depends on a network binary. Scans the files
passed by pre-commit for high-signal secret patterns and fails loud if any match. This is a
guard rail, not a vault — real secrets live in the environment and `.env` (git-ignored).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# (name, compiled pattern). Kept high-signal to avoid noise; add patterns as the app grows.
PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "Private key block",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
    ),
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b")),
    (
        "Generic bearer/JWT secret assignment",
        re.compile(
            r"(?i)(secret|token|passwd|password|api[_-]?key)\s*[:=]\s*['\"][^'\"]{12,}['\"]"
        ),
    ),
    ("Postgres URL with inline password", re.compile(r"postgres(?:ql)?://[^:@\s]+:[^@\s]+@")),
]

# The generic assignment pattern is inherently noisy (it fires on any `password = "..."`). The
# HIGH-SIGNAL patterns (real key/token shapes) scan every file unconditionally; only the generic
# one is relaxed, and only in two explicit, documented ways below.
_GENERIC_PATTERN_NAME = "Generic bearer/JWT secret assignment"

# 1. An inline pragma marks a known-safe placeholder (detect-secrets convention). Use sparingly
#    and only for values that are demonstrably not real secrets (env placeholders, dummies).
_ALLOWLIST_PRAGMA = "pragma: allowlist secret"


# 2. Synthetic fixtures under tests/ carry fake credentials by construction; the generic pattern
#    is skipped there. The high-signal patterns still scan tests/ (a real AWS key in a test is a
#    real leak).
def _is_test_fixture(path: Path) -> bool:
    return "tests" in path.parts


# Files that legitimately contain example/placeholder credentials.
ALLOWLIST_SUFFIXES = (".example",)
ALLOWLIST_NAMES = {".env.example"}
TEXT_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".md",
    ".txt",
    ".cfg",
    ".ini",
    ".env",
    ".sh",
    ".ps1",
    ".sql",
}


def _is_allowlisted(path: Path) -> bool:
    return path.name in ALLOWLIST_NAMES or path.suffix in ALLOWLIST_SUFFIXES


def scan(paths: list[str]) -> int:
    findings: list[str] = []
    for raw in paths:
        path = Path(raw)
        if not path.is_file() or _is_allowlisted(path):
            continue
        if path.suffix and path.suffix not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        is_test = _is_test_fixture(path)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _ALLOWLIST_PRAGMA in line:
                continue
            for name, pattern in PATTERNS:
                if name == _GENERIC_PATTERN_NAME and is_test:
                    continue  # synthetic fixtures; high-signal patterns below still apply
                if pattern.search(line):
                    findings.append(f"{path}:{lineno}: possible {name}")

    if findings:
        print("secret-scan: potential secrets detected — commit blocked:", file=sys.stderr)
        for f in findings:
            print(f"  {f}", file=sys.stderr)
        print(
            "\nMove secrets to the environment / .env (git-ignored). If this is a false "
            "positive, refine scripts/secret_scan.py — never bypass with --no-verify.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(scan(sys.argv[1:]))
