"""
Context Compactor for Research-to-Plan Synthesis.

Implements the "Compaction Point" from the RPI workflow:
- Synthesizes messy research findings into clean, actionable plans
- Retains signal (relevant findings) and discards noise
- Creates structured artifacts with specific filenames and constraints

Reference: "No Vibes Allowed: Solving Hard Problems in Complex Codebases" - Dex Horthy
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class CompactionStrategy(Enum):
    """Strategy for compacting research context."""
    SUMMARIZE = "summarize"      # Summarize findings into key points
    EXTRACT = "extract"          # Extract specific artifacts (files, functions)
    HIERARCHICAL = "hierarchical"  # Create hierarchy of importance
    PLAN = "plan"               # Generate actionable plan


@dataclass
class ResearchFinding:
    """A single finding from research phase."""
    content: str
    source: str  # File path, tool name, etc.
    relevance_score: float = 1.0
    category: str = "general"
    line_numbers: Optional[str] = None  # e.g., "45-67"
    
    def to_reference(self) -> str:
        """Convert to compact reference format."""
        if self.line_numbers:
            return f"{self.source}:{self.line_numbers}"
        return self.source


@dataclass
class ResearchSummary:
    """Compacted summary of research findings."""
    key_findings: List[str]
    relevant_files: List[str]
    constraints: List[str]
    dependencies: List[str]
    patterns_found: List[str]
    
    # Metrics
    original_tokens: int = 0
    compacted_tokens: int = 0
    compression_ratio: float = 0.0
    
    def to_context_string(self) -> str:
        """Convert to a string suitable for context injection."""
        sections = []
        
        if self.key_findings:
            sections.append("## Key Findings\n" + "\n".join(f"- {f}" for f in self.key_findings))
        
        if self.relevant_files:
            sections.append("## Relevant Files\n" + "\n".join(f"- `{f}`" for f in self.relevant_files))
        
        if self.constraints:
            sections.append("## Constraints\n" + "\n".join(f"- {c}" for c in self.constraints))
        
        if self.dependencies:
            sections.append("## Dependencies\n" + "\n".join(f"- {d}" for d in self.dependencies))
        
        if self.patterns_found:
            sections.append("## Patterns\n" + "\n".join(f"- {p}" for p in self.patterns_found))
        
        return "\n\n".join(sections)


@dataclass
class PlanStep:
    """A single step in an implementation plan."""
    description: str
    target_file: str
    action: str  # create, modify, delete
    details: str = ""
    test_command: Optional[str] = None
    verification: Optional[str] = None


@dataclass
class CompactionResult:
    """Result of context compaction."""
    success: bool
    strategy: CompactionStrategy
    summary: Optional[ResearchSummary] = None
    plan_steps: List[PlanStep] = field(default_factory=list)
    
    # Compaction metrics
    original_token_count: int = 0
    compacted_token_count: int = 0
    tokens_saved: int = 0
    
    # Timing
    compaction_time_ms: float = 0.0
    
    @property
    def compression_ratio(self) -> float:
        """Calculate compression ratio achieved."""
        if self.original_token_count == 0:
            return 0.0
        return 1.0 - (self.compacted_token_count / self.original_token_count)


class ContextCompactor:
    """
    Compacts research context into clean, actionable artifacts.
    
    The Compaction Point is the critical transition between the messy
    research phase and the clean implementation phase. This class:
    
    1. Takes raw research findings (files read, search results, etc.)
    2. Extracts the signal (relevant findings with file:line references)
    3. Discards the noise (failed searches, irrelevant content)
    4. Produces a Plan artifact with specific steps
    
    Example:
        >>> compactor = ContextCompactor()
        >>> 
        >>> # Add research findings
        >>> compactor.add_finding(ResearchFinding(
        ...     content="User class handles authentication",
        ...     source="src/models/user.ts",
        ...     line_numbers="45-67",
        ...     category="core_logic"
        ... ))
        >>> 
        >>> # Compact into summary
        >>> result = compactor.compact(strategy=CompactionStrategy.PLAN)
        >>> print(f"Saved {result.tokens_saved} tokens")
    """
    
    def __init__(
        self,
        max_findings: int = 100,
        min_relevance: float = 0.5,
    ):
        """
        Initialize the Context Compactor.
        
        Args:
            max_findings: Maximum findings to retain.
            min_relevance: Minimum relevance score to keep.
        """
        self.max_findings = max_findings
        self.min_relevance = min_relevance
        
        self._findings: List[ResearchFinding] = []
        self._categories: Dict[str, List[ResearchFinding]] = {}
        self._total_input_tokens = 0
    
    def add_finding(self, finding: ResearchFinding) -> None:
        """
        Add a research finding.
        
        Args:
            finding: The finding to add.
        """
        if finding.relevance_score >= self.min_relevance:
            self._findings.append(finding)
            
            # Categorize
            if finding.category not in self._categories:
                self._categories[finding.category] = []
            self._categories[finding.category].append(finding)
        
        # Estimate tokens (rough approximation)
        self._total_input_tokens += len(finding.content.split()) * 1.3
    
    def add_raw_content(
        self,
        content: str,
        source: str,
        category: str = "general",
        relevance: float = 1.0,
    ) -> None:
        """
        Add raw content as a finding.
        
        Args:
            content: The raw content.
            source: Source of the content.
            category: Category for organization.
            relevance: Relevance score (0-1).
        """
        self.add_finding(ResearchFinding(
            content=content,
            source=source,
            relevance_score=relevance,
            category=category,
        ))
    
    def compact(
        self,
        strategy: CompactionStrategy = CompactionStrategy.SUMMARIZE,
        objective: Optional[str] = None,
    ) -> CompactionResult:
        """
        Compact the research findings.
        
        Args:
            strategy: Compaction strategy to use.
            objective: Optional objective to guide compaction.
            
        Returns:
            CompactionResult with compacted context.
        """
        start_time = datetime.utcnow()
        
        # Sort by relevance
        sorted_findings = sorted(
            self._findings,
            key=lambda f: f.relevance_score,
            reverse=True
        )[:self.max_findings]
        
        if strategy == CompactionStrategy.SUMMARIZE:
            result = self._compact_summarize(sorted_findings)
        elif strategy == CompactionStrategy.EXTRACT:
            result = self._compact_extract(sorted_findings)
        elif strategy == CompactionStrategy.PLAN:
            result = self._compact_plan(sorted_findings, objective)
        else:
            result = self._compact_hierarchical(sorted_findings)
        
        # Calculate metrics
        result.original_token_count = int(self._total_input_tokens)
        result.compacted_token_count = self._estimate_tokens(result)
        result.tokens_saved = result.original_token_count - result.compacted_token_count
        result.compaction_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return result
    
    def _compact_summarize(self, findings: List[ResearchFinding]) -> CompactionResult:
        """Summarize findings into key points."""
        key_findings = []
        relevant_files = set()
        
        for finding in findings:
            # Extract key point
            key_point = finding.content[:200].strip()
            if finding.line_numbers:
                key_point += f" ({finding.source}:{finding.line_numbers})"
            else:
                key_point += f" ({finding.source})"
            
            key_findings.append(key_point)
            relevant_files.add(finding.source)
        
        summary = ResearchSummary(
            key_findings=key_findings[:20],  # Top 20
            relevant_files=list(relevant_files)[:15],
            constraints=[],
            dependencies=[],
            patterns_found=[],
        )
        
        return CompactionResult(
            success=True,
            strategy=CompactionStrategy.SUMMARIZE,
            summary=summary,
        )
    
    def _compact_extract(self, findings: List[ResearchFinding]) -> CompactionResult:
        """Extract specific artifacts from findings."""
        relevant_files = []
        constraints = []
        dependencies = []
        
        for finding in findings:
            relevant_files.append(finding.to_reference())
            
            # Look for constraints in content
            content_lower = finding.content.lower()
            if any(word in content_lower for word in ["must", "required", "constraint", "cannot"]):
                constraints.append(finding.content[:100])
            
            # Look for dependencies
            if any(word in content_lower for word in ["import", "require", "depends", "uses"]):
                dependencies.append(finding.to_reference())
        
        summary = ResearchSummary(
            key_findings=[],
            relevant_files=relevant_files[:20],
            constraints=constraints[:10],
            dependencies=dependencies[:10],
            patterns_found=[],
        )
        
        return CompactionResult(
            success=True,
            strategy=CompactionStrategy.EXTRACT,
            summary=summary,
        )
    
    def _compact_plan(
        self,
        findings: List[ResearchFinding],
        objective: Optional[str],
    ) -> CompactionResult:
        """Generate an actionable plan from findings."""
        # Group findings by file
        by_file: Dict[str, List[ResearchFinding]] = {}
        for finding in findings:
            if finding.source not in by_file:
                by_file[finding.source] = []
            by_file[finding.source].append(finding)
        
        # Generate plan steps
        plan_steps = []
        for file_path, file_findings in by_file.items():
            # Determine action based on findings
            action = "modify"
            details = "; ".join(f.content[:50] for f in file_findings[:3])
            
            step = PlanStep(
                description=f"Update {file_path}",
                target_file=file_path,
                action=action,
                details=details,
                test_command="make test",
                verification=f"Verify changes in {file_path}",
            )
            plan_steps.append(step)
        
        # Create summary
        summary = ResearchSummary(
            key_findings=[f"Found {len(findings)} relevant items"],
            relevant_files=list(by_file.keys()),
            constraints=[],
            dependencies=[],
            patterns_found=[],
        )
        
        return CompactionResult(
            success=True,
            strategy=CompactionStrategy.PLAN,
            summary=summary,
            plan_steps=plan_steps,
        )
    
    def _compact_hierarchical(self, findings: List[ResearchFinding]) -> CompactionResult:
        """Create hierarchical summary by category."""
        key_findings = []
        
        for category, cat_findings in self._categories.items():
            cat_findings_sorted = sorted(cat_findings, key=lambda f: f.relevance_score, reverse=True)
            top_in_category = cat_findings_sorted[:5]
            
            for finding in top_in_category:
                key_findings.append(f"[{category}] {finding.content[:100]} ({finding.to_reference()})")
        
        summary = ResearchSummary(
            key_findings=key_findings[:25],
            relevant_files=[f.source for f in findings[:15]],
            constraints=[],
            dependencies=[],
            patterns_found=list(self._categories.keys()),
        )
        
        return CompactionResult(
            success=True,
            strategy=CompactionStrategy.HIERARCHICAL,
            summary=summary,
        )
    
    def _estimate_tokens(self, result: CompactionResult) -> int:
        """Estimate token count of compacted result."""
        total = 0
        
        if result.summary:
            summary_text = result.summary.to_context_string()
            total += len(summary_text.split()) * 1.3
        
        for step in result.plan_steps:
            total += len(step.description.split()) * 1.3
            total += len(step.details.split()) * 1.3
        
        return int(total)
    
    def clear(self) -> None:
        """Clear all findings."""
        self._findings.clear()
        self._categories.clear()
        self._total_input_tokens = 0


__all__ = [
    "ContextCompactor",
    "CompactionStrategy",
    "CompactionResult",
    "ResearchFinding",
    "ResearchSummary",
    "PlanStep",
]

