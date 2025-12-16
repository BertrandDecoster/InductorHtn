"""
HTN Semantic Analyzer
Deep analysis of HTN rulesets including call graphs, state flow, and invariant checking.
"""

from typing import List, Dict, Set, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum, auto

from htn_parser import parse_htn, Rule, Term, Diagnostic


class NodeType(Enum):
    """Types of nodes in the call graph"""
    METHOD = auto()
    OPERATOR = auto()
    FACT = auto()
    PREDICATE = auto()
    GOAL = auto()


@dataclass
class CallGraphNode:
    """A node in the call graph"""
    key: str  # name/arity
    name: str
    arity: int
    node_type: NodeType
    line: int = 0
    calls: Set[str] = field(default_factory=set)  # outgoing edges
    called_by: Set[str] = field(default_factory=set)  # incoming edges
    # For operators: state changes
    deletes: List[str] = field(default_factory=list)  # patterns deleted
    adds: List[str] = field(default_factory=list)  # patterns added
    # For methods: conditions
    conditions: List[str] = field(default_factory=list)
    # Metadata
    has_else: bool = False
    has_allof: bool = False
    has_anyof: bool = False
    definition_count: int = 1

    def to_dict(self) -> Dict:
        return {
            'key': self.key,
            'name': self.name,
            'arity': self.arity,
            'type': self.node_type.name.lower(),
            'line': self.line,
            'calls': list(self.calls),
            'called_by': list(self.called_by),
            'deletes': self.deletes,
            'adds': self.adds,
            'conditions': self.conditions,
            'has_else': self.has_else,
            'has_allof': self.has_allof,
            'has_anyof': self.has_anyof,
            'definition_count': self.definition_count
        }


@dataclass
class StateFlowEdge:
    """An edge showing state changes between nodes"""
    from_node: str
    to_node: str
    deleted_facts: List[str]
    added_facts: List[str]


@dataclass
class AnalysisResult:
    """Complete analysis result"""
    # Call graph
    nodes: Dict[str, CallGraphNode] = field(default_factory=dict)
    edges: List[Dict] = field(default_factory=list)

    # Reachability
    goals: List[str] = field(default_factory=list)
    reachable: Set[str] = field(default_factory=set)
    unreachable: Set[str] = field(default_factory=set)

    # Cycles
    cycles: List[List[str]] = field(default_factory=list)

    # Issues found
    diagnostics: List[Diagnostic] = field(default_factory=list)

    # State analysis
    initial_facts: List[str] = field(default_factory=list)
    state_changes: Dict[str, Dict] = field(default_factory=dict)  # operator -> {deletes, adds}

    # Invariant violations
    invariant_violations: List[Dict] = field(default_factory=list)

    # Statistics
    stats: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'nodes': {k: v.to_dict() for k, v in self.nodes.items()},
            'edges': self.edges,
            'goals': self.goals,
            'reachable': list(self.reachable),
            'unreachable': list(self.unreachable),
            'cycles': self.cycles,
            'diagnostics': [d.to_dict() for d in self.diagnostics],
            'initial_facts': self.initial_facts,
            'state_changes': self.state_changes,
            'invariant_violations': self.invariant_violations,
            'stats': self.stats
        }


class HtnAnalyzer:
    """Semantic analyzer for HTN rulesets"""

    def __init__(self, source: str):
        self.source = source
        self.rules: List[Rule] = []
        self.result = AnalysisResult()
        self.invariants: List['StateInvariant'] = []

    def analyze(self, invariants: List['StateInvariant'] = None) -> AnalysisResult:
        """Run full semantic analysis"""
        if invariants:
            self.invariants = invariants

        # Parse
        self.rules, parse_errors = parse_htn(self.source)
        self.result.diagnostics.extend(parse_errors)

        # Build call graph
        self._build_call_graph()

        # Extract goals
        self._extract_goals()

        # Compute reachability
        self._compute_reachability()

        # Detect cycles
        self._detect_cycles()

        # Analyze state flow
        self._analyze_state_flow()

        # Check invariants
        self._check_invariants()

        # Compute statistics
        self._compute_stats()

        # Generate edges for visualization
        self._generate_edges()

        return self.result

    def _build_call_graph(self):
        """Build the call graph from parsed rules"""
        for rule in self.rules:
            head_name = rule.head.name
            head_arity = len(rule.head.args)
            key = f"{head_name}/{head_arity}"

            # Determine node type
            node_type = NodeType.GOAL if head_name == 'goals' else \
                       NodeType.METHOD if rule.is_method else \
                       NodeType.OPERATOR if rule.is_operator else \
                       NodeType.FACT if rule.is_fact else NodeType.PREDICATE

            # Get or create node
            if key not in self.result.nodes:
                self.result.nodes[key] = CallGraphNode(
                    key=key,
                    name=head_name,
                    arity=head_arity,
                    node_type=node_type,
                    line=rule.line
                )
            else:
                # Node may have been created by a call reference - update its type
                existing = self.result.nodes[key]
                existing.node_type = node_type
                existing.line = rule.line  # Use the definition line, not call site
                existing.definition_count += 1

            node = self.result.nodes[key]

            # Update modifiers
            if rule.has_else:
                node.has_else = True
            if rule.has_allof:
                node.has_allof = True
            if rule.has_anyof:
                node.has_anyof = True

            # Extract calls from do() clause
            if rule.do_clause:
                for task in rule.do_clause.args:
                    self._extract_calls(key, task)

            # Extract conditions from if() clause
            if rule.if_clause:
                for cond in rule.if_clause.args:
                    cond_str = self._term_to_string(cond)
                    if cond_str:
                        node.conditions.append(cond_str)

            # Extract state changes from del()/add() clauses
            if rule.del_clause:
                for fact in rule.del_clause.args:
                    fact_str = self._term_to_string(fact)
                    if fact_str:
                        node.deletes.append(fact_str)

            if rule.add_clause:
                for fact in rule.add_clause.args:
                    fact_str = self._term_to_string(fact)
                    if fact_str:
                        node.adds.append(fact_str)

            # Track facts
            if rule.is_fact and head_name != 'goals':
                self.result.initial_facts.append(self._term_to_string(rule.head))

    def _extract_calls(self, caller_key: str, task: Term):
        """Extract call relationships from a task term"""
        # Handle try() and first() wrappers
        if task.name in ('try', 'first'):
            for arg in task.args:
                self._extract_calls(caller_key, arg)
            return

        if task.is_variable:
            return

        callee_key = f"{task.name}/{len(task.args)}"

        # Add edge
        if caller_key in self.result.nodes:
            self.result.nodes[caller_key].calls.add(callee_key)

        # Create callee node if doesn't exist
        if callee_key not in self.result.nodes:
            self.result.nodes[callee_key] = CallGraphNode(
                key=callee_key,
                name=task.name,
                arity=len(task.args),
                node_type=NodeType.METHOD,  # Assume method until proven otherwise
                line=task.line
            )

        self.result.nodes[callee_key].called_by.add(caller_key)

    def _term_to_string(self, term: Term) -> str:
        """Convert a term to string representation"""
        if term.is_variable:
            return term.name
        if not term.args:
            return term.name
        args = ', '.join(self._term_to_string(a) for a in term.args)
        return f"{term.name}({args})"

    def _extract_goals(self):
        """Extract goal terms from goals() declarations"""
        for rule in self.rules:
            if rule.head.name == 'goals':
                for arg in rule.head.args:
                    goal_key = f"{arg.name}/{len(arg.args)}"
                    self.result.goals.append(goal_key)

    def _compute_reachability(self):
        """Compute which nodes are reachable from goals"""
        if not self.result.goals:
            # Without goals, consider all methods as potential entry points
            # and mark operators called by them as reachable
            for key, node in self.result.nodes.items():
                if node.node_type == NodeType.METHOD:
                    self.result.reachable.add(key)
                    self._mark_reachable(key)
        else:
            # Start from goals
            for goal in self.result.goals:
                self._mark_reachable(goal)

        # Find unreachable nodes
        for key, node in self.result.nodes.items():
            if node.node_type in (NodeType.METHOD, NodeType.OPERATOR):
                if key not in self.result.reachable:
                    self.result.unreachable.add(key)
                    self.result.diagnostics.append(Diagnostic(
                        node.line, 1, len(node.name), 'warning',
                        f"{'Method' if node.node_type == NodeType.METHOD else 'Operator'} "
                        f"'{node.name}' is not reachable from any goal",
                        'ANA001'
                    ))

    def _mark_reachable(self, key: str):
        """Recursively mark nodes as reachable"""
        if key in self.result.reachable:
            return
        self.result.reachable.add(key)

        if key in self.result.nodes:
            for callee in self.result.nodes[key].calls:
                self._mark_reachable(callee)

    def _detect_cycles(self):
        """Detect cycles in the call graph"""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        all_cycles: List[List[str]] = []

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            if node in self.result.nodes:
                for callee in self.result.nodes[node].calls:
                    if callee not in visited:
                        dfs(callee, path)
                    elif callee in rec_stack:
                        # Found cycle
                        cycle_start = path.index(callee)
                        cycle = path[cycle_start:] + [callee]
                        # Normalize cycle (start from smallest element)
                        min_idx = cycle.index(min(cycle[:-1]))
                        normalized = cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]]
                        if normalized not in all_cycles:
                            all_cycles.append(normalized)

            path.pop()
            rec_stack.remove(node)

        for node in self.result.nodes:
            if node not in visited:
                dfs(node, [])

        self.result.cycles = all_cycles

        # Add diagnostics for cycles
        for cycle in all_cycles:
            cycle_names = [c.split('/')[0] for c in cycle]
            first_node = cycle[0]
            if first_node in self.result.nodes:
                node = self.result.nodes[first_node]
                self.result.diagnostics.append(Diagnostic(
                    node.line, 1, len(node.name), 'warning',
                    f"Potential infinite recursion: {' -> '.join(cycle_names)}",
                    'ANA002'
                ))

    def _analyze_state_flow(self):
        """Analyze how state flows through operators"""
        for key, node in self.result.nodes.items():
            if node.node_type == NodeType.OPERATOR:
                self.result.state_changes[key] = {
                    'deletes': node.deletes,
                    'adds': node.adds,
                    'net_effect': self._compute_net_effect(node.deletes, node.adds)
                }

    def _compute_net_effect(self, deletes: List[str], adds: List[str]) -> str:
        """Compute a human-readable net effect description"""
        effects = []
        if deletes:
            effects.append(f"-{{{', '.join(deletes)}}}")
        if adds:
            effects.append(f"+{{{', '.join(adds)}}}")
        return ' '.join(effects) if effects else '(no state change)'

    def _check_invariants(self):
        """Check state invariants against operators"""
        for invariant in self.invariants:
            for key, node in self.result.nodes.items():
                if node.node_type == NodeType.OPERATOR:
                    violation = invariant.check_operator(
                        node.name,
                        node.deletes,
                        node.adds,
                        self.result.initial_facts
                    )
                    if violation:
                        self.result.invariant_violations.append({
                            'invariant': invariant.name,
                            'operator': key,
                            'line': node.line,
                            'message': violation
                        })
                        self.result.diagnostics.append(Diagnostic(
                            node.line, 1, len(node.name), 'warning',
                            f"Invariant '{invariant.name}' may be violated: {violation}",
                            'INV001'
                        ))

    def _compute_stats(self):
        """Compute analysis statistics"""
        self.result.stats = {
            'total_rules': len(self.rules),
            'methods': sum(1 for n in self.result.nodes.values()
                          if n.node_type == NodeType.METHOD),
            'operators': sum(1 for n in self.result.nodes.values()
                            if n.node_type == NodeType.OPERATOR),
            'facts': len(self.result.initial_facts),
            'goals': len(self.result.goals),
            'reachable': len(self.result.reachable),
            'unreachable': len(self.result.unreachable),
            'cycles': len(self.result.cycles),
            'invariant_violations': len(self.result.invariant_violations),
            'errors': sum(1 for d in self.result.diagnostics if d.severity == 'error'),
            'warnings': sum(1 for d in self.result.diagnostics if d.severity == 'warning')
        }

    def _generate_edges(self):
        """Generate edge list for visualization"""
        for key, node in self.result.nodes.items():
            for callee in node.calls:
                self.result.edges.append({
                    'from': key,
                    'to': callee,
                    'type': 'calls'
                })


class StateInvariant:
    """A state invariant that can be checked against operators"""

    def __init__(self, name: str, description: str,
                 check_fn: Callable[[str, List[str], List[str], List[str]], Optional[str]]):
        """
        Args:
            name: Short identifier
            description: Human-readable description
            check_fn: Function(operator_name, deletes, adds, initial_facts) -> violation_message or None
        """
        self.name = name
        self.description = description
        self.check_fn = check_fn

    def check_operator(self, operator_name: str, deletes: List[str],
                       adds: List[str], initial_facts: List[str]) -> Optional[str]:
        """Check if an operator might violate this invariant"""
        try:
            return self.check_fn(operator_name, deletes, adds, initial_facts)
        except Exception as e:
            return f"Error checking invariant: {e}"


def analyze_htn(source: str, invariants: List[StateInvariant] = None) -> Dict:
    """Convenience function to analyze HTN source"""
    analyzer = HtnAnalyzer(source)
    result = analyzer.analyze(invariants or [])
    return result.to_dict()


def analyze_file(file_path: str, invariants: List[StateInvariant] = None) -> Dict:
    """Analyze an HTN file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    return analyze_htn(source, invariants)


# Predefined invariants for common game patterns

def create_single_position_invariant() -> StateInvariant:
    """Create an invariant that checks for duplicate positions"""
    def check(op_name: str, deletes: List[str], adds: List[str],
              initial_facts: List[str]) -> Optional[str]:
        # Check if operator adds position without deleting old one
        import re
        add_positions = [a for a in adds if re.match(r'at\([^,]+,', a)]
        del_positions = [d for d in deletes if re.match(r'at\([^,]+,', d)]

        if add_positions and not del_positions:
            return f"Adds position {add_positions[0]} without removing old position"
        return None

    return StateInvariant(
        'single_position',
        'Each unit can only be at one position',
        check
    )


def create_no_orphan_units_invariant() -> StateInvariant:
    """Create an invariant that checks for units without positions"""
    def check(op_name: str, deletes: List[str], adds: List[str],
              initial_facts: List[str]) -> Optional[str]:
        import re
        # Check if operator deletes position without deleting unit
        for d in deletes:
            match = re.match(r'at\(([^,]+),', d)
            if match:
                unit = match.group(1)
                # Check if unit is also being deleted or moved
                unit_deleted = any(unit in delt for delt in deletes if 'unit(' in delt)
                unit_moved = any(unit in addt for addt in adds if 'at(' in addt)
                if not unit_deleted and not unit_moved:
                    return f"Removes position of {unit} without moving or deleting it"
        return None

    return StateInvariant(
        'no_orphan_units',
        'Units must always have a position',
        check
    )


# Default invariants
DEFAULT_INVARIANTS = [
    create_single_position_invariant(),
    create_no_orphan_units_invariant(),
]
