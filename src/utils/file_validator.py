"""PDF upload validation utility for TruthLayer."""

from typing import Optional
from pydantic import BaseModel, Field

# Standard PDF magic byte sequence
PDF_HEADER_SIGNATURE = b"%PDF-"
PDF_EOF_SIGNATURE = b"%%EOF"


class FileValidationResult(BaseModel):
    """Encapsulates the result of a PDF file validation check."""

    is_valid: bool = Field(..., description="Whether the file passed all validation checks")
    error_message: Optional[str] = Field(default=None, description="User-facing error explanation if invalid")
    file_name: str = Field(..., description="Name of the uploaded file")
    file_size_bytes: int = Field(default=0, ge=0, description="Size of file in bytes")
    formatted_size: str = Field(default="0 B", description="Human-readable file size")
    page_count: Optional[int] = Field(default=None, description="Page count if safely read without extraction")


def format_file_size(size_bytes: int) -> str:
    """Format an integer byte count into a human-readable string (B, KB, MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def validate_uploaded_pdf(
    file_name: str,
    file_bytes: bytes,
    max_size_mb: int = 20,
) -> FileValidationResult:
    """Validate uploaded document for valid PDF format, non-empty content, and size limits.

    Args:
        file_name: Name of the uploaded file.
        file_bytes: Raw binary content of the file.
        max_size_mb: Maximum allowed file size in megabytes (default: 20 MB).

    Returns:
        FileValidationResult containing validity boolean and descriptive error message if invalid.
    """
    total_bytes = len(file_bytes)
    formatted_size = format_file_size(total_bytes)

    # 1. Check file extension
    if not file_name.lower().endswith(".pdf"):
        return FileValidationResult(
            is_valid=False,
            error_message=f"Invalid file type: '{file_name}'. Only PDF (.pdf) documents are accepted.",
            file_name=file_name,
            file_size_bytes=total_bytes,
            formatted_size=formatted_size,
        )

    # 2. Check for empty file (0 bytes)
    if total_bytes == 0:
        return FileValidationResult(
            is_valid=False,
            error_message="Empty document: The uploaded file contains 0 bytes. Please select a valid PDF.",
            file_name=file_name,
            file_size_bytes=0,
            formatted_size="0 B",
        )

    # 3. Check file size ceiling (20 MB)
    max_bytes = max_size_mb * 1024 * 1024
    if total_bytes > max_bytes:
        return FileValidationResult(
            is_valid=False,
            error_message=(
                f"File size limit exceeded: The uploaded file is {formatted_size}, which exceeds the "
                f"maximum allowed limit of {max_size_mb} MB. Please upload a smaller document."
            ),
            file_name=file_name,
            file_size_bytes=total_bytes,
            formatted_size=formatted_size,
        )

    # 4. Check PDF Magic Header (%PDF-)
    # Check within the first 1024 bytes to accommodate optional UTF-8 BOM or small preambles
    header_window = file_bytes[:1024]
    if PDF_HEADER_SIGNATURE not in header_window:
        return FileValidationResult(
            is_valid=False,
            error_message=(
                "Invalid or corrupted PDF format: The file lacks a valid PDF header signature (%PDF-). "
                "Please verify that the file is an authentic PDF and not a renamed non-PDF file."
            ),
            file_name=file_name,
            file_size_bytes=total_bytes,
            formatted_size=formatted_size,
        )

    # 5. Check structural validity via pure-Python pypdf (100% serverless safe)
    try:
        import io
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            return FileValidationResult(
                is_valid=False,
                error_message="Password protected: The uploaded PDF is encrypted. Please provide an unencrypted PDF.",
                file_name=file_name,
                file_size_bytes=total_bytes,
                formatted_size=formatted_size,
            )
        page_count = len(reader.pages)
        if page_count == 0:
            return FileValidationResult(
                is_valid=False,
                error_message="Corrupted PDF: Document contains 0 pages.",
                file_name=file_name,
                file_size_bytes=total_bytes,
                formatted_size=formatted_size,
            )
        return FileValidationResult(
            is_valid=True,
            error_message=None,
            file_name=file_name,
            file_size_bytes=total_bytes,
            formatted_size=formatted_size,
            page_count=page_count,
        )
    except Exception as exc:
        return FileValidationResult(
            is_valid=False,
            error_message=f"Corrupted PDF file: Unable to parse document structure ({str(exc)}).",
            file_name=file_name,
            file_size_bytes=total_bytes,
            formatted_size=formatted_size,
        )
