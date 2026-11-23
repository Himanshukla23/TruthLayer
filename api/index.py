"""FastAPI serverless backend for TruthLayer on Vercel.

Exposes RESTful endpoints under /api/py/* connecting to the preserved
Python AI, extraction, search, verification, and report engines in src/.
"""

import os
import sys
import traceback

# Ensure project root is in sys.path so 'src' package can be imported on Vercel serverless
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import io
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

_BOOT_ERROR = None
try:
    from src.config import Settings, get_settings
    from src.core.claim_extractor import extract_claims_from_document
    from src.core.pdf_processor import extract_text_from_pdf
    from src.core.pipeline import run_full_pipeline
    from src.core.report_generator import (
        generate_json_report,
        generate_markdown_report,
        generate_pdf_report,
    )
    from src.core.search_service import search_evidence_for_claim
    from src.core.verifier import verify_single_claim
    from src.models.schemas import (
        ClaimEvidenceResult,
        ClaimExtractionResponse,
        ClaimVerificationResult,
        ExtractedClaimItem,
        PDFExtractionResult,
        VerificationReport,
        VerificationStatus,
    )
    from src.utils.exceptions import PDFCorruptedError, PDFPasswordProtectedError
    from src.utils.file_validator import validate_uploaded_pdf
    from src.utils.logger import get_logger
    logger = get_logger("truthlayer.api")
except Exception as _exc:
    _BOOT_ERROR = traceback.format_exc()

app = FastAPI(
    title="TruthLayer API",
    description="AI-Powered Empirical Fact-Checking & Provenance Verification Engine",
    version="1.0.0",
    docs_url="/api/py/docs",
    openapi_url="/api/py/openapi.json",
    redirect_slashes=False,
)

# Enable CORS for local development and Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Reusable clients
_TAVILY_CLIENT = None

def get_cached_tavily_client(api_key: str):
    global _TAVILY_CLIENT
    if _TAVILY_CLIENT is None:
        from tavily import TavilyClient
        _TAVILY_CLIENT = TavilyClient(api_key=api_key)
    return _TAVILY_CLIENT


@app.get("/api/py/health")
@app.get("/api/health")
@app.get("/health")
@app.get("/api/index/health")
@app.get("/api/index")
@app.get("/api/")
@app.get("/api")
@app.get("/")
async def health_check() -> Any:
    """Health status and API integration readiness check."""
    if _BOOT_ERROR:
        return JSONResponse(
            status_code=500,
            content={
                "status": "boot_error",
                "error": "Failed during startup imports",
                "traceback": _BOOT_ERROR,
            },
        )
    try:
        settings = get_settings()
        return {
            "status": "healthy",
            "service": "TruthLayer API",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "integrations": {
                "gemini": {
                    "configured": settings.is_gemini_configured,
                    "model": settings.gemini_model,
                },
                "tavily": {
                    "configured": settings.is_tavily_configured,
                },
                "groq": {
                    "configured": settings.is_groq_configured,
                    "model": settings.groq_model,
                },
            },
            "limits": {
                "max_upload_size_mb": 4.0,  # Vercel serverless request body ceiling
                "max_pdf_pages": settings.max_pdf_pages,
            },
        }
    except Exception as exc:
        return {
            "status": "error",
            "service": "TruthLayer API",
            "error": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@app.post("/api/py/extract-text", response_model=PDFExtractionResult)
@app.post("/api/extract-text", response_model=PDFExtractionResult)
@app.post("/api/index/extract-text", response_model=PDFExtractionResult)
@app.post("/extract-text", response_model=PDFExtractionResult)
async def extract_text_endpoint(
    file: UploadFile = File(...),
) -> PDFExtractionResult:
    """Step 1: Extract text page-by-page from uploaded PDF using PyMuPDF."""
    settings = get_settings()

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided.",
        )

    file_bytes = await file.read()
    val_result = validate_uploaded_pdf(
        file_name=file.filename,
        file_bytes=file_bytes,
        max_size_mb=4.0,
    )

    if not val_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=val_result.error_message or "Invalid PDF document.",
        )

    extraction_result = extract_text_from_pdf(
        file_name=file.filename,
        file_bytes=file_bytes,
        max_pages=settings.max_pdf_pages,
    )

    if extraction_result.is_scanned_document:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Scanned document detected. TruthLayer requires text-based PDFs. OCR is not yet supported.",
        )

    return extraction_result


@app.post("/api/py/search-claim-evidence", response_model=ClaimEvidenceResult)
@app.post("/api/search-claim-evidence", response_model=ClaimEvidenceResult)
@app.post("/api/index/search-claim-evidence", response_model=ClaimEvidenceResult)
@app.post("/search-claim-evidence", response_model=ClaimEvidenceResult)
async def search_claim_evidence_endpoint(
    claim: ExtractedClaimItem,
) -> ClaimEvidenceResult:
    """Step 3: Query live web evidence for a single claim via Tavily Search API."""
    settings = get_settings()
    if not settings.is_tavily_configured:
        return ClaimEvidenceResult(
            claim_id=claim.claim_id,
            original_claim=claim.original_claim,
            search_queries=[],
            evidence=[],
            search_status="no_api_key",
        )

    try:
        client = get_cached_tavily_client(settings.tavily_api_key)
        return search_evidence_for_claim(
            claim=claim,
            client=client,
            query_cache=None,
        )
    except Exception as exc:
        logger.error(f"Search evidence failed for {claim.claim_id}: {exc}")
        return ClaimEvidenceResult(
            claim_id=claim.claim_id,
            original_claim=claim.original_claim,
            search_queries=[],
            evidence=[],
            search_status=f"error: {str(exc)}",
        )


@app.post("/api/py/extract-claims", response_model=ClaimExtractionResponse)
@app.post("/api/extract-claims", response_model=ClaimExtractionResponse)
@app.post("/api/index/extract-claims", response_model=ClaimExtractionResponse)
@app.post("/extract-claims", response_model=ClaimExtractionResponse)
async def extract_claims_endpoint(
    file: UploadFile = File(...),
) -> Any:
    """Stage 1 & 2: Ingest PDF, extract text with PyMuPDF/pypdf, and isolate empirical claims with Gemini."""
    if _BOOT_ERROR:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backend startup error: {_BOOT_ERROR}",
        )
    try:
        settings = get_settings()

        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided.",
            )

        # Pre-check API key configuration
        if not settings.has_active_llm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing API Key: Please configure GEMINI_API_KEY in your Vercel Project Settings > Environment Variables, then redeploy.",
            )

        # Read binary bytes into memory (zero disk footprint)
        file_bytes = await file.read()

        # Validate file format and size (enforce 4.0 MB limit for Vercel)
        val_result = validate_uploaded_pdf(
            file_name=file.filename,
            file_bytes=file_bytes,
            max_size_mb=4.0,
        )

        if not val_result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=val_result.error_message or "Invalid PDF document.",
            )

        # Step 1: Text extraction via PyMuPDF with pypdf fallback
        extraction_result = extract_text_from_pdf(
            file_name=file.filename,
            file_bytes=file_bytes,
            max_pages=settings.max_pdf_pages,
        )

        if extraction_result.extraction_status == "failed":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=extraction_result.error_message or "Failed to extract text from PDF.",
            )

        if extraction_result.is_scanned_document:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Scanned document detected. TruthLayer requires text-based PDFs. OCR is not yet supported.",
            )

        if extraction_result.total_characters == 0 or extraction_result.extraction_status == "empty":
            return ClaimExtractionResponse(
                document_name=file.filename,
                total_claims=0,
                claims=[],
                extraction_model_used="None",
                error_message="No extractable text found in this PDF.",
            )

        # Step 2: Empirical claim isolation via Gemini (with Groq fallback)
        try:
            claims_response = extract_claims_from_document(
                extraction_result=extraction_result,
                settings=settings,
            )
            return claims_response
        except Exception as exc:
            logger.error(f"Claim extraction encountered an error: {exc}", exc_info=True)
            return ClaimExtractionResponse(
                document_name=file.filename,
                total_claims=0,
                claims=[],
                error_message=f"Claim extraction error: {str(exc)}",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Unexpected extraction endpoint error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server extraction error: {str(exc)}",
        )


class VerifySingleClaimRequest(BaseModel):
    claim: ExtractedClaimItem
    document_name: str


@app.post("/api/py/verify-single-claim", response_model=ClaimVerificationResult)
@app.post("/api/verify-single-claim", response_model=ClaimVerificationResult)
@app.post("/api/index/verify-single-claim", response_model=ClaimVerificationResult)
@app.post("/verify-single-claim", response_model=ClaimVerificationResult)
async def verify_single_claim_endpoint(
    request: VerifySingleClaimRequest,
) -> ClaimVerificationResult:
    """Stage 3 & 4: Query live web evidence via Tavily and verify a single claim via Gemini.

    Completes within 2-3 seconds, fully immune to Vercel Hobby 10-second timeouts.
    """
    settings = get_settings()
    claim = request.claim

    # Step 3: Query live web evidence via Tavily
    query_cache: Dict[str, Any] = {}
    evidence_result: ClaimEvidenceResult

    if settings.is_tavily_configured:
        try:
            client = get_cached_tavily_client(settings.tavily_api_key)
            evidence_result = search_evidence_for_claim(
                claim=claim,
                client=client,
                query_cache=None,
            )
        except Exception as exc:
            logger.error(f"Tavily search failed for claim {claim.claim_id}: {exc}")
            evidence_result = ClaimEvidenceResult(
                claim_id=claim.claim_id,
                original_claim=claim.original_claim,
                search_queries=[],
                evidence=[],
                search_status=f"error: {str(exc)}",
            )
    else:
        evidence_result = ClaimEvidenceResult(
            claim_id=claim.claim_id,
            original_claim=claim.original_claim,
            search_queries=[],
            evidence=[],
            search_status="no_api_key",
        )

    # Step 4: Verify claim veracity with Gemini reasoning
    decision = verify_single_claim(
        claim=claim,
        evidence_result=evidence_result,
        settings=settings,
    )

    return decision


@app.post("/api/py/verify-full-document", response_model=VerificationReport)
@app.post("/api/verify-full-document", response_model=VerificationReport)
@app.post("/api/index/verify-full-document", response_model=VerificationReport)
@app.post("/verify-full-document", response_model=VerificationReport)
async def verify_full_document_endpoint(
    file: UploadFile = File(...),
) -> VerificationReport:
    """Full monolithic pipeline execution for documents with few claims or Vercel Pro."""
    settings = get_settings()

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided.",
        )

    file_bytes = await file.read()
    val_result = validate_uploaded_pdf(
        file_name=file.filename,
        file_bytes=file_bytes,
        max_size_mb=4.0,
    )

    if not val_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=val_result.error_message or "Invalid PDF document.",
        )

    try:
        report = run_full_pipeline(
            file_name=file.filename,
            file_bytes=file_bytes,
            settings=settings,
        )
        return report
    except Exception as exc:
        logger.error(f"Full pipeline execution failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification pipeline failed: {str(exc)}",
        )


class GenerateReportRequest(BaseModel):
    report: VerificationReport
    format: str = "pdf"  # pdf | markdown | json


@app.post("/api/py/generate-report")
@app.post("/api/generate-report")
@app.post("/api/index/generate-report")
@app.post("/generate-report")
async def generate_report_endpoint(request: GenerateReportRequest) -> Response:
    """Generate in-memory downloadable verification audit report in PDF, Markdown, or JSON."""
    report = request.report
    export_format = request.format.lower().strip()
    clean_base_name = report.document_name.replace(".pdf", "").replace(" ", "_")

    if export_format == "pdf":
        pdf_bytes = generate_pdf_report(report)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{clean_base_name}_verification_audit.pdf"'
            },
        )
    elif export_format in ["markdown", "md"]:
        md_text = generate_markdown_report(report)
        return Response(
            content=md_text.encode("utf-8"),
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{clean_base_name}_verification_report.md"'
            },
        )
    elif export_format == "json":
        json_text = generate_json_report(report)
        return Response(
            content=json_text.encode("utf-8"),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{clean_base_name}_verification_data.json"'
            },
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{export_format}'. Choose 'pdf', 'markdown', or 'json'.",
        )
