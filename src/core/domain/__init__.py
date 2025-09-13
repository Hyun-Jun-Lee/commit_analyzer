"""
Domain layer for GitHub Commit Analyzer.
Contains core types, constants, and error definitions.
"""

from .types import *
from .errors import *
from .constants import *

__all__ = [
    # Types
    'WorkType', 'WorkStatus', 'CodeContext', 'ChangeType',
    'RepositoryInfo', 'CommitData', 'FileChange', 'DiffData',
    'AuthorStats', 'TimePatterns', 'VelocityMetrics', 'ComplexityMetrics',
    'FileHotspot', 'WorkTypeDistribution', 'WorkStatusDistribution',
    'AnalysisData', 'AnalysisResult',
    'AnalyzeCommitsParams', 'GetCommitDiffParams', 'RepositorySummaryParams',
    'AnalyzeCodeChangesParams',
    
    # Errors
    'AnalysisError', 'ValidationError', 'GitHubAPIError', 'NetworkError',
    'ParseError', 'CodeAnalysisError', 'ConfigError', 'MCPError',
    'InvalidRepositoryName', 'InvalidCommitSHA', 'InvalidDateRange',
    'RepositoryNotFound', 'RateLimitExceeded', 'UnauthorizedAccess',
    'AnyError',
    
    # Constants
    'DEFAULT_ANALYSIS_DAYS', 'MAX_ANALYSIS_DAYS', 'MAX_COMMITS_PER_REQUEST',
    'BINARY_FILE_EXTENSIONS', 'LANGUAGE_EXTENSIONS', 'API_PATTERNS',
    'EMOJI_MAP', 'REPORT_SECTIONS'
]