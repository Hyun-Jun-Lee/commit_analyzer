"""
Analysis pipelines for GitHub Commit Analyzer.
Orchestrates the complete analysis workflows using functional composition.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from core.utils.functional import (
    Result, ok, err, pipe, map_result, safe,
    pipeline, collect_results
)
from core.domain.types import (
    RepositoryInfo, CommitData, DiffData, AnalysisResult,
    VelocityMetrics, TimePatterns, ComplexityMetrics,
    WorkTypeDistribution, WorkStatusDistribution
)
from core.domain.errors import AnyError
from core.utils.data_transformation import (
    transform_to_json_serializable, format_analysis_summary
)
from core.analysis.work_type_inference import (
    analyze_commits_comprehensive,
    build_work_type_distribution,
    build_work_status_distribution
)
from core.analysis.metrics_calculation import (
    calculate_velocity_with_diffs,
    calculate_time_patterns,
    calculate_author_statistics,
    calculate_file_hotspots,
    calculate_code_quality_indicators,
    estimate_complexity_changes,
    calculate_repository_health
)
from infrastructure.github_client import (
    fetch_repository_analysis_data,
    fetch_commit_details,
    GitHubAPIClient
)


# ============================================================================
# Core Pipeline Functions
# ============================================================================

@safe
async def run_commit_analysis_pipeline(
    owner: str,
    repo: str,
    days: int = 7
) -> Dict[str, Any]:
    """Complete commit analysis pipeline."""
    
    # Step 1: Fetch data from GitHub
    fetch_result = fetch_repository_analysis_data(owner, repo, days)
    if not fetch_result:
        return fetch_result
    
    repo_info, commits, diffs = fetch_result.value
    
    if not commits:
        return ok({
            'repository': transform_to_json_serializable(repo_info),
            'analysis_period_days': days,
            'total_commits': 0,
            'message': 'No commits found in the specified time period'
        })
    
    # Step 2: Run comprehensive work analysis
    work_analysis_result = analyze_commits_comprehensive(commits, diffs)
    if not work_analysis_result:
        return work_analysis_result
    
    work_analysis = work_analysis_result.value
    
    # Step 3: Calculate metrics
    velocity_metrics = calculate_velocity_with_diffs(commits, diffs, days).value
    time_patterns = calculate_time_patterns(commits).value
    author_stats = calculate_author_statistics(commits, diffs).value
    hotspots = calculate_file_hotspots(diffs, commits).value
    complexity_metrics = estimate_complexity_changes(diffs)
    quality_indicators = calculate_code_quality_indicators(diffs, commits)
    
    # Step 4: Build distributions
    work_type_counts = work_analysis['work_patterns']['work_type_distribution']
    work_status_counts = work_analysis['work_patterns']['work_status_distribution']
    
    work_distribution = build_work_type_distribution(work_type_counts)
    status_distribution = build_work_status_distribution(work_status_counts)
    
    # Step 5: Calculate repository health
    health_metrics = calculate_repository_health(
        repo_info, velocity_metrics, author_stats,
        hotspots, quality_indicators
    )
    
    # Step 6: Build comprehensive result
    analysis_result = AnalysisResult(
        repository_info=repo_info,
        analysis_period_days=days,
        total_commits=len(commits),
        unique_authors=len(author_stats),
        work_distribution=work_distribution,
        status_distribution=status_distribution,
        velocity_metrics=velocity_metrics,
        complexity_metrics=complexity_metrics,
        time_patterns=time_patterns,
        author_stats=author_stats,
        hotspots=hotspots,
        top_changed_files=[str(h.path) for h in hotspots[:10]],
        summary=format_analysis_summary(
            # Create a minimal AnalysisResult for summary formatting
            AnalysisResult(
                repository_info=repo_info,
                analysis_period_days=days,
                total_commits=len(commits),
                unique_authors=len(author_stats),
                work_distribution=work_distribution,
                status_distribution=status_distribution,
                velocity_metrics=velocity_metrics,
                complexity_metrics=complexity_metrics,
                time_patterns=time_patterns,
                author_stats=author_stats,
                hotspots=hotspots,
                top_changed_files=[],
                summary=""
            )
        )
    )
    
    # Step 7: Format final response
    return ok({
        'repository': transform_to_json_serializable(repo_info),
        'analysis_period_days': days,
        'total_commits': len(commits),
        'unique_authors': len(author_stats),
        'work_distribution': transform_to_json_serializable(work_distribution),
        'status_distribution': transform_to_json_serializable(status_distribution),
        'velocity_metrics': transform_to_json_serializable(velocity_metrics),
        'time_patterns': transform_to_json_serializable(time_patterns),
        'author_stats': transform_to_json_serializable(author_stats[:10]),  # Top 10
        'hotspots': transform_to_json_serializable(hotspots[:10]),  # Top 10
        'complexity_metrics': transform_to_json_serializable(complexity_metrics),
        'quality_indicators': quality_indicators,
        'health_metrics': health_metrics,
        'work_analysis': work_analysis,
        'summary': analysis_result.summary
    })


@safe
async def run_commit_diff_pipeline(
    owner: str,
    repo: str,
    commit_sha: str
) -> Dict[str, Any]:
    """Analyze a specific commit and its diff."""
    
    # Fetch commit details
    fetch_result = fetch_commit_details(owner, repo, commit_sha)
    if not fetch_result:
        return fetch_result
    
    commit, diff = fetch_result.value
    
    # Analyze work types for this commit
    from ..analysis.work_type_inference import (
        infer_work_types_from_commit,
        infer_work_status_from_commit
    )
    
    work_types_result = infer_work_types_from_commit(commit, diff.file_changes)
    work_status_result = infer_work_status_from_commit(commit, diff.file_changes)
    
    work_types = work_types_result.value if work_types_result else set()
    work_status = work_status_result.value if work_status_result else None
    
    # Analyze file patterns
    from ..analysis.work_type_inference import analyze_file_change_patterns
    file_patterns = analyze_file_change_patterns(diff.file_changes)
    
    # Format response
    return ok({
        'commit': transform_to_json_serializable(commit),
        'diff': transform_to_json_serializable(diff),
        'work_types': [wt.value for wt in work_types],
        'work_status': work_status.value if work_status else None,
        'file_patterns': file_patterns,
        'analysis': {
            'total_files_changed': len(diff.file_changes),
            'total_lines_changed': diff.total_additions + diff.total_deletions,
            'net_lines_changed': diff.net_changes(),
            'is_large_change': (diff.total_additions + diff.total_deletions) > 100,
            'primary_language': file_patterns.get('languages', {})
        }
    })


@safe
async def run_repository_summary_pipeline(
    owner: str,
    repo: str
) -> Dict[str, Any]:
    """Generate comprehensive repository summary."""
    
    try:
        with GitHubAPIClient() as client:
            # Get repository info
            repo_info_result = client.get_repository_info(owner, repo)
            if not repo_info_result:
                return repo_info_result
            
            # Get repository stats
            stats_result = client.get_repository_stats(owner, repo)
            if not stats_result:
                return stats_result
            
            repo_info = repo_info_result.value
            stats = stats_result.value
            
            # Get recent activity (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            recent_commits_result = client.get_commits(
                owner, repo,
                since=start_date,
                per_page=50
            )
            
            recent_activity = {}
            if recent_commits_result:
                recent_commits = recent_commits_result.value
                recent_activity = {
                    'recent_commits_count': len(recent_commits),
                    'last_commit_date': recent_commits[0].authored_date.isoformat() if recent_commits else None,
                    'active_authors': len(set(c.author for c in recent_commits)),
                    'avg_commits_per_week': len(recent_commits) / 4.0  # 30 days ≈ 4 weeks
                }
            
            # Calculate repository health indicators
            health_indicators = {
                'activity_level': 'high' if recent_activity.get('recent_commits_count', 0) > 20 else 
                                'medium' if recent_activity.get('recent_commits_count', 0) > 5 else 'low',
                'community_size': 'large' if len(stats.get('contributors', [])) > 10 else
                                'medium' if len(stats.get('contributors', [])) > 3 else 'small',
                'popularity': 'high' if repo_info.stars_count > 100 else
                            'medium' if repo_info.stars_count > 10 else 'low'
            }
            
            return ok({
                'repository': transform_to_json_serializable(repo_info),
                'languages': stats.get('languages', {}),
                'contributors': stats.get('contributors', []),
                'recent_activity': recent_activity,
                'health_indicators': health_indicators,
                'summary': {
                    'description': repo_info.description or 'No description provided',
                    'primary_language': repo_info.primary_language,
                    'created_years_ago': (datetime.now() - repo_info.created_at).days / 365.25,
                    'last_updated_days_ago': (datetime.now() - repo_info.updated_at).days,
                    'community_engagement': {
                        'stars': repo_info.stars_count,
                        'forks': repo_info.forks_count,
                        'contributors': len(stats.get('contributors', []))
                    }
                }
            })
            
    except Exception as e:
        return err(e)


@safe
async def run_code_analysis_pipeline(
    owner: str,
    repo: str,
    days: int = 7,
    deep_analysis: bool = True
) -> Dict[str, Any]:
    """Deep code analysis pipeline with advanced metrics."""
    
    # First run the basic commit analysis
    basic_analysis_result = await run_commit_analysis_pipeline(owner, repo, days)
    if not basic_analysis_result:
        return basic_analysis_result
    
    basic_analysis = basic_analysis_result.value
    
    if not deep_analysis:
        return basic_analysis
    
    # Fetch additional data for deep analysis
    fetch_result = fetch_repository_analysis_data(owner, repo, days, max_commits=100)
    if not fetch_result:
        return fetch_result
    
    repo_info, commits, diffs = fetch_result.value
    
    if not commits:
        return basic_analysis
    
    # Enhanced analysis
    from ..analysis.work_type_inference import (
        analyze_temporal_work_patterns,
        identify_work_focus_areas
    )
    from ..analysis.metrics_calculation import (
        analyze_commit_rhythm,
        calculate_collaboration_metrics,
        analyze_hotspot_patterns
    )
    
    # Get work patterns from basic analysis
    work_patterns = basic_analysis.get('work_analysis', {}).get('work_patterns', {})
    
    # Advanced temporal analysis
    temporal_patterns = analyze_temporal_work_patterns(
        work_patterns.get('commit_work_types', {}),
        commits
    )
    
    # Focus area analysis
    focus_areas = identify_work_focus_areas(
        work_patterns.get('commit_contexts', {}),
        work_patterns.get('commit_work_types', {})
    )
    
    # Team collaboration metrics
    author_stats = basic_analysis.get('author_stats', [])
    # Convert back to AuthorStats objects for analysis
    from ..domain.types import AuthorStats
    author_stats_objects = []
    for stat in author_stats:
        if isinstance(stat, dict):
            author_stats_objects.append(AuthorStats(
                name=stat.get('name', ''),
                email=stat.get('email', ''),
                commits_count=stat.get('commits_count', 0),
                lines_added=stat.get('lines_added', 0),
                lines_deleted=stat.get('lines_deleted', 0),
                files_modified=stat.get('files_modified', 0),
                most_active_day=stat.get('most_active_day'),
                most_active_hour=stat.get('most_active_hour')
            ))
    
    collaboration_metrics = calculate_collaboration_metrics(author_stats_objects)
    
    # Commit rhythm analysis
    rhythm_analysis = analyze_commit_rhythm(commits)
    
    # Hotspot pattern analysis
    hotspots = basic_analysis.get('hotspots', [])
    # Convert back to FileHotspot objects
    from ..domain.types import FileHotspot
    from pathlib import Path
    hotspot_objects = []
    for hotspot in hotspots:
        if isinstance(hotspot, dict):
            hotspot_objects.append(FileHotspot(
                path=Path(hotspot.get('path', '')),
                change_frequency=hotspot.get('change_frequency', 0),
                total_lines_changed=hotspot.get('total_lines_changed', 0),
                last_modified=datetime.fromisoformat(hotspot.get('last_modified', '').replace('Z', '+00:00')) if hotspot.get('last_modified') else datetime.now(),
                authors_count=hotspot.get('authors_count', 0)
            ))
    
    hotspot_patterns = analyze_hotspot_patterns(hotspot_objects)
    
    # Combine with basic analysis
    enhanced_analysis = {
        **basic_analysis,
        'deep_analysis': {
            'temporal_patterns': temporal_patterns,
            'focus_areas': transform_to_json_serializable(focus_areas),
            'collaboration_metrics': collaboration_metrics,
            'rhythm_analysis': rhythm_analysis,
            'hotspot_patterns': hotspot_patterns
        },
        'insights': {
            'development_style': determine_development_style(
                rhythm_analysis, collaboration_metrics, work_patterns
            ),
            'team_dynamics': analyze_team_dynamics(collaboration_metrics, author_stats),
            'code_health_trends': analyze_code_health_trends(
                basic_analysis.get('quality_indicators', {}),
                hotspot_patterns
            ),
            'productivity_indicators': analyze_productivity_indicators(
                basic_analysis.get('velocity_metrics', {}),
                rhythm_analysis
            )
        }
    }
    
    return ok(enhanced_analysis)


# ============================================================================
# Analysis Helper Functions
# ============================================================================

def determine_development_style(
    rhythm_analysis: Dict[str, Any],
    collaboration_metrics: Dict[str, Any],
    work_patterns: Dict[str, Any]
) -> Dict[str, str]:
    """Determine development style characteristics."""
    
    style = {}
    
    # Commit frequency style
    avg_interval = rhythm_analysis.get('average_interval_hours', 24)
    if avg_interval < 4:
        style['commit_frequency'] = 'continuous'
    elif avg_interval < 24:
        style['commit_frequency'] = 'frequent'
    else:
        style['commit_frequency'] = 'batch'
    
    # Collaboration style
    total_authors = collaboration_metrics.get('total_authors', 1)
    if total_authors == 1:
        style['collaboration'] = 'solo'
    elif collaboration_metrics.get('collaboration_score', 0) > 0.7:
        style['collaboration'] = 'collaborative'
    else:
        style['collaboration'] = 'mixed'
    
    # Work distribution style
    distribution = collaboration_metrics.get('contribution_distribution', 'even')
    style['work_distribution'] = distribution
    
    return style


def analyze_team_dynamics(
    collaboration_metrics: Dict[str, Any],
    author_stats: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyze team collaboration dynamics."""
    
    dynamics = {}
    
    # Team size assessment
    total_authors = len(author_stats)
    dynamics['team_size'] = total_authors
    dynamics['team_size_category'] = (
        'solo' if total_authors == 1 else
        'small' if total_authors <= 3 else
        'medium' if total_authors <= 8 else
        'large'
    )
    
    # Contribution balance
    if total_authors > 1:
        contributions = [stat.get('commits_count', 0) for stat in author_stats]
        max_contrib = max(contributions)
        total_contrib = sum(contributions)
        
        dominance_ratio = max_contrib / total_contrib if total_contrib > 0 else 0
        
        if dominance_ratio > 0.8:
            dynamics['contribution_balance'] = 'dominated'
        elif dominance_ratio > 0.5:
            dynamics['contribution_balance'] = 'uneven'
        else:
            dynamics['contribution_balance'] = 'balanced'
    else:
        dynamics['contribution_balance'] = 'solo'
    
    # Bus factor
    dynamics['bus_factor'] = collaboration_metrics.get('bus_factor', 1)
    dynamics['risk_level'] = (
        'high' if dynamics['bus_factor'] <= 1 else
        'medium' if dynamics['bus_factor'] <= 2 else
        'low'
    )
    
    return dynamics


def analyze_code_health_trends(
    quality_indicators: Dict[str, Any],
    hotspot_patterns: Dict[str, Any]
) -> Dict[str, str]:
    """Analyze code health trends."""
    
    trends = {}
    
    # Test coverage trend
    trends['test_coverage'] = quality_indicators.get('test_coverage_trend', 'unknown')
    
    # Refactoring activity
    refactor_freq = quality_indicators.get('refactoring_frequency', 0)
    if refactor_freq > 0.2:
        trends['maintenance'] = 'active'
    elif refactor_freq > 0.1:
        trends['maintenance'] = 'moderate'
    else:
        trends['maintenance'] = 'minimal'
    
    # Hotspot risk
    critical_hotspots = hotspot_patterns.get('critical_hotspots', 0)
    if critical_hotspots == 0:
        trends['hotspot_risk'] = 'low'
    elif critical_hotspots <= 2:
        trends['hotspot_risk'] = 'medium'
    else:
        trends['hotspot_risk'] = 'high'
    
    # Change size trend
    large_change_freq = quality_indicators.get('large_change_frequency', 0)
    if large_change_freq < 0.1:
        trends['change_discipline'] = 'excellent'
    elif large_change_freq < 0.3:
        trends['change_discipline'] = 'good'
    else:
        trends['change_discipline'] = 'needs_improvement'
    
    return trends


def analyze_productivity_indicators(
    velocity_metrics: Dict[str, Any],
    rhythm_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Analyze productivity indicators."""
    
    indicators = {}
    
    # Velocity assessment
    commits_per_day = velocity_metrics.get('commits_per_day', 0)
    if commits_per_day > 3:
        indicators['velocity'] = 'high'
    elif commits_per_day > 1:
        indicators['velocity'] = 'medium'
    else:
        indicators['velocity'] = 'low'
    
    # Consistency assessment
    consistency_score = rhythm_analysis.get('consistency_score', 0)
    if consistency_score > 0.8:
        indicators['consistency'] = 'excellent'
    elif consistency_score > 0.6:
        indicators['consistency'] = 'good'
    else:
        indicators['consistency'] = 'variable'
    
    # Work-life balance indicators
    working_days = rhythm_analysis.get('working_days_active', 0)
    if working_days > 0:
        avg_commits_per_working_day = commits_per_day * 7 / 5  # Convert to working days
        if avg_commits_per_working_day < 1:
            indicators['work_intensity'] = 'sustainable'
        elif avg_commits_per_working_day < 3:
            indicators['work_intensity'] = 'moderate'
        else:
            indicators['work_intensity'] = 'intense'
    
    # Change size efficiency
    avg_change_size = velocity_metrics.get('average_commit_size', 0)
    if 20 <= avg_change_size <= 100:
        indicators['change_size_efficiency'] = 'optimal'
    elif avg_change_size < 20:
        indicators['change_size_efficiency'] = 'fragmented'
    else:
        indicators['change_size_efficiency'] = 'large_batches'
    
    return indicators