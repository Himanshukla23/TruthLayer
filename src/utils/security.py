"""Security hardening, input sanitization, and prompt-injection defense utilities for TruthLayer."""

import os
import re
from typing import Any, Dict, List, Optional
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger("truthlayer.utils.security")

# Known prompt injection pattern signatures
PROMPT_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"(?i)system\s*override",
    r"(?i)disregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"(?i)you\s+are\s+now\s+(an?\s+)?assistant\s+who",
    r"(?i)you\s+must\s+classify\s+(this\s+claim\s+as\s+)?verified",
    r"(?i)output\s+only\s+verified",
    r"(?i)bypass\s+verification\s+rules?",
    r"(?i)<\/?untrusted_(claim|evidence|document)_data>",
    r"(?i)new\s+system\s+prompt:",
    r"(?i)jailbreak",
]


def mask_secret(secret: Optional[str], visible_chars: int = 4) -> str:
    """Mask sensitive API keys or credentials for safe telemetry and logging.

    Args:
        secret: Raw API key or credential string.
        visible_chars: Number of prefix and suffix characters to retain.

    Returns:
        Masked string e.g. 'AIza...abcd' or '[EMPTY]'.
    """
    if not secret:
        return "[NOT CONFIGURED]"
    s = str(secret).strip()
    if len(s) <= visible_chars * 2:
        return "********"
    return f"{s[:visible_chars]}...{s[-visible_chars:]}"


def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded document filenames to prevent directory traversal and shell injection.

    Args:
        filename: Original uploaded file name.

    Returns:
        Sanitized safe basename string.
    """
    if not filename:
        return "unnamed_document.pdf"

    # Strip directory paths to prevent path traversal (e.g. ../../etc/passwd)
    base = Path(filename).name

    # Remove dangerous characters and control characters
    cleaned = re.sub(r'[\r\n\t\x00-\x1f\\/*?:"<>|]', "_", base)
    cleaned = re.sub(r"\.{2,}", ".", cleaned).strip(" .")

    if not cleaned.lower().endswith(".pdf"):
        cleaned = f"{cleaned}.pdf"

    return cleaned or "document.pdf"


def sanitize_untrusted_text(text: Optional[str]) -> str:
    """Sanitize untrusted document or web text to prevent XML/delimiter breakout attacks.

    Neutralizes any closing or opening XML boundary tags so user input cannot escape
    the secure enclosing fences: <untrusted_claim_data> or <untrusted_evidence_data>.

    Args:
        text: Untrusted raw text from user PDF or public web snippet.

    Returns:
        Safe inert text with XML tag injection vectors neutralized.
    """
    if not text:
        return ""

    sanitized = str(text)

    # Neutralize XML tag escapes
    sanitized = re.sub(
        r"(?i)<\/?\s*untrusted_(claim|evidence|document)_data\s*>",
        "[TAG_DEFUSED]",
        sanitized,
    )

    # Neutralize raw XML delimiter breakout attempts
    sanitized = sanitized.replace("</", "&lt;/").replace("/>", "/&gt;")

    return sanitized


def scan_for_prompt_injection(text: Optional[str]) -> List[str]:
    """Scan untrusted text for recognized prompt injection and role override signatures.

    Args:
        text: Text to evaluate.

    Returns:
        List of matched signature descriptions (empty list if clean).
    """
    if not text:
        return []

    matched: List[str] = []
    for pattern in PROMPT_INJECTION_PATTERNS:
        match = re.search(pattern, text)
        if match:
            matched.append(match.group(0))

    return matched


def verify_gitignore_protects_env(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """Verify that .gitignore exists and properly protects .env and secret files.

    Args:
        project_root: Root workspace path.

    Returns:
        Dict reporting status of .gitignore protection.
    """
    if project_root is None:
        project_root = Path.cwd()

    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        return {
            "is_protected": False,
            "error": ".gitignore file does not exist in workspace root.",
        }

    try:
        content = gitignore_path.read_text(encoding="utf-8")
        lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
        
        has_env = any(pat in lines for pat in [".env", "*.env", ".env*", ".env.local"])
        has_secrets = any("secrets" in line.lower() for line in lines)

        return {
            "is_protected": has_env,
            "gitignore_found": True,
            "protects_env": has_env,
            "protects_secrets": has_secrets,
            "tracked_patterns": lines,
        }
    except Exception as exc:
        return {"is_protected": False, "error": str(exc)}
