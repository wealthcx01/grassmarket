"""Design tokens for the client report PDF (GRS-0219).

Set once here, never per element — the ticket's scope item 2. These mirror
`frontend/app/globals.css`, so the PDF and the web rendition (GRS-0220) are the same design system
rather than two people's idea of it. If a value changes there, it changes here.

The palette is paper/ink with a single chromatic accent (Bottle Green). That restraint is what makes
the greyscale requirement achievable at all: a document with one accent colour degrades to a
printout that still reads, which scope item 4 demands.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- Palette (mirrors globals.css :root) -------------------------------------------------

PAPER = HexColor("#f7f6f2")
PAPER_SUNKEN = HexColor("#efede6")
INK = HexColor("#17191f")
INK_SOFT = HexColor("#3a3d45")
INK_MUTED = HexColor("#6e7079")
ACCENT = HexColor("#1a3b26")  # Bottle Green — the only chromatic colour
ACCENT_TINT = HexColor("#e4eae3")
ACCENT_CONTRAST = HexColor("#f7f6f2")
RULE = HexColor("#dddbd6")
RULE_STRONG = HexColor("#b9b6ae")

# --- Page geometry -----------------------------------------------------------------------

PAGE_SIZE = A4
MARGIN_L = 22 * mm
MARGIN_R = 22 * mm
MARGIN_T = 24 * mm
MARGIN_B = 20 * mm
#: Space reserved above the frame for the running head, and below it for the folio.
HEAD_GAP = 10 * mm
FOOT_GAP = 12 * mm

#: A contents page is worth it beyond this many pages (scope item 3).
CONTENTS_THRESHOLD_PAGES = 8

# --- Fonts -------------------------------------------------------------------------------

_FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"

#: (reportlab name, file). Vendored because reportlab can only embed a TTF on disk, and because the
#: frontend's next/font/google pipeline is no help to a Python renderer. All three families are
#: SIL OFL 1.1; their licences sit beside them.
_FACES: tuple[tuple[str, str], ...] = (
    ("SourceSerif4", "SourceSerif4-Regular.ttf"),
    ("SourceSerif4-Bold", "SourceSerif4-Semibold.ttf"),
    ("SourceSerif4-Italic", "SourceSerif4-It.ttf"),
    ("Inter", "Inter-Regular.ttf"),
    ("Inter-Bold", "Inter-SemiBold.ttf"),
    ("IBMPlexMono", "IBMPlexMono-Regular.ttf"),
    ("IBMPlexMono-Bold", "IBMPlexMono-SemiBold.ttf"),
)

SERIF = "SourceSerif4"
SERIF_BOLD = "SourceSerif4-Bold"
SERIF_ITALIC = "SourceSerif4-Italic"
SANS = "Inter"
SANS_BOLD = "Inter-Bold"
MONO = "IBMPlexMono"
MONO_BOLD = "IBMPlexMono-Bold"


class MissingReportFontError(Exception):
    """A vendored font is absent. Refuse rather than let reportlab substitute Helvetica.

    Substitution is silent, and a report that quietly loses the house typography is exactly the
    "has no branding" failure this ticket exists to fix — so it fails loud instead.
    """


def register_fonts() -> None:
    """Register the vendored faces with reportlab. Idempotent; safe to call per render."""
    for name, filename in _FACES:
        if name in pdfmetrics.getRegisteredFontNames():
            continue
        path = _FONT_DIR / filename
        if not path.is_file():
            raise MissingReportFontError(
                f"{filename} is missing from {_FONT_DIR}. Run "
                "`uv run python scripts/vendor_report_fonts.py` to vendor the report fonts. "
                "Refusing to render with substituted fonts."
            )
        pdfmetrics.registerFont(TTFont(name, str(path)))

    # Bind the family so <b>/<i> markup in paragraphs resolves to the real faces rather than
    # reportlab's synthesised slant/smear.
    pdfmetrics.registerFontFamily(
        SERIF, normal=SERIF, bold=SERIF_BOLD, italic=SERIF_ITALIC, boldItalic=SERIF_BOLD
    )
    pdfmetrics.registerFontFamily(
        SANS, normal=SANS, bold=SANS_BOLD, italic=SANS, boldItalic=SANS_BOLD
    )
    pdfmetrics.registerFontFamily(
        MONO, normal=MONO, bold=MONO_BOLD, italic=MONO, boldItalic=MONO_BOLD
    )


# --- Type scale --------------------------------------------------------------------------
# Sizes in points, leading paired with each. Body leading is generous (1.45) because the report is
# read, not skimmed.

COVER_TITLE = (30, 36)
COVER_SUBTITLE = (13, 19)
SECTION_TITLE = (19, 24)
SUBHEAD = (12, 17)
BODY = (10.5, 15.2)
CAPTION = (8.5, 12)
FIGURE_KEY = (8, 11.5)  # sized so a version string fits its column without breaking mid-word
RUNNING_HEAD = (8, 10)
FOLIO = (8.5, 11)

# --- Spacing -----------------------------------------------------------------------------

SPACE_PARA = 6.5
SPACE_SECTION = 16
SPACE_FIGURE = 12
