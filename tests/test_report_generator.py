"""Comprehensive unit tests for Phase 7 - Results Dashboard and Report Generation.

Validates PDF report generation, Markdown export, JSON certificates,
metadata embedding, 4-status scorecards, citations, corrections, and empty states.
"""

import json
import pytest
import pymupdf
from datetime import datetime, timezone

from src.models.schemas import (
    VerificationReport,
    ClaimVerificationResult,
    VerificationStatus,
    VerificationSourceCitation,
)
from src.core.report_generator import (
    generate_pdf_report,
    generate_markdown_report,
    generate_json_report,
    _format_confidence_label,
    _clean_text_for_xml,
)


def create_comprehensive_test_report() -> VerificationReport:
    """Create a realistic VerificationReport featuring all four statuses, multiple sources, and corrections."""
    results = [
        ClaimVerificationResult(
            claim_id="C001",
            original_claim="India's real GDP grew by 8.2% in fiscal year 2023-24.",
            page_number=1,
            claim_type="Macroeconomic Statistic",
            status=VerificationStatus.VERIFIED,
            confidence=0.98,
            explanation="Official release from MoSPI corroborates real GDP growth of 8.2% for FY 2023-24.",
            corrected_information=None,
            evidence_summary="Government economic release confirms exact 8.2% growth rate.",
            sources=[
                VerificationSourceCitation(
                    title="Ministry of Statistics GDP Press Release",
                    url="https://mospi.gov.in/gdp-2024",
                    publication_date="2024-05-31",
                    evidence_type="supporting",
                    snippet="Real GDP growth estimated at 8.2% for 2023-24.",
                ),
                VerificationSourceCitation(
                    title="Reserve Bank of India Annual Report",
                    url="https://rbi.org.in/annual-report",
                    publication_date="2024-06-15",
                    evidence_type="supporting",
                    snippet="Economic survey highlights 8.2% expansion in output.",
                ),
            ],
            verification_notes="Primary government statistical source.",
        ),
        ClaimVerificationResult(
            claim_id="C002",
            original_claim="Company Q3 revenue reached $15 billion.",
            page_number=2,
            claim_type="Financial Metric",
            status=VerificationStatus.INACCURATE,
            confidence=0.95,
            explanation="Regulatory 10-Q filing documents consolidated revenue of $12.4 billion, not $15 billion.",
            corrected_information="Official Q3 revenue was $12.4 billion.",
            evidence_summary="SEC 10-Q documents $12.4 billion in quarterly revenue.",
            sources=[
                VerificationSourceCitation(
                    title="SEC EDGAR Quarterly Form 10-Q",
                    url="https://sec.gov/edgar/filing123",
                    publication_date="2024-10-20",
                    evidence_type="contradicting",
                    snippet="Revenue was $12.4 billion for the third quarter.",
                )
            ],
            verification_notes="Claim overstates revenue by $2.6 billion.",
        ),
        ClaimVerificationResult(
            claim_id="C003",
            original_claim="Microsoft was founded by Steve Jobs in 1999.",
            page_number=3,
            claim_type="Historical Fact",
            status=VerificationStatus.FALSE,
            confidence=0.99,
            explanation="Microsoft was founded on April 4, 1975, by Bill Gates and Paul Allen, not Steve Jobs in 1999.",
            corrected_information="Microsoft was founded on April 4, 1975, by Bill Gates and Paul Allen.",
            evidence_summary="Official corporate history documents founding by Gates and Allen in 1975.",
            sources=[
                VerificationSourceCitation(
                    title="Microsoft Corporate History & Archives",
                    url="https://microsoft.com/en-us/about/history",
                    publication_date="2023-01-01",
                    evidence_type="contradicting",
                    snippet="Founded by Bill Gates and Paul Allen on April 4, 1975.",
                )
            ],
            verification_notes="Complete factual fabrication.",
        ),
        ClaimVerificationResult(
            claim_id="C004",
            original_claim="Internal proprietary ML model reduced operational latency by 99.4%.",
            page_number=4,
            claim_type="Proprietary Metric",
            status=VerificationStatus.UNVERIFIED,
            confidence=0.0,
            explanation="Insufficient public evidence found to substantiate or refute this proprietary internal claim.",
            corrected_information=None,
            evidence_summary="No external web sources retrieved for internal proprietary benchmark.",
            sources=[],
            verification_notes="Absence of evidence is never treated as falsity.",
        ),
    ]

    return VerificationReport(
        document_name="q3_corporate_presentation.pdf",
        processed_at=datetime(2026, 11, 22, 3, 0, 0, tzinfo=timezone.utc),
        total_pages=4,
        total_claims=4,
        verified_count=1,
        inaccurate_count=1,
        false_count=1,
        unverified_count=1,
        results=results,
    )


class TestReportGeneration:
    """Verify PDF, Markdown, and JSON report generation engines."""

    def test_pdf_report_structure_and_header(self):
        report = create_comprehensive_test_report()
        pdf_bytes = generate_pdf_report(report)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 2000
        assert pdf_bytes.startswith(b"%PDF-")

        # Open with PyMuPDF and verify page-level content
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        assert doc.page_count >= 1

        full_text = "".join(page.get_text() for page in doc)
        assert "TruthLayer" in full_text
        assert "Verification Audit Report" in full_text
        assert "q3_corporate_presentation.pdf" in full_text
        assert "Total Pages:" in full_text

    def test_pdf_scorecard_and_all_four_statuses_rendered(self):
        report = create_comprehensive_test_report()
        pdf_bytes = generate_pdf_report(report)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        full_text = "".join(page.get_text() for page in doc)

        # Statuses must be present in scorecard and claim headers
        assert "VERIFIED" in full_text
        assert "INACCURATE" in full_text
        assert "FALSE" in full_text
        assert "UNVERIFIED" in full_text

        # Verify claim IDs are present
        assert "[C001]" in full_text
        assert "[C002]" in full_text
        assert "[C003]" in full_text
        assert "[C004]" in full_text

    def test_pdf_contains_corrections_and_evidence(self):
        report = create_comprehensive_test_report()
        pdf_bytes = generate_pdf_report(report)
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        full_text = "".join(page.get_text() for page in doc)

        # Verified corrections
        assert "12.4 billion" in full_text
        assert "Bill Gates" in full_text

        # Sources
        assert "Ministry of Statistics" in full_text
        assert "SEC EDGAR" in full_text
        assert "Microsoft Corporate History" in full_text

        # Unverified fallback note
        assert "No external web evidence sources retrieved" in full_text

    def test_markdown_report_content_and_formatting(self):
        report = create_comprehensive_test_report()
        md_text = generate_markdown_report(report)

        assert isinstance(md_text, str)
        assert "# TruthLayer Fact-Checking Audit Report" in md_text
        assert "q3_corporate_presentation.pdf" in md_text
        assert "| 🟢 **Verified** | **1** |" in md_text
        assert "| 🟠 **Inaccurate** | **1** |" in md_text
        assert "| 🔴 **False** | **1** |" in md_text
        assert "| ⚪ **Unverified** | **1** |" in md_text

        # Claim headers
        assert "### Claim [C001]" in md_text
        assert "### Claim [C002]" in md_text
        assert "### Claim [C003]" in md_text
        assert "### Claim [C004]" in md_text

        # Corrections and links
        assert "Official Q3 revenue was $12.4 billion." in md_text
        assert "Microsoft was founded on April 4, 1975" in md_text
        assert "[Ministry of Statistics GDP Press Release](https://mospi.gov.in/gdp-2024)" in md_text

    def test_json_report_serialization_and_deserialization(self):
        report = create_comprehensive_test_report()
        json_str = generate_json_report(report)

        assert isinstance(json_str, str)
        parsed = json.loads(json_str)

        assert parsed["document_name"] == "q3_corporate_presentation.pdf"
        assert parsed["total_claims"] == 4
        assert parsed["verified_count"] == 1
        assert parsed["inaccurate_count"] == 1
        assert parsed["false_count"] == 1
        assert parsed["unverified_count"] == 1
        assert len(parsed["results"]) == 4

        # Validate round-trip back to Pydantic model
        restored = VerificationReport.model_validate(parsed)
        assert restored.document_name == report.document_name
        assert restored.total_claims == report.total_claims
        assert restored.results[1].corrected_information == "Official Q3 revenue was $12.4 billion."

    def test_empty_document_report_generation(self):
        empty_report = VerificationReport(
            document_name="empty_document.pdf",
            total_pages=1,
            total_claims=0,
            verified_count=0,
            inaccurate_count=0,
            false_count=0,
            unverified_count=0,
            results=[],
        )

        # PDF generation should not crash
        pdf_bytes = generate_pdf_report(empty_report)
        assert pdf_bytes.startswith(b"%PDF-")
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        text = doc[0].get_text()
        assert "empty_document.pdf" in text
        assert "No factual claims were identified" in text

        # Markdown should not crash
        md_text = generate_markdown_report(empty_report)
        assert "*No factual claims were identified in this document.*" in md_text

        # JSON should not crash
        json_str = generate_json_report(empty_report)
        assert '"total_claims": 0' in json_str

    def test_confidence_label_helper(self):
        assert "High Confidence" in _format_confidence_label(0.95)
        assert "Moderate Confidence" in _format_confidence_label(0.75)
        assert "Low Confidence" in _format_confidence_label(0.40)
        assert "No Evidence Found" in _format_confidence_label(0.0)

    def test_xml_text_cleaner_escaping(self):
        raw = 'Revenue was $10M & profits were <5% with "guaranteed" ROI > 0.'
        cleaned = _clean_text_for_xml(raw)

        assert "&dollar;" in cleaned
        assert "&amp;" in cleaned
        assert "&lt;" in cleaned
        assert "&gt;" in cleaned
        assert "&quot;" in cleaned
        assert "<" not in cleaned
        assert ">" not in cleaned
