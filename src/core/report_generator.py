"""Report Generation Module for TruthLayer.

Generates downloadable verification reports in PDF, Markdown, and JSON formats
with complete provenance, scorecards, source citations, and verified corrections.
"""

import io
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from src.models.schemas import (
    VerificationReport,
    ClaimVerificationResult,
    VerificationStatus,
    VerificationSourceCitation,
)
from src.utils.logger import get_logger

logger = get_logger("truthlayer.core.report_generator")


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and draw total page counts and running headers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Dict[str, Any]] = []
        self.doc_title: str = "TruthLayer Fact-Checking Audit Report"

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int) -> None:
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running header on page 2 and onwards
        if self._pageNumber > 1:
            self.drawString(40, 755, f"TruthLayer Audit Report — {self.doc_title[:50]}")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(40, 747, 572, 747)

        # Running footer on every page
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(572, 30, page_text)
        self.drawString(40, 30, "TruthLayer AI Fact-Checking Engine • Confidential Audit Report")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(40, 42, 572, 42)

        self.restoreState()


def _format_confidence_label(conf: float) -> str:
    """Format numeric confidence score with qualitative assessment."""
    pct = int(conf * 100)
    if conf >= 0.90:
        return f"{pct}% (High Confidence)"
    elif conf >= 0.70:
        return f"{pct}% (Moderate Confidence)"
    elif conf > 0.0:
        return f"{pct}% (Low Confidence)"
    else:
        return "0% (No Evidence Found)"


def _clean_text_for_xml(text: Optional[str]) -> str:
    """Clean plain text for safe inclusion inside ReportLab XML Paragraphs."""
    if not text:
        return ""
    # Remove unsupported multi-byte emojis that do not exist in Type1 Helvetica fonts
    sanitized = "".join(ch for ch in str(text) if ord(ch) < 0xFFFF and not (0xD800 <= ord(ch) <= 0xDFFF))
    clean = (
        sanitized
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
        .replace("$", "&dollar;")
    )
    return clean


def generate_pdf_report(report: VerificationReport) -> bytes:
    """Generate a clean, professional, publication-ready PDF audit report.

    Args:
        report: Document verification report containing claims and verification metrics.

    Returns:
        bytes: Raw PDF document bytes.
    """
    logger.info(f"Generating PDF audit report for '{report.document_name}'...")
    buffer = io.BytesIO()

    # Document setup: Letter size with 40pt side margins and 50pt top/bottom margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=50,
        bottomMargin=50,
    )

    # Styles definition
    base_styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=base_styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=14,
    )

    meta_label_style = ParagraphStyle(
        "MetaLabel",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#475569"),
    )

    meta_val_style = ParagraphStyle(
        "MetaValue",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
    )

    section_heading_style = ParagraphStyle(
        "SectionHeading",
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=14,
        spaceAfter=6,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#FFFFFF"),
        alignment=1,  # Center
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        alignment=1,
    )

    claim_title_style = ParagraphStyle(
        "ClaimTitle",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#0F172A"),
    )

    claim_quote_style = ParagraphStyle(
        "ClaimQuote",
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=3,
        spaceAfter=3,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )

    correction_style = ParagraphStyle(
        "CorrectionText",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E3A8A"),
    )

    citation_style = ParagraphStyle(
        "CitationText",
        fontName="Helvetica",
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#475569"),
    )

    story: List[Any] = []

    # 1. Header Banner
    story.append(Paragraph("TruthLayer — Verification Audit Report", title_style))
    story.append(
        Paragraph(
            "Automated Fact-Checking &amp; Empirical Evidence Provenance Analysis",
            subtitle_style,
        )
    )

    # 2. Document Metadata Box
    date_str = (
        report.processed_at.strftime("%B %d, %Y • %H:%M UTC")
        if hasattr(report.processed_at, "strftime")
        else str(report.processed_at)
    )

    meta_table_data = [
        [
            Paragraph("Document File:", meta_label_style),
            Paragraph(f"<b>{_clean_text_for_xml(report.document_name)}</b>", meta_val_style),
            Paragraph("Analysis Date:", meta_label_style),
            Paragraph(date_str, meta_val_style),
        ],
        [
            Paragraph("Total Pages:", meta_label_style),
            Paragraph(str(report.total_pages), meta_val_style),
            Paragraph("Claims Extracted:", meta_label_style),
            Paragraph(f"<b>{report.total_claims}</b>", meta_val_style),
        ],
    ]

    meta_table = Table(meta_table_data, colWidths=[90, 180, 90, 172])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#E2E8F0")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#EDF2F7")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # 3. Executive Scorecard Summary Table
    story.append(Paragraph("Executive Fact-Checking Scorecard", section_heading_style))

    tot = max(1, report.total_claims)
    pct_v = f"{int(report.verified_count / tot * 100)}%"
    pct_i = f"{int(report.inaccurate_count / tot * 100)}%"
    pct_f = f"{int(report.false_count / tot * 100)}%"
    pct_u = f"{int(report.unverified_count / tot * 100)}%"

    summary_headers = [
        Paragraph("Verification Status", table_header_style),
        Paragraph("Count", table_header_style),
        Paragraph("Share", table_header_style),
        Paragraph("Operational Meaning", table_header_style),
    ]

    summary_rows = [
        summary_headers,
        [
            Paragraph("<font color='#16A34A'><b>VERIFIED</b></font>", table_cell_style),
            Paragraph(str(report.verified_count), table_cell_style),
            Paragraph(pct_v, table_cell_style),
            Paragraph("Reliable public evidence corroborates the core assertion.", body_style),
        ],
        [
            Paragraph("<font color='#D97706'><b>INACCURATE</b></font>", table_cell_style),
            Paragraph(str(report.inaccurate_count), table_cell_style),
            Paragraph(pct_i, table_cell_style),
            Paragraph("Partially incorrect, outdated figure, or wrong context.", body_style),
        ],
        [
            Paragraph("<font color='#DC2626'><b>FALSE</b></font>", table_cell_style),
            Paragraph(str(report.false_count), table_cell_style),
            Paragraph(pct_f, table_cell_style),
            Paragraph("Reliable evidence directly contradicts the assertion.", body_style),
        ],
        [
            Paragraph("<font color='#475569'><b>UNVERIFIED</b></font>", table_cell_style),
            Paragraph(str(report.unverified_count), table_cell_style),
            Paragraph(pct_u, table_cell_style),
            Paragraph("Evidence is absent, insufficient, or conflicting.", body_style),
        ],
    ]

    summary_table = Table(summary_rows, colWidths=[110, 50, 50, 322])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F0FDF4")),
                ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#FFFBEB")),
                ("BACKGROUND", (0, 3), (-1, 3), colors.HexColor("#FEF2F2")),
                ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 14))

    # 4. Itemized Claim Audit Details
    story.append(Paragraph(f"Itemized Claim Verification Ledger ({report.total_claims})", section_heading_style))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#CBD5E1"),
            spaceBefore=0,
            spaceAfter=10,
        )
    )

    if not report.results:
        story.append(
            Paragraph("No factual claims were identified in this document.", body_style)
        )
    else:
        for idx, item in enumerate(report.results, start=1):
            claim_elements: List[Any] = []

            # Badge text & color
            if item.status == VerificationStatus.VERIFIED:
                status_color = "#16A34A"
                status_bg = "#DCFCE7"
                badge_label = "VERIFIED"
            elif item.status == VerificationStatus.INACCURATE:
                status_color = "#D97706"
                status_bg = "#FEF3C7"
                badge_label = "INACCURATE"
            elif item.status == VerificationStatus.FALSE:
                status_color = "#DC2626"
                status_bg = "#FEE2E2"
                badge_label = "FALSE"
            else:
                status_color = "#475569"
                status_bg = "#F1F5F9"
                badge_label = "UNVERIFIED"

            conf_str = _format_confidence_label(item.confidence)

            # Claim Card Header Table
            card_header_data = [
                [
                    Paragraph(
                        f"<b>[{item.claim_id}]</b> • Page {item.page_number} • {item.claim_type}",
                        claim_title_style,
                    ),
                    Paragraph(
                        f"<font color='{status_color}'><b>[{badge_label}]</b></font> ({conf_str})",
                        claim_title_style,
                    ),
                ]
            ]
            card_header_table = Table(card_header_data, colWidths=[290, 242])
            card_header_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(status_bg)),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            claim_elements.append(card_header_table)

            # Original Claim Text
            claim_elements.append(Spacer(1, 4))
            clean_claim = _clean_text_for_xml(item.original_claim)
            claim_elements.append(
                Paragraph(f'<b>Target Claim:</b> "{clean_claim}"', claim_quote_style)
            )

            # Explanation
            clean_exp = _clean_text_for_xml(item.explanation)
            claim_elements.append(
                Paragraph(f"<b>Evaluation:</b> {clean_exp}", body_style)
            )

            # Corrected Information (if present)
            if item.corrected_information:
                clean_corr = _clean_text_for_xml(item.corrected_information)
                corr_data = [
                    [
                        Paragraph(
                            f"<b>Verified Correction:</b> {clean_corr}",
                            correction_style,
                        )
                    ]
                ]
                corr_table = Table(corr_data, colWidths=[532])
                corr_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
                            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BFDBFE")),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ]
                    )
                )
                claim_elements.append(Spacer(1, 3))
                claim_elements.append(corr_table)

            # Evidence summary (if present)
            if item.evidence_summary:
                clean_summary = _clean_text_for_xml(item.evidence_summary)
                claim_elements.append(Spacer(1, 2))
                claim_elements.append(
                    Paragraph(f"<b>Evidence Summary:</b> {clean_summary}", body_style)
                )

            # Verification notes (if present)
            if item.verification_notes:
                clean_notes = _clean_text_for_xml(item.verification_notes)
                claim_elements.append(Spacer(1, 2))
                claim_elements.append(
                    Paragraph(
                        f"<b>Context / Reporting Note:</b> {clean_notes}",
                        body_style,
                    )
                )

            # Sources & citations
            if item.sources:
                claim_elements.append(Spacer(1, 3))
                claim_elements.append(
                    Paragraph("<b>Corroborating Evidence Sources:</b>", body_style)
                )
                for s_idx, src in enumerate(item.sources, start=1):
                    type_str = f"[{src.evidence_type.capitalize()}]" if src.evidence_type else ""
                    clean_title = _clean_text_for_xml(src.title)
                    pub_info = f" • Published: {src.publication_date}" if src.publication_date else ""
                    domain_info = f" ({src.source_domain}{pub_info})" if src.source_domain else pub_info

                    src_line = (
                        f"• {type_str} <a href='{src.url}' color='#2563EB'><b><u>{clean_title}</u></b></a>"
                        f"{domain_info}"
                    )
                    claim_elements.append(Paragraph(src_line, citation_style))
            else:
                claim_elements.append(Spacer(1, 2))
                claim_elements.append(
                    Paragraph(
                        "<i>No external web evidence sources retrieved.</i>",
                        citation_style,
                    )
                )

            claim_elements.append(Spacer(1, 8))
            story.append(KeepTogether(claim_elements))

    # Build PDF using NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_bytes = buffer.getvalue()
    logger.info(f"Successfully generated PDF audit report ({len(pdf_bytes)} bytes).")
    return pdf_bytes


def generate_markdown_report(report: VerificationReport) -> str:
    """Generate an exportable Markdown verification audit report.

    Args:
        report: Document verification report.

    Returns:
        str: Markdown formatted document text.
    """
    date_str = (
        report.processed_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        if hasattr(report.processed_at, "strftime")
        else str(report.processed_at)
    )

    tot = max(1, report.total_claims)
    pct_v = f"{int(report.verified_count / tot * 100)}%"
    pct_i = f"{int(report.inaccurate_count / tot * 100)}%"
    pct_f = f"{int(report.false_count / tot * 100)}%"
    pct_u = f"{int(report.unverified_count / tot * 100)}%"

    lines = [
        f"# TruthLayer Fact-Checking Audit Report",
        "",
        f"**Source Document:** `{report.document_name}`  ",
        f"**Analysis Timestamp:** `{date_str}`  ",
        f"**Total Pages Analyzed:** {report.total_pages}  ",
        f"**Total Claims Evaluated:** {report.total_claims}  ",
        "",
        "---",
        "",
        "## Executive Summary Scorecard",
        "",
        "| Verification Status | Count | Share (%) | Description |",
        "| :--- | :---: | :---: | :--- |",
        f"| 🟢 **Verified** | **{report.verified_count}** | {pct_v} | Corroborated by reliable web evidence. |",
        f"| 🟠 **Inaccurate** | **{report.inaccurate_count}** | {pct_i} | Partially incorrect, outdated, or wrong context. |",
        f"| 🔴 **False** | **{report.false_count}** | {pct_f} | Directly contradicted by reliable evidence. |",
        f"| ⚪ **Unverified** | **{report.unverified_count}** | {pct_u} | Evidence insufficient, absent, or inconclusive. |",
        "",
        "---",
        "",
        "## Itemized Claim Verification Ledger",
        "",
    ]

    if not report.results:
        lines.append("*No factual claims were identified in this document.*")
    else:
        for item in report.results:
            conf_str = _format_confidence_label(item.confidence)
            lines.append(f"### Claim [{item.claim_id}] (Page {item.page_number}) — {item.status.value}")
            lines.append(f"> \"{item.original_claim}\"")
            lines.append("")
            lines.append(f"- **Status:** `{item.status.value}`")
            lines.append(f"- **Confidence:** {conf_str}")
            lines.append(f"- **Evaluation:** {item.explanation}")

            if item.corrected_information:
                lines.append(f"- **💡 Verified Correction:** {item.corrected_information}")

            if item.evidence_summary:
                lines.append(f"- **Evidence Summary:** {item.evidence_summary}")

            if item.verification_notes:
                lines.append(f"- **📌 Notes:** {item.verification_notes}")

            if item.sources:
                lines.append("- **Supporting / Contradicting Sources:**")
                for src in item.sources:
                    pub = f" (Published: {src.publication_date})" if src.publication_date else ""
                    type_str = f"`[{src.evidence_type.capitalize()}]`" if src.evidence_type else ""
                    lines.append(f"  - {type_str} [{src.title}]({src.url}){pub}")
            else:
                lines.append("- **Sources:** None available (conservative unverified default).")

            lines.append("")

    lines.append("---")
    lines.append("*Report generated automatically by TruthLayer AI Fact-Checking Engine. Verify facts. Build trust.*")
    return "\n".join(lines)


def generate_json_report(report: VerificationReport) -> str:
    """Generate structured JSON verification audit data for programmatic integration.

    Args:
        report: Document verification report.

    Returns:
        str: Indented JSON string.
    """
    return report.model_dump_json(indent=2)
