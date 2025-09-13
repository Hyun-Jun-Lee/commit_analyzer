"""
Data transformation functions for GitHub Commit Analyzer.
Pure functions that transform data between different representations.
"""

from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
import json
import re

from .functional import Result, ok, err, map_result, safe
from ..domain.types import (
    RepositoryInfo, CommitData, FileChange, DiffData, AuthorStats,
    WorkType, WorkStatus, ChangeType, VelocityMetrics, TimePatterns,
    ComplexityMetrics, FileHotspot, WorkTypeDistribution, 
    WorkStatusDistribution, AnalysisResult
)
from ..domain.constants import (
    LANGUAGE_EXTENSIONS, BINARY_FILE_EXTENSIONS, TEST_FILE_PATTERNS,
    TEST_DIRECTORY_PATTERNS, CONFIG_FILE_EXTENSIONS, DOCUMENTATION_EXTENSIONS
)


# ============================================================================
# GitHub API Response Transformations
# ============================================================================

def transform_github_repo_response(repo_data: Dict[str, Any]) -> Result[RepositoryInfo, Exception]:
    """Transform GitHub repository API response to RepositoryInfo."""
    try:
        return ok(RepositoryInfo(
            owner=repo_data['owner']['login'],
            name=repo_data['name'],
            description=repo_data.get('description'),
            primary_language=repo_data.get('language'),
            stars_count=repo_data.get('stargazers_count', 0),
            forks_count=repo_data.get('forks_count', 0),
            created_at=datetime.fromisoformat(repo_data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(repo_data['updated_at'].replace('Z', '+00:00')),
            html_url=repo_data['html_url'],
            clone_url=repo_data['clone_url']
        ))
    except (KeyError, ValueError, TypeError) as e:
        return err(e)


def transform_github_commit_response(commit_data: Dict[str, Any]) -> Result[CommitData, Exception]:
    """Transform GitHub commit API response to CommitData."""
    try:
        commit = commit_data['commit']
        
        return ok(CommitData(
            sha=commit_data['sha'],
            message=commit['message'],
            author=commit['author']['name'],
            author_email=commit['author']['email'],
            authored_date=datetime.fromisoformat(commit['author']['date'].replace('Z', '+00:00')),
            committer=commit['committer']['name'],
            committer_email=commit['committer']['email'],
            committed_date=datetime.fromisoformat(commit['committer']['date'].replace('Z', '+00:00')),
            parent_shas=[parent['sha'] for parent in commit_data.get('parents', [])]
        ))
    except (KeyError, ValueError, TypeError) as e:
        return err(e)


def transform_github_diff_response(diff_data: Dict[str, Any]) -> Result[List[FileChange], Exception]:
    """Transform GitHub diff API response to FileChange list."""
    try:
        file_changes = []
        
        for file_info in diff_data.get('files', []):
            # Determine change type
            status = file_info.get('status', 'modified')
            change_type = {
                'added': ChangeType.ADDED,
                'removed': ChangeType.DELETED,
                'modified': ChangeType.MODIFIED,
                'renamed': ChangeType.RENAMED
            }.get(status, ChangeType.MODIFIED)
            
            file_change = FileChange(
                path=Path(file_info['filename']),
                lines_added=file_info.get('additions', 0),
                lines_deleted=file_info.get('deletions', 0),
                change_type=change_type,
                content_before=file_info.get('patch'),  # Raw patch data
                content_after=None  # Not provided in GitHub API
            )
            
            file_changes.append(file_change)
        
        return ok(file_changes)
    except (KeyError, ValueError, TypeError) as e:
        return err(e)


def transform_to_diff_data(commit_sha: str, file_changes: List[FileChange]) -> DiffData:
    """Transform file changes to DiffData."""
    total_additions = sum(change.lines_added for change in file_changes)
    total_deletions = sum(change.lines_deleted for change in file_changes)
    
    return DiffData(
        commit_sha=commit_sha,
        file_changes=file_changes,
        total_additions=total_additions,
        total_deletions=total_deletions
    )


# ============================================================================
# File Classification Transformations
# ============================================================================

def classify_file_type(file_path: Path) -> str:
    """Classify file type based on path and extension."""
    path_str = str(file_path).lower()
    extension = file_path.suffix.lower()
    
    # Binary files
    if extension in BINARY_FILE_EXTENSIONS:
        return 'binary'
    
    # Documentation
    if extension in DOCUMENTATION_EXTENSIONS:
        return 'documentation'
    
    # Configuration
    if extension in CONFIG_FILE_EXTENSIONS:
        return 'configuration'
    
    # Test files (by pattern)
    for pattern in TEST_FILE_PATTERNS:
        if pattern in path_str:
            return 'test'
    
    # Test files (by directory)
    path_parts = file_path.parts
    for pattern in TEST_DIRECTORY_PATTERNS:
        if any(pattern in part.lower() for part in path_parts):
            return 'test'
    
    # Programming language files
    if extension in LANGUAGE_EXTENSIONS:
        return 'source'
    
    return 'other'


def extract_programming_language(file_path: Path) -> Optional[str]:
    """Extract programming language from file extension."""
    extension = file_path.suffix.lower()
    return LANGUAGE_EXTENSIONS.get(extension)


def is_test_file(file_path: Path) -> bool:
    """Check if file is a test file."""
    return classify_file_type(file_path) == 'test'


def is_source_file(file_path: Path) -> bool:
    """Check if file is a source code file."""
    return classify_file_type(file_path) == 'source'


def is_documentation_file(file_path: Path) -> bool:
    """Check if file is a documentation file."""
    return classify_file_type(file_path) == 'documentation'


# ============================================================================
# Work Type Inference Transformations
# ============================================================================

def infer_work_type_from_files(file_changes: List[FileChange]) -> Set[WorkType]:
    """Infer work types from file changes."""
    work_types = set()
    
    file_types = [classify_file_type(change.path) for change in file_changes]
    
    # Test-related work
    if any(file_type == 'test' for file_type in file_types):
        work_types.add(WorkType.TESTING)
    
    # Documentation work
    if any(file_type == 'documentation' for file_type in file_types):
        work_types.add(WorkType.DOCUMENTATION)
    
    # Configuration work
    if any(file_type == 'configuration' for file_type in file_types):
        work_types.add(WorkType.CONFIGURATION)
    
    # Source code analysis
    source_changes = [change for change in file_changes if is_source_file(change.path)]
    
    if source_changes:
        # Check for new files (potential features)
        new_files = [change for change in source_changes if change.change_type == ChangeType.ADDED]
        if new_files:
            work_types.add(WorkType.FEATURE_DEVELOPMENT)
        
        # Check for small changes (potential bug fixes)
        small_changes = [change for change in source_changes if change.is_small_change()]
        large_changes = [change for change in source_changes if not change.is_small_change()]
        
        if small_changes and not large_changes:
            work_types.add(WorkType.BUG_FIX)
        elif large_changes:
            work_types.add(WorkType.REFACTORING)
    
    # Default to feature development if no specific type identified
    if not work_types and source_changes:
        work_types.add(WorkType.FEATURE_DEVELOPMENT)
    
    return work_types


def infer_work_status_from_commit(commit: CommitData, file_changes: List[FileChange]) -> WorkStatus:
    """Infer work status from commit and file changes."""
    message_lower = commit.message.lower()
    
    # Status indicators in commit message
    if any(word in message_lower for word in ['wip', 'todo', 'fixme', 'partial']):
        return WorkStatus.IN_PROGRESS
    
    if any(word in message_lower for word in ['done', 'complete', 'finish', 'close']):
        return WorkStatus.COMPLETED
    
    if any(word in message_lower for word in ['plan', 'draft', 'skeleton']):
        return WorkStatus.PLANNED
    
    # Analyze file changes
    has_tests = any(is_test_file(change.path) for change in file_changes)
    has_source = any(is_source_file(change.path) for change in file_changes)
    
    # If has both source and tests, likely completed work
    if has_source and has_tests:
        return WorkStatus.COMPLETED
    
    # If only source changes, might be in progress
    if has_source and not has_tests:
        return WorkStatus.IN_PROGRESS
    
    return WorkStatus.COMPLETED  # Default assumption


# ============================================================================
# Metrics Calculation Transformations
# ============================================================================

def calculate_velocity_metrics(commits: List[CommitData], diffs: List[DiffData], days: int) -> VelocityMetrics:
    """Calculate development velocity metrics."""
    if not commits or days == 0:
        return VelocityMetrics(
            commits_per_day=0.0,
            lines_per_day=0.0,
            files_per_commit=0.0,
            average_commit_size=0.0
        )
    
    # Calculate metrics
    commits_per_day = len(commits) / days
    
    total_lines_changed = sum(diff.total_additions + diff.total_deletions for diff in diffs)
    lines_per_day = total_lines_changed / days if days > 0 else 0.0
    
    total_files_changed = sum(len(diff.file_changes) for diff in diffs)
    files_per_commit = total_files_changed / len(commits) if commits else 0.0
    
    average_commit_size = total_lines_changed / len(commits) if commits else 0.0
    
    return VelocityMetrics(
        commits_per_day=commits_per_day,
        lines_per_day=lines_per_day,
        files_per_commit=files_per_commit,
        average_commit_size=average_commit_size
    )


def calculate_time_patterns(commits: List[CommitData]) -> TimePatterns:
    """Calculate temporal patterns from commits."""
    if not commits:
        return TimePatterns(
            most_active_hour=9,
            most_active_day='Monday',
            commit_time_distribution={},
            day_distribution={},
            commits_per_day=0.0
        )
    
    # Collect time data
    hours = [commit.authored_date.hour for commit in commits]
    days = [commit.authored_date.strftime('%A') for commit in commits]
    
    # Calculate distributions
    hour_dist = {}
    for hour in hours:
        hour_dist[hour] = hour_dist.get(hour, 0) + 1
    
    day_dist = {}
    for day in days:
        day_dist[day] = day_dist.get(day, 0) + 1
    
    # Find peaks
    most_active_hour = max(hour_dist.items(), key=lambda x: x[1])[0] if hour_dist else 9
    most_active_day = max(day_dist.items(), key=lambda x: x[1])[0] if day_dist else 'Monday'
    
    # Calculate daily rate
    if commits:
        time_span = (max(commit.authored_date for commit in commits) - 
                    min(commit.authored_date for commit in commits)).days
        commits_per_day = len(commits) / max(1, time_span)
    else:
        commits_per_day = 0.0
    
    return TimePatterns(
        most_active_hour=most_active_hour,
        most_active_day=most_active_day,
        commit_time_distribution=hour_dist,
        day_distribution=day_dist,
        commits_per_day=commits_per_day
    )


def calculate_author_stats(commits: List[CommitData], diffs: List[DiffData]) -> List[AuthorStats]:
    """Calculate statistics for each author."""
    author_data = {}
    
    # Process commits
    for commit in commits:
        author_key = (commit.author, commit.author_email)
        if author_key not in author_data:
            author_data[author_key] = {
                'commits': 0,
                'lines_added': 0,
                'lines_deleted': 0,
                'files_modified': set(),
                'hours': [],
                'days': []
            }
        
        author_data[author_key]['commits'] += 1
        author_data[author_key]['hours'].append(commit.authored_date.hour)
        author_data[author_key]['days'].append(commit.authored_date.strftime('%A'))
    
    # Process diffs
    diff_by_commit = {diff.commit_sha: diff for diff in diffs}
    
    for commit in commits:
        if commit.sha in diff_by_commit:
            diff = diff_by_commit[commit.sha]
            author_key = (commit.author, commit.author_email)
            
            if author_key in author_data:
                author_data[author_key]['lines_added'] += diff.total_additions
                author_data[author_key]['lines_deleted'] += diff.total_deletions
                
                for file_change in diff.file_changes:
                    author_data[author_key]['files_modified'].add(str(file_change.path))
    
    # Create AuthorStats objects
    stats = []
    for (name, email), data in author_data.items():
        # Find most active hour and day
        most_active_hour = None
        if data['hours']:
            hour_counts = {}
            for hour in data['hours']:
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            most_active_hour = max(hour_counts.items(), key=lambda x: x[1])[0]
        
        most_active_day = None
        if data['days']:
            day_counts = {}
            for day in data['days']:
                day_counts[day] = day_counts.get(day, 0) + 1
            most_active_day = max(day_counts.items(), key=lambda x: x[1])[0]
        
        stats.append(AuthorStats(
            name=name,
            email=email,
            commits_count=data['commits'],
            lines_added=data['lines_added'],
            lines_deleted=data['lines_deleted'],
            files_modified=len(data['files_modified']),
            most_active_day=most_active_day,
            most_active_hour=most_active_hour
        ))
    
    return sorted(stats, key=lambda x: x.commits_count, reverse=True)


def calculate_file_hotspots(diffs: List[DiffData]) -> List[FileHotspot]:
    """Calculate file change hotspots."""
    file_stats = {}
    
    for diff in diffs:
        for file_change in diff.file_changes:
            path_str = str(file_change.path)
            
            if path_str not in file_stats:
                file_stats[path_str] = {
                    'changes': 0,
                    'total_lines': 0,
                    'authors': set(),
                    'last_modified': file_change.path  # We'll update this
                }
            
            file_stats[path_str]['changes'] += 1
            file_stats[path_str]['total_lines'] += file_change.lines_added + file_change.lines_deleted
    
    # Convert to FileHotspot objects
    hotspots = []
    for path_str, stats in file_stats.items():
        # For now, we don't have author information per file, so we'll use placeholder
        hotspots.append(FileHotspot(
            path=Path(path_str),
            change_frequency=stats['changes'],
            total_lines_changed=stats['total_lines'],
            last_modified=datetime.now(),  # Placeholder
            authors_count=1  # Placeholder
        ))
    
    return sorted(hotspots, key=lambda x: x.change_frequency, reverse=True)


# ============================================================================
# Output Formatting Transformations
# ============================================================================

def transform_to_json_serializable(obj: Any) -> Any:
    """Transform objects to JSON-serializable format."""
    if hasattr(obj, '__dict__'):
        result = {}
        for key, value in obj.__dict__.items():
            result[key] = transform_to_json_serializable(value)
        return result
    elif isinstance(obj, list):
        return [transform_to_json_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: transform_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Path):
        return str(obj)
    elif hasattr(obj, 'value'):  # Enum
        return obj.value
    else:
        return obj


def format_analysis_summary(result: AnalysisResult) -> str:
    """Format analysis result as human-readable summary."""
    lines = [
        f"# Analysis Summary for {result.repository_info.owner}/{result.repository_info.name}",
        "",
        f"**Analysis Period:** {result.analysis_period_days} days",
        f"**Total Commits:** {result.total_commits}",
        f"**Unique Authors:** {result.unique_authors}",
        "",
        "## Work Distribution",
    ]
    
    work_dist = result.work_distribution
    total_work = work_dist.total_work_items()
    
    if total_work > 0:
        lines.extend([
            f"- Feature Development: {work_dist.feature_development} ({work_dist.feature_development/total_work*100:.1f}%)",
            f"- Bug Fixes: {work_dist.bug_fix} ({work_dist.bug_fix/total_work*100:.1f}%)",
            f"- Testing: {work_dist.testing} ({work_dist.testing/total_work*100:.1f}%)",
            f"- Refactoring: {work_dist.refactoring} ({work_dist.refactoring/total_work*100:.1f}%)",
            f"- Documentation: {work_dist.documentation} ({work_dist.documentation/total_work*100:.1f}%)",
            f"- Configuration: {work_dist.configuration} ({work_dist.configuration/total_work*100:.1f}%)",
        ])
    
    lines.extend([
        "",
        "## Velocity Metrics",
        f"- Commits per day: {result.velocity_metrics.commits_per_day:.2f}",
        f"- Lines per day: {result.velocity_metrics.lines_per_day:.2f}",
        f"- Files per commit: {result.velocity_metrics.files_per_commit:.2f}",
        "",
        "## Top Contributors",
    ])
    
    for i, author in enumerate(result.author_stats[:5]):
        lines.append(f"{i+1}. {author.name} - {author.commits_count} commits, {author.net_contribution()} lines net")
    
    return "\n".join(lines)


# ============================================================================
# Error Transformation Helpers
# ============================================================================

@safe
def parse_json_response(response_text: str) -> Dict[str, Any]:
    """Safely parse JSON response."""
    return json.loads(response_text)


def extract_error_message(error_response: Dict[str, Any]) -> str:
    """Extract error message from API error response."""
    if 'message' in error_response:
        return error_response['message']
    elif 'error' in error_response:
        if isinstance(error_response['error'], dict):
            return error_response['error'].get('message', str(error_response['error']))
        else:
            return str(error_response['error'])
    else:
        return str(error_response)


def normalize_commit_message(message: str) -> str:
    """Normalize commit message for analysis."""
    # Remove extra whitespace
    message = ' '.join(message.split())
    
    # Limit length
    if len(message) > 200:
        message = message[:197] + "..."
    
    return message