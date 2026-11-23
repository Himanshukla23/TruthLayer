"""Centralized configuration management for TruthLayer with safe secret resolution."""

import os
from functools import lru_cache
from typing import Any, Dict, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable loading and safe fallbacks."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application Metadata
    app_name: str = Field(default="TruthLayer", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    app_env: str = Field(default="development", description="Environment: development, staging, production")
    log_level: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR")
    port: int = Field(default=8000, description="Application port")

    # Document Processing Limits
    max_upload_size_mb: int = Field(default=20, description="Max upload file size in megabytes")
    max_pdf_pages: int = Field(default=10, description="Max PDF pages processed in MVP")

    # AI Orchestration - Primary (Gemini) and Fallback (Groq)
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-3.5-flash-lite", description="Gemini model name")
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key for fallback")
    groq_model: str = Field(default="qwen/qwen3.8-27b", description="Groq model name")

    # Web Search API (Tavily)
    tavily_api_key: Optional[str] = Field(default=None, description="Tavily Search API key")

    @property
    def is_gemini_configured(self) -> bool:
        """Return True if a valid Gemini API key is configured."""
        if not self.gemini_api_key:
            return False
        clean_key = self.gemini_api_key.strip()
        return bool(clean_key and clean_key != "your_gemini_api_key_here")

    @property
    def is_groq_configured(self) -> bool:
        """Return True if a valid Groq API key is configured for fallback."""
        if not self.groq_api_key:
            return False
        clean_key = self.groq_api_key.strip()
        return bool(clean_key and clean_key != "your_groq_api_key_here")

    @property
    def is_tavily_configured(self) -> bool:
        """Return True if a valid Tavily API key is configured."""
        if not self.tavily_api_key:
            return False
        clean_key = self.tavily_api_key.strip()
        return bool(clean_key and clean_key != "your_tavily_api_key_here")

    @property
    def has_active_llm(self) -> bool:
        """Return True if either Gemini or Groq is configured for AI execution."""
        return self.is_gemini_configured or self.is_groq_configured

    @property
    def is_fully_configured(self) -> bool:
        """Return True if an LLM (Gemini or Groq) and Tavily search are both configured."""
        return self.has_active_llm and self.is_tavily_configured

    def safe_summary(self) -> Dict[str, Any]:
        """Return configuration dictionary with masked secrets for safe logging and UI display."""
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "app_env": self.app_env,
            "log_level": self.log_level,
            "port": self.port,
            "max_upload_size_mb": self.max_upload_size_mb,
            "max_pdf_pages": self.max_pdf_pages,
            "gemini_configured": self.is_gemini_configured,
            "groq_configured": self.is_groq_configured,
            "tavily_configured": self.is_tavily_configured,
            "gemini_model": self.gemini_model,
            "groq_model": self.groq_model,
        }

    def __repr__(self) -> str:
        """Represent configuration safely without exposing sensitive tokens."""
        summary = self.safe_summary()
        items = ", ".join(f"{k}={v!r}" for k, v in summary.items())
        return f"Settings({items})"

    def __str__(self) -> str:
        return self.__repr__()


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings singleton instance."""
    return Settings()
