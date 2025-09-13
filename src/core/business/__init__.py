"""
Business logic layer for GitHub Commit Analyzer.
Contains business rules and domain logic.
"""

from .rules import (
    Rule, RuleSet, RuleContext, RuleEngine,
    create_default_rule_engine,
    analyze_commit_with_rules,
    extract_work_types,
    extract_work_status,
    extract_code_contexts
)

__all__ = [
    'Rule',
    'RuleSet', 
    'RuleContext',
    'RuleEngine',
    'create_default_rule_engine',
    'analyze_commit_with_rules',
    'extract_work_types',
    'extract_work_status',
    'extract_code_contexts'
]