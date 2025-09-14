"""
FastMCP server implementation for GitHub Commit Analyzer.
Provides tools for Claude Code to analyze GitHub repositories using FastMCP.
"""

import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

import fastmcp

from core.utils.functional import Result, ok, err
from core.utils.validation import (
    validate_analyze_commits_params,
    validate_get_commit_diff_params,
    validate_repository_summary_params,
    validate_analyze_code_changes_params
)
from core.domain.errors import (
    AnyError, format_user_friendly_message
)


# ============================================================================
# FastMCP Server Configuration
# ============================================================================

# Create FastMCP app
app = fastmcp.FastMCP("GitHub Commit Analyzer")


# ============================================================================
# Tool Implementation Functions
# ============================================================================

async def handle_analyze_commits(arguments: Dict[str, Any]) -> Result[Dict[str, Any], AnyError]:
    """Handle analyze_commits tool call."""
    # Import here to avoid circular imports
    from .pipelines import run_commit_analysis_pipeline
    
    # Validate parameters
    validation_result = validate_analyze_commits_params(arguments)
    if validation_result.is_err():
        return validation_result

    params = validation_result.unwrap()
    
    # Run analysis pipeline
    return await run_commit_analysis_pipeline(
        owner=params['owner'],
        repo=params['repo'],
        days=params.get('days', 7)
    )


async def handle_get_commit_diff(arguments: Dict[str, Any]) -> Result[Dict[str, Any], AnyError]:
    """Handle get_commit_diff tool call."""
    # Import here to avoid circular imports
    from .pipelines import run_commit_diff_pipeline
    
    # Validate parameters
    validation_result = validate_get_commit_diff_params(arguments)
    if validation_result.is_err():
        return validation_result

    params = validation_result.unwrap()
    
    # Run diff pipeline
    return await run_commit_diff_pipeline(
        owner=params['owner'],
        repo=params['repo'],
        commit_sha=params['commit_sha']
    )


async def handle_repository_summary(arguments: Dict[str, Any]) -> Result[Dict[str, Any], AnyError]:
    """Handle repository_summary tool call."""
    # Import here to avoid circular imports
    from .pipelines import run_repository_summary_pipeline
    
    # Validate parameters
    validation_result = validate_repository_summary_params(arguments)
    if validation_result.is_err():
        return validation_result

    params = validation_result.unwrap()
    
    # Run summary pipeline
    return await run_repository_summary_pipeline(
        owner=params['owner'],
        repo=params['repo']
    )


async def handle_analyze_code_changes(arguments: Dict[str, Any]) -> Result[Dict[str, Any], AnyError]:
    """Handle analyze_code_changes tool call."""
    # Import here to avoid circular imports
    from .pipelines import run_code_analysis_pipeline

    # Validate parameters
    validation_result = validate_analyze_code_changes_params(arguments)
    if validation_result.is_err():
        return validation_result

    params = validation_result.unwrap()

    # Run code analysis pipeline
    return await run_code_analysis_pipeline(
        owner=params['owner'],
        repo=params['repo'],
        days=params.get('days', 7),
        deep_analysis=params.get('deep_analysis', True)
    )


# ============================================================================
# FastMCP Tool Definitions
# ============================================================================

@app.tool()
async def analyze_commits(
    owner: str,
    repo: str,
    days: int = 7
) -> str:
    """
    Analyze recent commits in a GitHub repository to understand work patterns.
    
    Args:
        owner: GitHub repository owner (username or organization)
        repo: GitHub repository name  
        days: Number of days to analyze (1-30, default: 7)
    
    Returns:
        Formatted analysis report of commit patterns, work types, and metrics
    """
    arguments = {"owner": owner, "repo": repo, "days": days}
    
    result = await handle_analyze_commits(arguments)

    if result.is_ok():
        data = result.unwrap()
        return format_commit_analysis_response(data)
    else:
        error = result.unwrap_err()
        error_msg = format_user_friendly_message(error)
        return f"❌ **Error**: {error_msg}"


@app.tool()
async def get_commit_diff(
    owner: str,
    repo: str,
    commit_sha: str
) -> str:
    """
    Get detailed diff information for a specific commit.
    
    Args:
        owner: GitHub repository owner
        repo: GitHub repository name
        commit_sha: Commit SHA (7-40 characters)
    
    Returns:
        Detailed analysis of the specific commit's changes
    """
    arguments = {"owner": owner, "repo": repo, "commit_sha": commit_sha}
    
    result = await handle_get_commit_diff(arguments)

    if result.is_ok():
        data = result.unwrap()
        return format_commit_diff_response(data)
    else:
        error = result.unwrap_err()
        error_msg = format_user_friendly_message(error)
        return f"❌ **Error**: {error_msg}"


@app.tool()
async def repository_summary(
    owner: str,
    repo: str
) -> str:
    """
    Get comprehensive summary of a GitHub repository.
    
    Args:
        owner: GitHub repository owner
        repo: GitHub repository name
    
    Returns:
        Overview of repository statistics, languages, and health indicators
    """
    arguments = {"owner": owner, "repo": repo}
    
    result = await handle_repository_summary(arguments)

    if result.is_ok():
        data = result.unwrap()
        return format_repository_summary_response(data)
    else:
        error = result.unwrap_err()
        error_msg = format_user_friendly_message(error)
        return f"❌ **Error**: {error_msg}"


@app.tool()
async def analyze_code_changes(
    owner: str,
    repo: str,
    days: int = 7,
    deep_analysis: bool = True
) -> str:
    """
    Deep analysis of code changes and work patterns.
    
    Args:
        owner: GitHub repository owner
        repo: GitHub repository name
        days: Number of days to analyze (1-30, default: 7)
        deep_analysis: Enable deep code analysis (default: true)
    
    Returns:
        Comprehensive analysis including advanced metrics and insights
    """
    arguments = {
        "owner": owner, 
        "repo": repo, 
        "days": days, 
        "deep_analysis": deep_analysis
    }
    
    result = await handle_analyze_code_changes(arguments)

    if result.is_ok():
        data = result.unwrap()
        return format_code_analysis_response(data)
    else:
        error = result.unwrap_err()
        error_msg = format_user_friendly_message(error)
        return f"❌ **Error**: {error_msg}"


# ============================================================================
# Response Formatting Functions
# ============================================================================

def format_commit_analysis_response(data: Dict[str, Any]) -> str:
    """Format commit analysis response with full data for Claude Code."""
    import json

    # Create comprehensive response with both human-readable summary and full data
    repo = data.get('repository', {})
    commits = data.get('commits', [])
    diffs = data.get('diffs', [])

    response = f"""📊 **Commit Analysis Report**

**Repository:** {repo.get('full_name', 'Unknown')}
**Language:** {repo.get('primary_language', 'Unknown')}
**Stars:** {repo.get('stars_count', 0):,}
**Period:** {data.get('analysis_period_days', 7)} days

**Summary:** {data.get('summary', 'No summary available')}

**Statistics:**
- Total Commits: {data.get('total_commits', 0)}
- Unique Authors: {data.get('unique_authors', 0)}

**Recent Commits Preview:**"""

    # Show sample commits for human readability
    for i, commit in enumerate(commits[:5], 1):
        sha = commit.get('sha', 'unknown')[:8]
        message = commit.get('message', 'No message')
        author = commit.get('author', 'Unknown')
        # Truncate long messages
        if len(message) > 60:
            message = message[:60] + '...'
        response += f"\n{i}. `{sha}` - {message} ({author})"

    if len(commits) > 5:
        response += f"\n... and {len(commits) - 5} more commits"

    # Include full data as JSON for Claude Code to analyze
    response += f"""

**Full Data for Analysis:**
```json
{json.dumps({
    'repository': repo,
    'analysis_period_days': data.get('analysis_period_days'),
    'total_commits': data.get('total_commits'),
    'unique_authors': data.get('unique_authors'),
    'summary': data.get('summary'),
    'commits': commits,
    'diffs': diffs
}, indent=2, default=str)}
```"""

    return response


def format_commit_diff_response(data: Dict[str, Any]) -> str:
    """Format commit diff response with full data for Claude Code."""
    import json

    # The actual pipeline returns commit and diff data directly, not nested
    commit_data = data.get('commit_data', {}) or data.get('commit', {})
    file_changes = data.get('file_changes', [])
    total_additions = data.get('total_additions', 0)
    total_deletions = data.get('total_deletions', 0)

    response = f"""🔬 **Commit Diff Analysis**

**Commit:** {commit_data.get('sha', 'unknown')[:8]}
**Author:** {commit_data.get('author', 'Unknown')}
**Date:** {commit_data.get('date', 'Unknown')}
**Message:** {commit_data.get('message', 'No message')}
**URL:** {commit_data.get('url', 'N/A')}

**Changes Summary:**
- Files modified: {len(file_changes)}
- Lines added: +{total_additions}
- Lines deleted: -{total_deletions}
- Net change: {total_additions - total_deletions:+d}

**Modified Files Preview:**"""

    # Show file changes preview
    for i, file_change in enumerate(file_changes[:10], 1):
        filename = file_change.get('filename', 'unknown')
        additions = file_change.get('additions', 0)
        deletions = file_change.get('deletions', 0)
        status = file_change.get('status', 'modified')

        response += f"\n{i}. `{filename}` ({status}): +{additions} -{deletions}"

    if len(file_changes) > 10:
        response += f"\n... and {len(file_changes) - 10} more files"

    # Include full data as JSON for Claude Code to analyze
    response += f"""

**Full Data for Analysis:**
```json
{json.dumps(data, indent=2, default=str)}
```"""

    return response


def format_repository_summary_response(data: Dict[str, Any]) -> str:
    """Format repository summary response."""
    repo_info = data.get('repository', {})
    
    response = f"""📁 **Repository Summary**

**Repository:** {repo_info.get('owner', 'unknown')}/{repo_info.get('name', 'unknown')}
**Description:** {repo_info.get('description', 'No description')}
**Primary Language:** {repo_info.get('primary_language', 'Unknown')}
**Stars:** {repo_info.get('stars_count', 0):,}
**Forks:** {repo_info.get('forks_count', 0):,}
**Created:** {repo_info.get('created_at', 'unknown')}
**Last Updated:** {repo_info.get('updated_at', 'unknown')}"""
    
    # Add language breakdown if available
    languages = data.get('languages', {})
    if languages:
        response += f"\n\n**Language Breakdown:**"
        total_bytes = sum(languages.values())
        for lang, bytes_count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
            percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
            response += f"\n- {lang}: {percentage:.1f}%"
    
    # Add contributor info if available
    contributors = data.get('contributors', [])
    if contributors:
        response += f"\n\n**Top Contributors:**"
        for contributor in contributors[:5]:
            login = contributor.get('login', 'unknown')
            contributions = contributor.get('contributions', 0)
            response += f"\n- {login}: {contributions} contributions"
    
    return response


def format_code_analysis_response(data: Dict[str, Any]) -> str:
    """Format code analysis response with full data for Claude Code."""
    import json

    # Use actual data structure returned by the simplified pipeline
    repo = data.get('repository', {})
    commits = data.get('commits', [])
    diffs = data.get('diffs', [])

    # Calculate basic metrics from actual data
    total_additions = sum(d.get('total_additions', 0) for d in diffs)
    total_deletions = sum(d.get('total_deletions', 0) for d in diffs)
    total_files_changed = sum(d.get('files_modified_count', 0) for d in diffs)

    response = f"""💡 **Code Analysis Report**

**Repository:** {repo.get('full_name', 'Unknown')}
**Language:** {repo.get('primary_language', 'Unknown')}
**Analysis Period:** {data.get('analysis_period_days', 7)} days
**Deep Analysis:** {data.get('deep_analysis', 'Unknown')}

**Activity Summary:**
- Total Commits: {data.get('total_commits', 0)}
- Unique Authors: {data.get('unique_authors', 0)}
- Lines Added: +{total_additions:,}
- Lines Deleted: -{total_deletions:,}
- Files Changed: {total_files_changed:,}

**Code Quality Indicators:**"""

    # Show quality indicators if available
    quality_indicators = data.get('quality_indicators', {})
    if quality_indicators:
        for indicator, value in quality_indicators.items():
            response += f"\n- {indicator.replace('_', ' ').title()}: {value}"

    # Show hotspots if available
    hotspots = data.get('hotspots', [])
    if hotspots:
        response += f"\n\n**File Hotspots (Top 5):**"
        for i, hotspot in enumerate(hotspots[:5], 1):
            path = hotspot.get('path', 'unknown')
            changes = hotspot.get('change_frequency', 0)
            response += f"\n{i}. `{path}` - {changes} changes"

    # Show insights if available
    insights = data.get('insights', [])
    if insights:
        response += f"\n\n**Insights:**"
        for insight in insights[:5]:
            response += f"\n- {insight}"

    # Show recommendations if available
    recommendations = data.get('recommendations', [])
    if recommendations:
        response += f"\n\n**Recommendations:**"
        for i, rec in enumerate(recommendations[:5], 1):
            response += f"\n{i}. {rec}"

    # Include full data as JSON for Claude Code to analyze
    response += f"""

**Full Data for Analysis:**
```json
{json.dumps(data, indent=2, default=str)}
```"""

    return response


# ============================================================================
# Server Entry Point
# ============================================================================

def run_server():
    """Run the FastMCP server."""
    app.run()


if __name__ == "__main__":
    run_server()