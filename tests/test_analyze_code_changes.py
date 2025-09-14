#!/usr/bin/env python3
"""
analyze_code_changes 도구 독립 실행 테스트
fastmcp_server.py의 analyze_code_changes 함수를 @app.tool() 데코레이터 없이 테스트

Usage: python test_analyze_code_changes.py <owner/repo> [--days N] [--deep-analysis]
Example: python test_analyze_code_changes.py microsoft/vscode --days 7 --deep-analysis
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
from core.utils.validation import validate_analyze_code_changes_params


async def handle_analyze_code_changes(arguments: Dict[str, Any]) -> Result[Dict[str, Any], AnyError]:
    """Handle analyze_code_changes tool call."""
    # Import here to avoid circular imports
    from infrastructure.pipelines import run_code_analysis_pipeline
    from core.utils.functional import Result

    # Validate parameters
    validation_result = validate_analyze_code_changes_params(arguments)
    if validation_result.is_err():
        return validation_result

    params = validation_result.unwrap()

    # Direct implementation without pipeline to avoid @safe decorator issues
    try:
        # Fetch data from GitHub using the existing function
        from infrastructure.github_client import fetch_repository_analysis_data
        from core.utils.functional import ok, err
        from core.utils.data_transformation import transform_to_json_serializable

        fetch_result = fetch_repository_analysis_data(
            owner=params['owner'],
            repo=params['repo'],
            days=params.get('days', 7)
        )

        if fetch_result.is_err():
            return fetch_result

        repo_info, commits, diffs = fetch_result.unwrap()

        if not commits:
            return ok({
                'repository': transform_to_json_serializable(repo_info),
                'analysis_period_days': params.get('days', 7),
                'deep_analysis': params.get('deep_analysis', True),
                'total_commits': 0,
                'unique_authors': 0,
                'message': 'No commits found in the specified time period'
            })

        # Basic analysis without complex pipelines
        unique_authors = len(set(commit.author for commit in commits if commit.author))

        # Calculate basic quality indicators
        total_files_changed = sum(len(diff.file_changes) for diff in diffs)
        total_additions = sum(diff.total_additions for diff in diffs)
        total_deletions = sum(diff.total_deletions for diff in diffs)

        # Find hotspot files (most frequently changed)
        file_change_counts = {}
        for diff in diffs:
            for file_change in diff.file_changes:
                path_str = str(file_change.path)
                file_change_counts[path_str] = file_change_counts.get(path_str, 0) + 1

        hotspots = [{'path': path, 'change_frequency': count}
                   for path, count in sorted(file_change_counts.items(), key=lambda x: x[1], reverse=True)]

        # Return comprehensive results
        result = {
            'repository': transform_to_json_serializable(repo_info),
            'analysis_period_days': params.get('days', 7),
            'deep_analysis': params.get('deep_analysis', True),
            'total_commits': len(commits),
            'unique_authors': unique_authors,
            'quality_indicators': {
                'total_files_changed': total_files_changed,
                'average_files_per_commit': total_files_changed / len(commits) if commits else 0,
                'code_churn_ratio': total_deletions / total_additions if total_additions > 0 else 0
            },
            'complexity_metrics': {
                'total_lines_changed': total_additions + total_deletions,
                'average_commit_size': (total_additions + total_deletions) / len(commits) if commits else 0
            },
            'hotspots': hotspots[:10],  # Top 10 hotspots
        }

        # Add deep analysis insights if enabled
        if params.get('deep_analysis', True):
            insights = []

            # Development patterns
            if unique_authors > 1:
                insights.append(f"Collaborative development with {unique_authors} active contributors")
            elif unique_authors == 1:
                insights.append("Single developer workflow - consistent code style expected")

            # File change patterns
            avg_files_per_commit = total_files_changed / len(commits) if commits else 0
            if avg_files_per_commit > 3:
                insights.append(f"Higher than average file changes per commit ({avg_files_per_commit:.1f}) - possible refactoring")
            elif avg_files_per_commit < 1.5:
                insights.append("Focused commits with few file changes - good practice")

            # Code volume trends
            if total_deletions > total_additions:
                insights.append("Code reduction trend - potential optimization or cleanup")
            elif total_additions > total_deletions * 2:
                insights.append("Significant code expansion - new features or functionality")

            # Commit size analysis
            avg_commit_size = (total_additions + total_deletions) / len(commits) if commits else 0
            if avg_commit_size > 500:
                insights.append(f"Large commits ({avg_commit_size:.0f} lines avg) - consider smaller increments")
            elif avg_commit_size < 50:
                insights.append("Small, focused commits - excellent development practice")

            result['insights'] = insights

            # Add recommendations
            recommendations = []

            # Hotspot analysis
            if len(hotspots) > 0:
                top_hotspot = hotspots[0]
                if top_hotspot['change_frequency'] >= 2:
                    recommendations.append(f"Monitor {top_hotspot['path']} - changed in {top_hotspot['change_frequency']} commits")

            # Commit size recommendations
            if avg_files_per_commit > 5:
                recommendations.append("Consider breaking large commits into smaller, focused changes")

            # Quality recommendations
            if total_files_changed > len(commits) * 4:
                recommendations.append("High file churn detected - ensure adequate testing coverage")

            result['recommendations'] = recommendations

        return ok(result)

    except Exception as e:
        from core.domain.errors import AnalysisError
        return err(AnalysisError(
            message=f"Code analysis failed: {str(e)}",
            context={'arguments': arguments}
        ))


def format_code_analysis_response(data: Dict[str, Any]) -> str:
    """Format code analysis response for display."""
    response = f"""# 🔬 **Code Changes Analysis**

## 📁 **Repository**: {data.get('repository', {}).get('full_name', 'Unknown')}
- **Analysis Period**: {data.get('analysis_period_days', 7)} days
- **Deep Analysis**: {'Enabled' if data.get('deep_analysis', False) else 'Disabled'}"""

    # Basic metrics
    if 'total_commits' in data:
        response += f"""

## 📊 **Basic Metrics**
- **Total Commits**: {data.get('total_commits', 0)}
- **Unique Authors**: {data.get('unique_authors', 0)}"""

    # Code quality indicators
    if 'quality_indicators' in data:
        quality = data['quality_indicators']
        response += f"""

## ✅ **Code Quality Indicators**"""
        for indicator, value in quality.items():
            if isinstance(value, (int, float)):
                response += f"""
- **{indicator.replace('_', ' ').title()}**: {value}"""
            elif isinstance(value, bool):
                response += f"""
- **{indicator.replace('_', ' ').title()}**: {'Yes' if value else 'No'}"""
            else:
                response += f"""
- **{indicator.replace('_', ' ').title()}**: {value}"""

    # Complexity metrics
    if 'complexity_metrics' in data:
        complexity = data['complexity_metrics']
        response += f"""

## 🧮 **Complexity Metrics**"""
        for metric, value in complexity.items():
            if isinstance(value, (int, float)):
                response += f"""
- **{metric.replace('_', ' ').title()}**: {value:.2f}"""
            else:
                response += f"""
- **{metric.replace('_', ' ').title()}**: {value}"""

    # File hotspots
    if 'hotspots' in data:
        hotspots = data['hotspots']
        if hotspots:
            response += f"""

## 🔥 **File Hotspots** (Top 10)"""
            for i, hotspot in enumerate(hotspots[:10], 1):
                filename = hotspot.get('path', 'Unknown')
                changes = hotspot.get('change_frequency', 0)
                response += f"""
{i}. **{filename}** - {changes} changes"""

    # Work patterns if available
    if 'work_patterns' in data:
        patterns = data['work_patterns']
        work_dist = patterns.get('work_type_distribution', {})

        if work_dist:
            response += f"""

## 🔨 **Work Distribution**"""
            for work_type, count in work_dist.items():
                response += f"""
- **{work_type.replace('_', ' ').title()}**: {count}"""

    # Advanced insights if deep analysis was performed
    if data.get('deep_analysis') and 'insights' in data:
        insights = data['insights']
        if insights:
            response += f"""

## 💡 **Deep Analysis Insights**"""
            for i, insight in enumerate(insights[:5], 1):  # Show top 5 insights
                response += f"""
{i}. {insight}"""

    # Performance recommendations
    if 'recommendations' in data:
        recommendations = data['recommendations']
        if recommendations:
            response += f"""

## 🚀 **Recommendations**"""
            for i, rec in enumerate(recommendations[:5], 1):
                response += f"""
{i}. {rec}"""

    return response


async def analyze_code_changes(owner: str, repo: str, days: int = 7, deep_analysis: bool = True) -> str:
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
        try:
            error_msg = format_user_friendly_message(error)
        except:
            error_msg = str(error)
        return f"❌ **Error**: {error_msg}"


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Perform deep analysis of GitHub repository code changes",
        epilog="Example: python test_analyze_code_changes.py microsoft/vscode --days 7 --deep-analysis"
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

    # Validate repository format
    if '/' not in args.repository:
        print("❌ Repository must be in 'owner/repo' format")
        return 1

    owner, repo = args.repository.split('/', 1)

    print(f"🚀 Testing analyze_code_changes with {args.repository}")
    print(f"📊 Parameters: days={args.days}, deep_analysis={getattr(args, 'deep_analysis', True)}")
    print("=" * 70)

    try:
        # Run the analyze_code_changes function
        result = await analyze_code_changes(
            owner,
            repo,
            args.days,
            getattr(args, 'deep_analysis', True)
        )
        print(result)
        return 0

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))