"""Vendor the design-system fonts the client report PDF embeds (GRS-0219).

The PDF has to carry Bruntsfield's typography — Source Serif 4 for body, Inter for labels and
captions, IBM Plex Mono for figures and keys. The frontend gets these from `next/font/google` at
build time, which is no help to a Python renderer, and reportlab can only embed a TTF that is on
disk. So the faces are vendored into the package.

All three families are SIL Open Font License 1.1, which permits redistribution provided the licence
travels with the fonts — so each family's licence is downloaded alongside it and committed too.

This script exists rather than a bare `curl` in a README so the provenance of every committed binary
is auditable: run it again and you get byte-identical files, or you find out the upstream moved.

    uv run python scripts/vendor_report_fonts.py

Inter ships only as a variable font on Google Fonts, and reportlab renders a variable TTF at its
default instance — which would silently give us Regular everywhere we asked for SemiBold. So the two
static weights are instanced from the variable source with fontTools instead of being downloaded.
"""

from __future__ import annotations

import io
import sys
import urllib.request
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

DEST = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "grassmarket"
    / "deliverables"
    / "assets"
    / "fonts"
)

#: Static faces we can take as-is. (filename, url)
STATIC: tuple[tuple[str, str], ...] = (
    (
        "SourceSerif4-Regular.ttf",
        "https://raw.githubusercontent.com/adobe-fonts/source-serif/release/TTF/SourceSerif4-Regular.ttf",
    ),
    (
        "SourceSerif4-Semibold.ttf",
        "https://raw.githubusercontent.com/adobe-fonts/source-serif/release/TTF/SourceSerif4-Semibold.ttf",
    ),
    (
        "SourceSerif4-It.ttf",
        "https://raw.githubusercontent.com/adobe-fonts/source-serif/release/TTF/SourceSerif4-It.ttf",
    ),
    (
        "IBMPlexMono-Regular.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexmono/IBMPlexMono-Regular.ttf",
    ),
    (
        "IBMPlexMono-SemiBold.ttf",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexmono/IBMPlexMono-SemiBold.ttf",
    ),
)

#: The licence that must accompany each family. (filename, url)
LICENCES: tuple[tuple[str, str], ...] = (
    (
        "LICENSE-SourceSerif4.md",
        "https://raw.githubusercontent.com/adobe-fonts/source-serif/release/LICENSE.md",
    ),
    (
        "LICENSE-IBMPlexMono.txt",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexmono/OFL.txt",
    ),
    (
        "LICENSE-Inter.txt",
        "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/OFL.txt",
    ),
)

INTER_VARIABLE = (
    "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz,wght%5D.ttf"
)

#: (filename, weight) instanced from the Inter variable font.
INTER_INSTANCES: tuple[tuple[str, int], ...] = (
    ("Inter-Regular.ttf", 400),
    ("Inter-SemiBold.ttf", 600),
)


def _fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310 - pinned https sources
        return bytes(response.read())


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)

    for name, url in (*STATIC, *LICENCES):
        (DEST / name).write_bytes(_fetch(url))
        print(f"  {name}")

    variable = _fetch(INTER_VARIABLE)
    for name, weight in INTER_INSTANCES:
        font = TTFont(io.BytesIO(variable))
        # Pin BOTH axes. Leaving `opsz` free would keep the font variable, and reportlab would fall
        # back to its default instance — the silent wrong-weight failure this avoids.
        static = instancer.instantiateVariableFont(font, {"wght": weight, "opsz": 14})
        static.save(DEST / name)
        print(f"  {name} (instanced at wght={weight})")

    print(f"\nVendored into {DEST.relative_to(Path.cwd())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
