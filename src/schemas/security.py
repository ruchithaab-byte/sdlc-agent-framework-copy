"""
Sentinel Agent Output Schema.

Structured output for security scans, vulnerability assessments,
and compliance checks.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from src.schemas.base import ActionItem, FileReference, Severity


class Vulnerability(BaseModel):
    """A security vulnerability finding."""
    id: str = Field(description="Vulnerability ID (CVE if applicable)")
    title: str = Field(description="Vulnerability title")
    description: str = Field(description="Detailed description")
    severity: Severity = Field(description="Severity level")
    category: str = Field(description="Category: injection, xss, auth, config, etc.")
    cwe_id: Optional[str] = Field(default=None, description="CWE identifier")
    cvss_score: Optional[float] = Field(default=None, ge=0, le=10, description="CVSS score")
    location: FileReference = Field(description="Code location")
    proof_of_concept: Optional[str] = Field(default=None, description="PoC or attack vector")
    remediation: str = Field(description="How to fix this vulnerability")
    references: List[str] = Field(default_factory=list, description="Reference URLs")


class DependencyVulnerability(BaseModel):
    """A vulnerability in a dependency."""
    package: str = Field(description="Package name")
    version: str = Field(description="Current version")
    vulnerability_id: str = Field(description="CVE or advisory ID")
    severity: Severity = Field(description="Severity level")
    description: str = Field(description="Vulnerability description")
    fixed_version: Optional[str] = Field(default=None, description="Version with fix")
    upgrade_path: Optional[str] = Field(default=None, description="Upgrade path")


class SecretFinding(BaseModel):
    """An exposed secret or credential."""
    type: str = Field(description="Secret type: api_key, password, token, etc.")
    file: str = Field(description="File path")
    line: int = Field(description="Line number")
    snippet: str = Field(description="Redacted code snippet")
    confidence: str = Field(description="Confidence: high, medium, low")
    recommendation: str = Field(description="How to remediate")


class ComplianceCheck(BaseModel):
    """A compliance check result."""
    framework: str = Field(description="Compliance framework: OWASP, PCI-DSS, HIPAA, etc.")
    control_id: str = Field(description="Control identifier")
    control_name: str = Field(description="Control name")
    status: str = Field(description="Status: passed, failed, not_applicable")
    findings: List[str] = Field(default_factory=list, description="Related findings")


class SecurityScanResult(BaseModel):
    """
    Complete output from Sentinel agent.
    
    This schema captures security scan results including
    vulnerabilities, secrets, and compliance status.
    """
    # Summary
    summary: str = Field(description="Executive security summary")
    security_score: float = Field(ge=0, le=100, description="Overall security score")
    risk_level: str = Field(description="Risk level: critical, high, medium, low")
    scan_status: str = Field(description="PASSED, FAILED, or NEEDS_REVIEW")
    
    # Code Vulnerabilities
    vulnerabilities: List[Vulnerability] = Field(
        default_factory=list,
        description="Code vulnerabilities found"
    )
    vulnerabilities_by_severity: dict = Field(
        default_factory=dict,
        description="Count by severity"
    )
    
    # Dependency Vulnerabilities
    dependency_vulnerabilities: List[DependencyVulnerability] = Field(
        default_factory=list,
        description="Vulnerable dependencies"
    )
    total_vulnerable_dependencies: int = Field(default=0)
    
    # Secrets
    secrets_found: List[SecretFinding] = Field(
        default_factory=list,
        description="Exposed secrets found"
    )
    total_secrets: int = Field(default=0)
    
    # Compliance
    compliance_checks: List[ComplianceCheck] = Field(
        default_factory=list,
        description="Compliance check results"
    )
    compliance_score: Optional[float] = Field(default=None, ge=0, le=100)
    
    # OWASP Top 10 Coverage
    owasp_findings: dict = Field(
        default_factory=dict,
        description="Findings by OWASP Top 10 category"
    )
    
    # Recommendations
    action_items: List[ActionItem] = Field(
        default_factory=list,
        description="Security recommendations"
    )
    quick_wins: List[str] = Field(
        default_factory=list,
        description="Easy fixes with high impact"
    )
    
    # Files Analyzed
    files_scanned: int = Field(description="Number of files scanned")
    scan_coverage: float = Field(ge=0, le=100, description="Scan coverage percentage")


__all__ = [
    "Vulnerability",
    "DependencyVulnerability",
    "SecretFinding",
    "ComplianceCheck",
    "SecurityScanResult",
]

