"""
Infrastructure layer for GitHub Commit Analyzer.
Contains GitHub API client, MCP server, and analysis pipelines.
"""

from .github_client import (
    GitHubAPIClient,
    fetch_repository_analysis_data,
    fetch_commit_details,
    test_github_connection
)

from .fastmcp_server import (
    run_server
)

from .pipelines import (
    run_commit_analysis_pipeline,
    run_commit_diff_pipeline,
    run_repository_summary_pipeline,
    run_code_analysis_pipeline
)

__all__ = [
    # GitHub client
    'GitHubAPIClient',
    'fetch_repository_analysis_data',
    'fetch_commit_details',
    'test_github_connection',
    
    # MCP server
    'GitHubCommitAnalyzerServer',
    'run_server',
    
    # Analysis pipelines
    'run_commit_analysis_pipeline',
    'run_commit_diff_pipeline',
    'run_repository_summary_pipeline',
    'run_code_analysis_pipeline'
]