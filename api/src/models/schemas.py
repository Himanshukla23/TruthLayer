"""Data models and schemas for TruthLayer."""

from enum import Enum
from typing import Any, List, Optional
from datetime import datetime, timezone
from urllib.parse import urlparse
from pydantic import BaseModel, Field, model_validator


# ==========================================
# Phase 3: PDF Ingestion & Text Extraction
# ==========================================

class PageExtraction(BaseModel):
    """Extracted text and metadata for a single PDF page."""

    page_number: int = Field(..., ge=1, description="1-indexed document page number")
    text: str = Field(..., description="Extracted and cleaned text from the page")
    character_count: int = Field(..., ge=0, description="Character count of cleaned text")
    is_empty: bool = Field(default=False, description="Whether the page contains no extractable text")

    @property
    def char_count(self) -> int:
        return self.character_count


class PDFExtractionResult(BaseModel):
    """Structured extraction result for an entire PDF document."""

    document_name: str = Field(..., description="Name of the parsed PDF document")
    total_pages: int = Field(..., ge=0, description="Total number of pages in the document")
    extraction_status: str = Field(
        default="success",
        description="Status: 'success', 'failed', 'empty', or 'scanned'"
    )
    pages: List[PageExtraction] = Field(
        default_factory=list,
        description="List of extracted page models"
    )
    total_characters: int = Field(
        default=0,
        ge=0,
        description="Total characters extracted across all pages"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Explanatory error message if extraction failed or is partial"
    )
    is_scanned_document: bool = Field(
        default=False,
        description="True if document appears to be scanned or image-based without selectable text"
    )

    @property
    def full_text(self) -> str:
        """Concatenated full text across all pages separated by newlines."""
        return "\n\n".join(p.text for p in self.pages if not p.is_empty)


# ==========================================
# Phase 4: AI-Based Claim Extraction
# ==========================================

class ExtractedClaimItem(BaseModel):
    """Discrete factual assertion extracted from a PDF page."""

    claim_id: str = Field(..., description="Unique claim identifier, e.g. 'C001'")
    original_claim: str = Field(..., min_length=3, description="Exact factual assertion extracted from text")
    claim_type: str = Field(
        default="General Fact",
        description="Classification: Statistic, Financial, Market Forecast, Date / Event, Technical, General Fact"
    )
    page_number: int = Field(..., ge=1, description="1-indexed source PDF page number")
    entities: List[str] = Field(default_factory=list, description="Key entities involved in the claim")
    numbers: List[str] = Field(default_factory=list, description="Numbers, percentages, financial amounts")
    dates: List[str] = Field(default_factory=list, description="Calendar dates, years, quarters, timeframes")
    requires_verification: bool = Field(default=True, description="Flag indicating external verification is needed")

    @property
    def id(self) -> str:
        return self.claim_id

    @property
    def claim_text(self) -> str:
        return self.original_claim


class ClaimExtractionResponse(BaseModel):
    """Structured output containing all factual claims extracted from a document."""

    document_name: str = Field(..., description="Source PDF document name")
    total_claims: int = Field(default=0, ge=0, description="Total number of claims extracted")
    claims: List[ExtractedClaimItem] = Field(
        default_factory=list,
        description="List of extracted factual claims"
    )
    extraction_model_used: Optional[str] = Field(
        default=None,
        description="Model name that performed the extraction (e.g. gemini-2.5-flash or groq/llama-3.3-70b-versatile)"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if claim extraction failed"
    )


# ==========================================
# Phase 5: Live Web Search & Evidence Retrieval
# ==========================================

class EvidenceItem(BaseModel):
    """Individual web citation retrieved as corroborating or refuting evidence."""

    source_title: str = Field(..., description="Web page title")
    source_url: str = Field(..., description="Direct source URL")
    source_domain: str = Field(..., description="Extracted source domain name")
    content_snippet: str = Field(..., description="Relevant text excerpt extracted from source")
    publication_date: Optional[str] = Field(default=None, description="Source publication date if available")
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp of retrieval"
    )
    relevance_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Search relevance score")

    @property
    def title(self) -> str:
        return self.source_title

    @property
    def url(self) -> str:
        return self.source_url

    @property
    def domain(self) -> str:
        return self.source_domain

    @property
    def snippet(self) -> str:
        return self.content_snippet


class ClaimEvidenceResult(BaseModel):
    """Corroborating web evidence collected for a specific factual claim."""

    claim_id: str = Field(..., description="Target claim identifier, e.g. 'C001'")
    original_claim: str = Field(..., description="Original claim text")
    search_queries: List[str] = Field(
        default_factory=list,
        description="List of targeted search queries executed"
    )
    evidence: List[EvidenceItem] = Field(
        default_factory=list,
        description="List of retrieved evidence sources"
    )
    search_status: str = Field(
        default="success",
        description="Status: 'success', 'no_results', or 'failed'"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if search failed"
    )

    @property
    def sources(self) -> List[EvidenceItem]:
        return self.evidence


class DocumentEvidenceResult(BaseModel):
    """Aggregate search and evidence retrieval results for an entire document."""

    document_name: str = Field(..., description="Source document name")
    total_claims_researched: int = Field(default=0, ge=0, description="Total claims researched")
    claims_evidence: List[ClaimEvidenceResult] = Field(
        default_factory=list,
        description="Per-claim evidence records"
    )
    total_sources_retrieved: int = Field(default=0, ge=0, description="Total unique evidence sources found")
    error_message: Optional[str] = Field(default=None, description="Error details if pipeline failed")


# ==========================================
# Phase 6 & 7: Verification & Reporting
# ==========================================

class VerificationStatus(str, Enum):
    """Standardized 4-state fact-checking classification."""
    VERIFIED = "VERIFIED"          # Reliable evidence sufficiently supports the original claim
    INACCURATE = "INACCURATE"      # The claim is partially incorrect, misleading, outdated or uses incorrect context
    FALSE = "FALSE"                # Reliable evidence directly contradicts the original claim
    UNVERIFIED = "UNVERIFIED"      # Available evidence is insufficient or inconclusive


class VerificationSourceCitation(BaseModel):
    """Source citation explicitly linked to a verification determination."""
    title: str = Field(..., description="Title of the cited source")
    url: str = Field(..., description="Actual retrieved source URL")
    publication_date: Optional[str] = Field(default=None, description="Publication date if available")
    evidence_type: str = Field(
        default="supporting",
        description="Relationship to claim: 'supporting', 'contradicting', or 'contextual'"
    )
    snippet: Optional[str] = Field(default="", description="Relevant excerpt from evidence")

    @property
    def source_title(self) -> str:
        return self.title

    @property
    def source_url(self) -> str:
        return self.url

    @property
    def source_domain(self) -> str:
        try:
            return urlparse(self.url).netloc
        except Exception:
            return ""

    @property
    def content_snippet(self) -> str:
        return self.snippet or ""


class ClaimVerificationResult(BaseModel):
    """Complete verification determination for an individual factual claim."""

    claim_id: str = Field(..., description="Unique claim identifier, e.g. 'C001'")
    original_claim: str = Field(..., description="Original claim text from document")
    status: VerificationStatus = Field(..., description="VERIFIED, INACCURATE, FALSE, or UNVERIFIED")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence in verdict (0.0 to 1.0)")
    explanation: str = Field(..., description="Objective explanation of the verdict grounded in evidence")
    corrected_information: Optional[str] = Field(
        default=None,
        description="Corrected accurate info supported by evidence if Inaccurate or False"
    )
    evidence_summary: Optional[str] = Field(
        default=None,
        description="Summary of supporting or contradicting evidence"
    )
    sources: List[VerificationSourceCitation] = Field(
        default_factory=list,
        description="List of cited sources directly supporting or refuting the claim"
    )
    verification_notes: Optional[str] = Field(
        default=None,
        description="Contextual limitations, reporting period notes, or conflicting source details"
    )
    page_number: int = Field(default=1, ge=1, description="Source page number in PDF")
    claim_type: str = Field(default="General Fact", description="Claim classification")

    @model_validator(mode="before")
    @classmethod
    def _map_backwards_compatible_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            # claim_text -> original_claim
            if "original_claim" not in values and "claim_text" in values:
                values["original_claim"] = values["claim_text"]
            # confidence_score -> confidence
            if "confidence" not in values and "confidence_score" in values:
                values["confidence"] = values["confidence_score"]
            # evidence_sources -> sources
            if "sources" not in values and "evidence_sources" in values:
                ev_sources = values.get("evidence_sources") or []
                mapped_sources = []
                for s in ev_sources:
                    if isinstance(s, dict):
                        mapped_sources.append(
                            VerificationSourceCitation(
                                title=s.get("title") or s.get("source_title", "Source"),
                                url=s.get("url") or s.get("source_url", ""),
                                publication_date=s.get("publication_date"),
                                evidence_type=s.get("evidence_type", "supporting"),
                                snippet=s.get("snippet") or s.get("content_snippet", ""),
                            )
                        )
                    elif hasattr(s, "source_url"):  # e.g. EvidenceItem
                        mapped_sources.append(
                            VerificationSourceCitation(
                                title=getattr(s, "source_title", "Source"),
                                url=getattr(s, "source_url", ""),
                                publication_date=getattr(s, "publication_date", None),
                                evidence_type="supporting",
                                snippet=getattr(s, "content_snippet", ""),
                            )
                        )
                    else:
                        mapped_sources.append(s)
                values["sources"] = mapped_sources
        return values

    # Compatibility accessors
    @property
    def claim_text(self) -> str:
        return self.original_claim

    @property
    def confidence_score(self) -> float:
        return self.confidence

    @property
    def evidence_sources(self) -> List[VerificationSourceCitation]:
        return self.sources


class VerificationReport(BaseModel):
    """Aggregate document verification report."""

    document_name: str = Field(..., description="Document filename")
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_pages: int = Field(default=0, ge=0)
    total_claims: int = Field(default=0, ge=0)
    verified_count: int = Field(default=0, ge=0)
    inaccurate_count: int = Field(default=0, ge=0)
    false_count: int = Field(default=0, ge=0)
    unverified_count: int = Field(default=0, ge=0)
    results: List[ClaimVerificationResult] = Field(default_factory=list)
