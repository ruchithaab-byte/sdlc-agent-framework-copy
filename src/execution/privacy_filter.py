"""
Privacy Filter for PII Protection in Code Execution.

Implements the privacy-preserving execution pattern from Anthropic's best practices:
- Intermediate variables (PII, raw data) stay inside container
- Tokenization if data must pass through model (PERSON_1, EMAIL_1)
- Automatic detokenization on return
- Audit logging of data access patterns

Reference: "Code execution with MCP: building more efficient AI agents"
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum


class PIIType(Enum):
    """Types of PII that can be detected and tokenized."""
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    SSN = "SSN"
    CREDIT_CARD = "CREDIT_CARD"
    IP_ADDRESS = "IP_ADDRESS"
    PERSON_NAME = "PERSON"
    API_KEY = "API_KEY"
    PASSWORD = "PASSWORD"
    ADDRESS = "ADDRESS"


@dataclass
class TokenizationResult:
    """Result of PII tokenization."""
    filtered_text: str
    tokens_replaced: int
    token_map: Dict[str, str] = field(default_factory=dict)
    pii_types_found: List[PIIType] = field(default_factory=list)
    
    def detokenize(self, text: str) -> str:
        """Reverse tokenization to restore original values."""
        result = text
        for token, original in self.token_map.items():
            result = result.replace(token, original)
        return result


@dataclass
class AuditEntry:
    """Audit log entry for PII access."""
    timestamp: datetime
    pii_type: PIIType
    token: str
    action: str  # "tokenized", "detokenized", "accessed"
    context: Optional[str] = None


class PrivacyFilter:
    """
    Filters PII from execution output before returning to context.
    
    This is critical for the privacy-preserving execution pattern:
    - PII stays inside the container/execution environment
    - Only tokenized references pass through the model
    - Detokenization happens on the return path
    
    Example:
        >>> filter = PrivacyFilter()
        >>> result = filter.filter_output("Email: john@example.com")
        >>> print(result.filtered_text)
        "Email: EMAIL_1"
        >>> # Original value available for detokenization
        >>> original = result.detokenize(result.filtered_text)
    """
    
    # PII detection patterns
    PATTERNS: Dict[PIIType, re.Pattern] = {
        PIIType.EMAIL: re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ),
        PIIType.PHONE: re.compile(
            r'\b(?:\+?1[-.\s]?)?(?:\([0-9]{3}\)|[0-9]{3})[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
        ),
        PIIType.SSN: re.compile(
            r'\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b'
        ),
        PIIType.CREDIT_CARD: re.compile(
            r'\b(?:[0-9]{4}[-\s]?){3}[0-9]{4}\b'
        ),
        PIIType.IP_ADDRESS: re.compile(
            r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ),
        PIIType.API_KEY: re.compile(
            r'\b(?:sk-|pk_|api[_-]?key[_-]?)[A-Za-z0-9_-]{20,}\b',
            re.IGNORECASE
        ),
        PIIType.PASSWORD: re.compile(
            r'(?:password|passwd|pwd|secret)["\']?\s*[:=]\s*["\']?[^\s"\']+["\']?',
            re.IGNORECASE
        ),
    }
    
    # Patterns that look like API keys or secrets
    SECRET_PATTERNS = [
        re.compile(r'\b[A-Za-z0-9]{32,}\b'),  # Generic long alphanumeric
        re.compile(r'ghp_[A-Za-z0-9]{36}'),  # GitHub PAT
        re.compile(r'gho_[A-Za-z0-9]{36}'),  # GitHub OAuth
        re.compile(r'github_pat_[A-Za-z0-9]{22}_[A-Za-z0-9]{59}'),  # GitHub fine-grained
        re.compile(r'sk-[A-Za-z0-9]{48}'),  # OpenAI
        re.compile(r'sk-ant-[A-Za-z0-9-]{90,}'),  # Anthropic
        re.compile(r'xoxb-[A-Za-z0-9-]+'),  # Slack bot token
        re.compile(r'xoxp-[A-Za-z0-9-]+'),  # Slack user token
    ]
    
    def __init__(
        self,
        enable_audit: bool = True,
        aggressive_mode: bool = False,
    ):
        """
        Initialize the Privacy Filter.
        
        Args:
            enable_audit: Enable audit logging of PII access.
            aggressive_mode: Enable aggressive pattern matching (more false positives).
        """
        self._enable_audit = enable_audit
        self._aggressive_mode = aggressive_mode
        self._audit_log: List[AuditEntry] = []
        self._token_counter: Dict[PIIType, int] = {t: 0 for t in PIIType}
    
    def filter_output(self, text: str) -> TokenizationResult:
        """
        Filter PII from text output.
        
        Replaces detected PII with tokens (EMAIL_1, PHONE_1, etc.)
        while preserving a mapping for potential detokenization.
        
        Args:
            text: Raw text output from execution.
            
        Returns:
            TokenizationResult with filtered text and token mapping.
        """
        filtered_text = text
        token_map: Dict[str, str] = {}
        pii_types_found: List[PIIType] = []
        
        # Apply standard PII patterns
        for pii_type, pattern in self.PATTERNS.items():
            matches = pattern.findall(filtered_text)
            for match in matches:
                if match not in token_map.values():
                    self._token_counter[pii_type] += 1
                    token = f"{pii_type.value}_{self._token_counter[pii_type]}"
                    token_map[token] = match
                    filtered_text = filtered_text.replace(match, token)
                    
                    if pii_type not in pii_types_found:
                        pii_types_found.append(pii_type)
                    
                    if self._enable_audit:
                        self._audit_log.append(AuditEntry(
                            timestamp=datetime.utcnow(),
                            pii_type=pii_type,
                            token=token,
                            action="tokenized",
                        ))
        
        # Apply secret patterns in aggressive mode
        if self._aggressive_mode:
            for pattern in self.SECRET_PATTERNS:
                matches = pattern.findall(filtered_text)
                for match in matches:
                    if match not in token_map.values() and len(match) > 20:
                        self._token_counter[PIIType.API_KEY] += 1
                        token = f"SECRET_{self._token_counter[PIIType.API_KEY]}"
                        token_map[token] = match
                        filtered_text = filtered_text.replace(match, token)
                        
                        if PIIType.API_KEY not in pii_types_found:
                            pii_types_found.append(PIIType.API_KEY)
        
        return TokenizationResult(
            filtered_text=filtered_text,
            tokens_replaced=len(token_map),
            token_map=token_map,
            pii_types_found=pii_types_found,
        )
    
    def filter_input(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Filter PII from input before sending to model.
        
        Similar to filter_output but designed for input processing.
        
        Args:
            text: Input text that may contain PII.
            
        Returns:
            Tuple of (filtered_text, token_map).
        """
        result = self.filter_output(text)
        return result.filtered_text, result.token_map
    
    def detokenize(self, text: str, token_map: Dict[str, str]) -> str:
        """
        Reverse tokenization to restore original PII values.
        
        Args:
            text: Text with tokens.
            token_map: Mapping of tokens to original values.
            
        Returns:
            Text with original values restored.
        """
        result = text
        for token, original in token_map.items():
            result = result.replace(token, original)
            
            if self._enable_audit:
                self._audit_log.append(AuditEntry(
                    timestamp=datetime.utcnow(),
                    pii_type=self._get_pii_type_from_token(token),
                    token=token,
                    action="detokenized",
                ))
        
        return result
    
    def _get_pii_type_from_token(self, token: str) -> PIIType:
        """Extract PII type from token string."""
        for pii_type in PIIType:
            if token.startswith(pii_type.value):
                return pii_type
        return PIIType.API_KEY  # Default for SECRET_ tokens
    
    def get_audit_log(self) -> List[AuditEntry]:
        """Get the audit log of PII operations."""
        return self._audit_log.copy()
    
    def clear_audit_log(self) -> None:
        """Clear the audit log."""
        self._audit_log.clear()
    
    def reset_counters(self) -> None:
        """Reset token counters for a new session."""
        self._token_counter = {t: 0 for t in PIIType}


__all__ = [
    "PrivacyFilter",
    "PIIType",
    "TokenizationResult",
    "AuditEntry",
]

