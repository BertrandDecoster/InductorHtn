"""Per-plan causal graphs: is this plan a combo, or a chore?

A plan of eight operators that could be executed in any order is a to-do
list. A plan where operator 1 creates the condition operator 4 needs, which
creates what operator 7 needs, is the Primer -> Catalyst -> Detonator chain
the GDD is built around. Both have length 8; only one is satisfying.

The graph is built from two kinds of evidence:

  - **effect links** - operator i adds a fact operator j deletes;
  - **precondition links** - operator i adds a fact that some method ancestor
    of operator j consumed as a grounded condition, evaluated *after* i ran.

Preconditions live on methods, not operators, in HTN - so the second kind is
what carries almost all the signal, and it is only available because the
decomposition path carries `conditionTerms` plus the bindings that ground
them.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from .extract import Plan, normalize_fact

# Condition functors that never denote a consumed fact: negation, control,
# comparison and arithmetic. A `not(at(x,y))` condition is not satisfied *by*
# an operator adding `at(x,y)` - it is broken by it.
_NON_FACT_FUNCTORS = {
    "not", "\\+", "==", "\\==", "=", "\\=", "<", ">", "=<", ">=", "=:=", "=\\=",
    "is", "!", "or", "call", "findall", "bagof", "setof",
    "forall", "count", "distinct", "sortBy", "atomic", "var", "nonvar",
}

# Wrappers whose arguments are ordinary conditions: `first(and(a, b))` still
# consumes `a` and `b`.
_TRANSPARENT_FUNCTORS = {"first", "and"}


@dataclass
class CausalGraph:
    """Operator-level DAG for one plan."""

    edges: Set[Tuple[int, int]] = field(default_factory=set)
    operator_count: int = 0
    reasons: Dict[Tuple[int, int], str] = field(default_factory=dict)

    def successors(self, i: int) -> Set[int]:
        return {b for a, b in self.edges if a == i}

    @property
    def depth(self) -> int:
        """Longest chain, counted in operators. A lone operator scores 1."""
        if self.operator_count == 0:
            return 0
        best = [1] * self.operator_count
        for i in range(self.operator_count):
            for a, b in sorted(self.edges):
                if b == i and a < i:
                    best[i] = max(best[i], best[a] + 1)
        return max(best)

    @property
    def interlock(self) -> float:
        """Fraction of operators on at least one causal edge.

        A proxy for "causally necessary": participation, not necessity. An
        operator on an edge may still be removable; proving otherwise needs a
        re-plan per operator, which is deliberately out of scope.
        """
        if self.operator_count == 0:
            return 0.0
        touched: Set[int] = set()
        for a, b in self.edges:
            touched.add(a)
            touched.add(b)
        return len(touched) / self.operator_count

    @property
    def insight_depth(self) -> int:
        """Operators whose effect is first consumed >= 2 steps later.

        A setup move you must plan ahead for. Greedy play finds a chain of
        immediate consequences; it does not find the move that only pays off
        three actions later.
        """
        count = 0
        for i in range(self.operator_count):
            gaps = [b - i for a, b in self.edges if a == i and b > i]
            if gaps and min(gaps) >= 2:
                count += 1
        return count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operator_count": self.operator_count,
            "edges": sorted(list(self.edges)),
            "depth": self.depth,
            "interlock": self.interlock,
            "insight_depth": self.insight_depth,
        }


# --------------------------------------------------------------------------
# Grounding tree conditions
# --------------------------------------------------------------------------

def node_bindings(node: Dict[str, Any]) -> Dict[str, str]:
    """Merge a tree node's `unifiers` and `conditionBindings` into one map.

    Both are lists of single-entry dicts keyed by `?name`.
    """
    out: Dict[str, str] = {}
    for group in ("unifiers", "conditionBindings"):
        for entry in node.get(group) or []:
            if isinstance(entry, dict):
                for key, value in entry.items():
                    out[str(key)] = str(value)
    return out


def _render_condition(term: Dict[str, Any], bindings: Dict[str, str]) -> Optional[str]:
    """Render a `conditionTerms` entry with `bindings` applied.

    A variable with no binding is kept as `?name`, so the result is a
    *pattern* rather than a ground fact. `allOf`/`anyOf` nodes record no
    condition bindings at all - the planner merges their resolutions - and
    dropping their conditions would hide exactly the consequences those
    methods exist to apply (everyone in the sludge is snared). A pattern is
    matched against operator effects by `matches_pattern`.
    """
    if not isinstance(term, dict):
        return None
    functor = term.get("functor", "")
    if term.get("isVariable"):
        value = bindings.get(f"?{functor}")
        return normalize_fact(value) if value else f"?{functor}"
    args = term.get("args") or []
    if not args:
        return functor
    parts: List[str] = []
    for arg in args:
        rendered = _render_condition(arg, bindings)
        if rendered is None:
            return None
        parts.append(rendered)
    return f"{functor}({','.join(parts)})"


def _flatten_conditions(terms: Sequence[Any]) -> List[Dict[str, Any]]:
    """Unwrap transparent wrappers, drop control/negation terms."""
    out: List[Dict[str, Any]] = []
    for term in terms:
        if not isinstance(term, dict):
            continue
        functor = term.get("functor")
        if functor in _TRANSPARENT_FUNCTORS:
            out.extend(_flatten_conditions(term.get("args") or []))
        elif functor in _NON_FACT_FUNCTORS:
            continue
        else:
            out.append(term)
    return out


def grounded_conditions(node: Dict[str, Any]) -> Set[str]:
    """The facts (or fact patterns) a method node's `if()` clause consumed."""
    bindings = node_bindings(node)
    out: Set[str] = set()
    for term in _flatten_conditions(node.get("conditionTerms") or []):
        rendered = _render_condition(term, bindings)
        if rendered:
            out.add(normalize_fact(rendered))
    return out


def matches_pattern(pattern: str, fact: str) -> bool:
    """`regionHas(corridor,?feat)` matches `regionHas(corridor,sludge)`."""
    if "?" not in pattern:
        return pattern == fact
    if pattern.find("(") != fact.find("(") or pattern[: pattern.find("(")] != fact[: fact.find("(")]:
        return False
    from .extract import split_args

    p_args = split_args(pattern[pattern.find("(") + 1: pattern.rfind(")")])
    f_args = split_args(fact[fact.find("(") + 1: fact.rfind(")")])
    if len(p_args) != len(f_args):
        return False
    return all(p.startswith("?") or p == f for p, f in zip(p_args, f_args))


def _overlap(added: Set[str], conditions: Set[str]) -> Set[str]:
    """The added facts some condition (ground or pattern) consumes."""
    ground = {c for c in conditions if "?" not in c}
    patterns = [c for c in conditions if "?" in c]
    hit = added & ground
    if patterns:
        for fact in added:
            if fact in hit:
                continue
            if any(matches_pattern(p, fact) for p in patterns):
                hit.add(fact)
    return hit


# --------------------------------------------------------------------------
# Graph construction
# --------------------------------------------------------------------------

def build_causal_graph(plan: Plan, initial_facts: Sequence[str] = ()) -> CausalGraph:
    """Build the operator DAG for one plan.

    Three edge kinds, in decreasing strength of evidence:

    1. **consumes** - i adds a fact j deletes. Unambiguous.
    2. **enables** - i adds a fact consumed by a method ancestor of j whose
       condition was evaluated *after* i ran (compared by visit order, which
       path reconstruction has shown agrees with operator order).
    3. **provides** - i is the *first* producer of a fact that was not true
       initially, and some method ancestor of j consumed it. This catches the
       dependency HTN hides: methods check their conditions top-down, before
       their subtasks run, so a plan that acquires a skill and then uses it
       has no re-check to observe. The world still requires i before j.

    Without (3) this domain's `causal_depth` would read ~2 for every plan -
    not because the plans are shallow but because operators here are
    unconditional and ordering is expressed structurally.
    """
    graph = CausalGraph(operator_count=len(plan.operators))
    if not plan.operators:
        return graph

    ordered = sorted(plan.path, key=lambda n: n.get("treeNodeID", 0))
    by_id = {n.get("treeNodeID"): n for n in ordered}

    # rank = position in visit order; operator ranks map onto plan indices.
    rank = {n.get("treeNodeID"): i for i, n in enumerate(ordered)}
    op_index_of_rank: Dict[int, int] = {}
    seq = 0
    for node in ordered:
        if node.get("isOperator"):
            if seq < len(plan.operators):
                op_index_of_rank[rank[node.get("treeNodeID")]] = seq
            seq += 1

    # For each operator: the conditions its method ancestors consumed, tagged
    # with the rank at which each ancestor was evaluated.
    enabling: Dict[int, List[Tuple[int, Set[str]]]] = {}
    for node in ordered:
        if not node.get("isOperator"):
            continue
        node_rank = rank[node.get("treeNodeID")]
        op_index = op_index_of_rank.get(node_rank)
        if op_index is None:
            continue
        chain: List[Tuple[int, Set[str]]] = []
        cursor = by_id.get(node.get("parentNodeID"))
        while cursor is not None:
            conditions = grounded_conditions(cursor)
            if conditions:
                chain.append((rank.get(cursor.get("treeNodeID"), -1), conditions))
            cursor = by_id.get(cursor.get("parentNodeID"))
        enabling[op_index] = chain

    added_by = [set(op.adds) for op in plan.operators]
    deleted_by = [set(op.dels) for op in plan.operators]
    op_rank = {v: k for k, v in op_index_of_rank.items()}
    initial = set(initial_facts)

    # First producer of each fact that was not already true. Only the first
    # producer earns a "provides" edge - a later re-add of the same fact did
    # not make it available.
    first_producer: Dict[str, int] = {}
    for i, adds in enumerate(added_by):
        for fact in adds:
            if fact not in initial and fact not in first_producer:
                first_producer[fact] = i

    for i in range(len(plan.operators)):
        if not added_by[i]:
            continue
        rank_i = op_rank.get(i, i)
        for j in range(i + 1, len(plan.operators)):
            shared_effect = added_by[i] & deleted_by[j]
            if shared_effect:
                graph.edges.add((i, j))
                graph.reasons[(i, j)] = f"consumes {sorted(shared_effect)[0]}"
                continue
            edge_reason: Optional[str] = None
            for cond_rank, conditions in enabling.get(j, []):
                overlap = _overlap(added_by[i], conditions)
                if not overlap:
                    continue
                if cond_rank > rank_i:
                    edge_reason = f"enables {sorted(overlap)[0]}"
                    break
                provided = {f for f in overlap if first_producer.get(f) == i}
                if provided and edge_reason is None:
                    edge_reason = f"provides {sorted(provided)[0]}"
            if edge_reason:
                graph.edges.add((i, j))
                graph.reasons[(i, j)] = edge_reason

    return graph


def decomposition_depth(plan: Plan) -> int:
    """Deepest method nesting on the plan's path."""
    by_id = {n.get("treeNodeID"): n for n in plan.path}
    best = 0
    for node in plan.path:
        depth = 0
        cursor: Optional[Dict[str, Any]] = node
        while cursor is not None:
            parent = by_id.get(cursor.get("parentNodeID"))
            if parent is None:
                break
            depth += 1
            cursor = parent
        best = max(best, depth)
    return best


def intermediate_states(plan: Plan, initial: Sequence[str]) -> List[Set[str]]:
    """World state after each step: `[state_0, state_1, ..., state_n]`.

    Replaying the plan's del/add reproduces exactly what the planner reports
    as the final state (asserted against `GetSolutionFacts` in the test
    suite), which is what makes step-by-step inspection possible at all - the
    planner itself only exposes the endpoints.
    """
    from .extract import replay_states

    return replay_states(initial, plan.operators)
