"""
Validation functions for GitHub Commit Analyzer.
Pure functions that validate inputs and return Result types.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, List
from pathlib import Path

from .functional import Result, ok, err, validate_all, not_none
from ..domain.errors import (
    ValidationError, InvalidRepositoryName, InvalidCommitSHA, 
    InvalidDateRange, MissingRequiredField
)
from ..domain.constants import (
    MIN_ANALYSIS_DAYS, MAX_ANALYSIS_DAYS,
    MIN_COMMITS_PER_REQUEST, MAX_COMMITS_PER_REQUEST
)


# ============================================================================
# Basic Type Validators
# ============================================================================

def validate_non_empty_string(value: str, field_name: str) -> Result[str, ValidationError]:
    """Validate that string is not empty."""
    if not value or not value.strip():
        return err(MissingRequiredField(field_name=field_name))
    return ok(value.strip())


def validate_positive_integer(value: int, field_name: str, min_value: int = 1) -> Result[int, ValidationError]:
    """Validate that integer is positive and above minimum."""
    if not isinstance(value, int):
        return err(ValidationError(
            message=f"Field '{field_name}' must be an integer",
            field_name=field_name,
            invalid_value=value
        ))
    
    if value < min_value:
        return err(ValidationError(
            message=f"Field '{field_name}' must be >= {min_value}",
            field_name=field_name,
            invalid_value=value
        ))
    
    return ok(value)


def validate_string_length(value: str, field_name: str, max_length: int) -> Result[str, ValidationError]:
    """Validate string length."""
    if len(value) > max_length:
        return err(ValidationError(
            message=f"Field '{field_name}' must be <= {max_length} characters",
            field_name=field_name,
            invalid_value=value
        ))
    return ok(value)


# ============================================================================
# GitHub-Specific Validators
# ============================================================================

def validate_repository_name(repo_name: str) -> Result[str, InvalidRepositoryName]:
    """Validate GitHub repository name format (owner/repo)."""
    if not repo_name:
        return err(InvalidRepositoryName(invalid_value=repo_name))
    
    # GitHub repository pattern: owner/repo-name
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-_.])*[a-zA-Z0-9]/[a-zA-Z0-9]([a-zA-Z0-9\-_.])*[a-zA-Z0-9]$'
    
    if not re.match(pattern, repo_name):
        return err(InvalidRepositoryName(invalid_value=repo_name))
    
    parts = repo_name.split('/')
    if len(parts) != 2:
        return err(InvalidRepositoryName(invalid_value=repo_name))
    
    owner, repo = parts
    
    # Additional validations
    if len(owner) > 39 or len(repo) > 100:  # GitHub limits
        return err(InvalidRepositoryName(invalid_value=repo_name))
    
    return ok(repo_name)


def validate_commit_sha(sha: str) -> Result[str, InvalidCommitSHA]:
    """Validate Git commit SHA format."""
    if not sha:
        return err(InvalidCommitSHA(invalid_value=sha))
    
    # Git SHA: 7-40 hexadecimal characters
    if not (7 <= len(sha) <= 40):
        return err(InvalidCommitSHA(invalid_value=sha))
    
    if not re.match(r'^[a-fA-F0-9]+$', sha):
        return err(InvalidCommitSHA(invalid_value=sha))
    
    return ok(sha.lower())


def validate_github_token(token: str) -> Result[str, ValidationError]:
    """Validate GitHub personal access token format."""
    if not token:
        return err(ValidationError(
            message="GitHub token is required",
            field_name="github_token"
        ))
    
    # GitHub classic tokens start with 'ghp_', fine-grained with 'github_pat_'
    if not (token.startswith('ghp_') or token.startswith('github_pat_')):
        return err(ValidationError(
            message="Invalid GitHub token format",
            field_name="github_token",
            invalid_value="[REDACTED]"
        ))
    
    return ok(token)


# ============================================================================
# Date and Time Validators
# ============================================================================

def validate_analysis_days(days: int) -> Result[int, InvalidDateRange]:
    """Validate analysis period in days."""
    if not (MIN_ANALYSIS_DAYS <= days <= MAX_ANALYSIS_DAYS):
        return err(InvalidDateRange(invalid_value=days))
    return ok(days)


def validate_date_range(start_date: datetime, end_date: datetime) -> Result[tuple[datetime, datetime], ValidationError]:
    """Validate date range is logical."""
    if start_date >= end_date:
        return err(ValidationError(
            message="Start date must be before end date",
            field_name="date_range",
            invalid_value=f"{start_date} to {end_date}"
        ))
    
    # Check if range is too large
    duration = end_date - start_date
    if duration.days > MAX_ANALYSIS_DAYS:
        return err(ValidationError(
            message=f"Date range cannot exceed {MAX_ANALYSIS_DAYS} days",
            field_name="date_range",
            invalid_value=duration.days
        ))
    
    return ok((start_date, end_date))


def validate_iso_datetime(date_str: str) -> Result[datetime, ValidationError]:
    """Validate and parse ISO format datetime string."""
    try:
        # Try parsing with timezone info first
        try:
            return ok(datetime.fromisoformat(date_str.replace('Z', '+00:00')))
        except ValueError:
            # Fallback to simple format
            return ok(datetime.fromisoformat(date_str))
    except ValueError as e:
        return err(ValidationError(
            message=f"Invalid datetime format: {e}",
            field_name="datetime",
            invalid_value=date_str
        ))


# ============================================================================
# File and Path Validators
# ============================================================================

def validate_file_path(path_str: str) -> Result[Path, ValidationError]:
    """Validate file path and convert to Path object."""
    if not path_str:
        return err(ValidationError(
            message="File path cannot be empty",
            field_name="file_path"
        ))
    
    try:
        path = Path(path_str)
        return ok(path)
    except Exception as e:
        return err(ValidationError(
            message=f"Invalid file path: {e}",
            field_name="file_path",
            invalid_value=path_str
        ))


def validate_file_extension(path: Path, allowed_extensions: set[str]) -> Result[Path, ValidationError]:
    """Validate file has allowed extension."""
    if path.suffix.lower() not in allowed_extensions:
        return err(ValidationError(
            message=f"File extension must be one of: {allowed_extensions}",
            field_name="file_extension",
            invalid_value=path.suffix
        ))
    return ok(path)


# ============================================================================
# API Parameter Validators
# ============================================================================

def validate_commit_count(count: int) -> Result[int, ValidationError]:
    """Validate number of commits to fetch."""
    if not (MIN_COMMITS_PER_REQUEST <= count <= MAX_COMMITS_PER_REQUEST):
        return err(ValidationError(
            message=f"Commit count must be between {MIN_COMMITS_PER_REQUEST} and {MAX_COMMITS_PER_REQUEST}",
            field_name="commit_count",
            invalid_value=count
        ))
    return ok(count)


def validate_analysis_options(options: Dict[str, Any]) -> Result[Dict[str, Any], ValidationError]:
    """Validate analysis configuration options."""
    validated = {}
    
    # Validate deep_analysis flag
    if 'deep_analysis' in options:
        if not isinstance(options['deep_analysis'], bool):
            return err(ValidationError(
                message="deep_analysis must be boolean",
                field_name="deep_analysis",
                invalid_value=options['deep_analysis']
            ))
        validated['deep_analysis'] = options['deep_analysis']
    else:
        validated['deep_analysis'] = True  # Default
    
    # Validate include_merges flag
    if 'include_merges' in options:
        if not isinstance(options['include_merges'], bool):
            return err(ValidationError(
                message="include_merges must be boolean",
                field_name="include_merges",
                invalid_value=options['include_merges']
            ))
        validated['include_merges'] = options['include_merges']
    else:
        validated['include_merges'] = False  # Default
    
    # Validate author filter
    if 'author' in options:
        author_result = validate_non_empty_string(options['author'], 'author')
        if not author_result:
            return author_result
        validated['author'] = author_result.value
    
    return ok(validated)


# ============================================================================
# Complex Object Validators
# ============================================================================

def validate_mcp_params(params: Dict[str, Any], required_fields: List[str]) -> Result[Dict[str, Any], ValidationError]:
    """Validate MCP tool parameters."""
    # Check required fields
    for field in required_fields:
        if field not in params:
            return err(MissingRequiredField(field_name=field))
        
        if params[field] is None or (isinstance(params[field], str) and not params[field].strip()):
            return err(MissingRequiredField(field_name=field))
    
    return ok(params)


def validate_analyze_commits_params(params: Dict[str, Any]) -> Result[Dict[str, Any], ValidationError]:
    """Validate parameters for analyze_commits tool."""
    # Required fields validation
    required_result = validate_mcp_params(params, ['owner', 'repo'])
    if not required_result:
        return required_result
    
    validated = required_result.value.copy()
    
    # Validate owner
    owner_result = validate_non_empty_string(params['owner'], 'owner')
    if not owner_result:
        return owner_result
    validated['owner'] = owner_result.value
    
    # Validate repo
    repo_result = validate_non_empty_string(params['repo'], 'repo')
    if not repo_result:
        return repo_result
    validated['repo'] = repo_result.value
    
    # Validate repository name format
    repo_name = f"{validated['owner']}/{validated['repo']}"
    repo_name_result = validate_repository_name(repo_name)
    if not repo_name_result:
        return repo_name_result
    
    # Validate days (optional)
    if 'days' in params:
        days_result = validate_analysis_days(params['days'])
        if not days_result:
            return days_result
        validated['days'] = days_result.value
    else:
        validated['days'] = 7  # Default
    
    return ok(validated)


def validate_get_commit_diff_params(params: Dict[str, Any]) -> Result[Dict[str, Any], ValidationError]:
    """Validate parameters for get_commit_diff tool."""
    # Required fields validation
    required_result = validate_mcp_params(params, ['owner', 'repo', 'commit_sha'])
    if not required_result:
        return required_result
    
    validated = required_result.value.copy()
    
    # Validate owner and repo
    repo_name = f"{params['owner']}/{params['repo']}"
    repo_name_result = validate_repository_name(repo_name)
    if not repo_name_result:
        return repo_name_result
    
    validated['owner'] = params['owner']
    validated['repo'] = params['repo']
    
    # Validate commit SHA
    sha_result = validate_commit_sha(params['commit_sha'])
    if not sha_result:
        return sha_result
    validated['commit_sha'] = sha_result.value
    
    return ok(validated)


def validate_repository_summary_params(params: Dict[str, Any]) -> Result[Dict[str, Any], ValidationError]:
    """Validate parameters for repository_summary tool."""
    # Required fields validation
    required_result = validate_mcp_params(params, ['owner', 'repo'])
    if not required_result:
        return required_result
    
    validated = required_result.value.copy()
    
    # Validate repository name format
    repo_name = f"{params['owner']}/{params['repo']}"
    repo_name_result = validate_repository_name(repo_name)
    if not repo_name_result:
        return repo_name_result
    
    validated['owner'] = params['owner']
    validated['repo'] = params['repo']
    
    return ok(validated)


def validate_analyze_code_changes_params(params: Dict[str, Any]) -> Result[Dict[str, Any], ValidationError]:
    """Validate parameters for analyze_code_changes tool."""
    # Start with analyze_commits validation
    base_result = validate_analyze_commits_params(params)
    if not base_result:
        return base_result
    
    validated = base_result.value.copy()
    
    # Validate deep_analysis flag (optional)
    if 'deep_analysis' in params:
        if not isinstance(params['deep_analysis'], bool):
            return err(ValidationError(
                message="deep_analysis must be boolean",
                field_name="deep_analysis",
                invalid_value=params['deep_analysis']
            ))
        validated['deep_analysis'] = params['deep_analysis']
    else:
        validated['deep_analysis'] = True  # Default
    
    return ok(validated)


# ============================================================================
# Validation Pipeline Builders
# ============================================================================

def build_string_validator(field_name: str, max_length: int = None, required: bool = True) -> callable:
    """Build a string validator with specified constraints."""
    def validator(value: str) -> Result[str, ValidationError]:
        if required:
            result = validate_non_empty_string(value, field_name)
            if not result:
                return result
            value = result.value
        
        if max_length and len(value) > max_length:
            return err(ValidationError(
                message=f"Field '{field_name}' must be <= {max_length} characters",
                field_name=field_name,
                invalid_value=value
            ))
        
        return ok(value)
    
    return validator


def build_combined_validator(*validators) -> callable:
    """Build a validator that runs multiple validators in sequence."""
    def combined(value):
        for validator in validators:
            result = validator(value)
            if not result:
                return result
            value = result.value
        return ok(value)
    
    return combined


# ============================================================================
# Validation Result Helpers
# ============================================================================

def collect_validation_errors(results: List[Result]) -> Result[List, List]:
    """Collect validation results, gathering all errors."""
    values = []
    errors = []
    
    for result in results:
        if result:  # is_ok
            values.append(result.value)
        else:  # is_err
            errors.append(result.error)
    
    if errors:
        return err(errors)
    return ok(values)


def first_validation_error(results: List[Result]) -> Result:
    """Return first successful validation or first error."""
    for result in results:
        if result:  # is_ok
            return result
    
    # Return first error if all failed
    return results[0] if results else err(ValidationError("No validations provided"))