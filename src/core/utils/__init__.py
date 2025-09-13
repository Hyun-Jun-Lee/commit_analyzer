"""
Utilities module for GitHub Commit Analyzer.
Contains functional programming utilities, validation, and data transformation functions.
"""

from .functional import *
from .validation import *
from .data_transformation import *

__all__ = [
    # Functional utilities
    'Result', 'Ok', 'Err', 'ok', 'err', 'is_ok', 'is_err',
    'map_result', 'flat_map', 'pipe', 'compose', 'safe',
    'Pipeline', 'pipeline', 'collect_results',
    
    # Validation
    'validate_repository_name', 'validate_commit_sha', 'validate_analysis_days',
    'validate_analyze_commits_params', 'validate_get_commit_diff_params',
    'validate_repository_summary_params', 'validate_analyze_code_changes_params',
    
    # Data transformation
    'transform_github_repo_response', 'transform_github_commit_response',
    'transform_github_diff_response', 'classify_file_type',
    'infer_work_type_from_files', 'calculate_velocity_metrics',
    'transform_to_json_serializable', 'format_analysis_summary'
]