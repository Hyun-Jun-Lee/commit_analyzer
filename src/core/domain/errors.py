"""
Error types for functional error handling.
All errors are immutable and support pattern matching.
"""

from dataclasses import dataclass, field
from typing import Union, Optional, Any, List
from datetime import timedelta


# ============================================================================
# Base Error Types
# ============================================================================

@dataclass(frozen=True)
class AnalysisError:
    """Base class for all analysis errors."""
    message: str = ""
    context: Optional[dict] = None
    
    def with_context(self, **context) -> 'AnalysisError':
        """Add context information to error."""
        from dataclasses import replace
        new_context = {**(self.context or {}), **context}
        return replace(self, context=new_context)


# ============================================================================
# Validation Errors
# ============================================================================

@dataclass(frozen=True)
class ValidationError(AnalysisError):
    """Input validation failed."""
    field_name: Optional[str] = None
    invalid_value: Optional[Any] = None


@dataclass(frozen=True)
class InvalidRepositoryName(ValidationError):
    """Repository name format is invalid."""
    message: str = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'message', 
                          f"Invalid repository format. Expected 'owner/repo-name', got: {self.invalid_value}")


@dataclass(frozen=True)
class InvalidCommitSHA(ValidationError):
    """Commit SHA format is invalid."""
    message: str = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'message', 
                          f"Commit SHA must be 7-40 hex characters, got: {self.invalid_value}")


@dataclass(frozen=True)
class InvalidDateRange(ValidationError):
    """Date range is invalid."""
    message: str = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'message', 
                          f"Date range must be 1-30 days, got: {self.invalid_value}")


@dataclass(frozen=True)
class MissingRequiredField(ValidationError):
    """Required field is missing."""
    message: str = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'message', 
                          f"Required field '{self.field_name}' is missing")


# ============================================================================
# GitHub API Errors
# ============================================================================

@dataclass(frozen=True)
class GitHubAPIError(AnalysisError):
    """GitHub API request failed."""
    status_code: int = 0
    response_body: Optional[str] = None


@dataclass(frozen=True)
class RepositoryNotFound(GitHubAPIError):
    """Repository not found on GitHub."""
    repository_name: str = ""
    message: str = field(init=False)
    status_code: int = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'message', 
                          f"Repository '{self.repository_name}' not found. Check the name and permissions.")
        object.__setattr__(self, 'status_code', 404)


@dataclass(frozen=True)
class RateLimitExceeded(GitHubAPIError):
    """GitHub API rate limit exceeded."""
    retry_after: timedelta = field(default_factory=lambda: timedelta(seconds=3600))
    limit: int = 0
    remaining: int = 0
    message: str = field(init=False)
    status_code: int = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'message', 
                          f"GitHub API rate limit exceeded. {self.remaining}/{self.limit} requests remaining. "
                          f"Retry after {self.retry_after.total_seconds():.0f} seconds.")
        object.__setattr__(self, 'status_code', 429)


@dataclass(frozen=True)
class UnauthorizedAccess(GitHubAPIError):
    """GitHub API authentication failed."""
    message: str = field(init=False)
    status_code: int = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'message', 
                          "GitHub API authentication failed. Check your GITHUB_TOKEN.")
        object.__setattr__(self, 'status_code', 401)


@dataclass(frozen=True)
class ForbiddenAccess(GitHubAPIError):
    """Access to repository is forbidden."""
    repository_name: str = ""
    message: str = field(init=False)
    status_code: int = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'message', 
                          f"Access to repository '{self.repository_name}' is forbidden. "
                          "Check your permissions or repository visibility.")
        object.__setattr__(self, 'status_code', 403)


# ============================================================================
# Network Errors
# ============================================================================

@dataclass(frozen=True)
class NetworkError(AnalysisError):
    """Network communication failed."""
    original_error: Optional[Exception] = None


@dataclass(frozen=True)
class ConnectionTimeout(NetworkError):
    """Connection timed out."""
    timeout_seconds: float = 0.0
    message: str = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'message', 
                          f"Connection timed out after {self.timeout_seconds} seconds. "
                          "Check your network connection.")


@dataclass(frozen=True)
class ConnectionRefused(NetworkError):
    """Connection was refused."""
    host: str = ""
    port: Optional[int] = None
    message: str = field(init=False)
    
    def __post_init__(self):
        port_info = f":{self.port}" if self.port else ""
        object.__setattr__(self, 'message', 
                          f"Connection refused to {self.host}{port_info}. "
                          "Check if the service is running.")


@dataclass(frozen=True)
class DNSResolutionError(NetworkError):
    """DNS resolution failed."""
    hostname: str = ""
    message: str = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'message', 
                          f"Failed to resolve hostname '{self.hostname}'. "
                          "Check your network connection and DNS settings.")


# ============================================================================
# Parsing and Processing Errors
# ============================================================================

@dataclass(frozen=True)
class ParseError(AnalysisError):
    """Data parsing failed."""
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    expected_format: Optional[str] = None


@dataclass(frozen=True)
class JSONParseError(ParseError):
    """JSON parsing failed."""
    message: str = field(init=False)
    
    def __post_init__(self):
        location = f" at {self.file_path}:{self.line_number}" if self.file_path and self.line_number else ""
        object.__setattr__(self, 'message', 
                          f"Failed to parse JSON{location}. Check the data format.")


@dataclass(frozen=True)
class GitDiffParseError(ParseError):
    """Git diff parsing failed."""
    commit_sha: str = ""
    message: str = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'message', 
                          f"Failed to parse git diff for commit {self.commit_sha}. "
                          "The diff format may be unsupported.")


@dataclass(frozen=True)
class CodeAnalysisError(AnalysisError):
    """Code analysis processing failed."""
    analysis_type: str = ""
    file_path: Optional[str] = None


@dataclass(frozen=True)
class UnsupportedLanguage(CodeAnalysisError):
    """Programming language is not supported."""
    language: str = ""
    analysis_type: str = field(init=False)
    message: str = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'analysis_type', 'language_detection')
        object.__setattr__(self, 'message', 
                          f"Programming language '{self.language}' is not supported for analysis. "
                          "Falling back to basic analysis.")


@dataclass(frozen=True)
class ComplexityTimeout(CodeAnalysisError):
    """Code complexity analysis timed out."""
    timeout_seconds: float = 0.0
    analysis_type: str = field(init=False)
    message: str = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'analysis_type', 'complexity')
        object.__setattr__(self, 'message', 
                          f"Complexity analysis timed out after {self.timeout_seconds} seconds. "
                          "Using simplified metrics.")


# ============================================================================
# Configuration Errors
# ============================================================================

@dataclass(frozen=True)
class ConfigError(AnalysisError):
    """Configuration is invalid or missing."""
    config_key: Optional[str] = None


@dataclass(frozen=True)
class MissingEnvironmentVariable(ConfigError):
    """Required environment variable is missing."""
    variable_name: str = ""
    config_key: Optional[str] = field(init=False)
    message: str = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'config_key', self.variable_name)
        object.__setattr__(self, 'message', 
                          f"Required environment variable '{self.variable_name}' is not set. "
                          "Check your configuration.")


@dataclass(frozen=True)
class InvalidConfiguration(ConfigError):
    """Configuration value is invalid."""
    message: str = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'message', 
                          f"Configuration key '{self.config_key}' has invalid value. "
                          "Check your settings.")


# ============================================================================
# MCP Protocol Errors
# ============================================================================

@dataclass(frozen=True)
class MCPError(AnalysisError):
    """MCP protocol error."""
    error_code: Optional[str] = None


@dataclass(frozen=True)
class MCPHandshakeError(MCPError):
    """MCP handshake failed."""
    protocol_version: str = ""
    message: str = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'message', 
                          f"MCP handshake failed with protocol version {self.protocol_version}. "
                          "Check client compatibility.")


@dataclass(frozen=True)
class MCPToolNotFound(MCPError):
    """MCP tool not found."""
    tool_name: str = ""
    message: str = field(init=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'message', 
                          f"MCP tool '{self.tool_name}' not found. "
                          "Check tool registration.")


@dataclass(frozen=True)
class MCPInvalidParams(MCPError):
    """MCP tool parameters are invalid."""
    tool_name: str = ""
    param_errors: List[str] = field(default_factory=list)
    message: str = field(init=False)
    
    def __post_init__(self):
        errors_str = ", ".join(self.param_errors)
        object.__setattr__(self, 'message', 
                          f"Invalid parameters for tool '{self.tool_name}': {errors_str}")


# ============================================================================
# Union Type for All Errors (for Result<T, E> type)
# ============================================================================

AnyError = Union[
    # Validation errors
    ValidationError, InvalidRepositoryName, InvalidCommitSHA, 
    InvalidDateRange, MissingRequiredField,
    
    # GitHub API errors
    GitHubAPIError, RepositoryNotFound, RateLimitExceeded,
    UnauthorizedAccess, ForbiddenAccess,
    
    # Network errors  
    NetworkError, ConnectionTimeout, ConnectionRefused, DNSResolutionError,
    
    # Parsing errors
    ParseError, JSONParseError, GitDiffParseError,
    
    # Code analysis errors
    CodeAnalysisError, UnsupportedLanguage, ComplexityTimeout,
    
    # Configuration errors
    ConfigError, MissingEnvironmentVariable, InvalidConfiguration,
    
    # MCP errors
    MCPError, MCPHandshakeError, MCPToolNotFound, MCPInvalidParams,
    
    # Base error
    AnalysisError
]


# ============================================================================
# Error Utilities
# ============================================================================

def is_retryable_error(error: AnyError) -> bool:
    """Check if an error is retryable."""
    retryable_types = (
        NetworkError, ConnectionTimeout, RateLimitExceeded,
        ComplexityTimeout
    )
    return isinstance(error, retryable_types)


def is_user_error(error: AnyError) -> bool:
    """Check if an error is caused by user input."""
    user_error_types = (
        ValidationError, InvalidRepositoryName, InvalidCommitSHA,
        InvalidDateRange, MissingRequiredField, MCPInvalidParams
    )
    return isinstance(error, user_error_types)


def get_error_severity(error: AnyError) -> str:
    """Get error severity level."""
    if isinstance(error, (ValidationError, MCPInvalidParams)):
        return "low"
    elif isinstance(error, (NetworkError, ParseError)):
        return "medium"
    elif isinstance(error, (GitHubAPIError, ConfigError)):
        return "high"
    else:
        return "medium"


def format_user_friendly_message(error: AnyError) -> str:
    """Format error message for end users."""
    if isinstance(error, RepositoryNotFound):
        return f"Repository '{error.repository_name}' not found. Please check the repository name and your access permissions."
    elif isinstance(error, RateLimitExceeded):
        return f"GitHub API rate limit exceeded. Please wait {error.retry_after.total_seconds():.0f} seconds before trying again."
    elif isinstance(error, UnauthorizedAccess):
        return "GitHub authentication failed. Please check your GITHUB_TOKEN environment variable."
    elif isinstance(error, ValidationError):
        return f"Invalid input: {error.message}"
    elif isinstance(error, NetworkError):
        return "Network connection failed. Please check your internet connection and try again."
    else:
        return error.message