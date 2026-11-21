"""Unit tests for Phase 4 - AI-Based Claim Extraction with Gemini and Groq fallback."""

import pytest
from unittest.mock import patch, MagicMock
from src.config import Settings
from src.models.schemas import (
    PageExtraction,
    PDFExtractionResult,
    ExtractedClaimItem,
    ClaimExtractionResponse,
)
from src.core.claim_extractor import (
    extract_claims_from_document,
    deduplicate_and_validate_claims,
    format_document_text_for_prompt,
    parse_llm_json_response,
)
from src.utils.exceptions import ClaimExtractionError


def create_sample_extraction_result(pages_data: list) -> PDFExtractionResult:
    """Helper to generate a mock PDFExtractionResult."""
    pages = [
        PageExtraction(
            page_number=idx + 1,
            text=text,
            character_count=len(text),
            is_empty=(len(text.strip()) == 0),
        )
        for idx, text in enumerate(pages_data)
    ]
    return PDFExtractionResult(
        document_name="market_brief.pdf",
        total_pages=len(pages),
        extraction_status="success",
        pages=pages,
        total_characters=sum(p.character_count for p in pages),
    )


class TestClaimExtractionSchemasAndValidation:
    """Verify structured output data contracts and validation."""

    def test_extracted_claim_item_schema(self):
        claim = ExtractedClaimItem(
            claim_id="C001",
            original_claim="India's GDP grew by 8.2% in 2024.",
            claim_type="Statistic",
            page_number=1,
            entities=["India", "GDP"],
            numbers=["8.2%"],
            dates=["2024"],
            requires_verification=True,
        )
        assert claim.claim_id == "C001"
        assert claim.page_number == 1
        assert "8.2%" in claim.numbers
        assert "2024" in claim.dates
        assert claim.requires_verification is True
        assert claim.id == "C001"
        assert claim.claim_text == "India's GDP grew by 8.2% in 2024."

    def test_deduplicate_and_validate_claims(self):
        raw_claims = [
            {
                "claim_id": "C001",
                "original_claim": "The global AI market will reach $500 billion by 2030.",
                "claim_type": "Market Forecast",
                "page_number": 1,
                "entities": ["Global AI market"],
                "numbers": ["$500 billion"],
                "dates": ["2030"],
            },
            # Exact duplicate statement on page 2
            {
                "claim_id": "C002",
                "original_claim": "The global AI market will reach $500 billion by 2030.",
                "claim_type": "Market Forecast",
                "page_number": 2,
                "entities": ["Global AI market"],
                "numbers": ["$500 billion"],
                "dates": ["2030"],
            },
            # Distinct claim
            {
                "claim_id": "C003",
                "original_claim": "OpenAI was founded in December 2015.",
                "claim_type": "Date / Event",
                "page_number": 3,
                "entities": ["OpenAI"],
                "numbers": [],
                "dates": ["December 2015"],
            },
        ]

        response = deduplicate_and_validate_claims(
            raw_claims=raw_claims,
            total_pages=3,
            document_name="sample.pdf",
            model_used="gemini-2.5-flash",
        )

        assert response.total_claims == 2  # Deduplicated from 3 to 2
        assert response.claims[0].claim_id == "C001"
        assert response.claims[0].page_number == 1  # Kept earlier page
        assert response.claims[1].claim_id == "C002"  # Sequentially renumbered
        assert response.claims[1].original_claim == "OpenAI was founded in December 2015."

    def test_page_number_bounds_clamping(self):
        raw_claims = [
            {
                "original_claim": "Out-of-bounds claim from page 99.",
                "page_number": 99,
            }
        ]
        response = deduplicate_and_validate_claims(
            raw_claims=raw_claims,
            total_pages=2,
            document_name="short_doc.pdf",
            model_used="test-model",
        )
        assert response.claims[0].page_number == 2  # Clamped to total_pages (2)

    def test_json_parsing_with_code_fences(self):
        fenced_json = """```json
        {
            "document_name": "test.pdf",
            "total_claims": 1,
            "claims": [
                {
                    "claim_id": "C001",
                    "original_claim": "Revenue increased by 15% in Q2.",
                    "claim_type": "Financial",
                    "page_number": 1
                }
            ]
        }
        ```"""
        parsed = parse_llm_json_response(fenced_json)
        assert parsed["total_claims"] == 1
        assert parsed["claims"][0]["claim_id"] == "C001"


class TestClaimExtractionOrchestrator:
    """Verify Gemini execution, Groq fallback, and edge cases."""

    def test_missing_api_keys_handling(self):
        empty_settings = Settings(gemini_api_key=None, groq_api_key=None)
        doc = create_sample_extraction_result(["Page 1 contains some statistical facts."])

        response = extract_claims_from_document(doc, settings=empty_settings)
        assert response.total_claims == 0
        assert "API credentials missing" in response.error_message

    def test_empty_document_handling(self):
        settings = Settings(gemini_api_key="AIzaSyDummyKey1234567890abcdefghijklmno")
        empty_doc = create_sample_extraction_result(["", "   "])

        response = extract_claims_from_document(empty_doc, settings=settings)
        assert response.total_claims == 0
        assert "no readable text" in response.error_message.lower() or "blank" in response.error_message.lower()

    @patch("src.core.claim_extractor.extract_claims_with_gemini")
    def test_successful_gemini_extraction(self, mock_gemini):
        mock_gemini.return_value = {
            "document_name": "market_brief.pdf",
            "total_claims": 2,
            "claims": [
                {
                    "claim_id": "C001",
                    "original_claim": "India's GDP grew by 8.2% in 2024.",
                    "claim_type": "Statistic",
                    "page_number": 1,
                    "entities": ["India", "GDP"],
                    "numbers": ["8.2%"],
                    "dates": ["2024"],
                },
                {
                    "claim_id": "C002",
                    "original_claim": "Satya Nadella is the current CEO of Microsoft.",
                    "claim_type": "General Fact",
                    "page_number": 2,
                    "entities": ["Satya Nadella", "Microsoft"],
                    "numbers": [],
                    "dates": [],
                },
            ],
        }

        settings = Settings(
            gemini_api_key="AIzaSyValidGeminiKey1234567890abcdef",
            gemini_model="gemini-2.5-flash",
        )
        doc = create_sample_extraction_result(["Page 1 text", "Page 2 text"])

        result = extract_claims_from_document(doc, settings=settings)

        assert result.total_claims == 2
        assert result.extraction_model_used == "gemini-2.5-flash"
        assert result.claims[0].original_claim == "India's GDP grew by 8.2% in 2024."
        assert result.claims[1].original_claim == "Satya Nadella is the current CEO of Microsoft."
        mock_gemini.assert_called_once()

    @patch("src.core.claim_extractor.extract_claims_with_gemini")
    @patch("src.core.claim_extractor.extract_claims_with_groq")
    def test_groq_fallback_when_gemini_fails(self, mock_groq, mock_gemini):
        # Simulate Gemini failure (e.g. RateLimit / Quota 429)
        mock_gemini.side_effect = Exception("429 ResourceExhausted: Quota exceeded for gemini-2.5-flash")

        # Simulate Groq fallback succeeding
        mock_groq.return_value = {
            "document_name": "market_brief.pdf",
            "total_claims": 1,
            "claims": [
                {
                    "claim_id": "C001",
                    "original_claim": "The global cloud market reached $600B in 2023.",
                    "claim_type": "Financial",
                    "page_number": 1,
                    "entities": ["Cloud market"],
                    "numbers": ["$600B"],
                    "dates": ["2023"],
                }
            ],
        }

        settings = Settings(
            gemini_api_key="AIzaSyValidGeminiKey1234567890abcdef",
            groq_api_key="gsk_ValidGroqKeyForFallback1234567890123",
            groq_model="llama-3.3-70b-versatile",
        )
        doc = create_sample_extraction_result(["Cloud market was $600B in 2023."])

        result = extract_claims_from_document(doc, settings=settings)

        assert result.total_claims == 1
        assert "groq/llama-3.3-70b-versatile" in result.extraction_model_used
        assert result.claims[0].numbers == ["$600B"]
        mock_gemini.assert_called_once()
        mock_groq.assert_called_once()

    def test_prompt_formatter_tags(self):
        doc = create_sample_extraction_result(["First page facts.", "Second page numbers."])
        prompt_str = format_document_text_for_prompt(doc)
        assert "[PAGE 1]" in prompt_str
        assert "First page facts." in prompt_str
        assert "[/PAGE 1]" in prompt_str
        assert "[PAGE 2]" in prompt_str
        assert "Second page numbers." in prompt_str
        assert "[/PAGE 2]" in prompt_str
