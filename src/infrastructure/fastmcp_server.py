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
    if not validation_result:
        return validation_result
    
    params = validation_result.value
    
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
    if not validation_result:
        return validation_result
    
    params = validation_result.value
    
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
    if not validation_result:
        return validation_result
    
    params = validation_result.value
    
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
    if not validation_result:
        return validation_result
    
    params = validation_result.value
    
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
    
    if result:
        data = result.value
        return format_commit_analysis_response(data)
    else:
        error_msg = format_user_friendly_message(result.error)
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
    
    if result:
        data = result.value
        return format_commit_diff_response(data)
    else:
        error_msg = format_user_friendly_message(result.error)
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
    
    if result:
        data = result.value
        return format_repository_summary_response(data)
    else:
        error_msg = format_user_friendly_message(result.error)
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
    
    if result:
        data = result.value
        return format_code_analysis_response(data)
    else:
        error_msg = format_user_friendly_message(result.error)
        return f"❌ **Error**: {error_msg}"


# ============================================================================
# Response Formatting Functions
# ============================================================================

def format_commit_analysis_response(data: Dict[str, Any]) -> str:
    """Format commit analysis response."""
    # Extract key metrics
    summary = data.get('summary', {})
    work_patterns = data.get('work_patterns', {})
    
    primary_work = summary.get('primary_work_type', 'unknown')
    total_commits = summary.get('total_commits_analyzed', 0)
    completion_rate = summary.get('completion_rate', 0)
    
    # Format response
    response = f"""📊 **Commit Analysis Report**

**Overview:**
- Primary work type: {primary_work.replace('_', ' ').title()}
- Total commits analyzed: {total_commits}
- Work completion rate: {completion_rate:.1%}

**Work Distribution:**"""
    
    work_dist = summary.get('work_type_distribution', {})
    for work_type, count in work_dist.items():
        if count > 0:
            response += f"\n- {work_type.replace('_', ' ').title()}: {count}"
    
    # Add development patterns
    patterns = summary.get('development_patterns', [])
    if patterns:
        response += f"\n\n**Development Patterns:**"
        for pattern in patterns:
            response += f"\n- {pattern.replace('_', ' ').title()}"
    
    # Add language distribution
    languages = summary.get('language_distribution', {})
    if languages:
        response += f"\n\n**Languages Used:**"
        for lang, files in languages.items():
            response += f"\n- {lang}: {files} files"
    
    return response


def format_commit_diff_response(data: Dict[str, Any]) -> str:
    """Format commit diff response."""
    commit_info = data.get('commit', {})
    diff_info = data.get('diff', {})
    
    response = f"""🔬 **Commit Diff Analysis**

**Commit:** {commit_info.get('sha', 'unknown')[:8]}
**Author:** {commit_info.get('author', 'unknown')}
**Date:** {commit_info.get('authored_date', 'unknown')}
**Message:** {commit_info.get('message', 'No message')}

**Changes:**
- Files modified: {diff_info.get('files_modified_count', 0)}
- Lines added: {diff_info.get('total_additions', 0)}
- Lines deleted: {diff_info.get('total_deletions', 0)}
- Net change: {diff_info.get('net_changes', 0)}"""
    
    # Add file-level details
    file_changes = diff_info.get('file_changes', [])
    if file_changes:
        response += f"\n\n**Modified Files:**"
        for file_change in file_changes[:10]:  # Limit to first 10 files
            path = file_change.get('path', 'unknown')
            added = file_change.get('lines_added', 0)
            deleted = file_change.get('lines_deleted', 0)
            change_type = file_change.get('change_type', 'modified')
            
            response += f"\n- {path} ({change_type}): +{added}/-{deleted}"
    
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
    """Format code analysis response."""
    summary = data.get('summary', {})
    focus_areas = data.get('focus_areas', {})
    
    response = f"""💡 **Code Analysis Report**

**Work Focus:**
- Primary context: {summary.get('primary_context', 'unknown').replace('_', ' ').title()}
- Most active hour: {summary.get('most_active_hour', 'unknown')}
- Average change size: {summary.get('average_change_size', 0):.1f} lines
- Total lines changed: {summary.get('total_lines_changed', 0):,}"""
    
    # Add focus scores
    focus_scores = summary.get('focus_scores', {})
    if focus_scores:
        response += f"\n\n**Development Focus Distribution:**"
        for context, score in sorted(focus_scores.items(), key=lambda x: x[1], reverse=True):
            response += f"\n- {context.replace('_', ' ').title()}: {score:.1%}"
    
    # Add development patterns
    patterns = summary.get('development_patterns', [])
    if patterns:
        response += f"\n\n**Development Patterns:**"
        for pattern in patterns:
            response += f"\n- {pattern.replace('_', ' ').title()}"
    
    return response


# ============================================================================
# Server Entry Point
# ============================================================================

def run_server():
    """Run the FastMCP server."""
    app.run()


if __name__ == "__main__":
    run_server()