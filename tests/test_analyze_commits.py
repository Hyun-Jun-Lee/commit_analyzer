#!/usr/bin/env python3
"""
analyze_commits 도구 독립 실행 테스트
fastmcp_server.py의 analyze_commits 함수를 @app.tool() 데코레이터 없이 테스트

Usage: python test_analyze_commits.py <owner/repo> [--days N]
Example: python test_analyze_commits.py microsoft/vscode --days 7
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any

# Add src to Python path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
from core.utils.functional import Result
from core.domain.errors import AnyError, format_user_friendly_message
from core.utils.validation import validate_analyze_commits_params


async def handle_analyze_commits(arguments: Dict[str, Any]) -> Result[Dict[str, Any], AnyError]:
    """Handle analyze_commits tool call."""
    # Import here to avoid circular imports
    from infrastructure.pipelines import run_commit_analysis_pipeline

    # Validate parameters
    validation_result = validate_analyze_commits_params(arguments)
    if validation_result.is_err():
        return validation_result

    params = validation_result.unwrap()

    # Use the updated pipeline
    try:
        result = await run_commit_analysis_pipeline(
            owner=params['owner'],
            repo=params['repo'],
            days=params.get('days', 7)
        )

        if result.is_ok():
            data = result.unwrap()
            # Debug: Check if diffs are included
            commits = data.get('commits', [])
            diffs = data.get('diffs', [])

            print(f"\n🔍 Debug: Pipeline returned {len(commits)} commits and {len(diffs)} diffs")
            if diffs and len(diffs) > 0:
                # Show first diff details for debugging
                first_diff = diffs[0]
                if isinstance(first_diff, dict):
                    print(f"📁 Sample diff - Commit: {first_diff.get('commit_sha', 'unknown')}")
                    print(f"📊 Sample diff - Files changed: {first_diff.get('file_changes', [])}")
                else:
                    print(f"📁 Sample diff object: {type(first_diff)}")

            return result
        else:
            return result

    except Exception as e:
        from core.domain.errors import AnalysisError
        from core.utils.functional import err
        import traceback

        # Get full traceback for debugging
        tb_str = traceback.format_exc()
        print(f"\n❌ Exception in handle_analyze_commits:\n{tb_str}")

        return err(AnalysisError(
            message=f"Commit analysis failed: {str(e)}\n\nFull traceback:\n{tb_str}",
            context={'arguments': arguments, 'traceback': tb_str}
        ))


def format_commit_analysis_response(data: Dict[str, Any]) -> str:
    """Format simplified analysis response for display."""
    repo_info = data.get('repository', {})

    response = f"""# 📊 **Simplified Commit Analysis Report**

## 📁 **Repository**: {repo_info.get('full_name', 'Unknown')}
- **Language**: {repo_info.get('primary_language', 'Unknown')}
- **Stars**: {repo_info.get('stargazers_count', 0)}
- **Analysis Period**: {data.get('analysis_period_days', 7)} days

## 📈 **Basic Statistics**
- **Total Commits**: {data.get('total_commits', 0)}
- **Unique Authors**: {data.get('unique_authors', 0)}

## 💡 **Summary**
{data.get('summary', 'No summary available')}

## 📋 **Raw Data Available** (for Claude Code)
- **Commits**: {len(data.get('commits', []))} commit objects
- **Diffs**: {len(data.get('diffs', []))} diff objects"""

    # Show some sample commit info
    commits = data.get('commits', [])
    if commits:
        response += f"""

## 🔍 **Sample Recent Commits** (First 5)"""
        for i, commit in enumerate(commits[:5], 1):
            if isinstance(commit, dict):
                sha = commit.get('sha', 'unknown')
                message = commit.get('message', 'No message')[:50] + '...' if len(commit.get('message', '')) > 50 else commit.get('message', '')
                author = commit.get('author', 'Unknown')
                response += f"\n{i}. `{sha}` - {message} ({author})"

    # Show some sample diff info
    diffs = data.get('diffs', [])
    if diffs:
        response += f"""

## 📊 **Sample Diffs** (First 3)"""
        for i, diff in enumerate(diffs[:3], 1):
            if isinstance(diff, dict):
                sha = diff.get('commit_sha', 'unknown')
                # Handle different data structures
                if 'file_changes' in diff:
                    # If it's a list of file changes
                    file_changes = diff.get('file_changes', [])
                    if isinstance(file_changes, list):
                        files = len(file_changes)
                    else:
                        files = file_changes
                else:
                    files = diff.get('files_changed', 0)

                additions = diff.get('total_additions', diff.get('additions', 0))
                deletions = diff.get('total_deletions', diff.get('deletions', 0))
                response += f"\n{i}. Commit `{sha}`: {files} files, +{additions} -{deletions} lines"

    return response


async def analyze_commits(owner: str, repo: str, days: int = 7) -> str:
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
        try:
            error_msg = format_user_friendly_message(error)
        except:
            error_msg = str(error)

        # Add detailed error traceback for debugging
        import traceback
        if hasattr(error, '__traceback__'):
            tb_str = ''.join(traceback.format_tb(error.__traceback__))
            return f"❌ **Error**: {error_msg}\n\n**Traceback:**\n```\n{tb_str}\n```"
        else:
            # If error is a Result type, try to extract more info
            return f"❌ **Error**: {error_msg}\n\n**Error Type**: {type(error)}\n**Error Details**: {repr(error)}"


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze GitHub repository commits to understand work patterns",
        epilog="Example: python test_analyze_commits.py microsoft/vscode --days 7"
    )

    parser.add_argument(
        "repository",
        help="GitHub repository in 'owner/repo' format (e.g., microsoft/vscode)"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (1-30, default: 7)"
    )

    return parser.parse_args()


async def main():
    """Main function."""
    # Load environment variables
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print("✅ Environment variables loaded")
    else:
        print("❌ .env file not found")
        return 1

    # Check GitHub token
    if not os.getenv('GITHUB_TOKEN'):
        print("❌ GITHUB_TOKEN not set in environment")
        return 1

    # Parse arguments
    args = parse_arguments()

    # Validate repository format
    if '/' not in args.repository:
        print("❌ Repository must be in 'owner/repo' format")
        return 1

    owner, repo = args.repository.split('/', 1)

    print(f"🚀 Testing analyze_commits with {args.repository} (last {args.days} days)")
    print("=" * 70)

    try:
        # Run the analyze_commits function
        result = await analyze_commits(owner, repo, args.days)
        print(result)
        return 0

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))