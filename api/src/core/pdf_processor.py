"""PDF text extraction module for TruthLayer using PyMuPDF."""

import re
from typing import List, Optional
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


def _extract_text_with_pypdf(
    file_name: str,
    file_bytes: bytes,
    max_pages: Optional[int] = None,
) -> PDFExtractionResult:
    """Pure-Python fallback extractor using pypdf (zero C-library dependencies, 100% serverless safe)."""
    import io
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))

        if reader.is_encrypted:
            return PDFExtractionResult(
                document_name=file_name,
                total_pages=0,
                extraction_status="failed",
                error_message="Document is password-protected. Unencrypted PDFs are required.",
            )

        total_pages = len(reader.pages)
        if total_pages == 0:
            return PDFExtractionResult(
                document_name=file_name,
                total_pages=0,
                extraction_status="failed",
                error_message="Document contains 0 pages.",
            )

        pages_to_process = min(total_pages, max_pages) if max_pages and max_pages > 0 else total_pages
        extracted_pages: List[PageExtraction] = []
        total_characters = 0
        has_embedded_images = False

        for page_idx in range(pages_to_process):
            page_number = page_idx + 1
            page = reader.pages[page_idx]

            if not has_embedded_images:
                try:
                    if len(page.images) > 0:
                        has_embedded_images = True
                except Exception:
                    pass

            raw_text = page.extract_text() or ""
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

        logger.info(f"Successfully extracted text via pypdf: {len(extracted_pages)} pages, {total_characters} characters.")
        return PDFExtractionResult(
            document_name=file_name,
            total_pages=total_pages,
            extraction_status="success",
            pages=extracted_pages,
            total_characters=total_characters,
            is_scanned_document=False,
            error_message=None,
        )
    except Exception as exc:
        logger.error(f"pypdf fallback extraction failed for '{file_name}': {exc}")
        return PDFExtractionResult(
            document_name=file_name,
            total_pages=0,
            extraction_status="failed",
            error_message=f"Corrupted or invalid PDF structure: {str(exc)}",
        )


def extract_text_from_pdf(
    file_name: str,
    file_bytes: bytes,
    max_pages: Optional[int] = None,
) -> PDFExtractionResult:
    """Extract text from uploaded PDF bytes page-by-page while preserving page numbers.

    Uses pure-Python pypdf as the primary serverless extractor with zero C-library dependencies.

    Args:
        file_name: Name of the uploaded PDF file.
        file_bytes: Binary content of the PDF.
        max_pages: Optional maximum number of pages to process.

    Returns:
        Structured PDFExtractionResult containing per-page extractions, totals, and status.
    """
    if not file_bytes:
        return PDFExtractionResult(
            document_name=file_name,
            total_pages=0,
            extraction_status="failed",
            error_message="Empty file bytes provided for extraction.",
        )

    # Use pure-Python pypdf as primary, 100% reliable serverless extractor
    return _extract_text_with_pypdf(file_name, file_bytes, max_pages)
