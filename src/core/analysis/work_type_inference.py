"""
Work type inference engine for GitHub Commit Analyzer.
Analyzes commits and file changes to infer what type of work was done.
"""

from typing import List, Dict, Set, Tuple
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from ..utils.functional import Result, ok, err, pipe, map_list, safe
from ..domain.types import (
    CommitData, FileChange, DiffData, WorkType, WorkStatus, CodeContext,
    WorkTypeDistribution, WorkStatusDistribution
)
from ..business.rules import (
    create_default_rule_engine, RuleContext, RuleEngine,
    extract_work_types, extract_work_status, extract_code_contexts
)
from ..utils.data_transformation import (
    classify_file_type, extract_programming_language,
    is_test_file, is_source_file, is_documentation_file
)


# ============================================================================
# Work Type Analysis
# ============================================================================

@safe
def infer_work_types_from_commit(
    commit: CommitData,
    file_changes: List[FileChange],
    rule_engine: RuleEngine = None
) -> Set[WorkType]:
    """Infer work types from a single commit and its file changes."""
    if rule_engine is None:
        rule_engine = create_default_rule_engine()
    
    context = RuleContext(
        commit=commit,
        file_changes=file_changes,
        metadata={}
    )
    
    analysis_results = rule_engine.evaluate_all_sets(context)
    return extract_work_types(analysis_results)


@safe
def infer_work_status_from_commit(
    commit: CommitData,
    file_changes: List[FileChange],
    rule_engine: RuleEngine = None
) -> WorkStatus:
    """Infer work status from a single commit and its file changes."""
    if rule_engine is None:
        rule_engine = create_default_rule_engine()
    
    context = RuleContext(
        commit=commit,
        file_changes=file_changes,
        metadata={}
    )
    
    analysis_results = rule_engine.evaluate_all_sets(context)
    return extract_work_status(analysis_results)


@safe
def analyze_work_patterns_batch(
    commits_with_diffs: List[Tuple[CommitData, List[FileChange]]]
) -> Dict[str, any]:
    """Analyze work patterns across multiple commits."""
    rule_engine = create_default_rule_engine()
    
    work_type_counts = Counter()
    work_status_counts = Counter()
    context_counts = Counter()
    
    commit_work_types = {}
    commit_work_status = {}
    commit_contexts = {}
    
    for commit, file_changes in commits_with_diffs:
        context = RuleContext(
            commit=commit,
            file_changes=file_changes,
            metadata={}
        )
        
        analysis_results = rule_engine.evaluate_all_sets(context)
        
        # Extract and count work types
        work_types = extract_work_types(analysis_results)
        for work_type in work_types:
            work_type_counts[work_type] += 1
        commit_work_types[commit.sha] = work_types
        
        # Extract and count work status
        work_status = extract_work_status(analysis_results)
        work_status_counts[work_status] += 1
        commit_work_status[commit.sha] = work_status
        
        # Extract and count code contexts
        contexts = extract_code_contexts(analysis_results)
        for context_type in contexts:
            context_counts[context_type] += 1
        commit_contexts[commit.sha] = contexts
    
    return {
        'work_type_distribution': dict(work_type_counts),
        'work_status_distribution': dict(work_status_counts),
        'context_distribution': dict(context_counts),
        'commit_work_types': commit_work_types,
        'commit_work_status': commit_work_status,
        'commit_contexts': commit_contexts
    }


# ============================================================================
# Advanced Pattern Analysis
# ============================================================================

def analyze_file_change_patterns(file_changes: List[FileChange]) -> Dict[str, any]:
    """Analyze patterns in file changes."""
    patterns = {
        'file_types': defaultdict(int),
        'languages': defaultdict(int),
        'change_sizes': [],
        'new_files': 0,
        'deleted_files': 0,
        'modified_files': 0,
        'renamed_files': 0
    }
    
    for change in file_changes:
        # File type classification
        file_type = classify_file_type(change.path)
        patterns['file_types'][file_type] += 1
        
        # Programming language
        language = extract_programming_language(change.path)
        if language:
            patterns['languages'][language] += 1
        
        # Change size
        change_size = change.lines_added + change.lines_deleted
        patterns['change_sizes'].append(change_size)
        
        # Change type counts
        if change.change_type.value == 'added':
            patterns['new_files'] += 1
        elif change.change_type.value == 'deleted':
            patterns['deleted_files'] += 1
        elif change.change_type.value == 'modified':
            patterns['modified_files'] += 1
        elif change.change_type.value == 'renamed':
            patterns['renamed_files'] += 1
    
    # Calculate statistics
    if patterns['change_sizes']:
        patterns['avg_change_size'] = sum(patterns['change_sizes']) / len(patterns['change_sizes'])
        patterns['max_change_size'] = max(patterns['change_sizes'])
        patterns['total_lines_changed'] = sum(patterns['change_sizes'])
    else:
        patterns['avg_change_size'] = 0
        patterns['max_change_size'] = 0
        patterns['total_lines_changed'] = 0
    
    return patterns


def analyze_temporal_work_patterns(
    commits_with_work_types: Dict[str, Set[WorkType]],
    commits: List[CommitData]
) -> Dict[str, any]:
    """Analyze temporal patterns in work types."""
    commit_by_sha = {commit.sha: commit for commit in commits}
    
    temporal_patterns = {
        'work_by_hour': defaultdict(lambda: defaultdict(int)),
        'work_by_day': defaultdict(lambda: defaultdict(int)),
        'work_by_week': defaultdict(lambda: defaultdict(int)),
        'work_streaks': {},
        'work_transitions': defaultdict(int)
    }
    
    # Sort commits by date
    sorted_commits = sorted(commits, key=lambda c: c.authored_date)
    
    previous_work_types = set()
    
    for commit in sorted_commits:
        if commit.sha not in commits_with_work_types:
            continue
            
        work_types = commits_with_work_types[commit.sha]
        timestamp = commit.authored_date
        
        # Patterns by time
        hour = timestamp.hour
        day = timestamp.strftime('%A')
        week = timestamp.isocalendar()[1]
        
        for work_type in work_types:
            temporal_patterns['work_by_hour'][hour][work_type] += 1
            temporal_patterns['work_by_day'][day][work_type] += 1
            temporal_patterns['work_by_week'][week][work_type] += 1
        
        # Work type transitions
        if previous_work_types:
            for prev_type in previous_work_types:
                for curr_type in work_types:
                    if prev_type != curr_type:
                        transition = f"{prev_type.value} -> {curr_type.value}"
                        temporal_patterns['work_transitions'][transition] += 1
        
        previous_work_types = work_types
    
    return temporal_patterns


def identify_work_focus_areas(
    commits_with_contexts: Dict[str, Set[CodeContext]],
    commits_with_work_types: Dict[str, Set[WorkType]]
) -> Dict[str, any]:
    """Identify main areas of focus in the development work."""
    focus_analysis = {
        'primary_contexts': Counter(),
        'context_work_combinations': defaultdict(Counter),
        'focus_score_by_context': {},
        'work_distribution_by_context': defaultdict(Counter)
    }
    
    # Count contexts and their work type combinations
    for commit_sha in commits_with_contexts:
        contexts = commits_with_contexts.get(commit_sha, set())
        work_types = commits_with_work_types.get(commit_sha, set())
        
        for context in contexts:
            focus_analysis['primary_contexts'][context] += 1
            
            for work_type in work_types:
                focus_analysis['context_work_combinations'][context][work_type] += 1
                focus_analysis['work_distribution_by_context'][work_type][context] += 1
    
    # Calculate focus scores (how concentrated work is in each context)
    total_commits = len(commits_with_contexts)
    
    for context, count in focus_analysis['primary_contexts'].items():
        focus_score = count / total_commits if total_commits > 0 else 0
        focus_analysis['focus_score_by_context'][context] = focus_score
    
    return focus_analysis


# ============================================================================
# Work Summary Generation
# ============================================================================

def generate_work_summary(
    work_patterns: Dict[str, any],
    file_patterns: Dict[str, any],
    temporal_patterns: Dict[str, any],
    focus_areas: Dict[str, any]
) -> Dict[str, any]:
    """Generate comprehensive work summary from analysis results."""
    
    # Determine primary work type
    work_type_dist = work_patterns.get('work_type_distribution', {})
    primary_work_type = max(work_type_dist.items(), key=lambda x: x[1])[0] if work_type_dist else None
    
    # Determine primary context
    primary_contexts = focus_areas.get('primary_contexts', Counter())
    primary_context = primary_contexts.most_common(1)[0][0] if primary_contexts else None
    
    # Determine most active time
    work_by_hour = temporal_patterns.get('work_by_hour', {})
    most_active_hour = None
    if work_by_hour:
        hour_totals = {hour: sum(work_counts.values()) for hour, work_counts in work_by_hour.items()}
        most_active_hour = max(hour_totals.items(), key=lambda x: x[1])[0] if hour_totals else None
    
    # Calculate development velocity indicators
    total_commits = sum(work_patterns.get('work_status_distribution', {}).values())
    completed_work = work_patterns.get('work_status_distribution', {}).get(WorkStatus.COMPLETED, 0)
    completion_rate = completed_work / total_commits if total_commits > 0 else 0
    
    # Identify development patterns
    patterns = []
    
    if file_patterns.get('new_files', 0) > file_patterns.get('modified_files', 0):
        patterns.append("heavy_new_development")
    
    if file_patterns.get('file_types', {}).get('test', 0) > 0:
        patterns.append("test_driven")
    
    if len(file_patterns.get('languages', {})) > 3:
        patterns.append("multi_language")
    
    if file_patterns.get('avg_change_size', 0) < 20:
        patterns.append("incremental_development")
    
    return {
        'primary_work_type': primary_work_type.value if primary_work_type else None,
        'primary_context': primary_context.value if primary_context else None,
        'most_active_hour': most_active_hour,
        'completion_rate': completion_rate,
        'total_commits_analyzed': total_commits,
        'development_patterns': patterns,
        'work_type_distribution': {k.value: v for k, v in work_type_dist.items()},
        'language_distribution': dict(file_patterns.get('languages', {})),
        'file_type_distribution': dict(file_patterns.get('file_types', {})),
        'average_change_size': file_patterns.get('avg_change_size', 0),
        'total_lines_changed': file_patterns.get('total_lines_changed', 0),
        'focus_scores': {
            k.value: v for k, v in focus_areas.get('focus_score_by_context', {}).items()
        }
    }


# ============================================================================
# Main Analysis Pipeline
# ============================================================================

def analyze_commits_comprehensive(
    commits: List[CommitData],
    diffs: List[DiffData]
) -> Result[Dict[str, any], Exception]:
    """Comprehensive analysis of commits and their changes."""
    try:
        # Prepare data
        commits_with_diffs = []
        diff_by_commit = {diff.commit_sha: diff for diff in diffs}
        
        for commit in commits:
            if commit.sha in diff_by_commit:
                file_changes = diff_by_commit[commit.sha].file_changes
                commits_with_diffs.append((commit, file_changes))
        
        # Run analyses
        work_patterns_result = analyze_work_patterns_batch(commits_with_diffs)
        if not work_patterns_result:
            return work_patterns_result
        work_patterns = work_patterns_result.value
        
        # Analyze file patterns
        all_file_changes = []
        for _, file_changes in commits_with_diffs:
            all_file_changes.extend(file_changes)
        
        file_patterns = analyze_file_change_patterns(all_file_changes)
        
        # Analyze temporal patterns
        temporal_patterns = analyze_temporal_work_patterns(
            work_patterns['commit_work_types'],
            commits
        )
        
        # Identify focus areas
        focus_areas = identify_work_focus_areas(
            work_patterns['commit_contexts'],
            work_patterns['commit_work_types']
        )
        
        # Generate summary
        work_summary = generate_work_summary(
            work_patterns,
            file_patterns,
            temporal_patterns,
            focus_areas
        )
        
        return ok({
            'work_patterns': work_patterns,
            'file_patterns': file_patterns,
            'temporal_patterns': temporal_patterns,
            'focus_areas': focus_areas,
            'summary': work_summary
        })
        
    except Exception as e:
        return err(e)


# ============================================================================
# Distribution Builders
# ============================================================================

def build_work_type_distribution(work_type_counts: Dict[WorkType, int]) -> WorkTypeDistribution:
    """Build WorkTypeDistribution from counts."""
    return WorkTypeDistribution(
        feature_development=work_type_counts.get(WorkType.FEATURE_DEVELOPMENT, 0),
        bug_fix=work_type_counts.get(WorkType.BUG_FIX, 0),
        testing=work_type_counts.get(WorkType.TESTING, 0),
        refactoring=work_type_counts.get(WorkType.REFACTORING, 0),
        configuration=work_type_counts.get(WorkType.CONFIGURATION, 0),
        documentation=work_type_counts.get(WorkType.DOCUMENTATION, 0),
        dependency_update=work_type_counts.get(WorkType.DEPENDENCY_UPDATE, 0),
        performance=work_type_counts.get(WorkType.PERFORMANCE, 0),
        security=work_type_counts.get(WorkType.SECURITY, 0)
    )


def build_work_status_distribution(work_status_counts: Dict[WorkStatus, int]) -> WorkStatusDistribution:
    """Build WorkStatusDistribution from counts."""
    return WorkStatusDistribution(
        completed=work_status_counts.get(WorkStatus.COMPLETED, 0),
        in_progress=work_status_counts.get(WorkStatus.IN_PROGRESS, 0),
        planned=work_status_counts.get(WorkStatus.PLANNED, 0),
        blocked=work_status_counts.get(WorkStatus.BLOCKED, 0)
    )