"""Live Web Search and Evidence Retrieval Module using Tavily Search API."""

import re
import urllib.parse
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Set
from tavily import TavilyClient

from src.config import Settings, get_settings
from src.models.schemas import (
    ExtractedClaimItem,
    ClaimExtractionResponse,
    EvidenceItem,
    ClaimEvidenceResult,
    DocumentEvidenceResult,
)
from src.utils.logger import get_logger
from src.utils.exceptions import SearchServiceError

logger = get_logger("truthlayer.core.search_service")

# Domains recognized as high-authority institutional or reporting sources
AUTHORITATIVE_TLDS = (".gov", ".edu", ".org", ".int")
REPUTABLE_DOMAINS = {
    "reuters.com", "bloomberg.com", "apnews.com", "bbc.com", "bbc.co.uk",
    "wsj.com", "ft.com", "nytimes.com", "theguardian.com", "cnbc.com",
    "forbes.com", "worldbank.org", "imf.org", "who.int", "oecd.org",
    "sec.gov", "census.gov", "bls.gov", "federalreserve.gov", "statista.com",
    "nature.com", "science.org", "sciencedirect.com", "arxiv.org", "nasa.gov",
    "wikipedia.org"
}

# Module-level query cache to prevent redundant live searches across identical assertions
_GLOBAL_SEARCH_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def extract_domain(url: str) -> str:
    """Extract clean domain name without leading www. from a URL.

    Args:
        url: Full HTTP/HTTPS URL string.

    Returns:
        Cleaned domain string (e.g. 'reuters.com').
    """
    if not url:
        return "unknown"
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or "unknown"
    except Exception:
        return "unknown"


def generate_search_queries(claim: ExtractedClaimItem) -> List[str]:
    """Generate 2 to 3 targeted, diverse search queries for a factual claim.

    Strategy:
    1. Direct factual query: Core assertion cleaned of excess punctuation.
    2. Quantitative / Entity query: Primary entities + exact numbers/dates.
    3. Counter / Verification query: Entity + timeframe + verification keywords to uncover disputes.

    Args:
        claim: Extracted claim item with entities, numbers, and dates.

    Returns:
        List of 2 to 3 distinct search query strings.
    """
    queries: List[str] = []

    # Clean claim text of surrounding quotes and noisy punctuation
    cleaned_claim = re.sub(r'["\']', '', claim.original_claim).strip()
    words = cleaned_claim.split()

    # Query 1: Direct assertion query (trimmed to 12 words if long)
    if len(words) <= 12:
        q1 = cleaned_claim
    else:
        q1 = " ".join(words[:12])
    queries.append(q1)

    # Query 2: Entity + Numbers/Dates verification query
    entities_part = " ".join(claim.entities[:3]) if claim.entities else ""
    numbers_part = " ".join(claim.numbers[:2]) if claim.numbers else ""
    dates_part = " ".join(claim.dates[:2]) if claim.dates else ""

    q2_parts = [p for p in [entities_part, numbers_part, dates_part] if p]
    if q2_parts:
        q2 = " ".join(q2_parts).strip()
        if q2 and q2.lower() != q1.lower():
            queries.append(q2)

    # Query 3: Independent verification / official data query
    if claim.entities:
        main_entity = claim.entities[0]
        date_str = claim.dates[0] if claim.dates else ""
        num_str = claim.numbers[0] if claim.numbers else ""
        q3 = f"{main_entity} {num_str} {date_str} official statistics report".strip()
        # Clean extra spaces
        q3 = re.sub(r"\s+", " ", q3)
        if q3.lower() not in [q.lower() for q in queries]:
            queries.append(q3)
    elif len(queries) < 2:
        # Fallback second query
        queries.append(f"{cleaned_claim} fact check")

    # Ensure uniqueness while preserving order
    unique_queries = []
    seen = set()
    for q in queries:
        norm = q.lower().strip()
        if norm and norm not in seen:
            seen.add(norm)
            unique_queries.append(q.strip())

    return unique_queries[:3]


def is_authoritative_domain(domain: str) -> bool:
    """Return True if domain belongs to government, educational, or recognized news/research institutions."""
    if any(domain.endswith(tld) for tld in AUTHORITATIVE_TLDS):
        return True
    if domain in REPUTABLE_DOMAINS:
        return True
    return False


def search_evidence_for_claim(
    claim: ExtractedClaimItem,
    client: TavilyClient,
    max_results_per_query: int = 3,
    query_cache: Optional[Dict[str, Any]] = None,
) -> ClaimEvidenceResult:
    """Execute live web search for a claim across generated queries and collect evidence.

    Args:
        claim: Target extracted claim.
        client: Initialized TavilyClient.
        max_results_per_query: Maximum results retrieved per query.
        query_cache: Optional dict to cache and reuse search responses across identical queries.

    Returns:
        ClaimEvidenceResult containing retrieved sources, queries used, and search status.
    """
    queries = generate_search_queries(claim)
    logger.info(f"Researching claim {claim.claim_id} with {len(queries)} queries: {queries}")

    seen_urls: Set[str] = set()
    evidence_items: List[EvidenceItem] = []
    has_api_error = False
    last_error_message: Optional[str] = None
    active_cache = query_cache if query_cache is not None else _GLOBAL_SEARCH_CACHE

    for query in queries:
        norm_q = query.strip().lower()
        if norm_q in active_cache:
            results = active_cache[norm_q]
        else:
            try:
                response = client.search(
                    query=query,
                    search_depth="basic",
                    max_results=max_results_per_query,
                    include_answer=False,
                )
                results = response.get("results", []) if isinstance(response, dict) else []
                # Keep active cache bounded
                if len(active_cache) > 500:
                    active_cache.clear()
                active_cache[norm_q] = results
            except Exception as exc:
                has_api_error = True
                last_error_message = str(exc)
                logger.warning(f"Tavily query failed for '{query}': {exc}")
                results = []

        for item in results:
            raw_url = item.get("url", "").strip()
            if not raw_url or raw_url in seen_urls:
                continue

            seen_urls.add(raw_url)
            domain = extract_domain(raw_url)
            title = str(item.get("title", "Untitled Source")).strip()
            content = str(item.get("content", "")).strip()
            pub_date = item.get("published_date")
            score = item.get("score")

            norm_score = float(score) if score is not None else None

            evidence_items.append(
                EvidenceItem(
                    source_title=title,
                    source_url=raw_url,
                    source_domain=domain,
                    content_snippet=content,
                    publication_date=pub_date,
                    retrieved_at=datetime.now(timezone.utc).isoformat(),
                    relevance_score=norm_score,
                )
            )

        # Early exit optimization: If query returned >= 2 relevant evidence sources, stop redundant subsequent queries
        if len(evidence_items) >= 2:
            break

    # Prioritize evidence: rank authoritative domains and higher relevance scores first
    evidence_items.sort(
        key=lambda ev: (
            1 if is_authoritative_domain(ev.source_domain) else 0,
            ev.relevance_score if ev.relevance_score is not None else 0.5,
        ),
        reverse=True,
    )

    # Determine status
    if evidence_items:
        status = "success"
        error_msg = None
    elif has_api_error:
        status = "failed"
        error_msg = f"Web search error: {last_error_message}"
    else:
        status = "no_results"
        error_msg = "No relevant web evidence found for this claim."

    return ClaimEvidenceResult(
        claim_id=claim.claim_id,
        original_claim=claim.original_claim,
        search_queries=queries,
        evidence=evidence_items,
        search_status=status,
        error_message=error_msg,
    )


def search_evidence_for_document(
    claims_response: ClaimExtractionResponse,
    settings: Optional[Settings] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> DocumentEvidenceResult:
    """Execute live web search for all claims extracted from a document.

    Args:
        claims_response: Extracted claims from Phase 4.
        settings: Application settings with TAVILY_API_KEY.
        progress_callback: Optional callback reporting (current_index, total_claims, current_claim_text).

    Returns:
        DocumentEvidenceResult aggregating evidence across all claims.
    """
    if settings is None:
        settings = get_settings()

    doc_name = claims_response.document_name
    claims = claims_response.claims

    if not claims:
        return DocumentEvidenceResult(
            document_name=doc_name,
            total_claims_researched=0,
            claims_evidence=[],
            total_sources_retrieved=0,
            error_message="No claims provided to research.",
        )

    if not settings.is_tavily_configured:
        logger.warning("TAVILY_API_KEY is not configured.")
        return DocumentEvidenceResult(
            document_name=doc_name,
            total_claims_researched=0,
            claims_evidence=[],
            total_sources_retrieved=0,
            error_message=(
                "Tavily Search API key missing: Please configure TAVILY_API_KEY in your .env file "
                "or Streamlit secrets to retrieve live web evidence."
            ),
        )

    try:
        client = TavilyClient(api_key=settings.tavily_api_key)
    except Exception as exc:
        logger.error(f"Failed to initialize TavilyClient: {exc}")
        return DocumentEvidenceResult(
            document_name=doc_name,
            total_claims_researched=0,
            claims_evidence=[],
            total_sources_retrieved=0,
            error_message=f"Failed to initialize Tavily search client: {str(exc)}",
        )

    evidence_records: List[ClaimEvidenceResult] = []
    total = len(claims)
    query_cache: Dict[str, Any] = {}

    for idx, claim in enumerate(claims):
        if progress_callback:
            progress_callback(idx + 1, total, claim.original_claim)

        result = search_evidence_for_claim(claim=claim, client=client, query_cache=query_cache)
        evidence_records.append(result)

    total_sources = sum(len(r.evidence) for r in evidence_records)
    logger.info(
        f"Completed web evidence retrieval for '{doc_name}': {len(evidence_records)} claims, "
        f"{total_sources} total sources retrieved."
    )

    return DocumentEvidenceResult(
        document_name=doc_name,
        total_claims_researched=len(evidence_records),
        claims_evidence=evidence_records,
        total_sources_retrieved=total_sources,
        error_message=None,
    )
