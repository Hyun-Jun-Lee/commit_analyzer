"""
Analysis layer for GitHub Commit Analyzer.
Contains work type inference and metrics calculation logic.
"""

from .work_type_inference import (
    infer_work_types_from_commit,
    infer_work_status_from_commit,
    analyze_work_patterns_batch,
    analyze_commits_comprehensive,
    build_work_type_distribution,
    build_work_status_distribution
)

from .metrics_calculation import (
    calculate_commit_velocity,
    calculate_velocity_with_diffs,
    calculate_time_patterns,
    calculate_author_statistics,
    calculate_file_hotspots,
    calculate_code_quality_indicators,
    estimate_complexity_changes,
    calculate_repository_health,
    analyze_commit_rhythm,
    calculate_collaboration_metrics,
    analyze_hotspot_patterns
)

__all__ = [
    # Work type inference
    'infer_work_types_from_commit',
    'infer_work_status_from_commit',
    'analyze_work_patterns_batch',
    'analyze_commits_comprehensive',
    'build_work_type_distribution',
    'build_work_status_distribution',
    
    # Metrics calculation
    'calculate_commit_velocity',
    'calculate_velocity_with_diffs',
    'calculate_time_patterns',
    'calculate_author_statistics',
    'calculate_file_hotspots',
    'calculate_code_quality_indicators',
    'estimate_complexity_changes',
    'calculate_repository_health',
    'analyze_commit_rhythm',
    'calculate_collaboration_metrics',
    'analyze_hotspot_patterns'
]