"""
Metrics calculation engine for GitHub Commit Analyzer.
Calculates development metrics, velocity, complexity, and quality indicators.
"""

from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from statistics import mean, median, stdev
from pathlib import Path

from ..utils.functional import Result, ok, err, safe, map_list
from ..domain.types import (
    CommitData, FileChange, DiffData, AuthorStats, VelocityMetrics,
    TimePatterns, ComplexityMetrics, FileHotspot, RepositoryInfo
)
from ..utils.data_transformation import (
    extract_programming_language, classify_file_type,
    is_test_file, is_source_file
)


# ============================================================================
# Velocity Metrics Calculation
# ============================================================================

@safe
def calculate_commit_velocity(commits: List[CommitData], analysis_days: int) -> VelocityMetrics:
    """Calculate development velocity metrics."""
    if not commits or analysis_days <= 0:
        return VelocityMetrics(
            commits_per_day=0.0,
            lines_per_day=0.0,
            files_per_commit=0.0,
            average_commit_size=0.0
        )
    
    # Basic velocity
    commits_per_day = len(commits) / analysis_days
    
    # For lines per day and files per commit, we need diff data
    # This will be calculated separately when diff data is available
    return VelocityMetrics(
        commits_per_day=commits_per_day,
        lines_per_day=0.0,  # To be calculated with diff data
        files_per_commit=0.0,  # To be calculated with diff data
        average_commit_size=0.0  # To be calculated with diff data
    )


@safe
def calculate_velocity_with_diffs(
    commits: List[CommitData],
    diffs: List[DiffData],
    analysis_days: int
) -> VelocityMetrics:
    """Calculate comprehensive velocity metrics with diff data."""
    if not commits or analysis_days <= 0:
        return VelocityMetrics(0.0, 0.0, 0.0, 0.0)
    
    # Create commit-diff mapping
    diff_by_commit = {diff.commit_sha: diff for diff in diffs}
    
    # Calculate metrics
    commits_per_day = len(commits) / analysis_days
    
    total_lines_changed = 0
    total_files_changed = 0
    commit_sizes = []
    
    for commit in commits:
        if commit.sha in diff_by_commit:
            diff = diff_by_commit[commit.sha]
            lines_changed = diff.total_additions + diff.total_deletions
            files_changed = len(diff.file_changes)
            
            total_lines_changed += lines_changed
            total_files_changed += files_changed
            commit_sizes.append(lines_changed)
    
    lines_per_day = total_lines_changed / analysis_days
    files_per_commit = total_files_changed / len(commits) if commits else 0.0
    average_commit_size = mean(commit_sizes) if commit_sizes else 0.0
    
    return VelocityMetrics(
        commits_per_day=commits_per_day,
        lines_per_day=lines_per_day,
        files_per_commit=files_per_commit,
        average_commit_size=average_commit_size
    )


# ============================================================================
# Time Pattern Analysis
# ============================================================================

@safe
def calculate_time_patterns(commits: List[CommitData]) -> TimePatterns:
    """Calculate temporal patterns in commit activity."""
    if not commits:
        return TimePatterns(
            most_active_hour=9,
            most_active_day='Monday',
            commit_time_distribution={},
            day_distribution={},
            commits_per_day=0.0
        )
    
    # Collect temporal data
    hours = [commit.authored_date.hour for commit in commits]
    days = [commit.authored_date.strftime('%A') for commit in commits]
    
    # Calculate distributions
    hour_dist = Counter(hours)
    day_dist = Counter(days)
    
    # Find most active times
    most_active_hour = hour_dist.most_common(1)[0][0] if hour_dist else 9
    most_active_day = day_dist.most_common(1)[0][0] if day_dist else 'Monday'
    
    # Calculate commits per day over the actual time span
    if len(commits) > 1:
        time_span = (
            max(commit.authored_date for commit in commits) -
            min(commit.authored_date for commit in commits)
        ).days + 1  # +1 to include both start and end days
        commits_per_day = len(commits) / max(1, time_span)
    else:
        commits_per_day = 1.0
    
    return TimePatterns(
        most_active_hour=most_active_hour,
        most_active_day=most_active_day,
        commit_time_distribution=dict(hour_dist),
        day_distribution=dict(day_dist),
        commits_per_day=commits_per_day
    )


def analyze_commit_rhythm(commits: List[CommitData]) -> Dict[str, any]:
    """Analyze the rhythm and consistency of commits."""
    if len(commits) < 2:
        return {
            'commit_intervals': [],
            'average_interval_hours': 0.0,
            'consistency_score': 0.0,
            'longest_gap_hours': 0.0,
            'working_days_active': 0
        }
    
    # Sort commits by date
    sorted_commits = sorted(commits, key=lambda c: c.authored_date)
    
    # Calculate intervals between commits
    intervals = []
    for i in range(1, len(sorted_commits)):
        interval = (sorted_commits[i].authored_date - sorted_commits[i-1].authored_date).total_seconds() / 3600
        intervals.append(interval)
    
    # Calculate rhythm metrics
    avg_interval = mean(intervals) if intervals else 0.0
    longest_gap = max(intervals) if intervals else 0.0
    
    # Consistency score (lower standard deviation = more consistent)
    consistency_score = 1.0 / (1.0 + stdev(intervals)) if len(intervals) > 1 else 1.0
    
    # Count unique working days
    working_days = set()
    for commit in commits:
        # Consider weekdays as working days
        if commit.authored_date.weekday() < 5:  # Monday = 0, Friday = 4
            working_days.add(commit.authored_date.date())
    
    return {
        'commit_intervals': intervals,
        'average_interval_hours': avg_interval,
        'consistency_score': consistency_score,
        'longest_gap_hours': longest_gap,
        'working_days_active': len(working_days)
    }


# ============================================================================
# Author Statistics
# ============================================================================

@safe
def calculate_author_statistics(
    commits: List[CommitData],
    diffs: List[DiffData]
) -> List[AuthorStats]:
    """Calculate detailed statistics for each author."""
    # Group commits by author
    commits_by_author = defaultdict(list)
    for commit in commits:
        author_key = (commit.author, commit.author_email)
        commits_by_author[author_key].append(commit)
    
    # Create diff lookup
    diff_by_commit = {diff.commit_sha: diff for diff in diffs}
    
    # Calculate stats for each author
    author_stats = []
    
    for (name, email), author_commits in commits_by_author.items():
        # Basic counts
        commits_count = len(author_commits)
        
        # Time patterns
        hours = [commit.authored_date.hour for commit in author_commits]
        days = [commit.authored_date.strftime('%A') for commit in author_commits]
        
        most_active_hour = Counter(hours).most_common(1)[0][0] if hours else None
        most_active_day = Counter(days).most_common(1)[0][0] if days else None
        
        # Calculate code changes
        lines_added = 0
        lines_deleted = 0
        files_modified = set()
        
        for commit in author_commits:
            if commit.sha in diff_by_commit:
                diff = diff_by_commit[commit.sha]
                lines_added += diff.total_additions
                lines_deleted += diff.total_deletions
                
                for file_change in diff.file_changes:
                    files_modified.add(str(file_change.path))
        
        author_stats.append(AuthorStats(
            name=name,
            email=email,
            commits_count=commits_count,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            files_modified=len(files_modified),
            most_active_day=most_active_day,
            most_active_hour=most_active_hour
        ))
    
    # Sort by commit count descending
    return sorted(author_stats, key=lambda x: x.commits_count, reverse=True)


def calculate_collaboration_metrics(author_stats: List[AuthorStats]) -> Dict[str, any]:
    """Calculate team collaboration metrics."""
    if not author_stats:
        return {
            'total_authors': 0,
            'primary_contributors': 0,
            'contribution_distribution': 'even',
            'bus_factor': 0,
            'collaboration_score': 0.0
        }
    
    total_commits = sum(stat.commits_count for stat in author_stats)
    total_authors = len(author_stats)
    
    # Calculate contribution percentages
    contributions = [(stat.commits_count / total_commits * 100) for stat in author_stats]
    
    # Primary contributors (>= 20% of commits)
    primary_contributors = sum(1 for contrib in contributions if contrib >= 20.0)
    
    # Bus factor (minimum contributors needed for 50% of work)
    bus_factor = 0
    cumulative = 0.0
    for contrib in sorted(contributions, reverse=True):
        bus_factor += 1
        cumulative += contrib
        if cumulative >= 50.0:
            break
    
    # Determine distribution pattern
    if contributions[0] >= 70:
        distribution = 'concentrated'
    elif len([c for c in contributions if c >= 10]) >= 3:
        distribution = 'distributed'
    else:
        distribution = 'mixed'
    
    # Collaboration score (higher = more collaborative)
    # Based on how evenly work is distributed
    if total_authors > 1:
        # Gini coefficient approximation (simpler calculation)
        sorted_contributions = sorted(contributions)
        n = len(sorted_contributions)
        index = list(range(1, n + 1))
        collaboration_score = 1.0 - (2.0 * sum(index[i] * sorted_contributions[i] for i in range(n))) / (n * sum(sorted_contributions)) + (n + 1) / n
    else:
        collaboration_score = 0.0
    
    return {
        'total_authors': total_authors,
        'primary_contributors': primary_contributors,
        'contribution_distribution': distribution,
        'bus_factor': bus_factor,
        'collaboration_score': max(0.0, collaboration_score),
        'contribution_percentages': contributions
    }


# ============================================================================
# File Hotspot Analysis
# ============================================================================

@safe
def calculate_file_hotspots(diffs: List[DiffData], commits: List[CommitData]) -> List[FileHotspot]:
    """Calculate file change hotspots and their statistics."""
    file_stats = defaultdict(lambda: {
        'changes': 0,
        'total_lines': 0,
        'authors': set(),
        'last_modified': None
    })
    
    # Create commit lookup for author information
    commit_by_sha = {commit.sha: commit for commit in commits}
    
    # Process all diffs
    for diff in diffs:
        commit = commit_by_sha.get(diff.commit_sha)
        
        for file_change in diff.file_changes:
            path_str = str(file_change.path)
            
            file_stats[path_str]['changes'] += 1
            file_stats[path_str]['total_lines'] += file_change.lines_added + file_change.lines_deleted
            
            if commit:
                file_stats[path_str]['authors'].add(commit.author)
                
                # Track most recent modification
                if (file_stats[path_str]['last_modified'] is None or 
                    commit.authored_date > file_stats[path_str]['last_modified']):
                    file_stats[path_str]['last_modified'] = commit.authored_date
    
    # Convert to FileHotspot objects
    hotspots = []
    for path_str, stats in file_stats.items():
        hotspots.append(FileHotspot(
            path=Path(path_str),
            change_frequency=stats['changes'],
            total_lines_changed=stats['total_lines'],
            last_modified=stats['last_modified'] or datetime.now(),
            authors_count=len(stats['authors'])
        ))
    
    # Sort by change frequency (most changed files first)
    return sorted(hotspots, key=lambda x: x.change_frequency, reverse=True)


def analyze_hotspot_patterns(hotspots: List[FileHotspot]) -> Dict[str, any]:
    """Analyze patterns in file hotspots."""
    if not hotspots:
        return {
            'critical_hotspots': 0,
            'high_risk_files': [],
            'hotspot_languages': {},
            'hotspot_types': {},
            'change_concentration': 0.0
        }
    
    # Identify critical hotspots
    critical_hotspots = [h for h in hotspots if h.is_critical_hotspot()]
    
    # High risk files (high frequency + multiple authors)
    high_risk_files = [
        str(h.path) for h in hotspots
        if h.change_frequency >= 5 and h.authors_count >= 2
    ]
    
    # Analyze hotspot characteristics
    hotspot_languages = Counter()
    hotspot_types = Counter()
    
    for hotspot in hotspots:
        # Language analysis
        language = extract_programming_language(hotspot.path)
        if language:
            hotspot_languages[language] += 1
        
        # File type analysis
        file_type = classify_file_type(hotspot.path)
        hotspot_types[file_type] += 1
    
    # Change concentration (what % of changes are in top 20% of files)
    if len(hotspots) >= 5:
        top_20_percent = max(1, len(hotspots) // 5)
        top_changes = sum(h.change_frequency for h in hotspots[:top_20_percent])
        total_changes = sum(h.change_frequency for h in hotspots)
        change_concentration = (top_changes / total_changes) if total_changes > 0 else 0.0
    else:
        change_concentration = 1.0  # All files are "concentrated" if very few files
    
    return {
        'critical_hotspots': len(critical_hotspots),
        'high_risk_files': high_risk_files,
        'hotspot_languages': dict(hotspot_languages),
        'hotspot_types': dict(hotspot_types),
        'change_concentration': change_concentration
    }


# ============================================================================
# Code Quality Metrics
# ============================================================================

def calculate_code_quality_indicators(
    diffs: List[DiffData],
    commits: List[CommitData]
) -> Dict[str, any]:
    """Calculate indicators of code quality from changes."""
    quality_indicators = {
        'test_coverage_trend': 'unknown',
        'documentation_ratio': 0.0,
        'refactoring_frequency': 0.0,
        'average_change_size': 0.0,
        'large_change_frequency': 0.0,
        'code_to_test_ratio': 0.0
    }
    
    if not diffs:
        return quality_indicators
    
    # Collect file change statistics
    total_changes = 0
    test_file_changes = 0
    doc_file_changes = 0
    source_file_changes = 0
    refactoring_commits = 0
    change_sizes = []
    large_changes = 0
    
    commit_messages = [commit.message.lower() for commit in commits]
    
    for diff in diffs:
        for file_change in diff.file_changes:
            total_changes += 1
            change_size = file_change.lines_added + file_change.lines_deleted
            change_sizes.append(change_size)
            
            if change_size > 100:
                large_changes += 1
            
            if is_test_file(file_change.path):
                test_file_changes += 1
            elif classify_file_type(file_change.path) == 'documentation':
                doc_file_changes += 1
            elif is_source_file(file_change.path):
                source_file_changes += 1
    
    # Count refactoring commits
    refactoring_keywords = ['refactor', 'clean', 'reorganize', 'restructure']
    refactoring_commits = sum(
        1 for message in commit_messages
        if any(keyword in message for keyword in refactoring_keywords)
    )
    
    # Calculate quality indicators
    if total_changes > 0:
        quality_indicators['documentation_ratio'] = doc_file_changes / total_changes
        quality_indicators['large_change_frequency'] = large_changes / total_changes
    
    if len(commits) > 0:
        quality_indicators['refactoring_frequency'] = refactoring_commits / len(commits)
    
    if change_sizes:
        quality_indicators['average_change_size'] = mean(change_sizes)
    
    if source_file_changes > 0 and test_file_changes > 0:
        quality_indicators['code_to_test_ratio'] = source_file_changes / test_file_changes
        
        # Determine test coverage trend
        if test_file_changes >= source_file_changes:
            quality_indicators['test_coverage_trend'] = 'improving'
        elif test_file_changes >= source_file_changes * 0.5:
            quality_indicators['test_coverage_trend'] = 'stable'
        else:
            quality_indicators['test_coverage_trend'] = 'declining'
    
    return quality_indicators


# ============================================================================
# Complexity Analysis
# ============================================================================

def estimate_complexity_changes(diffs: List[DiffData]) -> ComplexityMetrics:
    """Estimate complexity changes based on file modifications."""
    # This is a simplified complexity estimation
    # In a full implementation, you'd parse code to calculate actual complexity
    
    total_complexity_change = 0.0
    cognitive_complexity_change = 0.0
    method_length_change = 0.0
    nesting_depth_change = 0.0
    
    for diff in diffs:
        for file_change in diff.file_changes:
            # Skip non-source files
            if not is_source_file(file_change.path):
                continue
            
            # Estimate based on lines added/deleted
            lines_added = file_change.lines_added
            lines_deleted = file_change.lines_deleted
            
            # Simple heuristics for complexity estimation
            if lines_added > lines_deleted:
                # More code added - likely increased complexity
                net_lines = lines_added - lines_deleted
                total_complexity_change += net_lines * 0.1
                method_length_change += net_lines * 0.05
            else:
                # Code removed - likely decreased complexity
                net_lines = lines_deleted - lines_added
                total_complexity_change -= net_lines * 0.05
                method_length_change -= net_lines * 0.03
    
    return ComplexityMetrics(
        cyclomatic_complexity_change=total_complexity_change,
        cognitive_complexity_change=cognitive_complexity_change,
        method_length_change=method_length_change,
        nesting_depth_change=nesting_depth_change
    )


# ============================================================================
# Repository Health Metrics
# ============================================================================

def calculate_repository_health(
    repo_info: RepositoryInfo,
    velocity_metrics: VelocityMetrics,
    author_stats: List[AuthorStats],
    hotspots: List[FileHotspot],
    quality_indicators: Dict[str, any]
) -> Dict[str, any]:
    """Calculate overall repository health score and indicators."""
    
    health_score = 0.0
    max_score = 0.0
    health_factors = {}
    
    # Velocity health (25% of score)
    velocity_score = 0.0
    max_score += 25.0
    
    if velocity_metrics.commits_per_day > 0.5:
        velocity_score += 10.0  # Active development
    if velocity_metrics.commits_per_day < 5.0:
        velocity_score += 5.0   # Not overwhelming
    if velocity_metrics.average_commit_size < 200:
        velocity_score += 10.0  # Manageable changes
    
    health_factors['velocity_health'] = velocity_score
    health_score += velocity_score
    
    # Collaboration health (25% of score)
    collaboration_score = 0.0
    max_score += 25.0
    
    if len(author_stats) > 1:
        collaboration_score += 15.0  # Multiple contributors
    if len(author_stats) >= 3:
        collaboration_score += 5.0   # Good team size
    if len(author_stats) > 1:
        # Check if work is reasonably distributed
        primary_author_percentage = (author_stats[0].commits_count / 
                                   sum(a.commits_count for a in author_stats))
        if primary_author_percentage < 0.8:  # Not overly concentrated
            collaboration_score += 5.0
    
    health_factors['collaboration_health'] = collaboration_score
    health_score += collaboration_score
    
    # Code quality health (30% of score)
    quality_score = 0.0
    max_score += 30.0
    
    if quality_indicators.get('test_coverage_trend') in ['improving', 'stable']:
        quality_score += 10.0
    if quality_indicators.get('documentation_ratio', 0) > 0.1:
        quality_score += 5.0
    if quality_indicators.get('refactoring_frequency', 0) > 0.1:
        quality_score += 5.0
    if quality_indicators.get('large_change_frequency', 1.0) < 0.3:
        quality_score += 10.0
    
    health_factors['quality_health'] = quality_score
    health_score += quality_score
    
    # Hotspot health (20% of score)
    hotspot_score = 0.0
    max_score += 20.0
    
    critical_hotspots = len([h for h in hotspots if h.is_critical_hotspot()])
    if critical_hotspots == 0:
        hotspot_score += 15.0
    elif critical_hotspots <= 2:
        hotspot_score += 10.0
    elif critical_hotspots <= 5:
        hotspot_score += 5.0
    
    if len(hotspots) > 0:
        # Check change concentration
        top_file_changes = hotspots[0].change_frequency if hotspots else 0
        total_changes = sum(h.change_frequency for h in hotspots)
        concentration = (top_file_changes / total_changes) if total_changes > 0 else 0
        if concentration < 0.5:  # Changes are well distributed
            hotspot_score += 5.0
    
    health_factors['hotspot_health'] = hotspot_score
    health_score += hotspot_score
    
    # Calculate final health percentage
    health_percentage = (health_score / max_score * 100) if max_score > 0 else 0
    
    # Determine health status
    if health_percentage >= 80:
        health_status = 'excellent'
    elif health_percentage >= 60:
        health_status = 'good'
    elif health_percentage >= 40:
        health_status = 'fair'
    else:
        health_status = 'needs_attention'
    
    return {
        'health_score': health_percentage,
        'health_status': health_status,
        'health_factors': health_factors,
        'recommendations': generate_health_recommendations(
            health_factors, quality_indicators, len(hotspots)
        )
    }


def generate_health_recommendations(
    health_factors: Dict[str, float],
    quality_indicators: Dict[str, any],
    hotspot_count: int
) -> List[str]:
    """Generate actionable recommendations based on health metrics."""
    recommendations = []
    
    # Velocity recommendations
    velocity_health = health_factors.get('velocity_health', 0)
    if velocity_health < 15:
        recommendations.append("Consider increasing development velocity with smaller, more frequent commits")
    
    # Collaboration recommendations
    collaboration_health = health_factors.get('collaboration_health', 0)
    if collaboration_health < 10:
        recommendations.append("Encourage more team collaboration and code review")
    elif collaboration_health < 20:
        recommendations.append("Work on distributing contributions more evenly across team members")
    
    # Quality recommendations
    quality_health = health_factors.get('quality_health', 0)
    if quality_health < 15:
        recommendations.append("Focus on improving test coverage and code documentation")
    if quality_indicators.get('large_change_frequency', 0) > 0.3:
        recommendations.append("Break down large changes into smaller, more manageable commits")
    
    # Hotspot recommendations
    hotspot_health = health_factors.get('hotspot_health', 0)
    if hotspot_health < 10:
        recommendations.append("Address critical file hotspots through refactoring or better modularization")
    elif hotspot_count > 10:
        recommendations.append("Monitor frequently changing files and consider architectural improvements")
    
    return recommendations