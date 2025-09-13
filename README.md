# GitHub Commit Analyzer MCP Server

A Model Context Protocol (MCP) server that analyzes GitHub repository commits to understand development work patterns. Built with functional programming principles, it provides insights into team productivity and project activity based on actual code changes rather than commit messages.

## 🎯 Key Features

### **Smart Commit Analysis**
- Analyzes commits from the **latest commit date** backwards (not from current time)
- Perfect for both active and dormant repositories
- Configurable time range (1-30 days)
- Handles repositories with irregular commit patterns

### **Code-Based Work Detection**
- Infers work types from actual code changes, not unreliable commit messages
- Detects: feature development, bug fixes, testing, refactoring, documentation
- Identifies code contexts: API, UI, database, infrastructure, configuration

### **Comprehensive Metrics**
- **Velocity Metrics**: Commits per day, lines changed, average commit size
- **Time Patterns**: Most active hours and days
- **Author Statistics**: Individual contributor metrics
- **Work Distribution**: Breakdown by work type and status

## 🏗️ Architecture

Built using functional programming principles with clean separation of concerns:

```
src/
├── core/
│   ├── domain/          # Immutable types, error types
│   ├── utils/           # Functional utilities, Result<T,E> monad
│   ├── business/        # Business rules engine
│   └── analysis/        # Work type inference, metrics
└── infrastructure/      
    ├── github_client.py # GitHub API client
    ├── fastmcp_server.py # FastMCP server implementation
    └── pipelines.py     # Analysis pipelines
```

### Design Principles
- **Functional Programming**: Pure functions, immutable data, no exceptions
- **Result<T,E> Pattern**: Explicit error handling without try/catch
- **Pipeline Composition**: Declarative data transformations
- **FastMCP Framework**: Simplified MCP server development

## 📦 Installation

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- GitHub Personal Access Token

### Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Hyun-Jun-Lee/commit_analyze.git
   cd commit_analyze
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Configure GitHub token**:
   ```bash
   # Create .env file
   echo "GITHUB_TOKEN=your_github_personal_access_token" > .env
   ```

   To create a GitHub token:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate new token with `repo` scope for private repositories
   - Public repositories work with minimal permissions

## 🚀 Usage

### Testing the Server

Before connecting to Claude Code, test the server functionality:

```bash
# Test repository commits (latest commit - N days)
uv run test_my_repo.py microsoft/vscode --days 7

# Test your own repository
uv run test_my_repo.py your-username/your-repo --days 3
```

### Connecting to Claude Code

Add to your Claude Code configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "github-commit-analyzer": {
      "command": "uv",
      "args": ["run", "python", "src/main.py"],
      "cwd": "/path/to/commit_analyze"
    }
  }
}
```

### Direct Server Execution

```bash
# Run the FastMCP server directly
uv run python src/main.py
```

## 🛠️ MCP Tools

### `analyze_commits`
Analyzes recent commits from the repository's latest commit date.

**Parameters**:
- `repository` (string): Repository in "owner/repo" format
- `days` (integer): Days to analyze from latest commit (1-30, default: 7)
- `max_commits` (integer): Maximum commits to analyze (default: 100)

**Example**:
```json
{
  "tool": "analyze_commits",
  "arguments": {
    "repository": "microsoft/vscode",
    "days": 7,
    "max_commits": 50
  }
}
```

### `get_commit_diff`
Gets detailed diff analysis for a specific commit.

**Parameters**:
- `repository` (string): Repository in "owner/repo" format
- `commit_sha` (string): Commit SHA (at least 7 characters)

### `repository_summary`
Provides comprehensive repository statistics and work patterns.

**Parameters**:
- `repository` (string): Repository in "owner/repo" format
- `days` (integer): Analysis period (1-30, default: 30)

### `analyze_code_changes`
Deep analysis of code changes with focus areas.

**Parameters**:
- `repository` (string): Repository in "owner/repo" format
- `commit_sha` (string): Specific commit or "HEAD" for latest
- `focus_areas` (array): Areas to focus on ["performance", "security", "quality"]

## 📊 Example Output

```json
{
  "success": true,
  "data": {
    "repository_info": {
      "full_name": "microsoft/vscode",
      "primary_language": "TypeScript",
      "stars": 176000
    },
    "analysis_period": "2025-09-06 to 2025-09-13 (7 days)",
    "total_commits": 45,
    "unique_authors": 12,
    "work_distribution": {
      "feature_development": 18,
      "bug_fix": 12,
      "testing": 8,
      "refactoring": 4,
      "documentation": 3
    },
    "velocity_metrics": {
      "commits_per_day": 6.4,
      "lines_per_day": 1240,
      "average_commit_size": 193
    },
    "top_contributors": [
      {
        "name": "Connor Peet",
        "commits": 8,
        "lines_changed": 2450
      }
    ],
    "insights": [
      "High development velocity with 6.4 commits/day",
      "Good test coverage with 18% of commits including tests",
      "Active refactoring indicates code health maintenance"
    ]
  }
}
```

## 🔧 Development

### Project Structure

```
commit_analyze/
├── src/
│   ├── core/           # Core business logic
│   │   ├── domain/     # Types and errors
│   │   ├── utils/      # Functional utilities
│   │   ├── business/   # Business rules
│   │   └── analysis/   # Analysis algorithms
│   ├── infrastructure/ # External integrations
│   └── main.py        # Entry point
├── test_my_repo.py    # Testing utility
├── pyproject.toml     # Project configuration
└── .env              # Environment variables
```

### Running Tests

```bash
# Test GitHub connection
uv run python -c "from src.infrastructure.github_client import test_github_connection; print(test_github_connection())"

# Test specific repository
uv run test_my_repo.py owner/repo --days 5
```

### Code Style

The project follows functional programming principles:
- **Immutable Data**: All data structures are immutable dataclasses
- **Pure Functions**: No side effects in core logic
- **Result Type**: Explicit error handling with Result<T,E>
- **Function Composition**: Pipeline-based data transformations
- **No Exceptions**: Errors as values, not exceptions

## 🎨 Key Design Decisions

1. **Latest Commit Reference**: Analysis period calculated from repository's latest commit, not current time
2. **Code Over Messages**: Work type inference based on file changes, not commit messages
3. **Functional Core**: Pure functional core with imperative shell
4. **FastMCP**: Simplified MCP server implementation with decorators
5. **Result Monad**: Explicit error handling without exceptions

## 🚦 Limitations

- **GitHub API Rate Limits**: 5000 requests/hour for authenticated users
- **Analysis Depth**: Limited to commit metadata and file changes (no full file content)
- **Time Range**: Maximum 30 days to prevent excessive API calls
- **Language Detection**: Based on file extensions and common patterns
---