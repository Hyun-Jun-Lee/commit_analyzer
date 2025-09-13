"""
GitHub API client for the commit analyzer.
Functional wrapper around GitHub REST API with error handling.
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin
from dataclasses import asdict
from pathlib import Path

import httpx
from dotenv import load_dotenv

from core.utils.functional import Result, ok, err, safe, pipe, map_result
from core.domain.errors import (
    GitHubAPIError, RepositoryNotFound, RateLimitExceeded,
    UnauthorizedAccess, ForbiddenAccess, NetworkError,
    ConnectionTimeout, JSONParseError
)
from core.domain.types import (
    RepositoryInfo, CommitData, FileChange, DiffData
)
from core.utils.data_transformation import (
    transform_github_repo_response,
    transform_github_commit_response,
    transform_github_diff_response,
    transform_to_diff_data,
    parse_json_response,
    extract_error_message
)
from core.domain.constants import (
    GITHUB_API_RATE_LIMIT, GITHUB_API_TIMEOUT,
    MAX_COMMITS_PER_REQUEST, MAX_DIFF_SIZE_CHARACTERS
)


# ============================================================================
# GitHub API Client Configuration
# ============================================================================

@safe
def get_github_token() -> str:
    """Get GitHub API token from environment or .env file."""
    # Try to load .env file from project root
    env_path = Path(__file__).parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        raise ValueError(
            "GITHUB_TOKEN is required. Set it as environment variable or in .env file."
        )
    return token


@safe
def create_github_headers(token: str) -> Dict[str, str]:
    """Create standard GitHub API headers."""
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'commit-analyzer-mcp/1.0',
        'X-GitHub-Api-Version': '2022-11-28'
    }


# ============================================================================
# HTTP Client Wrapper
# ============================================================================

class GitHubHTTPClient:
    """HTTP client wrapper with error handling and rate limiting."""
    
    def __init__(self, token: str, base_url: str = "https://api.github.com"):
        self.token = token
        self.base_url = base_url
        self.headers = create_github_headers(token).value
        self.client = httpx.Client(
            timeout=GITHUB_API_TIMEOUT,
            follow_redirects=True
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
    
    @safe
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request to GitHub API."""
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
        
        try:
            response = self.client.get(url, headers=self.headers, params=params)
            return self._handle_response(response)
            
        except httpx.TimeoutException as e:
            raise ConnectionTimeout(timeout_seconds=GITHUB_API_TIMEOUT)
        except httpx.ConnectError as e:
            raise NetworkError(message="Failed to connect to GitHub API", original_error=e)
        except Exception as e:
            raise NetworkError(message=f"HTTP request failed: {e}", original_error=e)
    
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle HTTP response with proper error mapping."""
        # Check rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('retry-after', 3600))
            remaining = int(response.headers.get('x-ratelimit-remaining', 0))
            limit = int(response.headers.get('x-ratelimit-limit', GITHUB_API_RATE_LIMIT))
            
            raise RateLimitExceeded(
                retry_after=timedelta(seconds=retry_after),
                limit=limit,
                remaining=remaining
            )
        
        # Check authentication
        if response.status_code == 401:
            raise UnauthorizedAccess()
        
        # Check authorization
        if response.status_code == 403:
            # Could be rate limit or forbidden access
            if 'rate limit' in response.text.lower():
                retry_after = int(response.headers.get('x-ratelimit-reset', 3600))
                raise RateLimitExceeded(
                    retry_after=timedelta(seconds=retry_after),
                    limit=GITHUB_API_RATE_LIMIT,
                    remaining=0
                )
            else:
                # Parse repository name from error if available
                repo_name = "unknown"
                try:
                    error_data = response.json()
                    message = error_data.get('message', '')
                    if 'not found' in message.lower():
                        # Extract repo name from URL if possible
                        repo_name = response.url.path.split('/repos/')[-1].split('/')[0] if '/repos/' in str(response.url) else "unknown"
                except:
                    pass
                
                raise ForbiddenAccess(repository_name=repo_name)
        
        # Check not found
        if response.status_code == 404:
            # Parse repository name from URL
            repo_name = "unknown"
            try:
                if '/repos/' in str(response.url):
                    path_parts = response.url.path.split('/repos/')[-1].split('/')
                    if len(path_parts) >= 2:
                        repo_name = f"{path_parts[0]}/{path_parts[1]}"
            except:
                pass
            
            raise RepositoryNotFound(repository_name=repo_name)
        
        # Check other client/server errors
        if response.status_code >= 400:
            try:
                error_data = response.json()
                message = extract_error_message(error_data)
            except:
                message = f"HTTP {response.status_code}: {response.text}"
            
            raise GitHubAPIError(
                message=message,
                status_code=response.status_code,
                response_body=response.text[:1000]  # Limit error body size
            )
        
        # Parse JSON response
        try:
            return response.json()
        except json.JSONDecodeError as e:
            raise JSONParseError(
                message="Failed to parse GitHub API response as JSON",
                line_number=e.lineno if hasattr(e, 'lineno') else None
            )


# ============================================================================
# GitHub API Operations
# ============================================================================

class GitHubAPIClient:
    """High-level GitHub API client with functional error handling."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or get_github_token().value
        self.http_client = None
    
    def __enter__(self):
        self.http_client = GitHubHTTPClient(self.token)
        self.http_client.__enter__()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.http_client:
            self.http_client.__exit__(exc_type, exc_val, exc_tb)
    
    def get_repository_info(self, owner: str, repo: str) -> Result[RepositoryInfo, Any]:
        """Get repository basic information."""
        if not self.http_client:
            return err(ValueError("Client not initialized. Use as context manager."))
        
        endpoint = f"/repos/{owner}/{repo}"
        
        return pipe(
            self.http_client.get(endpoint),
            lambda result: map_result(transform_github_repo_response, result) if result else result
        )
    
    def get_commits(
        self,
        owner: str,
        repo: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        author: Optional[str] = None,
        per_page: int = 30,
        page: int = 1
    ) -> Result[List[CommitData], Any]:
        """Get repository commits with optional filtering."""
        if not self.http_client:
            return err(ValueError("Client not initialized. Use as context manager."))
        
        endpoint = f"/repos/{owner}/{repo}/commits"
        
        params = {
            'per_page': min(per_page, MAX_COMMITS_PER_REQUEST),
            'page': page
        }
        
        if since:
            params['since'] = since.isoformat()
        if until:
            params['until'] = until.isoformat()
        if author:
            params['author'] = author
        
        response_result = self.http_client.get(endpoint, params)
        
        if not response_result:
            return response_result
        
        # Transform each commit in the response
        commits_data = response_result.value
        if not isinstance(commits_data, list):
            return err(ValueError("Expected list of commits from API"))
        
        commits = []
        for commit_data in commits_data:
            commit_result = transform_github_commit_response(commit_data)
            if not commit_result:
                return commit_result
            commits.append(commit_result.value)
        
        return ok(commits)
    
    def get_commit_diff(self, owner: str, repo: str, commit_sha: str) -> Result[DiffData, Any]:
        """Get detailed diff information for a specific commit."""
        if not self.http_client:
            return err(ValueError("Client not initialized. Use as context manager."))
        
        endpoint = f"/repos/{owner}/{repo}/commits/{commit_sha}"
        
        response_result = self.http_client.get(endpoint)
        
        if not response_result:
            return response_result
        
        # Transform response to file changes
        file_changes_result = transform_github_diff_response(response_result.value)
        
        if not file_changes_result:
            return file_changes_result
        
        # Create DiffData
        diff_data = transform_to_diff_data(commit_sha, file_changes_result.value)
        return ok(diff_data)
    
    def get_commits_with_diffs(
        self,
        owner: str,
        repo: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        max_commits: int = 50
    ) -> Result[tuple[List[CommitData], List[DiffData]], Any]:
        """Get commits and their corresponding diff data."""
        if not self.http_client:
            return err(ValueError("Client not initialized. Use as context manager."))
        
        # First get commits
        commits_result = self.get_commits(
            owner, repo, since=since, until=until, 
            per_page=min(max_commits, MAX_COMMITS_PER_REQUEST)
        )
        
        if not commits_result:
            return commits_result
        
        commits = commits_result.value[:max_commits]  # Limit total commits
        diffs = []
        
        # Get diff for each commit
        for commit in commits:
            diff_result = self.get_commit_diff(owner, repo, commit.sha)
            
            if diff_result:
                diffs.append(diff_result.value)
            # Continue even if some diffs fail - partial data is better than no data
        
        return ok((commits, diffs))
    
    def get_repository_stats(self, owner: str, repo: str) -> Result[Dict[str, Any], Any]:
        """Get repository statistics and metadata."""
        if not self.http_client:
            return err(ValueError("Client not initialized. Use as context manager."))
        
        # Get basic repo info
        repo_result = self.get_repository_info(owner, repo)
        if not repo_result:
            return repo_result
        
        repo_info = repo_result.value
        
        # Get additional stats
        stats = {
            'repository': asdict(repo_info),
            'languages': {},
            'contributors': []
        }
        
        # Try to get language stats (non-critical)
        try:
            languages_result = self.http_client.get(f"/repos/{owner}/{repo}/languages")
            if languages_result:
                stats['languages'] = languages_result.value
        except Exception:
            pass  # Language stats are optional
        
        # Try to get contributor stats (non-critical)
        try:
            contributors_result = self.http_client.get(f"/repos/{owner}/{repo}/contributors")
            if contributors_result:
                stats['contributors'] = contributors_result.value[:10]  # Limit to top 10
        except Exception:
            pass  # Contributor stats are optional
        
        return ok(stats)


# ============================================================================
# Convenience Functions
# ============================================================================

def fetch_repository_analysis_data(
    owner: str,
    repo: str,
    days: int = 7,
    max_commits: int = 100
) -> Result[tuple[RepositoryInfo, List[CommitData], List[DiffData]], Any]:
    """Fetch all data needed for repository analysis."""
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    try:
        with GitHubAPIClient() as client:
            # Get repository info
            repo_info_result = client.get_repository_info(owner, repo)
            if not repo_info_result:
                return repo_info_result
            
            # Get commits with diffs
            commits_diffs_result = client.get_commits_with_diffs(
                owner, repo,
                since=start_date,
                until=end_date,
                max_commits=max_commits
            )
            if not commits_diffs_result:
                return commits_diffs_result
            
            commits, diffs = commits_diffs_result.value
            
            return ok((repo_info_result.value, commits, diffs))
            
    except Exception as e:
        return err(e)


def fetch_commit_details(owner: str, repo: str, commit_sha: str) -> Result[tuple[CommitData, DiffData], Any]:
    """Fetch detailed information for a specific commit."""
    
    try:
        with GitHubAPIClient() as client:
            # Get commit diff (includes commit info)
            diff_result = client.get_commit_diff(owner, repo, commit_sha)
            if not diff_result:
                return diff_result
            
            # Get commit details
            commits_result = client.get_commits(owner, repo, per_page=1)
            if not commits_result:
                return commits_result
            
            # Find the specific commit
            target_commit = None
            for commit in commits_result.value:
                if commit.sha == commit_sha:
                    target_commit = commit
                    break
            
            if not target_commit:
                return err(ValueError(f"Commit {commit_sha} not found"))
            
            return ok((target_commit, diff_result.value))
            
    except Exception as e:
        return err(e)


def test_github_connection() -> Result[dict, Any]:
    """Test GitHub API connection and authentication."""
    
    try:
        with GitHubAPIClient() as client:
            # Try to get authenticated user info
            user_result = client.http_client.get("/user")
            if user_result.is_ok():
                user_data = user_result.unwrap()
                
                # Get rate limit info
                rate_limit_result = client.http_client.get("/rate_limit")
                rate_limit_data = None
                if rate_limit_result.is_ok():
                    rate_limit_data = rate_limit_result.unwrap()
                
                return ok({
                    **user_data,
                    'rate_limit': rate_limit_data.get('rate') if rate_limit_data else None
                })
            else:
                return user_result
            
    except Exception as e:
        return err(e)