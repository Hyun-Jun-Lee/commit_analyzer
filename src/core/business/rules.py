"""
Business rules engine for GitHub Commit Analyzer.
Declarative rules for work type inference and pattern detection.
"""

from typing import List, Dict, Callable, Set, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import re

from ..utils.functional import Result, ok, err, pipe, map_list, filter_list
from ..domain.types import (
    CommitData, FileChange, WorkType, WorkStatus, CodeContext,
    ChangeType
)
from ..domain.constants import (
    API_PATTERNS, DATABASE_PATTERNS, UI_PATTERNS, PERFORMANCE_PATTERNS,
    SECURITY_PATTERNS, TEST_FILE_PATTERNS, TEST_DIRECTORY_PATTERNS,
    BINARY_FILE_EXTENSIONS, CONFIG_FILE_EXTENSIONS, DOCUMENTATION_EXTENSIONS
)


# ============================================================================
# Rule Definition Types
# ============================================================================

@dataclass(frozen=True)
class Rule:
    """Individual business rule definition."""
    name: str
    condition: Callable[[Any], bool]
    action: Callable[[Any], Any]
    priority: int = 100  # Lower number = higher priority
    description: str = ""


@dataclass(frozen=True)
class RuleSet:
    """Collection of related rules."""
    name: str
    rules: List[Rule]
    combination_strategy: str = "first_match"  # first_match, all_matches, weighted


@dataclass(frozen=True)
class RuleContext:
    """Context passed to rules for evaluation."""
    commit: CommitData
    file_changes: List[FileChange]
    metadata: Dict[str, Any]


# ============================================================================
# Rule Engine
# ============================================================================

class RuleEngine:
    """Declarative rule engine for business logic."""
    
    def __init__(self):
        self.rule_sets: Dict[str, RuleSet] = {}
    
    def register_rule_set(self, rule_set: RuleSet) -> None:
        """Register a rule set with the engine."""
        self.rule_sets[rule_set.name] = rule_set
    
    def evaluate(self, rule_set_name: str, context: RuleContext) -> Result[List[Any], Exception]:
        """Evaluate rules against context and return results."""
        if rule_set_name not in self.rule_sets:
            return err(ValueError(f"Rule set '{rule_set_name}' not found"))
        
        rule_set = self.rule_sets[rule_set_name]
        results = []
        
        try:
            # Sort rules by priority
            sorted_rules = sorted(rule_set.rules, key=lambda r: r.priority)
            
            for rule in sorted_rules:
                if rule.condition(context):
                    result = rule.action(context)
                    results.append(result)
                    
                    # Stop at first match if that's the strategy
                    if rule_set.combination_strategy == "first_match":
                        break
            
            return ok(results)
            
        except Exception as e:
            return err(e)
    
    def evaluate_all_sets(self, context: RuleContext) -> Dict[str, List[Any]]:
        """Evaluate all rule sets against context."""
        results = {}
        
        for name, rule_set in self.rule_sets.items():
            result = self.evaluate(name, context)
            if result:
                results[name] = result.value
            else:
                results[name] = []
        
        return results


# ============================================================================
# File Analysis Rules
# ============================================================================

def create_file_classification_rules() -> RuleSet:
    """Create rules for classifying file types and purposes."""
    
    def is_binary_file(context: RuleContext) -> bool:
        return any(
            change.path.suffix.lower() in BINARY_FILE_EXTENSIONS
            for change in context.file_changes
        )
    
    def is_config_file(context: RuleContext) -> bool:
        return any(
            change.path.suffix.lower() in CONFIG_FILE_EXTENSIONS or
            change.path.name.lower() in {'dockerfile', 'makefile', '.gitignore', '.env'}
            for change in context.file_changes
        )
    
    def is_documentation_file(context: RuleContext) -> bool:
        return any(
            change.path.suffix.lower() in DOCUMENTATION_EXTENSIONS or
            'readme' in change.path.name.lower()
            for change in context.file_changes
        )
    
    def is_test_file(context: RuleContext) -> bool:
        for change in context.file_changes:
            path_str = str(change.path).lower()
            
            # Check file patterns
            if any(pattern in path_str for pattern in TEST_FILE_PATTERNS):
                return True
            
            # Check directory patterns
            path_parts = change.path.parts
            if any(
                any(test_pattern in part.lower() for part in path_parts)
                for test_pattern in TEST_DIRECTORY_PATTERNS
            ):
                return True
        
        return False
    
    def is_source_code_file(context: RuleContext) -> bool:
        programming_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.cpp', '.c',
            '.h', '.hpp', '.cs', '.rb', '.php', '.swift', '.kt', '.scala', '.clj'
        }
        return any(
            change.path.suffix.lower() in programming_extensions
            for change in context.file_changes
        )
    
    return RuleSet(
        name="file_classification",
        rules=[
            Rule("binary_files", is_binary_file, lambda _: "binary", 10),
            Rule("config_files", is_config_file, lambda _: "configuration", 20),
            Rule("documentation", is_documentation_file, lambda _: "documentation", 30),
            Rule("test_files", is_test_file, lambda _: "testing", 40),
            Rule("source_code", is_source_code_file, lambda _: "source", 50),
        ],
        combination_strategy="all_matches"
    )


# ============================================================================
# Work Type Inference Rules
# ============================================================================

def create_work_type_rules() -> RuleSet:
    """Create rules for inferring work types from changes."""
    
    def is_feature_work(context: RuleContext) -> bool:
        # Large additions of new source files
        new_source_files = [
            change for change in context.file_changes
            if change.change_type == ChangeType.ADDED and
            change.path.suffix.lower() in {'.py', '.js', '.ts', '.java', '.go'}
        ]
        
        # Significant line additions
        total_additions = sum(change.lines_added for change in context.file_changes)
        
        return len(new_source_files) > 0 or total_additions > 100
    
    def is_bug_fix_work(context: RuleContext) -> bool:
        # Small, focused changes in existing files
        source_changes = [
            change for change in context.file_changes
            if change.path.suffix.lower() in {'.py', '.js', '.ts', '.java', '.go'} and
            change.change_type == ChangeType.MODIFIED
        ]
        
        if not source_changes:
            return False
        
        # Small changes (less than 50 lines total)
        total_changes = sum(change.lines_added + change.lines_deleted for change in source_changes)
        avg_change_size = total_changes / len(source_changes)
        
        # Bug fix indicators in commit message
        message_lower = context.commit.message.lower()
        bug_keywords = ['fix', 'bug', 'issue', 'error', 'patch', 'hotfix']
        
        return (avg_change_size < 25 and total_changes < 100) or \
               any(keyword in message_lower for keyword in bug_keywords)
    
    def is_refactoring_work(context: RuleContext) -> bool:
        # Many modifications, few additions/deletions
        modified_files = [
            change for change in context.file_changes
            if change.change_type == ChangeType.MODIFIED
        ]
        
        if len(modified_files) < 2:
            return False
        
        # High modification to addition ratio
        total_modifications = len(modified_files)
        total_additions = len([c for c in context.file_changes if c.change_type == ChangeType.ADDED])
        
        # Refactoring keywords in commit message
        message_lower = context.commit.message.lower()
        refactor_keywords = ['refactor', 'clean', 'reorganize', 'restructure', 'improve']
        
        return (total_modifications > 3 and total_additions == 0) or \
               any(keyword in message_lower for keyword in refactor_keywords)
    
    def is_testing_work(context: RuleContext) -> bool:
        # Test file changes
        test_changes = [
            change for change in context.file_changes
            if any(pattern in str(change.path).lower() for pattern in TEST_FILE_PATTERNS)
        ]
        
        return len(test_changes) > 0
    
    def is_documentation_work(context: RuleContext) -> bool:
        # Documentation file changes
        doc_changes = [
            change for change in context.file_changes
            if change.path.suffix.lower() in DOCUMENTATION_EXTENSIONS or
            'readme' in change.path.name.lower()
        ]
        
        return len(doc_changes) > 0
    
    def is_configuration_work(context: RuleContext) -> bool:
        # Configuration file changes
        config_changes = [
            change for change in context.file_changes
            if change.path.suffix.lower() in CONFIG_FILE_EXTENSIONS or
            change.path.name.lower() in {'dockerfile', 'makefile', '.gitignore'}
        ]
        
        return len(config_changes) > 0
    
    def is_dependency_work(context: RuleContext) -> bool:
        # Package/dependency file changes
        dependency_files = {
            'package.json', 'package-lock.json', 'yarn.lock',
            'requirements.txt', 'pipfile', 'poetry.lock',
            'pom.xml', 'build.gradle', 'cargo.toml', 'go.mod'
        }
        
        changed_files = {change.path.name.lower() for change in context.file_changes}
        
        return bool(dependency_files.intersection(changed_files))
    
    def is_performance_work(context: RuleContext) -> bool:
        # Performance-related patterns in changes
        file_contents = []
        
        for change in context.file_changes:
            if hasattr(change, 'content_before') and change.content_before:
                file_contents.append(change.content_before.lower())
            if hasattr(change, 'content_after') and change.content_after:
                file_contents.append(change.content_after.lower())
        
        content_text = ' '.join(file_contents)
        
        return any(pattern.lower() in content_text for pattern in PERFORMANCE_PATTERNS)
    
    def is_security_work(context: RuleContext) -> bool:
        # Security-related patterns
        message_lower = context.commit.message.lower()
        security_keywords = ['security', 'auth', 'encrypt', 'secure', 'vulnerability']
        
        return any(keyword in message_lower for keyword in security_keywords)
    
    return RuleSet(
        name="work_type_inference",
        rules=[
            Rule("dependency_update", is_dependency_work, lambda _: WorkType.DEPENDENCY_UPDATE, 10),
            Rule("security_work", is_security_work, lambda _: WorkType.SECURITY, 20),
            Rule("testing_work", is_testing_work, lambda _: WorkType.TESTING, 30),
            Rule("documentation_work", is_documentation_work, lambda _: WorkType.DOCUMENTATION, 40),
            Rule("configuration_work", is_configuration_work, lambda _: WorkType.CONFIGURATION, 50),
            Rule("performance_work", is_performance_work, lambda _: WorkType.PERFORMANCE, 60),
            Rule("bug_fix_work", is_bug_fix_work, lambda _: WorkType.BUG_FIX, 70),
            Rule("refactoring_work", is_refactoring_work, lambda _: WorkType.REFACTORING, 80),
            Rule("feature_work", is_feature_work, lambda _: WorkType.FEATURE_DEVELOPMENT, 90),
        ],
        combination_strategy="all_matches"
    )


# ============================================================================
# Code Context Detection Rules
# ============================================================================

def create_code_context_rules() -> RuleSet:
    """Create rules for detecting code context (API, UI, Database, etc.)."""
    
    def is_api_context(context: RuleContext) -> bool:
        # Check file contents and paths for API patterns
        api_paths = ['api/', 'routes/', 'handlers/', 'controllers/']
        
        for change in context.file_changes:
            path_str = str(change.path).lower()
            
            # Path-based detection
            if any(api_path in path_str for api_path in api_paths):
                return True
            
            # Content-based detection (if available)
            if hasattr(change, 'content_after') and change.content_after:
                content = change.content_after.lower()
                if any(pattern.lower() in content for pattern in API_PATTERNS):
                    return True
        
        return False
    
    def is_database_context(context: RuleContext) -> bool:
        # Database-related files and patterns
        db_paths = ['models/', 'entities/', 'migrations/', 'schema/']
        db_files = ['.sql', '.migration']
        
        for change in context.file_changes:
            path_str = str(change.path).lower()
            
            # Path-based detection
            if any(db_path in path_str for db_path in db_paths):
                return True
            
            # File extension detection
            if any(ext in path_str for ext in db_files):
                return True
            
            # Content-based detection
            if hasattr(change, 'content_after') and change.content_after:
                content = change.content_after.lower()
                if any(pattern.lower() in content for pattern in DATABASE_PATTERNS):
                    return True
        
        return False
    
    def is_ui_context(context: RuleContext) -> bool:
        # UI-related files and patterns
        ui_paths = ['components/', 'views/', 'pages/', 'ui/', 'frontend/']
        ui_extensions = {'.jsx', '.tsx', '.vue', '.svelte', '.html', '.css', '.scss'}
        
        for change in context.file_changes:
            path_str = str(change.path).lower()
            
            # Path-based detection
            if any(ui_path in path_str for ui_path in ui_paths):
                return True
            
            # Extension-based detection
            if change.path.suffix.lower() in ui_extensions:
                return True
            
            # Content-based detection
            if hasattr(change, 'content_after') and change.content_after:
                content = change.content_after.lower()
                if any(pattern.lower() in content for pattern in UI_PATTERNS):
                    return True
        
        return False
    
    def is_infrastructure_context(context: RuleContext) -> bool:
        # Infrastructure and deployment files
        infra_files = {
            'dockerfile', 'docker-compose.yml', 'kubernetes.yml', 'k8s.yml',
            '.github/workflows', '.gitlab-ci.yml', 'jenkinsfile'
        }
        
        infra_paths = ['deploy/', 'infrastructure/', 'k8s/', 'docker/', '.github/']
        
        for change in context.file_changes:
            path_str = str(change.path).lower()
            file_name = change.path.name.lower()
            
            if file_name in infra_files or any(path in path_str for path in infra_paths):
                return True
        
        return False
    
    def is_business_logic_context(context: RuleContext) -> bool:
        # Business logic detection (default for most source code)
        business_paths = ['services/', 'business/', 'domain/', 'core/', 'lib/']
        
        for change in context.file_changes:
            path_str = str(change.path).lower()
            
            if any(path in path_str for path in business_paths):
                return True
            
            # Source code that's not in other categories
            if change.path.suffix.lower() in {'.py', '.js', '.ts', '.java', '.go'}:
                return True
        
        return False
    
    return RuleSet(
        name="code_context_detection",
        rules=[
            Rule("api_context", is_api_context, lambda _: CodeContext.API, 10),
            Rule("database_context", is_database_context, lambda _: CodeContext.DATABASE, 20),
            Rule("ui_context", is_ui_context, lambda _: CodeContext.UI, 30),
            Rule("infrastructure_context", is_infrastructure_context, lambda _: CodeContext.INFRASTRUCTURE, 40),
            Rule("business_context", is_business_logic_context, lambda _: CodeContext.BUSINESS, 50),
        ],
        combination_strategy="all_matches"
    )


# ============================================================================
# Work Status Detection Rules
# ============================================================================

def create_work_status_rules() -> RuleSet:
    """Create rules for detecting work status from commits."""
    
    def is_work_in_progress(context: RuleContext) -> bool:
        message_lower = context.commit.message.lower()
        wip_indicators = ['wip', 'work in progress', 'todo', 'fixme', 'partial', 'draft']
        
        return any(indicator in message_lower for indicator in wip_indicators)
    
    def is_work_completed(context: RuleContext) -> bool:
        message_lower = context.commit.message.lower()
        completion_indicators = ['done', 'complete', 'finish', 'close', 'resolve', 'implement']
        
        # Also check if both source and test files are modified (indicates completeness)
        has_source = any(
            change.path.suffix.lower() in {'.py', '.js', '.ts', '.java', '.go'}
            for change in context.file_changes
        )
        has_tests = any(
            any(pattern in str(change.path).lower() for pattern in TEST_FILE_PATTERNS)
            for change in context.file_changes
        )
        
        return any(indicator in message_lower for indicator in completion_indicators) or \
               (has_source and has_tests)
    
    def is_work_planned(context: RuleContext) -> bool:
        message_lower = context.commit.message.lower()
        planning_indicators = ['plan', 'draft', 'skeleton', 'scaffold', 'initial']
        
        return any(indicator in message_lower for indicator in planning_indicators)
    
    def is_work_blocked(context: RuleContext) -> bool:
        message_lower = context.commit.message.lower()
        blocked_indicators = ['block', 'blocked', 'wait', 'waiting', 'pending', 'stuck']
        
        return any(indicator in message_lower for indicator in blocked_indicators)
    
    return RuleSet(
        name="work_status_detection",
        rules=[
            Rule("blocked_work", is_work_blocked, lambda _: WorkStatus.BLOCKED, 10),
            Rule("planned_work", is_work_planned, lambda _: WorkStatus.PLANNED, 20),
            Rule("wip_work", is_work_in_progress, lambda _: WorkStatus.IN_PROGRESS, 30),
            Rule("completed_work", is_work_completed, lambda _: WorkStatus.COMPLETED, 40),
        ],
        combination_strategy="first_match"
    )


# ============================================================================
# Rule Engine Factory
# ============================================================================

def create_default_rule_engine() -> RuleEngine:
    """Create rule engine with default rule sets."""
    engine = RuleEngine()
    
    # Register all rule sets
    engine.register_rule_set(create_file_classification_rules())
    engine.register_rule_set(create_work_type_rules())
    engine.register_rule_set(create_code_context_rules())
    engine.register_rule_set(create_work_status_rules())
    
    return engine


# ============================================================================
# High-Level Analysis Functions
# ============================================================================

def analyze_commit_with_rules(
    commit: CommitData,
    file_changes: List[FileChange],
    metadata: Dict[str, Any] = None
) -> Dict[str, List[Any]]:
    """Analyze a commit using the complete rule engine."""
    engine = create_default_rule_engine()
    context = RuleContext(
        commit=commit,
        file_changes=file_changes,
        metadata=metadata or {}
    )
    
    return engine.evaluate_all_sets(context)


def extract_work_types(analysis_results: Dict[str, List[Any]]) -> Set[WorkType]:
    """Extract work types from rule analysis results."""
    work_types = set()
    
    if 'work_type_inference' in analysis_results:
        for work_type in analysis_results['work_type_inference']:
            if isinstance(work_type, WorkType):
                work_types.add(work_type)
    
    return work_types


def extract_work_status(analysis_results: Dict[str, List[Any]]) -> WorkStatus:
    """Extract work status from rule analysis results."""
    if 'work_status_detection' in analysis_results:
        statuses = analysis_results['work_status_detection']
        if statuses:
            return statuses[0]  # First match (highest priority)
    
    return WorkStatus.COMPLETED  # Default


def extract_code_contexts(analysis_results: Dict[str, List[Any]]) -> Set[CodeContext]:
    """Extract code contexts from rule analysis results."""
    contexts = set()
    
    if 'code_context_detection' in analysis_results:
        for context in analysis_results['code_context_detection']:
            if isinstance(context, CodeContext):
                contexts.add(context)
    
    return contexts