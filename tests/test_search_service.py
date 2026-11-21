"""Unit tests for Phase 5 - Live Web Search and Evidence Retrieval using Tavily API."""

import pytest
from unittest.mock import patch, MagicMock
from src.config import Settings
from src.models.schemas import (
    ExtractedClaimItem,
    ClaimExtractionResponse,
    EvidenceItem,
    ClaimEvidenceResult,
    DocumentEvidenceResult,
)
from src.core.search_service import (
    generate_search_queries,
    extract_domain,
    is_authoritative_domain,
    search_evidence_for_claim,
    search_evidence_for_document,
)


class TestSearchQueryGeneration:
    """Verify targeted query construction across different claim types."""

    def test_query_generation_numerical_claim(self):
        claim = ExtractedClaimItem(
            claim_id="C001",
            original_claim="India's GDP grew by 8.2% in 2024.",
            claim_type="Statistic",
            page_number=1,
            entities=["India", "GDP"],
            numbers=["8.2%"],
            dates=["2024"],
        )
        queries = generate_search_queries(claim)
        assert len(queries) >= 2
        # Check that entities and numbers are included across queries
        combined = " ".join(queries).lower()
        assert "india" in combined
        assert "gdp" in combined
        assert "8.2%" in combined or "2024" in combined

    def test_query_generation_financial_claim(self):
        claim = ExtractedClaimItem(
            claim_id="C002",
            original_claim="Stripe raised $6.5B at a $50B valuation in March 2023.",
            claim_type="Financial",
            page_number=1,
            entities=["Stripe"],
            numbers=["$6.5B", "$50B"],
            dates=["March 2023"],
        )
        queries = generate_search_queries(claim)
        assert len(queries) >= 2
        combined = " ".join(queries)
        assert "Stripe" in combined

    def test_query_generation_historical_claim(self):
        claim = ExtractedClaimItem(
            claim_id="C003",
            original_claim="Apollo 11 landed on the moon on July 20, 1969.",
            claim_type="Date / Event",
            page_number=2,
            entities=["Apollo 11", "Moon"],
            numbers=[],
            dates=["July 20, 1969"],
        )
        queries = generate_search_queries(claim)
        assert len(queries) >= 1
        assert any("Apollo 11" in q for q in queries)

    def test_query_generation_non_numerical_fact(self):
        claim = ExtractedClaimItem(
            claim_id="C004",
            original_claim="Satya Nadella is the chief executive officer of Microsoft.",
            claim_type="General Fact",
            page_number=3,
            entities=["Satya Nadella", "Microsoft"],
            numbers=[],
            dates=[],
        )
        queries = generate_search_queries(claim)
        assert len(queries) >= 1
        assert any("Satya Nadella" in q for q in queries)


class TestDomainExtractionAndAuthority:
    """Verify URL domain parsing and institutional authority scoring."""

    def test_extract_domain_standard_url(self):
        url = "https://www.reuters.com/markets/asia/india-gdp-growth-2024-05-31/"
        assert extract_domain(url) == "reuters.com"

    def test_extract_domain_subdomain(self):
        url = "https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=IN"
        assert extract_domain(url) == "data.worldbank.org"

    def test_extract_domain_empty_or_malformed(self):
        assert extract_domain("") == "unknown"
        assert extract_domain("not-a-valid-url") == "unknown"

    def test_is_authoritative_domain(self):
        assert is_authoritative_domain("sec.gov") is True
        assert is_authoritative_domain("mit.edu") is True
        assert is_authoritative_domain("who.int") is True
        assert is_authoritative_domain("worldbank.org") is True
        assert is_authoritative_domain("reuters.com") is True
        assert is_authoritative_domain("unverified-blog.xyz") is False


class TestEvidenceRetrievalOrchestrator:
    """Verify live search integration, deduplication, and error resilience."""

    def test_search_evidence_for_claim_success(self):
        claim = ExtractedClaimItem(
            claim_id="C001",
            original_claim="India's GDP grew by 8.2% in 2024.",
            claim_type="Statistic",
            page_number=1,
            entities=["India", "GDP"],
            numbers=["8.2%"],
            dates=["2024"],
        )

        mock_client = MagicMock()
        mock_client.search.return_value = {
            "results": [
                {
                    "title": "India GDP Growth Rate 2024 - Official Release",
                    "url": "https://www.mospi.gov.in/press-release/gdp-2024",
                    "content": "India's real GDP grew by an estimated 8.2% in financial year 2023-24.",
                    "score": 0.96,
                    "published_date": "2024-05-31",
                },
                {
                    "title": "Reuters: India economy surges in 2024",
                    "url": "https://www.reuters.com/world/india/india-gdp-2024",
                    "content": "India's economy expanded 8.2% in the fiscal year ended March 2024.",
                    "score": 0.92,
                    "published_date": "2024-06-01",
                },
            ]
        }

        result = search_evidence_for_claim(claim=claim, client=mock_client)

        assert result.claim_id == "C001"
        assert result.search_status == "success"
        assert len(result.evidence) == 2
        assert result.evidence[0].source_domain in ["mospi.gov.in", "reuters.com"]
        assert result.evidence[0].url.startswith("https://")
        assert result.evidence[0].publication_date is not None
        assert result.evidence[0].retrieved_at is not None

    def test_deduplicate_identical_urls_across_queries(self):
        claim = ExtractedClaimItem(
            claim_id="C002",
            original_claim="Sample claim statement.",
            page_number=1,
        )

        mock_client = MagicMock()
        # Query 1 and Query 2 return the same URL
        mock_client.search.side_effect = [
            {
                "results": [
                    {
                        "title": "Report Title",
                        "url": "https://example.com/unique-report",
                        "content": "First query snippet.",
                        "score": 0.9,
                    }
                ]
            },
            {
                "results": [
                    {
                        "title": "Report Title Duplicate",
                        "url": "https://example.com/unique-report",  # duplicate URL
                        "content": "Second query snippet.",
                        "score": 0.85,
                    }
                ]
            },
        ]

        result = search_evidence_for_claim(claim=claim, client=mock_client)
        assert len(result.evidence) == 1  # Deduplicated from 2 to 1
        assert result.evidence[0].source_url == "https://example.com/unique-report"

    def test_claims_with_no_search_results(self):
        claim = ExtractedClaimItem(
            claim_id="C003",
            original_claim="Non-existent claim with no evidence.",
            page_number=1,
        )

        mock_client = MagicMock()
        mock_client.search.return_value = {"results": []}

        result = search_evidence_for_claim(claim=claim, client=mock_client)
        assert result.search_status == "no_results"
        assert len(result.evidence) == 0
        assert "No relevant web evidence found" in result.error_message

    def test_missing_tavily_api_key_handling(self):
        claims_resp = ClaimExtractionResponse(
            document_name="doc.pdf",
            total_claims=1,
            claims=[
                ExtractedClaimItem(
                    claim_id="C001",
                    original_claim="Sample assertion.",
                    page_number=1,
                )
            ],
        )

        settings = Settings(tavily_api_key=None)
        doc_result = search_evidence_for_document(claims_resp, settings=settings)

        assert doc_result.total_sources_retrieved == 0
        assert "Tavily Search API key missing" in doc_result.error_message

    def test_api_timeout_and_error_handling(self):
        claim = ExtractedClaimItem(
            claim_id="C004",
            original_claim="Claim triggering network timeout.",
            page_number=1,
        )

        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("ReadTimeout: Request timed out after 30s")

        result = search_evidence_for_claim(claim=claim, client=mock_client)
        assert result.search_status == "failed"
        assert len(result.evidence) == 0
        assert "ReadTimeout" in result.error_message

    def test_conflicting_sources_are_preserved(self):
        claim = ExtractedClaimItem(
            claim_id="C005",
            original_claim="Company valuation reached $10B in 2023.",
            page_number=1,
        )

        mock_client = MagicMock()
        mock_client.search.return_value = {
            "results": [
                {
                    "title": "Source A: Company hits $10B valuation",
                    "url": "https://source-a.com/article",
                    "content": "Valuation reached $10B in late 2023.",
                    "score": 0.9,
                },
                {
                    "title": "Source B: Disputed valuation is only $6B",
                    "url": "https://source-b.com/article",
                    "content": "Reports suggest internal valuation was lowered to $6B.",
                    "score": 0.88,
                },
            ]
        }

        result = search_evidence_for_claim(claim=claim, client=mock_client)
        assert len(result.evidence) == 2
        # Both conflicting perspectives are preserved for verification
        urls = [e.source_url for e in result.evidence]
        assert "https://source-a.com/article" in urls
        assert "https://source-b.com/article" in urls
