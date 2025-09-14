#!/usr/bin/env python3
"""
FastMCP server 도구들의 독립 실행 테스트
실제 MCP 서버의 analyze_commits 등 함수들을 직접 테스트

Usage: python test_fastmcp_server.py <owner/repo> [--days N]
Example: python test_fastmcp_server.py microsoft/vscode --days 7
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv


async def test_analyze_commits(owner: str, repo: str, days: int = 7):
    """Test the analyze_commits MCP handler function."""
    # Import here to avoid module issues
    from infrastructure.fastmcp_server import handle_analyze_commits, format_commit_analysis_response

    print(f"🚀 Testing analyze_commits MCP handler...")
    print(f"📊 Repository: {owner}/{repo}")
    print(f"📅 Days: {days}")
    print("=" * 70)

    try:
        # Run the MCP handler function
        arguments = {"owner": owner, "repo": repo, "days": days}
        result = await handle_analyze_commits(arguments)

        print(f"🔍 Debug: result type = {type(result)}, value = {type(result).__name__}")

        if hasattr(result, 'is_ok') and result.is_ok():
            data = result.unwrap()
            formatted_result = format_commit_analysis_response(data)

            print("✅ analyze_commits handler completed successfully!")
            print(f"\n📊 Raw data keys: {list(data.keys())}")
            print("\n📋 Formatted Response Preview (first 1000 chars):")
            print(formatted_result[:1000] + ("..." if len(formatted_result) > 1000 else ""))

            # Check if JSON data is included
            if '"commits":' in formatted_result and '"diffs":' in formatted_result:
                print("\n✅ Full JSON data is included for Claude Code analysis")
            else:
                print("\n❌ Warning: Full JSON data may be missing")

            return True
        elif isinstance(result, dict):
            # Handle direct dict return
            data = result
            formatted_result = format_commit_analysis_response(data)

            print("✅ analyze_commits handler completed successfully (direct dict)!")
            print(f"\n📊 Raw data keys: {list(data.keys())}")
            print("\n📋 Formatted Response Preview (first 1000 chars):")
            print(formatted_result[:1000] + ("..." if len(formatted_result) > 1000 else ""))

            # Check if JSON data is included
            if '"commits":' in formatted_result and '"diffs":' in formatted_result:
                print("\n✅ Full JSON data is included for Claude Code analysis")
            else:
                print("\n❌ Warning: Full JSON data may be missing")

            return True
        else:
            if hasattr(result, 'unwrap_err'):
                error = result.unwrap_err()
                print(f"❌ Handler returned error: {error}")
            else:
                print(f"❌ Handler returned unexpected type: {type(result)}")
            return False

    except Exception as e:
        print(f"❌ Error testing analyze_commits: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_commit_diff(owner: str, repo: str, commit_sha: str):
    """Test the get_commit_diff MCP handler function."""
    from infrastructure.fastmcp_server import handle_get_commit_diff, format_commit_diff_response

    print(f"\n🚀 Testing get_commit_diff MCP handler...")
    print(f"📊 Repository: {owner}/{repo}")
    print(f"📝 Commit SHA: {commit_sha}")
    print("=" * 70)

    try:
        # Run the MCP handler function
        arguments = {"owner": owner, "repo": repo, "commit_sha": commit_sha}
        result = await handle_get_commit_diff(arguments)

        print(f"🔍 Debug: result type = {type(result)}, value = {type(result).__name__}")

        if hasattr(result, 'is_ok') and result.is_ok():
            data = result.unwrap()
            formatted_result = format_commit_diff_response(data)

            print("✅ get_commit_diff handler completed successfully!")
            print(f"\n📊 Raw data keys: {list(data.keys())}")
            print("\n📋 Formatted Response Preview (first 1000 chars):")
            print(formatted_result[:1000] + ("..." if len(formatted_result) > 1000 else ""))

            # Check if JSON data is included
            if '"file_changes":' in formatted_result:
                print("\n✅ Full JSON data is included for Claude Code analysis")
            else:
                print("\n❌ Warning: Full JSON data may be missing")

            return True
        elif isinstance(result, dict):
            # Handle direct dict return
            data = result
            formatted_result = format_commit_diff_response(data)

            print("✅ get_commit_diff handler completed successfully (direct dict)!")
            print(f"\n📊 Raw data keys: {list(data.keys())}")
            print("\n📋 Formatted Response Preview (first 1000 chars):")
            print(formatted_result[:1000] + ("..." if len(formatted_result) > 1000 else ""))

            # Check if JSON data is included
            if '"file_changes":' in formatted_result:
                print("\n✅ Full JSON data is included for Claude Code analysis")
            else:
                print("\n❌ Warning: Full JSON data may be missing")

            return True
        else:
            if hasattr(result, 'unwrap_err'):
                error = result.unwrap_err()
                print(f"❌ Handler returned error: {error}")
            else:
                print(f"❌ Handler returned unexpected type: {type(result)}")
            return False

    except Exception as e:
        print(f"❌ Error testing get_commit_diff: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_analyze_code_changes(owner: str, repo: str, days: int = 7):
    """Test the analyze_code_changes MCP handler function."""
    from infrastructure.fastmcp_server import handle_analyze_code_changes, format_code_analysis_response

    print(f"\n🚀 Testing analyze_code_changes MCP handler...")
    print(f"📊 Repository: {owner}/{repo}")
    print(f"📅 Days: {days}")
    print("=" * 70)

    try:
        # Run the MCP handler function
        arguments = {"owner": owner, "repo": repo, "days": days, "deep_analysis": True}
        result = await handle_analyze_code_changes(arguments)

        print(f"🔍 Debug: result type = {type(result)}, value = {type(result).__name__}")

        if hasattr(result, 'is_ok') and result.is_ok():
            data = result.unwrap()
            formatted_result = format_code_analysis_response(data)

            print("✅ analyze_code_changes handler completed successfully!")
            print(f"\n📊 Raw data keys: {list(data.keys())}")
            print("\n📋 Formatted Response Preview (first 1000 chars):")
            print(formatted_result[:1000] + ("..." if len(formatted_result) > 1000 else ""))

            # Check if JSON data is included
            if '"commits":' in formatted_result and '"diffs":' in formatted_result:
                print("\n✅ Full JSON data is included for Claude Code analysis")
            else:
                print("\n❌ Warning: Full JSON data may be missing")

            return True
        elif isinstance(result, dict):
            # Handle direct dict return
            data = result
            formatted_result = format_code_analysis_response(data)

            print("✅ analyze_code_changes handler completed successfully (direct dict)!")
            print(f"\n📊 Raw data keys: {list(data.keys())}")
            print("\n📋 Formatted Response Preview (first 1000 chars):")
            print(formatted_result[:1000] + ("..." if len(formatted_result) > 1000 else ""))

            # Check if JSON data is included
            if '"commits":' in formatted_result and '"diffs":' in formatted_result:
                print("\n✅ Full JSON data is included for Claude Code analysis")
            else:
                print("\n❌ Warning: Full JSON data may be missing")

            return True
        else:
            if hasattr(result, 'unwrap_err'):
                error = result.unwrap_err()
                print(f"❌ Handler returned error: {error}")
            else:
                print(f"❌ Handler returned unexpected type: {type(result)}")
            return False

    except Exception as e:
        print(f"❌ Error testing analyze_code_changes: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test FastMCP server functions",
        epilog="Example: python test_fastmcp_server.py microsoft/vscode --days 3"
    )

    parser.add_argument(
        "repository",
        help="GitHub repository in 'owner/repo' format (e.g., microsoft/vscode)"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=3,
        help="Number of days to analyze (1-30, default: 3)"
    )

    parser.add_argument(
        "--commit-sha",
        type=str,
        help="Specific commit SHA to test get_commit_diff (optional)"
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

    print(f"🧪 Testing FastMCP server functions with {args.repository}")
    print("=" * 70)

    results = []

    # Test analyze_commits
    result1 = await test_analyze_commits(owner, repo, args.days)
    results.append(("analyze_commits", result1))

    # Test analyze_code_changes
    result2 = await test_analyze_code_changes(owner, repo, args.days)
    results.append(("analyze_code_changes", result2))

    # Test get_commit_diff if SHA provided or get first commit from analyze_commits
    if args.commit_sha:
        result3 = await test_get_commit_diff(owner, repo, args.commit_sha)
        results.append(("get_commit_diff", result3))
    else:
        print(f"\n⏭️  Skipping get_commit_diff test (no --commit-sha provided)")

    # Summary
    print(f"\n" + "=" * 70)
    print("🏁 Test Summary:")
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {test_name}")
        if success:
            passed += 1

    print(f"\n📊 Results: {passed}/{len(results)} tests passed")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))