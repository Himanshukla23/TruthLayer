"""PDF text extraction module for TruthLayer using PyMuPDF."""

import re
from typing import List, Optional
import pymupdf
from src.models.schemas import PageExtraction, PDFExtractionResult
from src.utils.logger import get_logger
from src.utils.exceptions import (
    PDFProcessingError,
    PDFTextExtractionError,
    PDFCorruptedError,
    PDFPasswordProtectedError,
    PDFScannedDocumentError,
)

logger = get_logger("truthlayer.core.pdf_processor")


def clean_page_text(raw_text: str) -> str:
    """Normalize extracted page text by trimming excess whitespace and collapsing blank lines.

    Args:
        raw_text: Raw string extracted from a PDF page.

    Returns:
        Cleaned string preserving sentence and paragraph integrity.
    """
    if not raw_text:
        return ""

    # Replace non-breaking spaces and exotic space characters with standard ASCII space
    text = raw_text.replace("\xa0", " ").replace("\u200b", "")

    # Strip trailing whitespace on each line
    lines = [line.rstrip() for line in text.splitlines()]

    # Collapse sequences of 3 or more empty lines down to double newline (paragraph break)
    cleaned_lines: List[str] = []
    consecutive_empty = 0

    for line in lines:
        if not line.strip():
            consecutive_empty += 1
            if consecutive_empty <= 1:
                cleaned_lines.append("")
        else:
            consecutive_empty = 0
            cleaned_lines.append(line)

    result = "\n".join(cleaned_lines).strip()
    return result


def extract_text_from_pdf(
    file_name: str,
    file_bytes: bytes,
    max_pages: Optional[int] = None,
) -> PDFExtractionResult:
    """Extract text from uploaded PDF bytes page-by-page while preserving page numbers.

    Args:
        file_name: Name of the uploaded PDF file.
        file_bytes: Binary content of the PDF.
        max_pages: Optional maximum number of pages to process.

    Returns:
        Structured PDFExtractionResult containing per-page extractions, totals, and status.

    Raises:
        PDFCorruptedError: When PDF cannot be opened or is malformed.
        PDFPasswordProtectedError: When PDF is encrypted.
    """
    if not file_bytes:
        return PDFExtractionResult(
            document_name=file_name,
            total_pages=0,
            extraction_status="failed",
            error_message="Empty file bytes provided for extraction.",
        )

    doc = None
    try:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:
        logger.error(f"Failed to open PDF '{file_name}': {exc}")
        return PDFExtractionResult(
            document_name=file_name,
            total_pages=0,
            extraction_status="failed",
            error_message=f"Corrupted or invalid PDF structure: {str(exc)}",
        )

    try:
        # Check for password encryption
        if doc.is_encrypted:
            logger.warning(f"PDF '{file_name}' is password-protected.")
            return PDFExtractionResult(
                document_name=file_name,
                total_pages=0,
                extraction_status="failed",
                error_message="Document is password-protected. Unencrypted PDFs are required.",
            )

        total_pages = doc.page_count
        if total_pages == 0:
            logger.warning(f"PDF '{file_name}' contains 0 pages.")
            return PDFExtractionResult(
                document_name=file_name,
                total_pages=0,
                extraction_status="failed",
                error_message="Document contains 0 pages.",
            )

        # Apply max_pages boundary if specified
        pages_to_process = total_pages
        if max_pages and max_pages > 0:
            pages_to_process = min(total_pages, max_pages)

        extracted_pages: List[PageExtraction] = []
        total_characters = 0
        has_embedded_images = False

        for page_idx in range(pages_to_process):
            page_number = page_idx + 1  # 1-indexed
            page = doc[page_idx]

            # Check if page has images (useful for detecting scanned documents)
            if not has_embedded_images and len(page.get_images()) > 0:
                has_embedded_images = True

            raw_text = page.get_text("text") or ""
            cleaned_text = clean_page_text(raw_text)
            char_count = len(cleaned_text)

            is_empty = (char_count == 0)
            if not is_empty:
                total_characters += char_count

            extracted_pages.append(
                PageExtraction(
                    page_number=page_number,
                    text=cleaned_text,
                    character_count=char_count,
                    is_empty=is_empty,
                )
            )

        # Detect Scanned vs. Empty vs. Successful documents
        if total_characters == 0:
            if has_embedded_images:
                logger.info(f"PDF '{file_name}' has 0 text characters but embedded images: flagged as scanned.")
                return PDFExtractionResult(
                    document_name=file_name,
                    total_pages=total_pages,
                    extraction_status="scanned",
                    pages=extracted_pages,
                    total_characters=0,
                    is_scanned_document=True,
                    error_message=(
                        "Document appears to be scanned or contains image-only pages without selectable text. "
                        "OCR is not yet supported in this version."
                    ),
                )
            else:
                logger.info(f"PDF '{file_name}' has 0 text characters: flagged as empty.")
                return PDFExtractionResult(
                    document_name=file_name,
                    total_pages=total_pages,
                    extraction_status="empty",
                    pages=extracted_pages,
                    total_characters=0,
                    is_scanned_document=False,
                    error_message="Document contains no extractable text.",
                )

        # Scanned heuristic: multi-page PDF with very low text density (< 50 chars total) and images
        if total_characters < 50 and has_embedded_images:
            logger.info(f"PDF '{file_name}' has low text density ({total_characters} chars) and images: flagged as scanned.")
            return PDFExtractionResult(
                document_name=file_name,
                total_pages=total_pages,
                extraction_status="scanned",
                pages=extracted_pages,
                total_characters=total_characters,
                is_scanned_document=True,
                error_message=(
                    "Document appears to be predominantly scanned or image-based with insufficient extractable text. "
                    "OCR is not yet supported in this version."
                ),
            )

        logger.info(
            f"Successfully extracted text from '{file_name}': {len(extracted_pages)} pages, "
            f"{total_characters} characters."
        )

        return PDFExtractionResult(
            document_name=file_name,
            total_pages=total_pages,
            extraction_status="success",
            pages=extracted_pages,
            total_characters=total_characters,
            is_scanned_document=False,
            error_message=None,
        )

    finally:
        if doc is not None:
            doc.close()
