#!/usr/bin/env python3
"""
get_commit_diff 도구 독립 실행 테스트
fastmcp_server.py의 get_commit_diff 함수를 @app.tool() 데코레이터 없이 테스트

Usage: python test_get_commit_diff.py <owner/repo> <commit_sha>
Example: python test_get_commit_diff.py microsoft/vscode abc1234567
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
from core.utils.validation import validate_get_commit_diff_params


async def handle_get_commit_diff(arguments: Dict[str, Any]) -> Result[Dict[str, Any], AnyError]:
    """Handle get_commit_diff tool call."""
    import os
    import requests
    from datetime import datetime
    from core.utils.functional import Result, ok, err

    # Validate parameters
    validation_result = validate_get_commit_diff_params(arguments)
    if validation_result.is_err():
        return validation_result

    params = validation_result.unwrap()

    # Direct GitHub API calls to avoid circular dependencies
    try:
        token = os.getenv('GITHUB_TOKEN')
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.github.v3+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }

        # Get commit details
        commit_url = f"https://api.github.com/repos/{params['owner']}/{params['repo']}/commits/{params['commit_sha']}"
        commit_response = requests.get(commit_url, headers=headers)

        if commit_response.status_code == 404:
            from core.domain.errors import GitHubAPIError
            return err(GitHubAPIError(
                message=f"Commit {params['commit_sha']} not found",
                status_code=404
            ))

        if commit_response.status_code != 200:
            from core.domain.errors import GitHubAPIError
            return err(GitHubAPIError(
                message=f"GitHub API error: {commit_response.status_code}",
                status_code=commit_response.status_code
            ))

        commit_data = commit_response.json()

        # Extract basic commit info
        file_changes = []
        for file_info in commit_data.get('files', []):
            file_changes.append({
                'filename': file_info.get('filename', ''),
                'additions': file_info.get('additions', 0),
                'deletions': file_info.get('deletions', 0),
                'changes': file_info.get('changes', 0),
                'status': file_info.get('status', 'modified'),
                'patch': file_info.get('patch', '')[:500]  # Limit patch size
            })

        # Extract commit metadata
        commit_info = {
            'sha': commit_data.get('sha', ''),
            'message': commit_data.get('commit', {}).get('message', ''),
            'author': commit_data.get('commit', {}).get('author', {}).get('name', ''),
            'author_email': commit_data.get('commit', {}).get('author', {}).get('email', ''),
            'date': commit_data.get('commit', {}).get('author', {}).get('date', ''),
            'url': commit_data.get('html_url', '')
        }

        return ok({
            'commit_data': commit_info,
            'file_changes': file_changes,
            'total_additions': sum(f.get('additions', 0) for f in file_changes),
            'total_deletions': sum(f.get('deletions', 0) for f in file_changes)
        })

    except Exception as e:
        from core.domain.errors import AnalysisError
        from core.utils.functional import err
        return err(AnalysisError(
            message=f"Commit diff analysis failed: {str(e)}",
            context={'arguments': arguments}
        ))


def format_commit_diff_response(data: Dict[str, Any]) -> str:
    """Format commit diff response for display."""
    commit_info = data.get('commit_data', {})
    file_changes = data.get('file_changes', [])

    response = f"""# 🔍 **Commit Diff Analysis**

## 📝 **Commit Information**
- **SHA**: {commit_info.get('sha', 'Unknown')[:12]}...
- **Author**: {commit_info.get('author', 'Unknown')}
- **Email**: {commit_info.get('author_email', 'Unknown')}
- **Date**: {commit_info.get('date', 'Unknown')}
- **Message**: {commit_info.get('message', 'No message')[:100]}...

## 📊 **Change Summary**
- **Files Changed**: {len(file_changes)}"""

    if file_changes:
        total_additions = data.get('total_additions', 0)
        total_deletions = data.get('total_deletions', 0)

        response += f"""
- **Total Additions**: +{total_additions}
- **Total Deletions**: -{total_deletions}
- **Net Change**: {total_additions - total_deletions:+d}

## 📁 **Changed Files**"""

        for i, file_change in enumerate(file_changes[:10], 1):  # Show top 10 files
            filename = file_change.get('filename', 'Unknown')
            additions = file_change.get('additions', 0)
            deletions = file_change.get('deletions', 0)
            status = file_change.get('status', 'modified')

            response += f"""
{i}. **{filename}** ({status})
   - Changes: +{additions} -{deletions}"""

            # Show patch preview for small changes
            patch = file_change.get('patch', '')
            if patch and len(patch) < 500:
                lines = patch.split('\n')[:5]  # First 5 lines
                response += f"""
   - Preview:
```diff
{chr(10).join(lines)}
```"""

        if len(file_changes) > 10:
            response += f"\n\n... and {len(file_changes) - 10} more files"
    else:
        response += "\n- No file changes detected"

    return response


async def get_commit_diff(owner: str, repo: str, commit_sha: str) -> str:
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
        try:
            error_msg = format_user_friendly_message(error)
        except:
            error_msg = str(error)
        return f"❌ **Error**: {error_msg}"


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Get detailed diff information for a specific GitHub commit",
        epilog="Example: python test_get_commit_diff.py microsoft/vscode abc1234567"
    )

    parser.add_argument(
        "repository",
        help="GitHub repository in 'owner/repo' format (e.g., microsoft/vscode)"
    )

    parser.add_argument(
        "commit_sha",
        help="Commit SHA (at least 7 characters)"
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

    # Validate commit SHA length
    if len(args.commit_sha) < 7:
        print("❌ Commit SHA must be at least 7 characters")
        return 1

    owner, repo = args.repository.split('/', 1)

    print(f"🚀 Testing get_commit_diff with {args.repository} commit {args.commit_sha}")
    print("=" * 70)

    try:
        # Run the get_commit_diff function
        result = await get_commit_diff(owner, repo, args.commit_sha)
        print(result)
        return 0

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))