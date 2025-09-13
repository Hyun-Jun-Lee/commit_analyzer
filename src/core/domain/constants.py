"""
Constants for the GitHub Commit Analyzer.
"""

from typing import Set, Dict, List

# ============================================================================
# Analysis Configuration
# ============================================================================

# Default analysis parameters
DEFAULT_ANALYSIS_DAYS = 7
MIN_ANALYSIS_DAYS = 1
MAX_ANALYSIS_DAYS = 30
MAX_COMMITS_PER_REQUEST = 100
MIN_COMMITS_PER_REQUEST = 10

# GitHub API limits
GITHUB_API_RATE_LIMIT = 5000  # requests per hour
GITHUB_API_TIMEOUT = 30  # seconds

# Diff size limits
MAX_DIFF_SIZE_CHARACTERS = 5000
MAX_FILE_SIZE_BYTES = 1024 * 1024  # 1MB

# ============================================================================
# File Classification
# ============================================================================

# Binary file extensions (skip content analysis)
BINARY_FILE_EXTENSIONS: Set[str] = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.ico',
    '.pdf', '.zip', '.rar', '.tar', '.gz', '.7z',
    '.exe', '.dll', '.so', '.dylib', '.bin',
    '.mp3', '.mp4', '.avi', '.mov', '.wav',
    '.ttf', '.otf', '.woff', '.woff2', '.eot'
}

# Documentation file extensions
DOCUMENTATION_EXTENSIONS: Set[str] = {
    '.md', '.rst', '.txt', '.adoc', '.org'
}

# Configuration file extensions
CONFIG_FILE_EXTENSIONS: Set[str] = {
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.xml', '.properties', '.env'
}

# Test file patterns
TEST_FILE_PATTERNS: Set[str] = {
    '.test.', '.spec.', '_test.', '_spec.', 'test_', 'spec_'
}

# Test directory patterns
TEST_DIRECTORY_PATTERNS: Set[str] = {
    'test', 'tests', '__tests__', 'spec', 'specs', '__spec__'
}

# ============================================================================
# Programming Language Detection
# ============================================================================

# Language file extensions mapping
LANGUAGE_EXTENSIONS: Dict[str, str] = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.ts': 'TypeScript',
    '.jsx': 'JavaScript',
    '.tsx': 'TypeScript',
    '.java': 'Java',
    '.kt': 'Kotlin',
    '.go': 'Go',
    '.rs': 'Rust',
    '.cpp': 'C++',
    '.cc': 'C++',
    '.cxx': 'C++',
    '.c': 'C',
    '.h': 'C/C++',
    '.hpp': 'C++',
    '.cs': 'C#',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.swift': 'Swift',
    '.scala': 'Scala',
    '.clj': 'Clojure',
    '.hs': 'Haskell',
    '.elm': 'Elm',
    '.dart': 'Dart',
    '.r': 'R',
    '.m': 'Objective-C',
    '.mm': 'Objective-C++',
    '.sql': 'SQL',
    '.sh': 'Shell',
    '.bash': 'Bash',
    '.zsh': 'Zsh',
    '.fish': 'Fish',
    '.ps1': 'PowerShell',
    '.lua': 'Lua',
    '.pl': 'Perl',
    '.vim': 'VimScript'
}

# Languages with high complexity analysis support
SUPPORTED_COMPLEXITY_LANGUAGES: Set[str] = {
    'Python', 'JavaScript', 'TypeScript', 'Java', 'Go', 'Rust', 'C++', 'C#'
}

# ============================================================================
# Code Pattern Detection
# ============================================================================

# API development patterns
API_PATTERNS: List[str] = [
    '@Get', '@Post', '@Put', '@Delete', '@Patch',
    'app.get', 'app.post', 'app.put', 'app.delete', 'app.patch',
    'router.', 'endpoint', 'api/', 'rest/', 'graphql',
    'Route', 'Controller', 'Handler'
]

# Database patterns
DATABASE_PATTERNS: List[str] = [
    'CREATE TABLE', 'ALTER TABLE', 'DROP TABLE',
    'SELECT', 'INSERT', 'UPDATE', 'DELETE',
    'migration', 'schema', 'model', 'entity',
    'Database', 'Repository', 'Query', 'ORM'
]

# UI development patterns
UI_PATTERNS: List[str] = [
    'useState', 'useEffect', 'useCallback', 'useMemo',
    'render', 'component', 'Component',
    '<div', '<span', '<button', '<input',
    'className', 'styled', 'css', 'scss',
    'View', 'Widget', 'Fragment'
]

# Performance optimization patterns
PERFORMANCE_PATTERNS: List[str] = [
    'optimize', 'cache', 'lazy', 'async', 'await',
    'Promise', 'performance', 'benchmark',
    'memoiz', 'throttle', 'debounce'
]

# Security patterns
SECURITY_PATTERNS: List[str] = [
    'auth', 'login', 'password', 'token', 'jwt',
    'encrypt', 'decrypt', 'hash', 'security',
    'permission', 'access', 'role', 'csrf',
    'sanitize', 'validate', 'escape'
]

# ============================================================================
# Commit Message Patterns
# ============================================================================

# Work type indicators in commit messages (low priority due to unreliable commit messages)
COMMIT_TYPE_PATTERNS: Dict[str, List[str]] = {
    'feature': ['feat', 'feature', 'add', 'implement', 'new'],
    'fix': ['fix', 'bug', 'patch', 'resolve', 'hotfix'],
    'docs': ['doc', 'docs', 'readme', 'comment', 'documentation'],
    'refactor': ['refactor', 'clean', 'reorganize', 'restructure'],
    'test': ['test', 'spec', 'testing'],
    'style': ['style', 'format', 'lint', 'prettier'],
    'perf': ['perf', 'performance', 'optimize', 'speed'],
    'build': ['build', 'ci', 'cd', 'deploy', 'release'],
    'chore': ['chore', 'update', 'bump', 'maintenance']
}

# Work status indicators
WORK_STATUS_PATTERNS: Dict[str, List[str]] = {
    'completed': ['done', 'complete', 'finish', 'close', 'resolve', 'merge'],
    'in_progress': ['wip', 'work in progress', 'partial', 'ongoing', 'todo', 'fixme'],
    'planned': ['todo', 'plan', 'draft', 'skeleton', 'scaffold'],
    'blocked': ['block', 'wait', 'pending', 'stuck', 'issue']
}

# ============================================================================
# Analysis Thresholds
# ============================================================================

# File change thresholds
SMALL_CHANGE_THRESHOLD = 10  # lines
LARGE_CHANGE_THRESHOLD = 100  # lines
MASSIVE_CHANGE_THRESHOLD = 500  # lines

# Velocity thresholds
HIGH_VELOCITY_COMMITS_PER_DAY = 5.0
LOW_VELOCITY_COMMITS_PER_DAY = 0.5

# Hotspot thresholds
HOTSPOT_MIN_CHANGES = 5
CRITICAL_HOTSPOT_MIN_CHANGES = 10
CRITICAL_HOTSPOT_MIN_AUTHORS = 3

# Complexity thresholds
HIGH_COMPLEXITY_THRESHOLD = 10.0
CRITICAL_COMPLEXITY_THRESHOLD = 20.0

# ============================================================================
# Output Formatting
# ============================================================================

# Emoji mappings for output
EMOJI_MAP: Dict[str, str] = {
    'analysis': '📊',
    'statistics': '📈',
    'contributors': '👥',
    'patterns': '🔍',
    'files': '📝',
    'repository': '📁',
    'info': 'ℹ️',
    'activity': '📊',
    'links': '🔗',
    'code': '🔬',
    'changes': '📊',
    'complexity': '📈',
    'structure': '🏗️',
    'dependencies': '📦',
    'work_types': '💼',
    'insights': '💡',
    'focus': '🎯',
    'completed': '✅',
    'progress': '🔄',
    'prediction': '🔮',
    'metrics': '📈',
    'collaboration': '👥',
    'summary': '📝'
}

# Report section names
REPORT_SECTIONS: Dict[str, str] = {
    'commit_analysis': 'Commit Analysis Report',
    'code_analysis': 'Code Changes Analysis',
    'diff_content': 'Commit Diff Content',
    'repository_summary': 'Repository Summary',
    'work_summary': 'Work Content Insights'
}

# ============================================================================
# Performance and Resource Limits
# ============================================================================

# Analysis timeouts (seconds)
DEFAULT_ANALYSIS_TIMEOUT = 60
COMPLEXITY_ANALYSIS_TIMEOUT = 30
DIFF_PARSING_TIMEOUT = 10

# Memory limits
MAX_COMMITS_IN_MEMORY = 1000
MAX_FILE_CHANGES_IN_MEMORY = 5000

# Retry configuration
MAX_RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY = 1.0  # seconds
RETRY_EXPONENTIAL_BASE = 2.0