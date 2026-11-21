"""Custom exception taxonomy for TruthLayer."""


class TruthLayerError(Exception):
    """Base exception for all TruthLayer application errors."""

    def __init__(self, message: str, details: str = ""):
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message


class ConfigurationError(TruthLayerError):
    """Raised when environment variables or application configuration is invalid."""
    pass


class PDFProcessingError(TruthLayerError):
    """Base exception for errors during PDF ingestion and parsing."""
    pass


class PDFTextExtractionError(PDFProcessingError):
    """Raised when text cannot be extracted from a PDF document."""
    pass


class PDFCorruptedError(PDFProcessingError):
    """Raised when an uploaded PDF file is corrupted or malformed."""
    pass


class PDFPasswordProtectedError(PDFProcessingError):
    """Raised when an uploaded PDF is encrypted or password-protected."""
    pass


class PDFScannedDocumentError(PDFProcessingError):
    """Raised when an uploaded PDF consists of scanned images without extractable text."""
    pass


class ClaimExtractionError(TruthLayerError):
    """Raised when claim extraction fails or LLM schema validation fails."""
    pass


class SearchServiceError(TruthLayerError):
    """Raised when live web search retrieval encounters a failure or rate limit."""
    pass


class VerificationError(TruthLayerError):
    """Raised when evidence-based claim verification encounters a failure."""
    pass
