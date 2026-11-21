"""Unit tests for Phase 3 - PDF Text Extraction module."""

import io
import pytest
import pymupdf
from src.core.pdf_processor import extract_text_from_pdf, clean_page_text
from src.models.schemas import PDFExtractionResult


def create_single_page_pdf(text: str = "TruthLayer validates empirical claims.") -> bytes:
    """Generate in-memory single-page PDF with specific text."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 72), text, fontsize=12)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def create_multi_page_pdf(pages_text: list) -> bytes:
    """Generate in-memory multi-page PDF with distinct text per page."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page(width=595, height=842)
        if text:  # Insert text only if not empty string
            page.insert_text((50, 72), text, fontsize=12)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def create_scanned_style_pdf() -> bytes:
    """Generate in-memory PDF that contains an embedded image but zero selectable text."""
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)

    # Create a small dummy 100x100 pixmap (RGB image)
    pix = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 100, 100), 0)
    pix.clear_with(255)  # white image
    img_bytes = pix.tobytes("png")

    # Insert image into page (without adding any text)
    rect = pymupdf.Rect(50, 50, 200, 200)
    page.insert_image(rect, stream=img_bytes)

    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


class TestPDFProcessor:
    """Test suite verifying all acceptance criteria for PDF text extraction."""

    def test_single_page_pdf_extraction(self):
        sample_text = "Global SaaS market valuation reached $195B in 2023."
        pdf_bytes = create_single_page_pdf(sample_text)

        result: PDFExtractionResult = extract_text_from_pdf("single_page.pdf", pdf_bytes)

        assert result.extraction_status == "success"
        assert result.total_pages == 1
        assert len(result.pages) == 1
        assert result.pages[0].page_number == 1
        assert sample_text in result.pages[0].text
        assert result.pages[0].character_count == len(sample_text)
        assert result.pages[0].is_empty is False
        assert result.is_scanned_document is False

    def test_multi_page_pdf_extraction(self):
        pages_content = [
            "Executive Summary: Revenue grew by 24% year-over-year.",
            "Market Analysis: Sector adoption surged in Q3 2023.",
            "Conclusion: Strategic expansion planned for Q1 2024.",
        ]
        pdf_bytes = create_multi_page_pdf(pages_content)

        result: PDFExtractionResult = extract_text_from_pdf("multi_page.pdf", pdf_bytes)

        assert result.extraction_status == "success"
        assert result.total_pages == 3
        assert len(result.pages) == 3

        # Verify page numbering is preserved (1, 2, 3)
        for idx, page in enumerate(result.pages):
            assert page.page_number == idx + 1
            assert pages_content[idx] in page.text
            assert page.is_empty is False

        assert "24%" in result.full_text
        assert "Q1 2024" in result.full_text

    def test_mixed_text_and_empty_pages(self):
        # Page 1 has text, Page 2 is empty, Page 3 has text
        pages_content = [
            "First section has empirical data.",
            "",  # Empty page
            "Third section has final conclusions.",
        ]
        pdf_bytes = create_multi_page_pdf(pages_content)

        result: PDFExtractionResult = extract_text_from_pdf("mixed.pdf", pdf_bytes)

        assert result.extraction_status == "success"
        assert result.total_pages == 3
        assert result.pages[0].is_empty is False
        assert result.pages[1].is_empty is True
        assert result.pages[1].character_count == 0
        assert result.pages[1].text == ""
        assert result.pages[2].is_empty is False

    def test_empty_pdf_detection(self):
        # 2 completely blank pages
        pdf_bytes = create_multi_page_pdf(["", ""])

        result: PDFExtractionResult = extract_text_from_pdf("empty.pdf", pdf_bytes)

        assert result.extraction_status == "empty"
        assert result.total_characters == 0
        assert "contains no extractable text" in result.error_message.lower()

    def test_scanned_pdf_detection(self):
        # PDF with embedded image and no selectable text
        pdf_bytes = create_scanned_style_pdf()

        result: PDFExtractionResult = extract_text_from_pdf("scanned_contract.pdf", pdf_bytes)

        assert result.is_scanned_document is True
        assert result.extraction_status == "scanned"
        assert "scanned" in result.error_message.lower()
        assert "OCR is not yet supported" in result.error_message

    def test_corrupted_pdf_handling(self):
        garbage_bytes = b"NOT_A_VALID_PDF_STREAM_12345"
        result: PDFExtractionResult = extract_text_from_pdf("corrupt.pdf", garbage_bytes)

        assert result.extraction_status == "failed"
        assert result.total_pages == 0
        assert "Corrupted or invalid" in result.error_message

    def test_empty_byte_stream_handling(self):
        result: PDFExtractionResult = extract_text_from_pdf("zero_bytes.pdf", b"")

        assert result.extraction_status == "failed"
        assert result.total_pages == 0
        assert "Empty file bytes" in result.error_message

    def test_whitespace_normalization(self):
        messy_text = "Paragraph One.\n\n\n\n\n   \nParagraph Two with spaces   "
        cleaned = clean_page_text(messy_text)
        assert "\n\n\n" not in cleaned
        assert cleaned == "Paragraph One.\n\nParagraph Two with spaces"

    def test_max_pages_constraint(self):
        pages_content = [f"Page {i} content text." for i in range(1, 6)]
        pdf_bytes = create_multi_page_pdf(pages_content)

        # Enforce max_pages = 2
        result: PDFExtractionResult = extract_text_from_pdf("limited.pdf", pdf_bytes, max_pages=2)

        assert result.total_pages == 5  # Document total
        assert len(result.pages) == 2   # Processed count capped to 2
        assert result.pages[0].page_number == 1
        assert result.pages[1].page_number == 2
