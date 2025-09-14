#!/usr/bin/env python3
"""
repository_summary 도구 독립 실행 테스트
fastmcp_server.py의 repository_summary 함수를 @app.tool() 데코레이터 없이 테스트

Usage: python test_repository_summary.py <owner/repo>
Example: python test_repository_summary.py microsoft/vscode
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
from core.utils.validation import validate_repository_summary_params


async def handle_repository_summary(arguments: Dict[str, Any]) -> Result[Dict[str, Any], AnyError]:
    """Handle repository_summary tool call."""
    # Import here to avoid circular imports
    from infrastructure.github_client import GitHubAPIClient
    from core.utils.functional import Result, ok
    from core.utils.data_transformation import transform_to_json_serializable

    # Validate parameters
    validation_result = validate_repository_summary_params(arguments)
    if validation_result.is_err():
        return validation_result

    params = validation_result.unwrap()

    # Direct implementation without pipeline to avoid @safe decorator issues
    try:
        with GitHubAPIClient() as client:
            # Fetch repository info
            repo_result = client.get_repository_info(
                owner=params['owner'],
                repo=params['repo']
            )

            if repo_result.is_err():
                return repo_result

            repo_info = repo_result.unwrap()

            # Fetch additional data
            stats_result = client.get_repository_stats(
                owner=params['owner'],
                repo=params['repo']
            )

            languages = stats_result.unwrap().get('languages', {}) if stats_result.is_ok() else {}

            # Return formatted result
            return ok({
                'repository_info': transform_to_json_serializable(repo_info),
                'languages': languages
            })

    except Exception as e:
        from core.domain.errors import AnalysisError
        from core.utils.functional import err
        return err(AnalysisError(
            message=f"Repository summary failed: {str(e)}",
            context={'arguments': arguments}
        ))


def format_repository_summary_response(data: Dict[str, Any]) -> str:
    """Format repository summary response for display."""
    repo_info = data.get('repository_info', {})

    response = f"""# 📁 **Repository Summary**

## 📊 **Basic Information**
- **Name**: {repo_info.get('full_name', 'Unknown')}
- **Description**: {repo_info.get('description') or 'No description'}
- **Language**: {repo_info.get('primary_language', 'Unknown')}
- **Created**: {repo_info.get('created_at', 'Unknown')}
- **Last Updated**: {repo_info.get('updated_at', 'Unknown')}

## 🌟 **Statistics**
- **Stars**: {repo_info.get('stargazers_count', 0):,}
- **Forks**: {repo_info.get('forks_count', 0):,}
- **Watchers**: {repo_info.get('watchers_count', 0):,}
- **Open Issues**: {repo_info.get('open_issues_count', 0):,}

## 📏 **Size & Activity**
- **Size**: {repo_info.get('size', 0):,} KB
- **Default Branch**: {repo_info.get('default_branch', 'main')}"""

    # Add license information if available
    license_info = repo_info.get('license')
    if license_info:
        response += f"""
- **License**: {license_info.get('name', 'Unknown')}"""

    # Add topics if available
    topics = repo_info.get('topics', [])
    if topics:
        response += f"""
- **Topics**: {', '.join(topics)}"""

    # Add language statistics if available
    if 'languages' in data:
        languages = data['languages']
        response += f"""

## 💻 **Languages**"""
        for lang, bytes_count in languages.items():
            percentage = (bytes_count / sum(languages.values())) * 100 if languages else 0
            response += f"""
- **{lang}**: {percentage:.1f}% ({bytes_count:,} bytes)"""

    # Add recent activity summary if available
    if 'activity_summary' in data:
        activity = data['activity_summary']
        response += f"""

## 📈 **Recent Activity**
- **Total Commits**: {activity.get('total_commits', 0):,}
- **Active Contributors**: {activity.get('active_contributors', 0)}
- **Latest Commit**: {activity.get('latest_commit_date', 'Unknown')}"""

    # Add repository health indicators if available
    if 'health_indicators' in data:
        health = data['health_indicators']
        response += f"""

## 🔧 **Repository Health**"""
        for indicator, value in health.items():
            if isinstance(value, (int, float)):
                response += f"""
- **{indicator.replace('_', ' ').title()}**: {value}"""
            else:
                response += f"""
- **{indicator.replace('_', ' ').title()}**: {value}"""

    return response


async def repository_summary(owner: str, repo: str) -> str:
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
        try:
            error_msg = format_user_friendly_message(error)
        except:
            error_msg = str(error)
        return f"❌ **Error**: {error_msg}"


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Get comprehensive summary of a GitHub repository",
        epilog="Example: python test_repository_summary.py microsoft/vscode"
    )

    parser.add_argument(
        "repository",
        help="GitHub repository in 'owner/repo' format (e.g., microsoft/vscode)"
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

    print(f"🚀 Testing repository_summary with {args.repository}")
    print("=" * 70)

    try:
        # Run the repository_summary function
        result = await repository_summary(owner, repo)
        print(result)
        return 0

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))