"""
Core domain types for GitHub Commit Analyzer.
All types are immutable and follow functional programming principles.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import FrozenSet, List, Optional, Dict, Union
from pathlib import Path


# ============================================================================
# Base Types and Enums
# ============================================================================

class WorkType(Enum):
    """Classification of work based on code changes."""
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    FEATURE_DEVELOPMENT = "feature_development"
    BUG_FIX = "bug_fix"
    REFACTORING = "refactoring"
    DEPENDENCY_UPDATE = "dependency_update"
    PERFORMANCE = "performance"
    SECURITY = "security"


class WorkStatus(Enum):
    """Status of work based on code indicators."""
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    PLANNED = "planned"
    BLOCKED = "blocked"


class CodeContext(Enum):
    """Context of code changes."""
    API = "api"
    DATABASE = "database"
    UI = "ui"
    BUSINESS = "business"
    INFRASTRUCTURE = "infrastructure"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"


class ChangeType(Enum):
    """Type of file change."""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


# ============================================================================
# Core Data Types (Immutable)
# ============================================================================

@dataclass(frozen=True)
class RepositoryInfo:
    """Repository basic information."""
    owner: str
    name: str
    description: Optional[str]
    primary_language: Optional[str]
    stars_count: int
    forks_count: int
    created_at: datetime
    updated_at: datetime
    html_url: str
    clone_url: str


@dataclass(frozen=True)
class CommitData:
    """Individual commit information."""
    sha: str
    message: str
    author: str
    author_email: str
    authored_date: datetime
    committer: str
    committer_email: str
    committed_date: datetime
    parent_shas: List[str]
    
    def is_merge_commit(self) -> bool:
        """Check if this is a merge commit."""
        return len(self.parent_shas) > 1


@dataclass(frozen=True)
class FileChange:
    """Information about a single file change."""
    path: Path
    lines_added: int
    lines_deleted: int
    change_type: ChangeType
    content_before: Optional[str] = None
    content_after: Optional[str] = None
    
    def net_lines(self) -> int:
        """Calculate net line changes."""
        return self.lines_added - self.lines_deleted
    
    def is_small_change(self) -> bool:
        """Check if this is a small change (< 10 lines)."""
        return (self.lines_added + self.lines_deleted) < 10
    
    def is_binary_file(self) -> bool:
        """Check if this is a binary file."""
        binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.exe'}
        return self.path.suffix.lower() in binary_extensions
    
    def file_extension(self) -> str:
        """Get file extension."""
        return self.path.suffix.lower()


@dataclass(frozen=True)
class DiffData:
    """Git diff information."""
    commit_sha: str
    file_changes: List[FileChange]
    total_additions: int
    total_deletions: int
    
    def net_changes(self) -> int:
        """Calculate net changes across all files."""
        return self.total_additions - self.total_deletions
    
    def files_modified_count(self) -> int:
        """Count of files modified."""
        return len(self.file_changes)


@dataclass(frozen=True)
class AuthorStats:
    """Statistics for a single author."""
    name: str
    email: str
    commits_count: int
    lines_added: int
    lines_deleted: int
    files_modified: int
    most_active_day: Optional[str] = None
    most_active_hour: Optional[int] = None
    
    def net_contribution(self) -> int:
        """Net lines contributed."""
        return self.lines_added - self.lines_deleted


@dataclass(frozen=True)
class TimePatterns:
    """Temporal patterns in commits."""
    most_active_hour: int
    most_active_day: str
    commit_time_distribution: Dict[int, int]  # hour -> count
    day_distribution: Dict[str, int]  # day -> count
    commits_per_day: float
    
    def peak_hours(self) -> List[int]:
        """Get hours with highest activity."""
        sorted_hours = sorted(
            self.commit_time_distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [hour for hour, _ in sorted_hours[:3]]


@dataclass(frozen=True)
class VelocityMetrics:
    """Development velocity metrics."""
    commits_per_day: float
    lines_per_day: float
    files_per_commit: float
    average_commit_size: float
    
    def is_high_velocity(self) -> bool:
        """Check if velocity is considered high."""
        return self.commits_per_day > 5.0


@dataclass(frozen=True)
class ComplexityMetrics:
    """Code complexity metrics."""
    cyclomatic_complexity_change: float
    cognitive_complexity_change: float
    method_length_change: float
    nesting_depth_change: float
    
    def complexity_increased(self) -> bool:
        """Check if overall complexity increased."""
        return (self.cyclomatic_complexity_change + 
                self.cognitive_complexity_change) > 0


@dataclass(frozen=True)
class FileHotspot:
    """Frequently changed file information."""
    path: Path
    change_frequency: int
    total_lines_changed: int
    last_modified: datetime
    authors_count: int
    
    def is_critical_hotspot(self) -> bool:
        """Check if this is a critical hotspot."""
        return self.change_frequency > 10 and self.authors_count > 3


@dataclass(frozen=True)
class WorkTypeDistribution:
    """Distribution of work types."""
    feature_development: int = 0
    bug_fix: int = 0
    testing: int = 0
    refactoring: int = 0
    configuration: int = 0
    documentation: int = 0
    dependency_update: int = 0
    performance: int = 0
    security: int = 0
    
    def total_work_items(self) -> int:
        """Total number of work items."""
        return (self.feature_development + self.bug_fix + self.testing +
                self.refactoring + self.configuration + self.documentation +
                self.dependency_update + self.performance + self.security)
    
    def primary_work_type(self) -> WorkType:
        """Get the most common work type."""
        work_counts = {
            WorkType.FEATURE_DEVELOPMENT: self.feature_development,
            WorkType.BUG_FIX: self.bug_fix,
            WorkType.TESTING: self.testing,
            WorkType.REFACTORING: self.refactoring,
            WorkType.CONFIGURATION: self.configuration,
            WorkType.DOCUMENTATION: self.documentation,
            WorkType.DEPENDENCY_UPDATE: self.dependency_update,
            WorkType.PERFORMANCE: self.performance,
            WorkType.SECURITY: self.security,
        }
        return max(work_counts.items(), key=lambda x: x[1])[0]


@dataclass(frozen=True)
class WorkStatusDistribution:
    """Distribution of work statuses."""
    completed: int = 0
    in_progress: int = 0
    planned: int = 0
    blocked: int = 0
    
    def total_items(self) -> int:
        """Total number of work items."""
        return self.completed + self.in_progress + self.planned + self.blocked
    
    def completion_rate(self) -> float:
        """Calculate completion rate."""
        total = self.total_items()
        return (self.completed / total) if total > 0 else 0.0


@dataclass(frozen=True)
class AnalysisData:
    """Complete analysis data container (immutable)."""
    repository: RepositoryInfo
    commits: List[CommitData]
    diffs: List[DiffData]
    file_changes: List[FileChange]
    work_types: FrozenSet[WorkType]
    metrics: Dict[str, Union[int, float, str]]
    timestamp: datetime
    
    def with_metrics(self, new_metrics: Dict[str, Union[int, float, str]]) -> 'AnalysisData':
        """Create new instance with additional metrics."""
        from dataclasses import replace
        combined_metrics = {**self.metrics, **new_metrics}
        return replace(self, metrics=combined_metrics)
    
    def with_work_types(self, work_types: FrozenSet[WorkType]) -> 'AnalysisData':
        """Create new instance with work types."""
        from dataclasses import replace
        return replace(self, work_types=work_types)
    
    def add_file_change(self, change: FileChange) -> 'AnalysisData':
        """Create new instance with additional file change."""
        from dataclasses import replace
        new_file_changes = self.file_changes + [change]
        return replace(self, file_changes=new_file_changes)


@dataclass(frozen=True)
class AnalysisResult:
    """Final analysis result (immutable, combinable)."""
    repository_info: RepositoryInfo
    analysis_period_days: int
    total_commits: int
    unique_authors: int
    work_distribution: WorkTypeDistribution
    status_distribution: WorkStatusDistribution
    velocity_metrics: VelocityMetrics
    complexity_metrics: ComplexityMetrics
    time_patterns: TimePatterns
    author_stats: List[AuthorStats]
    hotspots: List[FileHotspot]
    top_changed_files: List[str]
    summary: str
    
    def combine(self, other: 'AnalysisResult') -> 'AnalysisResult':
        """Combine two analysis results (monoid operation)."""
        if self.repository_info.name != other.repository_info.name:
            raise ValueError("Cannot combine results from different repositories")
        
        # This is a simplified combination - in practice, you'd implement
        # proper monoid operations for each field
        from dataclasses import replace
        return replace(
            self,
            total_commits=self.total_commits + other.total_commits,
            unique_authors=max(self.unique_authors, other.unique_authors),
            summary=f"{self.summary}\n\nCombined with: {other.summary}"
        )


# ============================================================================
# Parameter Types for MCP Tools
# ============================================================================

@dataclass(frozen=True)
class AnalyzeCommitsParams:
    """Parameters for analyze_commits tool."""
    owner: str
    repo: str
    days: int = 7
    
    def __post_init__(self):
        """Validate parameters."""
        if self.days < 1 or self.days > 30:
            raise ValueError("Days must be between 1 and 30")


@dataclass(frozen=True)
class GetCommitDiffParams:
    """Parameters for get_commit_diff tool."""
    owner: str
    repo: str
    commit_sha: str
    
    def __post_init__(self):
        """Validate parameters."""
        if not self.commit_sha or len(self.commit_sha) < 7:
            raise ValueError("Commit SHA must be at least 7 characters")


@dataclass(frozen=True)
class RepositorySummaryParams:
    """Parameters for repository_summary tool."""
    owner: str
    repo: str


@dataclass(frozen=True)
class AnalyzeCodeChangesParams:
    """Parameters for analyze_code_changes tool."""
    owner: str
    repo: str
    days: int = 7
    deep_analysis: bool = True
    
    def __post_init__(self):
        """Validate parameters."""
        if self.days < 1 or self.days > 30:
            raise ValueError("Days must be between 1 and 30")


# ============================================================================
# Time-related utilities
# ============================================================================

def get_date_range(days: int) -> tuple[datetime, datetime]:
    """Get date range for analysis."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def format_duration(start: datetime, end: datetime) -> str:
    """Format duration between two dates."""
    duration = end - start
    days = duration.days
    hours = duration.seconds // 3600
    
    if days > 0:
        return f"{days} days, {hours} hours"
    else:
        return f"{hours} hours"