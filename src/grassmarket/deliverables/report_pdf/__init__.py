"""The client report as a Bruntsfield-branded PDF (GRS-0219)."""

from grassmarket.deliverables.report_pdf.render import (
    SECTION_TITLES,
    ReportMeta,
    render_client_report_pdf,
)
from grassmarket.deliverables.report_pdf.tokens import MissingReportFontError

__all__ = [
    "SECTION_TITLES",
    "MissingReportFontError",
    "ReportMeta",
    "render_client_report_pdf",
]
