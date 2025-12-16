"""
HTN Failure Analyzer
Analyzes HTN planning traces to provide detailed failure information.
"""

from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import re


class FailureCategory(Enum):
    """Categories of planning failures"""
    NO_MATCHING_METHOD = auto()     # Task has no applicable methods
    PRECONDITION_FAILED = auto()    # if() condition not satisfiable
    UNIFICATION_FAILED = auto()     # Arity or type mismatch
    SUBTASK_FAILED = auto()         # A child task in do() failed
    OPERATOR_FAILED = auto()        # del/add couldn't apply
    NO_SOLUTION = auto()            # Overall planning failed
    BACKTRACKED = auto()            # This branch was explored but backtracked
    UNKNOWN = auto()                # Unknown failure reason


@dataclass
class FailureDetail:
    """Detailed failure information"""
    category: FailureCategory
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'category': self.category.name,
            'message': self.message,
            'details': self.details,
            'suggestions': self.suggestions
        }


@dataclass
class AlternativeAttempt:
    """Information about an alternative that was tried"""
    method_name: str
    signature: str
    success: bool
    failure_reason: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'method_name': self.method_name,
            'signature': self.signature,
            'success': self.success,
            'failure_reason': self.failure_reason
        }


@dataclass
class EnhancedNode:
    """Enhanced node with failure analysis"""
    id: str
    name: str
    full_signature: str
    task_name: str
    is_operator: bool
    status: str  # 'success', 'failure', 'default'
    bindings: Dict[str, str]
    condition_bindings: Dict[str, str]
    condition_terms: List[str]
    children: List['EnhancedNode']

    # Enhanced failure information
    failure_detail: Optional[FailureDetail] = None
    alternatives_tried: List[AlternativeAttempt] = field(default_factory=list)
    missing_facts: List[str] = field(default_factory=list)
    failed_conditions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        result = {
            'id': self.id,
            'name': self.name,
            'fullSignature': self.full_signature,
            'taskName': self.task_name,
            'isOperator': self.is_operator,
            'status': self.status,
            'bindings': self.bindings,
            'conditionBindings': self.condition_bindings,
            'conditionTerms': self.condition_terms,
            'children': [c.to_dict() for c in self.children],
            'failureDetail': self.failure_detail.to_dict() if self.failure_detail else None,
            'alternativesTried': [a.to_dict() for a in self.alternatives_tried],
            'missingFacts': self.missing_facts,
            'failedConditions': self.failed_conditions
        }

        # Also include legacy failureReason for backwards compatibility
        if self.failure_detail:
            result['failureReason'] = self.failure_detail.message

        return result


class FailureAnalyzer:
    """Analyzes planning traces to provide detailed failure information"""

    def __init__(self):
        self.current_facts: Set[str] = set()
        self.all_methods: Dict[str, List[Dict]] = {}  # task_name -> list of method definitions

    def analyze_trace(self, nodes: List[Dict], solution_index: int,
                     initial_facts: List[str] = None) -> Optional[EnhancedNode]:
        """
        Analyze a trace and return an enhanced node tree

        Args:
            nodes: Flat list of trace nodes from C++
            solution_index: Index of this solution
            initial_facts: Initial state facts for missing fact analysis

        Returns:
            Enhanced root node with failure analysis
        """
        if not nodes:
            return None

        # Store facts for analysis
        if initial_facts:
            self.current_facts = set(initial_facts)

        # Build lookup map
        node_map = {n['nodeID']: n for n in nodes}

        # Find all nodes for each task (for alternative tracking)
        self._build_method_index(nodes)

        # Find root
        roots = [n for n in nodes if n['parentNodeID'] == -1]
        if not roots:
            return None

        # Build enhanced tree
        return self._build_enhanced_tree(roots[0], node_map, solution_index)

    def _build_method_index(self, nodes: List[Dict]):
        """Build index of all method attempts for each task"""
        self.all_methods.clear()

        for node in nodes:
            task_name = node.get('taskName', '')
            if task_name:
                # Extract base task name (without args)
                base_name = task_name.split('(')[0]
                if base_name not in self.all_methods:
                    self.all_methods[base_name] = []
                self.all_methods[base_name].append(node)

    def _build_enhanced_tree(self, node: Dict, node_map: Dict[int, Dict],
                            solution_index: int) -> EnhancedNode:
        """Build an enhanced node tree with failure analysis"""
        node_id = node['nodeID']
        is_operator = node.get('isOperator', False)

        # Determine display name and signature
        signature = node.get('operatorSignature') or node.get('methodSignature') or ''
        if signature:
            name = signature.split('(')[0]
        elif node.get('taskName'):
            name = node['taskName'].split('(')[0]
        else:
            name = '(leaf)'

        # Build bindings (with defensive checks for non-dict values)
        bindings = {}
        for u in node.get('unifiers', []):
            if isinstance(u, dict):
                bindings.update(u)

        condition_bindings = {}
        for cb in node.get('conditionBindings', []):
            if isinstance(cb, dict):
                condition_bindings.update(cb)

        # Determine status
        is_failed = node.get('isFailed', False)
        is_success = node.get('isSuccess', False)

        if is_failed and not is_success:
            status = 'failure'
        elif is_success:
            status = 'success'
        else:
            status = 'default'

        # Build children
        children = []
        for child_id in node.get('childNodeIDs', []):
            if child_id in node_map:
                children.append(self._build_enhanced_tree(
                    node_map[child_id], node_map, solution_index))

        # Create enhanced node
        enhanced = EnhancedNode(
            id=f'sol{solution_index}-node{node_id}',
            name=name,
            full_signature=signature,
            task_name=node.get('taskName', ''),
            is_operator=is_operator,
            status=status,
            bindings=bindings,
            condition_bindings=condition_bindings,
            condition_terms=node.get('conditionTerms', []),
            children=children
        )

        # Analyze failure if failed
        if status == 'failure':
            self._analyze_failure(enhanced, node)

        # Find alternatives tried
        self._find_alternatives(enhanced, node)

        return enhanced

    def _analyze_failure(self, enhanced: EnhancedNode, raw_node: Dict):
        """Analyze why a node failed and populate failure details"""
        raw_reason = raw_node.get('failureReason', '')
        condition_terms = raw_node.get('conditionTerms', [])

        # Categorize the failure
        category = self._categorize_failure(raw_reason, enhanced, raw_node)

        # Build detailed message and suggestions
        message, details, suggestions = self._build_failure_info(
            category, raw_reason, enhanced, raw_node, condition_terms)

        enhanced.failure_detail = FailureDetail(
            category=category,
            message=message,
            details=details,
            suggestions=suggestions
        )

        # Analyze missing facts
        if category == FailureCategory.PRECONDITION_FAILED:
            self._find_missing_facts(enhanced, condition_terms)

    def _categorize_failure(self, raw_reason: str, node: EnhancedNode,
                           raw_node: Dict) -> FailureCategory:
        """Categorize a failure based on available information"""
        reason_lower = raw_reason.lower() if raw_reason else ''

        # Check for specific failure patterns
        if 'no method' in reason_lower or 'no matching' in reason_lower:
            return FailureCategory.NO_MATCHING_METHOD

        if 'precondition' in reason_lower or 'condition' in reason_lower:
            return FailureCategory.PRECONDITION_FAILED

        if 'unif' in reason_lower or 'arity' in reason_lower or 'mismatch' in reason_lower:
            return FailureCategory.UNIFICATION_FAILED

        if 'subtask' in reason_lower or 'child' in reason_lower:
            return FailureCategory.SUBTASK_FAILED

        if 'operator' in reason_lower or 'del' in reason_lower or 'add' in reason_lower:
            return FailureCategory.OPERATOR_FAILED

        if 'backtrack' in reason_lower:
            return FailureCategory.BACKTRACKED

        # Infer from node structure
        if node.is_operator:
            return FailureCategory.OPERATOR_FAILED

        if node.condition_terms:
            return FailureCategory.PRECONDITION_FAILED

        # Check if any children failed
        if any(c.status == 'failure' for c in node.children):
            return FailureCategory.SUBTASK_FAILED

        return FailureCategory.UNKNOWN

    def _build_failure_info(self, category: FailureCategory, raw_reason: str,
                           node: EnhancedNode, raw_node: Dict,
                           conditions: List[str]) -> tuple:
        """Build detailed failure message and suggestions"""
        details = {}
        suggestions = []

        if category == FailureCategory.NO_MATCHING_METHOD:
            message = f"No applicable method found for task '{node.task_name}'"
            suggestions = [
                f"Define a method for '{node.name}' with matching arity",
                "Check that method preconditions can be satisfied",
                "Verify the task name spelling"
            ]

        elif category == FailureCategory.PRECONDITION_FAILED:
            failed_conds = conditions if conditions else ['(unknown conditions)']
            message = f"Precondition failed: {', '.join(failed_conds[:3])}"
            details['conditions'] = conditions
            suggestions = [
                "Add missing facts to the initial state",
                "Create an operator that establishes the required facts",
                "Check for typos in predicate names"
            ]

        elif category == FailureCategory.UNIFICATION_FAILED:
            message = f"Unification failed for '{node.task_name}'"
            suggestions = [
                "Check the number of arguments (arity)",
                "Verify variable types match",
                "Ensure bound variables have compatible values"
            ]

        elif category == FailureCategory.SUBTASK_FAILED:
            failed_children = [c.name for c in node.children if c.status == 'failure']
            message = f"Subtask failed: {', '.join(failed_children[:3])}"
            details['failed_subtasks'] = failed_children
            suggestions = [
                "Check the failed subtask(s) for more details",
                "Ensure subtasks are properly defined",
                "Verify the task decomposition order"
            ]

        elif category == FailureCategory.OPERATOR_FAILED:
            message = f"Operator '{node.name}' could not be applied"
            suggestions = [
                "Check that facts to delete exist in current state",
                "Verify operator preconditions",
                "Ensure variable bindings are correct"
            ]

        elif category == FailureCategory.BACKTRACKED:
            message = "This branch was explored but backtracked due to later failures"
            suggestions = [
                "This node succeeded but a later step failed",
                "Check subsequent tasks in the plan"
            ]

        else:
            message = raw_reason if raw_reason else "Unknown failure reason"
            suggestions = [
                "Check the task definition",
                "Verify all dependencies are met",
                "Enable verbose tracing for more details"
            ]

        return message, details, suggestions

    def _find_missing_facts(self, node: EnhancedNode, conditions: List[str]):
        """Find facts required by conditions that are missing from current state"""
        missing = []
        failed = []

        for cond in conditions:
            # Skip built-in predicates and comparisons
            if self._is_builtin_predicate(cond):
                continue

            # Check if this fact (or a matching pattern) exists
            cond_base = cond.split('(')[0] if '(' in cond else cond

            # Look for matching facts
            found = False
            for fact in self.current_facts:
                fact_base = fact.split('(')[0] if '(' in fact else fact
                if fact_base == cond_base:
                    found = True
                    break

            if not found:
                missing.append(cond)
                failed.append(cond)

        node.missing_facts = missing
        node.failed_conditions = failed

    def _is_builtin_predicate(self, term: str) -> bool:
        """Check if a term is a built-in predicate"""
        builtins = ['=', '\\=', '==', '\\==', '<', '>', '=<', '>=',
                   'is', 'not', '\\+', 'true', 'fail', 'false', '!']
        term_name = term.split('(')[0] if '(' in term else term
        return term_name in builtins

    def _find_alternatives(self, node: EnhancedNode, raw_node: Dict):
        """Find alternative methods that were tried for this task"""
        task_base = node.task_name.split('(')[0] if node.task_name else ''

        if not task_base or task_base not in self.all_methods:
            return

        alternatives = []
        for method_node in self.all_methods[task_base]:
            if method_node['nodeID'] == raw_node['nodeID']:
                continue  # Skip self

            sig = method_node.get('methodSignature') or method_node.get('operatorSignature', '')
            name = sig.split('(')[0] if sig else task_base

            is_success = method_node.get('isSuccess', False)
            is_failed = method_node.get('isFailed', False)

            alternatives.append(AlternativeAttempt(
                method_name=name,
                signature=sig,
                success=is_success and not is_failed,
                failure_reason=method_node.get('failureReason', '') if is_failed else None
            ))

        node.alternatives_tried = alternatives


def analyze_planning_trace(nodes: List[Dict], solution_index: int,
                          initial_facts: List[str] = None) -> Optional[Dict]:
    """
    Convenience function to analyze a planning trace

    Args:
        nodes: Flat list of trace nodes from C++
        solution_index: Index of this solution
        initial_facts: Initial state facts

    Returns:
        Enhanced node tree as dictionary
    """
    analyzer = FailureAnalyzer()
    enhanced = analyzer.analyze_trace(nodes, solution_index, initial_facts)
    return enhanced.to_dict() if enhanced else None


def categorize_failure_reason(reason: str) -> str:
    """Quick categorization of a failure reason string"""
    if not reason:
        return 'UNKNOWN'

    reason_lower = reason.lower()

    if 'no method' in reason_lower or 'no matching' in reason_lower:
        return 'NO_MATCHING_METHOD'
    if 'precondition' in reason_lower or 'condition' in reason_lower:
        return 'PRECONDITION_FAILED'
    if 'unif' in reason_lower or 'arity' in reason_lower:
        return 'UNIFICATION_FAILED'
    if 'subtask' in reason_lower or 'child' in reason_lower:
        return 'SUBTASK_FAILED'
    if 'operator' in reason_lower:
        return 'OPERATOR_FAILED'
    if 'backtrack' in reason_lower:
        return 'BACKTRACKED'

    return 'UNKNOWN'
