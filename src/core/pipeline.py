"""End-to-end verification pipeline coordinator for TruthLayer."""

from typing import Callable, Optional
from src.config import Settings, get_settings
from src.core.pdf_processor import extract_text_from_pdf
from src.core.claim_extractor import extract_claims_from_document
from src.core.search_service import search_evidence_for_document
from src.core.verifier import verify_claims_for_document
from src.models.schemas import (
    PDFExtractionResult,
    ClaimExtractionResponse,
    DocumentEvidenceResult,
    VerificationReport,
)
from src.utils.logger import get_logger

logger = get_logger("truthlayer.core.pipeline")


def run_full_pipeline(
    file_name: str,
    file_bytes: bytes,
    settings: Optional[Settings] = None,
    progress_callback: Optional[Callable[[str, float], None]] = None,
) -> VerificationReport:
    """Execute the full end-to-end TruthLayer verification pipeline.

    Stages:
    1. PDF Text Extraction (PyMuPDF) - 25%
    2. AI Claim Extraction (Gemini / Groq) - 50%
    3. Live Web Search (Tavily) - 75%
    4. Fact Verification Engine (Gemini / Groq) - 100%

    Args:
        file_name: PDF document name.
        file_bytes: Raw binary content of the PDF.
        settings: Application settings with API keys.
        progress_callback: Optional callback reporting (stage_name, progress_float).

    Returns:
        VerificationReport containing document scorecard and verified claim results.
    """
    if settings is None:
        settings = get_settings()

    logger.info(f"Starting full verification pipeline for '{file_name}'...")

    # Stage 1: Text Extraction
    if progress_callback:
        progress_callback("Stage 1/4: Extracting text from PDF pages...", 0.1)

    extraction_result: PDFExtractionResult = extract_text_from_pdf(
        file_name=file_name,
        file_bytes=file_bytes,
        max_pages=settings.max_pdf_pages,
    )

    if extraction_result.total_characters == 0 or extraction_result.extraction_status != "success":
        logger.warning(f"Pipeline early exit: extraction status is '{extraction_result.extraction_status}'.")
        return VerificationReport(
            document_name=file_name,
            total_pages=extraction_result.total_pages,
            total_claims=0,
            verified_count=0,
            inaccurate_count=0,
            false_count=0,
            unverified_count=0,
            results=[],
        )

    # Stage 2: AI Claim Extraction
    if progress_callback:
        progress_callback("Stage 2/4: Isolating empirical claims with AI...", 0.35)

    claims_response: ClaimExtractionResponse = extract_claims_from_document(
        extraction_result=extraction_result,
        settings=settings,
    )

    if claims_response.total_claims == 0 or not claims_response.claims:
        logger.info(f"No claims extracted from '{file_name}'.")
        return VerificationReport(
            document_name=file_name,
            total_pages=extraction_result.total_pages,
            total_claims=0,
            verified_count=0,
            inaccurate_count=0,
            false_count=0,
            unverified_count=0,
            results=[],
        )

    # Stage 3: Live Web Evidence Search
    if progress_callback:
        progress_callback("Stage 3/4: Querying live web evidence via Tavily...", 0.65)

    evidence_doc: DocumentEvidenceResult = search_evidence_for_document(
        claims_response=claims_response,
        settings=settings,
    )

    # Stage 4: Fact Verification Engine
    if progress_callback:
        progress_callback("Stage 4/4: Cross-referencing claims against evidence...", 0.85)

    report: VerificationReport = verify_claims_for_document(
        claims_response=claims_response,
        evidence_doc=evidence_doc,
        settings=settings,
    )

    if progress_callback:
        progress_callback("Verification complete!", 1.0)

    logger.info(
        f"Pipeline complete for '{file_name}': {report.total_claims} claims "
        f"({report.verified_count} Verified, {report.inaccurate_count} Inaccurate, "
        f"{report.false_count} False, {report.unverified_count} Unverified)."
    )

    return report
