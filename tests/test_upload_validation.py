"""Unit tests for Phase 2 - PDF Upload, File Validation, and Dashboard Helpers."""

import io
import pytest
from src.utils.file_validator import validate_uploaded_pdf, format_file_size, FileValidationResult


def create_minimal_pdf_bytes() -> bytes:
    """Generate minimal valid PDF binary payload with standard headers and EOF."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"0000000010 00000 n \n"
        b"0000000060 00000 n \n"
        b"0000000117 00000 n \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n193\n%%EOF"
    )


class TestFileValidation:
    """Verify acceptance criteria for PDF file validation."""

    def test_valid_pdf_passes_validation(self):
        pdf_bytes = create_minimal_pdf_bytes()
        result = validate_uploaded_pdf(file_name="annual_report.pdf", file_bytes=pdf_bytes, max_size_mb=20)
        assert result.is_valid is True
        assert result.error_message is None
        assert result.file_name == "annual_report.pdf"
        assert result.file_size_bytes == len(pdf_bytes)
        assert result.page_count == 1
        assert "KB" in result.formatted_size or "B" in result.formatted_size

    def test_uppercase_pdf_extension_is_accepted(self):
        pdf_bytes = create_minimal_pdf_bytes()
        result = validate_uploaded_pdf(file_name="MARKET_RESEARCH.PDF", file_bytes=pdf_bytes, max_size_mb=20)
        assert result.is_valid is True
        assert result.error_message is None

    def test_non_pdf_extension_rejected(self):
        result = validate_uploaded_pdf(
            file_name="malicious_payload.exe",
            file_bytes=b"MZ\x90\x00\x03\x00\x00\x00",
            max_size_mb=20,
        )
        assert result.is_valid is False
        assert "Only PDF (.pdf) documents are accepted" in result.error_message

    def test_docx_file_rejected(self):
        result = validate_uploaded_pdf(
            file_name="document.docx",
            file_bytes=b"PK\x03\x04SomeDocxContent",
            max_size_mb=20,
        )
        assert result.is_valid is False
        assert "Only PDF (.pdf) documents are accepted" in result.error_message

    def test_empty_file_rejected(self):
        result = validate_uploaded_pdf(file_name="empty_doc.pdf", file_bytes=b"", max_size_mb=20)
        assert result.is_valid is False
        assert "Empty document" in result.error_message
        assert result.file_size_bytes == 0

    def test_fake_pdf_corrupted_header_rejected(self):
        # File named .pdf but containing plain text or corrupted header
        fake_bytes = b"This is just a text file renamed to .pdf"
        result = validate_uploaded_pdf(file_name="fake.pdf", file_bytes=fake_bytes, max_size_mb=20)
        assert result.is_valid is False
        assert "lacks a valid PDF header signature" in result.error_message

    def test_oversized_file_rejected(self):
        # Max size set to 1 MB for test, upload 2 MB payload with valid header
        oversized_bytes = b"%PDF-1.4\n" + (b"X" * (2 * 1024 * 1024))
        result = validate_uploaded_pdf(
            file_name="large_whitepaper.pdf",
            file_bytes=oversized_bytes,
            max_size_mb=1,  # 1 MB threshold for test
        )
        assert result.is_valid is False
        assert "File size limit exceeded" in result.error_message
        assert "1 MB" in result.error_message

    def test_size_formatting_helper(self):
        assert format_file_size(500) == "500 B"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(20 * 1024 * 1024) == "20.00 MB"
