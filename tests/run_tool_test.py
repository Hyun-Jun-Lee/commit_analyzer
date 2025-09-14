#!/usr/bin/env python3
"""
MCP 도구 통합 테스트 실행기
모든 MCP 도구를 하나의 스크립트에서 선택적으로 실행할 수 있는 통합 인터페이스

Usage:
  python run_tool_test.py analyze_commits <owner/repo> [--days N]
  python run_tool_test.py get_commit_diff <owner/repo> <commit_sha>
  python run_tool_test.py repository_summary <owner/repo>
  python run_tool_test.py analyze_code_changes <owner/repo> [--days N] [--deep-analysis]

Examples:
  python run_tool_test.py analyze_commits microsoft/vscode --days 7
  python run_tool_test.py get_commit_diff microsoft/vscode abc1234567
  python run_tool_test.py repository_summary microsoft/vscode
  python run_tool_test.py analyze_code_changes microsoft/vscode --days 5 --deep-analysis
"""

import os
import sys
import asyncio
import argparse
import time
from pathlib import Path
from typing import Dict, Any, List

# Add src to Python path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv

# Import individual test functions
sys.path.insert(0, str(Path(__file__).parent))
from test_analyze_commits import analyze_commits
from test_get_commit_diff import get_commit_diff
from test_repository_summary import repository_summary
from test_analyze_code_changes import analyze_code_changes


class ToolTester:
    """MCP 도구 테스터 클래스"""

    def __init__(self):
        self.tools = {
            'analyze_commits': {
                'func': analyze_commits,
                'description': 'Analyze recent commits to understand work patterns',
                'args': ['owner', 'repo', 'days?'],
                'example': 'microsoft/vscode --days 7'
            },
            'get_commit_diff': {
                'func': get_commit_diff,
                'description': 'Get detailed diff information for a specific commit',
                'args': ['owner', 'repo', 'commit_sha'],
                'example': 'microsoft/vscode abc1234567'
            },
            'repository_summary': {
                'func': repository_summary,
                'description': 'Get comprehensive repository summary and statistics',
                'args': ['owner', 'repo'],
                'example': 'microsoft/vscode'
            },
            'analyze_code_changes': {
                'func': analyze_code_changes,
                'description': 'Deep analysis of code changes and work patterns',
                'args': ['owner', 'repo', 'days?', 'deep_analysis?'],
                'example': 'microsoft/vscode --days 5 --deep-analysis'
            }
        }

    def list_tools(self):
        """사용 가능한 도구 목록 출력"""
        print("🛠️  **Available MCP Tools**")
        print("=" * 70)

        for tool_name, info in self.tools.items():
            print(f"\n📋 **{tool_name}**")
            print(f"   Description: {info['description']}")
            print(f"   Arguments: {' '.join(info['args'])}")
            print(f"   Example: python run_tool_test.py {tool_name} {info['example']}")

    async def run_tool(self, tool_name: str, args: argparse.Namespace) -> bool:
        """지정된 도구 실행"""
        if tool_name not in self.tools:
            print(f"❌ Unknown tool: {tool_name}")
            print("Available tools:", list(self.tools.keys()))
            return False

        tool_info = self.tools[tool_name]

        print(f"🚀 Running {tool_name}...")
        print("=" * 70)

        start_time = time.time()

        try:
            # Repository validation
            if '/' not in args.repository:
                print("❌ Repository must be in 'owner/repo' format")
                return False

            owner, repo = args.repository.split('/', 1)

            # Tool-specific execution
            if tool_name == 'analyze_commits':
                days = getattr(args, 'days', 7)
                result = await analyze_commits(owner, repo, days)

            elif tool_name == 'get_commit_diff':
                if not hasattr(args, 'commit_sha') or not args.commit_sha:
                    print("❌ commit_sha is required for get_commit_diff")
                    return False
                if len(args.commit_sha) < 7:
                    print("❌ Commit SHA must be at least 7 characters")
                    return False
                result = await get_commit_diff(owner, repo, args.commit_sha)

            elif tool_name == 'repository_summary':
                result = await repository_summary(owner, repo)

            elif tool_name == 'analyze_code_changes':
                days = getattr(args, 'days', 7)
                deep_analysis = getattr(args, 'deep_analysis', True)
                result = await analyze_code_changes(owner, repo, days, deep_analysis)

            else:
                print(f"❌ Tool {tool_name} not implemented")
                return False

            # Output result
            print(result)

            # Performance info
            elapsed = time.time() - start_time
            print(f"\n⏱️  Execution time: {elapsed:.2f} seconds")

            # Success indicator
            success = not result.startswith("❌")
            if success:
                print("✅ Tool execution completed successfully")
            else:
                print("❌ Tool execution failed")

            return success

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ Unexpected error: {str(e)}")
            print(f"⏱️  Execution time: {elapsed:.2f} seconds")
            import traceback
            traceback.print_exc()
            return False

    async def run_all_tools_demo(self, repository: str):
        """모든 도구를 데모 모드로 실행"""
        print(f"🎭 Running all tools demo with repository: {repository}")
        print("=" * 70)

        if '/' not in repository:
            print("❌ Repository must be in 'owner/repo' format")
            return

        owner, repo = repository.split('/', 1)
        results = {}

        # 1. Repository Summary (가장 기본적인 정보)
        print("\n1️⃣ **Repository Summary**")
        print("-" * 40)
        try:
            start_time = time.time()
            result = await repository_summary(owner, repo)
            elapsed = time.time() - start_time
            results['repository_summary'] = {
                'success': not result.startswith("❌"),
                'time': elapsed,
                'preview': result[:200] + "..." if len(result) > 200 else result
            }
            print(f"⏱️  {elapsed:.2f}s - {'✅ Success' if results['repository_summary']['success'] else '❌ Failed'}")
        except Exception as e:
            results['repository_summary'] = {'success': False, 'time': 0, 'error': str(e)}
            print(f"❌ Error: {e}")

        # 2. Analyze Commits (최근 3일)
        print("\n2️⃣ **Analyze Commits (3 days)**")
        print("-" * 40)
        try:
            start_time = time.time()
            result = await analyze_commits(owner, repo, 3)
            elapsed = time.time() - start_time
            results['analyze_commits'] = {
                'success': not result.startswith("❌"),
                'time': elapsed,
                'preview': result[:200] + "..." if len(result) > 200 else result
            }
            print(f"⏱️  {elapsed:.2f}s - {'✅ Success' if results['analyze_commits']['success'] else '❌ Failed'}")
        except Exception as e:
            results['analyze_commits'] = {'success': False, 'time': 0, 'error': str(e)}
            print(f"❌ Error: {e}")

        # 3. Code Changes Analysis (최근 5일, 간단 분석)
        print("\n3️⃣ **Analyze Code Changes (5 days, basic)**")
        print("-" * 40)
        try:
            start_time = time.time()
            result = await analyze_code_changes(owner, repo, 5, False)  # Basic analysis
            elapsed = time.time() - start_time
            results['analyze_code_changes'] = {
                'success': not result.startswith("❌"),
                'time': elapsed,
                'preview': result[:200] + "..." if len(result) > 200 else result
            }
            print(f"⏱️  {elapsed:.2f}s - {'✅ Success' if results['analyze_code_changes']['success'] else '❌ Failed'}")
        except Exception as e:
            results['analyze_code_changes'] = {'success': False, 'time': 0, 'error': str(e)}
            print(f"❌ Error: {e}")

        # Summary
        print("\n" + "=" * 70)
        print("📋 **Demo Results Summary**")
        total_time = sum(r.get('time', 0) for r in results.values())
        success_count = sum(1 for r in results.values() if r.get('success', False))

        print(f"✅ Successful tools: {success_count}/{len(results)}")
        print(f"⏱️  Total execution time: {total_time:.2f} seconds")

        for tool, result in results.items():
            status = "✅ Success" if result.get('success', False) else "❌ Failed"
            time_str = f"{result.get('time', 0):.2f}s"
            print(f"   {tool}: {status} ({time_str})")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP Tools Test Runner - Run individual MCP tools for testing",
        epilog="""
Examples:
  python run_tool_test.py list
  python run_tool_test.py analyze_commits microsoft/vscode --days 7
  python run_tool_test.py get_commit_diff microsoft/vscode abc1234567
  python run_tool_test.py repository_summary microsoft/vscode
  python run_tool_test.py analyze_code_changes microsoft/vscode --days 5 --deep-analysis
  python run_tool_test.py demo microsoft/vscode
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "command",
        choices=['list', 'analyze_commits', 'get_commit_diff', 'repository_summary', 'analyze_code_changes', 'demo'],
        help="Command to run (use 'list' to see all available tools)"
    )

    parser.add_argument(
        "repository",
        nargs='?',
        help="GitHub repository in 'owner/repo' format (required for tools, not for 'list')"
    )

    parser.add_argument(
        "commit_sha",
        nargs='?',
        help="Commit SHA for get_commit_diff (at least 7 characters)"
    )

    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (1-30, default: 7)"
    )

    parser.add_argument(
        "--deep-analysis",
        action="store_true",
        default=True,
        help="Enable deep code analysis (default: enabled)"
    )

    parser.add_argument(
        "--no-deep-analysis",
        action="store_false",
        dest="deep_analysis",
        help="Disable deep code analysis"
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

    tester = ToolTester()

    # Handle list command
    if args.command == 'list':
        tester.list_tools()
        return 0

    # Handle demo command
    if args.command == 'demo':
        if not args.repository:
            print("❌ Repository is required for demo mode")
            print("Usage: python run_tool_test.py demo <owner/repo>")
            return 1
        await tester.run_all_tools_demo(args.repository)
        return 0

    # Handle individual tool commands
    if not args.repository:
        print(f"❌ Repository is required for {args.command}")
        print(f"Usage: python run_tool_test.py {args.command} <owner/repo> [options]")
        return 1

    # Run the specified tool
    success = await tester.run_tool(args.command, args)
    return 0 if success else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))