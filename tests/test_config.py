"""Unit tests for Phase 1 - Project Foundation, Configuration, and Security."""

import os
import io
import logging
import pytest
from pathlib import Path
from src.config import Settings, get_settings
from src.utils.logger import get_logger, SensitiveDataFilter
from src.utils.exceptions import (
    TruthLayerError,
    ConfigurationError,
    PDFProcessingError,
    PDFTextExtractionError,
    PDFCorruptedError,
    PDFPasswordProtectedError,
    PDFScannedDocumentError,
    ClaimExtractionError,
    SearchServiceError,
    VerificationError,
)


class TestProjectStructure:
    """Validate repository layout and required files for Phase 1."""

    def test_required_directories_exist(self):
        project_root = Path(__file__).resolve().parent.parent
        expected_dirs = [
            project_root / "src",
            project_root / "src" / "utils",
            project_root / "src" / "models",
            project_root / "src" / "core",
            project_root / "src" / "ui",
            project_root / "tests",
            project_root / ".streamlit",
        ]
        for directory in expected_dirs:
            assert directory.is_dir(), f"Expected directory {directory} does not exist"

    def test_required_foundation_files_exist(self):
        project_root = Path(__file__).resolve().parent.parent
        expected_files = [
            project_root / "requirements.txt",
            project_root / ".env.example",
            project_root / ".gitignore",
            project_root / "app.py",
            project_root / "PROBLEM_STATEMENT.md",
            project_root / "ARCHITECTURE.md",
            project_root / ".streamlit" / "config.toml",
            project_root / "src" / "config.py",
            project_root / "src" / "utils" / "logger.py",
            project_root / "src" / "utils" / "exceptions.py",
        ]
        for file_path in expected_files:
            assert file_path.is_file(), f"Expected file {file_path} does not exist"

    def test_gitignore_contains_sensitive_entries(self):
        project_root = Path(__file__).resolve().parent.parent
        gitignore_path = project_root / ".gitignore"
        content = gitignore_path.read_text(encoding="utf-8")
        assert ".env" in content
        assert ".streamlit/secrets.toml" in content
        assert "__pycache__" in content


class TestConfigurationModule:
    """Validate Settings loading, defaults, and credential safety."""

    def test_default_settings_instantiation(self):
        settings = Settings()
        assert settings.app_name == "TruthLayer"
        assert settings.app_version == "0.1.0"
        assert settings.app_env in ["development", "staging", "production"]
        assert settings.max_upload_size_mb == 20
        assert settings.max_pdf_pages == 10

    def test_missing_api_keys_do_not_crash(self):
        # Explicitly instantiate settings without keys
        settings = Settings(gemini_api_key=None, tavily_api_key=None)
        assert settings.is_gemini_configured is False
        assert settings.is_tavily_configured is False
        assert settings.is_fully_configured is False

    def test_placeholder_api_keys_are_not_considered_configured(self):
        settings = Settings(
            gemini_api_key="your_gemini_api_key_here",
            tavily_api_key="your_tavily_api_key_here",
        )
        assert settings.is_gemini_configured is False
        assert settings.is_tavily_configured is False

    def test_valid_keys_marked_configured(self):
        settings = Settings(
            gemini_api_key="AIzaSyDummyValidGeminiApiKeyForTest123",
            groq_api_key="gsk_DummyValidGroqApiKeyForTesting12345",
            tavily_api_key="tvly-DummyValidTavilyApiKeyForTesting123",
        )
        assert settings.is_gemini_configured is True
        assert settings.is_groq_configured is True
        assert settings.has_active_llm is True
        assert settings.is_tavily_configured is True
        assert settings.is_fully_configured is True

    def test_secrets_not_exposed_in_repr_or_str(self):
        secret_gemini = "AIzaSyDummySecretValueThatMustNeverLeak"
        secret_groq = "gsk_SecretValueThatMustNeverLeak12345678"
        secret_tavily = "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"
        settings = Settings(
            gemini_api_key=secret_gemini,
            groq_api_key=secret_groq,
            tavily_api_key=secret_tavily,
        )

        repr_str = repr(settings)
        str_str = str(settings)
        summary = settings.safe_summary()

        assert secret_gemini not in repr_str
        assert secret_groq not in repr_str
        assert secret_tavily not in repr_str
        assert secret_gemini not in str_str
        assert secret_groq not in str_str
        assert secret_tavily not in str_str
        assert secret_gemini not in str(summary)
        assert secret_groq not in str(summary)
        assert secret_tavily not in str(summary)


class TestLoggerAndSanitization:
    """Validate that the structured logger scrubs sensitive API keys."""

    def test_logger_redacts_gemini_key(self):
        test_key = "AIzaSyDummyKeyForTestingRedaction123456"
        redacted = SensitiveDataFilter._redact(f"Connecting with key {test_key}")
        assert test_key not in redacted
        assert "[REDACTED_CREDENTIAL]" in redacted

    def test_logger_redacts_groq_key(self):
        test_key = "gsk_testDummySecretKey1234567890abcdef123"
        redacted = SensitiveDataFilter._redact(f"Using Groq key {test_key}")
        assert test_key not in redacted
        assert "[REDACTED_CREDENTIAL]" in redacted

    def test_logger_redacts_tavily_key(self):
        test_key = "tvly-testDummySecretKey1234567890abcdef"
        redacted = SensitiveDataFilter._redact(f"Using Tavily key {test_key}")
        assert test_key not in redacted
        assert "[REDACTED_CREDENTIAL]" in redacted

    def test_logger_creation(self):
        logger = get_logger("test.logger", "DEBUG")
        assert logger is not None
        assert logger.name == "test.logger"
        assert logger.level == logging.DEBUG


class TestExceptionTaxonomy:
    """Validate exception hierarchy and inheritance."""

    def test_exceptions_inherit_from_truthlayer_error(self):
        exceptions_to_check = [
            ConfigurationError("Config error"),
            PDFProcessingError("PDF processing error"),
            PDFTextExtractionError("Extraction failed"),
            PDFCorruptedError("Corrupt PDF"),
            PDFPasswordProtectedError("Encrypted PDF"),
            PDFScannedDocumentError("Scanned PDF"),
            ClaimExtractionError("Claim extraction failed"),
            SearchServiceError("Search failed"),
            VerificationError("Verification error"),
        ]
        for exc in exceptions_to_check:
            assert isinstance(exc, TruthLayerError)
            assert isinstance(exc, Exception)
            assert str(exc) != ""
