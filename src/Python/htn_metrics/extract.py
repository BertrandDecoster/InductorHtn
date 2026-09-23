"""One planning run -> a `PlanSpace`.

This is the single source of raw data for every metric family. Nothing here
judges a level; it only assembles what the planner and the AST know into one
JSON-serializable object:

  - the level's declared facts, rules and goals (split so a perturbed copy of
    the world can be rebuilt for counterfactuals),
  - every plan, with its ground operators, decomposition tree, and the
    del/add effect of each operator,
  - the mechanism (owning component) and layer of every operator and method,
  - whether the plan space was truncated.

The del/add grounding is what closes the "intermediate state" gap: given a
plan, `Plan.state_at(i)` replays the world forward operator by operator.
"""

import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

# --------------------------------------------------------------------------
# Lazy imports of the sibling packages. htn_metrics is imported both as
# `htn_metrics.x` (PYTHONPATH=src/Python) and from the CLI, so we resolve the
# project root from this file rather than the cwd.
# --------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))

# Bump when the meaning of anything a cached probe records changes (what a
# fingerprint is, how effects are grounded, how truncation is reported).
EXTRACTOR_VERSION = 2

KNOWN_LAYER_DIRS = ("primitives", "actions", "strategies", "goals", "levels")
_LAYER_SINGULAR_TO_PLURAL = {
    "primitive": "primitives",
    "action": "actions",
    "strategy": "strategies",
    "goal": "goals",
    "level": "levels",
}


def _import_parse_htn():
    backend = os.path.join(PROJECT_ROOT, "gui", "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from htn_parser import parse_htn  # type: ignore
    return parse_htn


def _import_planner():
    py_dir = os.path.join(PROJECT_ROOT, "src", "Python")
    if py_dir not in sys.path:
        sys.path.insert(0, py_dir)
    from indhtnpy import HtnPlanner, termToString  # type: ignore
    return HtnPlanner, termToString


class ExtractError(Exception):
    """Raised when a level cannot be planned into a PlanSpace."""


# ==========================================================================
# Source splitting: facts vs. everything else
# ==========================================================================

def split_statements(source: str) -> List[str]:
    """Split HTN source into top-level statements, keeping original text.

    Splits on a period at paren/bracket depth 0 that is not inside a quoted
    atom and not a decimal point. Comments (`%` to end of line) are stripped,
    since they would otherwise attach to whichever statement follows.
    """
    statements: List[str] = []
    buf: List[str] = []
    depth = 0
    quote: Optional[str] = None
    i = 0
    n = len(source)

    while i < n:
        ch = source[i]

        if quote is not None:
            buf.append(ch)
            if ch == "\\" and i + 1 < n:
                buf.append(source[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue

        if ch == "%":
            while i < n and source[i] != "\n":
                i += 1
            continue

        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            i += 1
            continue

        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1

        if ch == "." and depth == 0:
            # A decimal point sits between two digits; a terminator does not.
            prev = source[i - 1] if i > 0 else " "
            nxt = source[i + 1] if i + 1 < n else "\n"
            if prev.isdigit() and nxt.isdigit():
                buf.append(ch)
                i += 1
                continue
            text = "".join(buf).strip()
            if text:
                statements.append(text + ".")
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


@dataclass
class LevelSpec:
    """A level's source, split so a perturbed world can be rebuilt."""

    level_id: str
    path: str
    facts: List[str]                 # ground fact statements, no trailing '.'
    other_source: str                # rules/methods/operators, verbatim
    goals: List[str]                 # goal terms, no trailing '.'
    dependencies: List[str]

    def source_hash(self) -> str:
        payload = json.dumps(
            {"f": sorted(self.facts), "o": self.other_source, "g": self.goals,
             "d": sorted(self.dependencies)},
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def render(self, facts: Optional[Sequence[str]] = None,
               goals: Optional[Sequence[str]] = None) -> str:
        """Re-emit level source with a (possibly perturbed) fact set."""
        use_facts = self.facts if facts is None else list(facts)
        use_goals = self.goals if goals is None else list(goals)
        parts = [f"{f}." for f in use_facts]
        if self.other_source.strip():
            parts.append(self.other_source)
        parts += [f"goals({g})." for g in use_goals]
        return "\n".join(parts) + "\n"


def load_level_spec(level_path: str) -> LevelSpec:
    """Parse a level directory's `level.htn` and `manifest.json`."""
    full_path = _resolve_level_dir(level_path)
    level_htn = os.path.join(full_path, "level.htn")
    if not os.path.exists(level_htn):
        raise ExtractError(f"No level.htn in {full_path}")

    with open(level_htn, "r", encoding="utf-8") as f:
        source = f.read()

    parse_htn = _import_parse_htn()

    facts: List[str] = []
    goals: List[str] = []
    other: List[str] = []

    for stmt in split_statements(source):
        rules, _diags = parse_htn(stmt)
        rule = rules[0] if rules else None
        if rule is None or rule.head is None:
            other.append(stmt)
            continue
        if rule.head.name == "goals":
            for arg in rule.head.args:
                goals.append(repr(arg))
            continue
        if rule.is_fact:
            facts.append(normalize_fact(stmt.rstrip().rstrip(".")))
        else:
            other.append(stmt)

    dependencies: List[str] = []
    manifest_path = os.path.join(full_path, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            dependencies = json.load(f).get("dependencies", [])

    return LevelSpec(
        level_id=os.path.basename(os.path.normpath(full_path)),
        path=full_path,
        facts=facts,
        other_source="\n".join(other),
        goals=goals,
        dependencies=dependencies,
    )


def _resolve_level_dir(level_path: str) -> str:
    if os.path.isabs(level_path) and os.path.isdir(level_path):
        return level_path
    for candidate in (
        os.path.join(PROJECT_ROOT, level_path),
        os.path.join(PROJECT_ROOT, "levels", level_path),
        os.path.join(PROJECT_ROOT, "levels", os.path.basename(level_path)),
        os.path.join(PROJECT_ROOT, "tests", "fun_fixtures", level_path),
        os.path.abspath(level_path),
    ):
        if os.path.isdir(candidate):
            return candidate
    raise ExtractError(f"Level not found: {level_path}")


# ==========================================================================
# Operator effect templates (del/add) from component ASTs
# ==========================================================================

@dataclass
class OperatorTemplate:
    """An operator's del/add clauses, ready to be grounded against a call."""

    name: str
    arity: int
    head_args: List[Any]           # parser Terms
    dels: List[Any]
    adds: List[Any]
    component: str

    @property
    def signature(self) -> str:
        return f"{self.name}/{self.arity}"


def split_args(inner: str) -> List[str]:
    """Split an argument list on top-level commas, stripped, empties dropped."""
    parts: List[str] = []
    depth = 0
    buf: List[str] = []
    for ch in inner:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    if buf:
        parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def normalize_fact(text: str) -> str:
    """Render a fact the way the planner's `GetStateFacts` does.

    The planner emits `at(player,arena)` with no spaces, while the AST
    pretty-printer emits `at(player, arena)`. Facts are compared as strings
    across both sources - by del/add replay, by ablation, by loadout
    perturbation - so they must agree exactly. Whitespace inside quoted atoms
    is preserved.
    """
    out: List[str] = []
    quote: Optional[str] = None
    for ch in text:
        if quote is not None:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            continue
        if ch.isspace():
            continue
        out.append(ch)
    return "".join(out)


def _term_text(term: Any, bindings: Dict[str, str]) -> Tuple[str, bool]:
    """Render a parser Term with `bindings` applied.

    Returns (text, fully_ground). `fully_ground` is False when a variable
    survived substitution, which happens for operators whose del/add mention
    a variable not bound by the head (rare, and never causally linked).
    """
    if getattr(term, "is_variable", False):
        if term.name in bindings:
            return bindings[term.name], True
        return term.name, False
    if not term.args:
        return term.name, True
    parts, ground = [], True
    for arg in term.args:
        text, arg_ground = _term_text(arg, bindings)
        parts.append(text)
        ground = ground and arg_ground
    if getattr(term, "is_list", False):
        return "[" + ",".join(parts) + "]", ground
    return f"{term.name}({','.join(parts)})", ground


def collect_operator_templates(
    sources: Sequence[Tuple[str, str]],
) -> Dict[str, OperatorTemplate]:
    """Parse component sources into `signature -> OperatorTemplate`."""
    parse_htn = _import_parse_htn()
    out: Dict[str, OperatorTemplate] = {}
    for component, text in sources:
        rules, _diags = parse_htn(text)
        for rule in rules:
            if not rule.is_operator or rule.head is None:
                continue
            dels = list(rule.del_clause.args) if rule.del_clause else []
            adds = list(rule.add_clause.args) if rule.add_clause else []
            tmpl = OperatorTemplate(
                name=rule.head.name,
                arity=len(rule.head.args),
                head_args=list(rule.head.args),
                dels=dels,
                adds=adds,
                component=component,
            )
            out[tmpl.signature] = tmpl
    return out


# ==========================================================================
# Plans
# ==========================================================================

@dataclass
class OperatorInstance:
    """One ground operator in a plan, with its resolved effects."""

    text: str
    name: str
    args: List[str]
    mechanism: str                   # owning component, or "?" if unknown
    dels: List[str] = field(default_factory=list)
    adds: List[str] = field(default_factory=list)
    effects_resolved: bool = True    # False if a del/add stayed unground

    @property
    def signature(self) -> str:
        return f"{self.name}/{len(self.args)}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text, "name": self.name, "args": self.args,
            "mechanism": self.mechanism, "dels": self.dels, "adds": self.adds,
            "effects_resolved": self.effects_resolved,
        }


@dataclass
class Plan:
    """One solution: its operators plus the decomposition path that produced it.

    `path` is *this plan's* decomposition, not the raw tree. `GetDecompositionTree(i)`
    returns everything the planner explored up to and including solution i -
    including branches belonging to other solutions - so the raw tree would
    make every plan look like it used every strategy. See
    `_reconstruct_path` for how the plan's own path is isolated.
    """

    index: int
    operators: List[OperatorInstance]
    path: List[Dict[str, Any]] = field(default_factory=list)
    explored_nodes: int = 0      # nodes newly explored for this solution
    dead_end_nodes: int = 0      # of those, ones marked isFailed

    @property
    def length(self) -> int:
        return len(self.operators)

    def operator_names(self) -> List[str]:
        return [op.name for op in self.operators]

    def mechanisms(self) -> Set[str]:
        return {op.mechanism for op in self.operators if op.mechanism != "?"}

    def state_at(self, step: int, initial: Sequence[str]) -> Set[str]:
        """World state after `step` operators have executed.

        step 0 is the initial state; step == len(operators) is the final one.
        Replaying del/add is what makes intermediate states available at all -
        the planner only exposes the initial and final fact sets.
        """
        state = set(initial)
        for op in self.operators[: max(0, step)]:
            for fact in op.dels:
                state.discard(fact)
            for fact in op.adds:
                state.add(fact)
        return state

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "operators": [op.to_dict() for op in self.operators],
            "path": self.path,
            "explored_nodes": self.explored_nodes,
            "dead_end_nodes": self.dead_end_nodes,
        }


@dataclass
class PlanSpace:
    """Everything one planning run knows about a level."""

    level_id: str
    goal: str
    initial_facts: List[str]
    plans: List[Plan]
    operator_owner: Dict[str, str]
    method_layer: Dict[str, str]           # "name/arity" -> layer of definer
    component_layer: Dict[str, str]        # component path -> layer
    truncated: bool = False
    truncation_reason: str = ""
    resolution_steps: int = -1
    spec: Optional[LevelSpec] = None
    notes: List[str] = field(default_factory=list)
    sources: List[Tuple[str, str]] = field(default_factory=list)
    facts_used: List[str] = field(default_factory=list)  # level facts as compiled

    @property
    def plan_count(self) -> int:
        return len(self.plans)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level_id": self.level_id,
            "goal": self.goal,
            "initial_facts": self.initial_facts,
            "plans": [p.to_dict() for p in self.plans],
            "operator_owner": self.operator_owner,
            "method_layer": self.method_layer,
            "component_layer": self.component_layer,
            "truncated": self.truncated,
            "truncation_reason": self.truncation_reason,
            "resolution_steps": self.resolution_steps,
            "notes": self.notes,
        }


# ==========================================================================
# Extraction
# ==========================================================================

def layer_of_component(component_path: str, manifest_layer: str = "") -> str:
    """Layer name (plural, matching the directory convention) for a component.

    The path is authoritative because it is unambiguous - `gamehack/actions/x`
    is an action even though `actions` is not one of the manifest's four
    `VALID_LAYERS`. The manifest is only a fallback.
    """
    for part in component_path.replace("\\", "/").split("/"):
        if part in KNOWN_LAYER_DIRS:
            return part
    if manifest_layer:
        return _LAYER_SINGULAR_TO_PLURAL.get(manifest_layer, manifest_layer)
    return "unknown"


class LevelPlanner:
    """Builds a planner for a level, optionally with a perturbed fact set.

    Kept as a class so `counterfactual.py` can reuse component loading (which
    is the expensive part) while swapping only the level facts.
    """

    def __init__(self, spec: LevelSpec, memory_budget: int = 0):
        self.spec = spec
        self.memory_budget = memory_budget

    def build(self, facts: Optional[Sequence[str]] = None,
              goals: Optional[Sequence[str]] = None):
        """Return (planner, loader) with components + level source compiled."""
        HtnPlanner, _ = _import_planner()
        sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "Python"))
        from htn_components.loader import ComponentLoader, LoadError  # type: ignore

        planner = HtnPlanner(False)
        if self.memory_budget:
            planner.SetMemoryBudget(self.memory_budget)

        loader = ComponentLoader(planner, PROJECT_ROOT, warn=lambda _m: None)
        try:
            for dep in self.spec.dependencies:
                loader.load(dep)
        except LoadError as exc:
            raise ExtractError(str(exc)) from exc

        source = self.spec.render(facts=facts, goals=goals)
        error = planner.HtnCompileCustomVariables(source)
        if error:
            raise ExtractError(f"Compile error in synthesized level: {error}")
        return planner, loader


def extract_plan_space(
    level_path: str,
    goal: Optional[str] = None,
    max_plans: int = 5000,
    memory_budget: int = 0,
    facts: Optional[Sequence[str]] = None,
    spec: Optional[LevelSpec] = None,
) -> PlanSpace:
    """Plan a level once and package everything the metrics need.

    `facts` overrides the level's own fact set (used by counterfactuals).
    `goal` overrides the level's `goals()` directive.
    """
    spec = spec or load_level_spec(level_path)
    builder = LevelPlanner(spec, memory_budget=memory_budget)
    planner, loader = builder.build(facts=facts)

    _, term_to_string = _import_planner()

    error, facts_json = planner.GetStateFacts()
    if error:
        raise ExtractError(f"Could not read state facts: {error}")
    initial_facts = [normalize_fact(f) for f in json.loads(facts_json)]

    if goal is None:
        if not spec.goals:
            raise ExtractError(f"No goals() directive in {spec.path}")
        goal = spec.goals[0]
    goal_query = goal if goal.rstrip().endswith(".") else goal + "."

    notes: List[str] = []
    truncated = False
    truncation_reason = ""

    error, result = planner.FindAllPlansCustomVariables(goal_query)
    if error:
        # An out-of-memory error still yields whatever was found so far, but
        # metrics over a partial space are meaningless - flag hard.
        if "out of memory" in error.lower():
            return PlanSpace(
                level_id=spec.level_id, goal=goal, initial_facts=initial_facts,
                plans=[], operator_owner=loader.operator_owner,
                method_layer={}, component_layer={},
                truncated=True,
                truncation_reason=f"planner ran out of memory: {error}",
                spec=spec, notes=notes,
            )
        raise ExtractError(f"Planning failed: {error}")

    raw_solutions = json.loads(result)
    if not raw_solutions or (
        isinstance(raw_solutions[0], dict) and "false" in raw_solutions[0]
    ):
        raw_solutions = []

    if len(raw_solutions) > max_plans:
        truncated = True
        truncation_reason = (
            f"plan count {len(raw_solutions)} exceeded cap max_plans={max_plans}"
        )
        raw_solutions = raw_solutions[:max_plans]

    all_sources = list(loader.sources) + [(f"levels/{spec.level_id}", spec.render(facts=facts))]
    templates = collect_operator_templates(all_sources)
    operator_owner = dict(loader.operator_owner)
    for sig, tmpl in templates.items():
        operator_owner.setdefault(sig, tmpl.component)
    component_layer = {c: layer_of_component(c) for c, _ in loader.sources}
    method_layer: Dict[str, str] = {}
    for sig, owners in loader.method_owners.items():
        if owners:
            method_layer[sig] = component_layer.get(
                owners[-1], layer_of_component(owners[-1])
            )

    # Methods defined in level.htn itself belong to the "levels" layer. A
    # self-contained level (a fixture, or puzzle1's goal composition) puts its
    # strategy alternatives here rather than in a component, and those
    # alternatives are exactly what distinguishes one idea from another.
    level_source = spec.render(facts=facts)
    parse_htn = _import_parse_htn()
    level_rules, _diags = parse_htn(level_source)
    for rule in level_rules:
        if rule.is_method and rule.head is not None:
            method_layer[f"{rule.head.name}/{len(rule.head.args)}"] = "levels"

    plans: List[Plan] = []
    unresolved_ops: Set[str] = set()
    previous_ids: Set[int] = set()
    path_mismatches = 0

    for idx, raw in enumerate(raw_solutions):
        op_terms = raw if isinstance(raw, list) else []
        operators: List[OperatorInstance] = []
        for term in op_terms:
            inst = _ground_operator(
                term, term_to_string, templates, operator_owner
            )
            if not inst.effects_resolved:
                unresolved_ops.add(inst.signature)
            operators.append(inst)

        tree: List[Dict[str, Any]] = []
        tree_err, tree_json = planner.GetDecompositionTree(idx)
        if not tree_err and tree_json:
            try:
                tree = json.loads(tree_json)
            except json.JSONDecodeError:
                tree = []

        path, new_ids, dead_ends = _reconstruct_path(tree, operators, previous_ids)
        previous_ids |= new_ids

        plan = Plan(
            index=idx, operators=operators, path=path,
            explored_nodes=len(new_ids), dead_end_nodes=dead_ends,
        )
        if not _path_matches_operators(plan):
            path_mismatches += 1
        plans.append(plan)

    if path_mismatches:
        notes.append(
            f"decomposition path could not be reconciled with the operator "
            f"sequence for {path_mismatches}/{len(plans)} plans; strategy "
            f"fingerprints for those plans may be coarse"
        )

    if unresolved_ops:
        notes.append(
            "operators with unground del/add effects (excluded from causal "
            "analysis): " + ", ".join(sorted(unresolved_ops))
        )

    steps = -1
    try:
        steps = planner.GetLastResolutionStepCount()
    except Exception:  # pragma: no cover - build without step tracking
        steps = -1

    return PlanSpace(
        level_id=spec.level_id,
        goal=goal,
        initial_facts=initial_facts,
        plans=plans,
        operator_owner=operator_owner,
        method_layer=method_layer,
        component_layer=component_layer,
        truncated=truncated,
        truncation_reason=truncation_reason,
        resolution_steps=steps,
        spec=spec,
        notes=notes,
        sources=all_sources,
        facts_used=list(facts) if facts is not None else list(spec.facts),
    )


def ground_solution(
    solution_terms: Sequence[Any],
    sources: Sequence[Tuple[str, str]],
    operator_owner: Optional[Dict[str, str]] = None,
) -> List[OperatorInstance]:
    """Ground one solution's operator terms against the HTN sources.

    Public entry point for callers that already have a solution from the
    planner and want its per-operator del/add - which is what makes
    intermediate states available. `sources` is (label, htn text) pairs;
    the labels only matter for mechanism attribution.
    """
    _, term_to_string = _import_planner()
    templates = collect_operator_templates(sources)
    owner = operator_owner or {
        sig: tmpl.component for sig, tmpl in templates.items()
    }
    return [
        _ground_operator(term, term_to_string, templates, owner)
        for term in solution_terms
    ]


def replay_states(
    initial_facts: Sequence[str], operators: Sequence[OperatorInstance]
) -> List[Set[str]]:
    """World state after each step: `[state_0, state_1, ..., state_n]`."""
    states = [set(normalize_fact(f) for f in initial_facts)]
    current = states[0]
    for op in operators:
        current = set(current)
        for fact in op.dels:
            current.discard(fact)
        for fact in op.adds:
            current.add(fact)
        states.append(current)
    return states


def replay_with_check(
    initial_facts: Sequence[str],
    operators: Sequence[OperatorInstance],
    expected_final: Optional[Set[str]] = None,
) -> Tuple[List[Set[str]], List[str]]:
    """`replay_states`, plus the warnings that make it honest.

    An operator whose effects could not be grounded (no template among the
    sources, or a del/add variable the head does not bind) is named, and if
    the planner's own final state is supplied the replayed final state is
    compared against it. A silent replay is worse than none: it shows the
    author a world that never happened.
    """
    warnings: List[str] = []
    for i, op in enumerate(operators):
        if not op.effects_resolved:
            warnings.append(
                f"step {i + 1} {op.text}: effects not replayed - no operator "
                f"template was found for {op.signature}, or its del/add mention "
                f"a variable the head does not bind"
            )
    states = replay_states(initial_facts, operators)
    if expected_final is not None:
        expected = {normalize_fact(f) for f in expected_final}
        if states[-1] != expected:
            only_replay = sorted(states[-1] - expected)[:5]
            only_planner = sorted(expected - states[-1])[:5]
            warnings.append(
                f"replayed final state differs from the planner's: "
                f"only-in-replay={only_replay}, only-in-planner={only_planner}"
            )
    return states, warnings


def _reconstruct_path(
    tree: Sequence[Dict[str, Any]],
    operators: Sequence["OperatorInstance"],
    previous_ids: Set[int],
) -> Tuple[List[Dict[str, Any]], Set[int], int]:
    """Isolate one solution's own decomposition from the accumulated tree.

    `GetDecompositionTree(i)` returns every node the planner has created up to
    solution i, so consecutive calls are nested: tree(i) ⊇ tree(i-1). Taking the
    raw tree would make every plan look like it used every strategy, and taking
    only the newly-created nodes would drop the prefix this solution shares
    with the previous one.

    So we anchor on the operators instead. The plan's ground operators must
    appear as operator nodes in the tree, in order; matching them **backwards,
    preferring the highest-numbered node each time**, picks the most recent
    occurrence of each - which is the one belonging to this solution. The
    decomposition is then the union of those operators' ancestor chains.

    Returns (path nodes ordered by treeNodeID, newly-explored ids, dead-ends).
    """
    by_id = {n["treeNodeID"]: n for n in tree if "treeNodeID" in n}
    new_ids = set(by_id) - previous_ids
    dead_ends = sum(1 for i in new_ids if by_id[i].get("isFailed"))

    op_nodes = [
        by_id[i] for i in sorted(by_id)
        if by_id[i].get("isOperator") and not by_id[i].get("isFailed")
    ]

    matched: List[Dict[str, Any]] = []
    cursor = len(op_nodes) - 1
    for op in reversed(list(operators)):
        wanted = normalize_fact(op.text)
        while cursor >= 0 and normalize_fact(op_nodes[cursor].get("taskName", "")) != wanted:
            cursor -= 1
        if cursor < 0:
            matched = []
            break
        matched.append(op_nodes[cursor])
        cursor -= 1
    matched.reverse()

    path_ids: Set[int] = {n["treeNodeID"] for n in matched}
    for node in matched:
        cursor_node: Optional[Dict[str, Any]] = node
        while cursor_node is not None:
            parent_id = cursor_node.get("parentNodeID", -1)
            if parent_id == -1 or parent_id in path_ids:
                break
            path_ids.add(parent_id)
            cursor_node = by_id.get(parent_id)

    path = [by_id[i] for i in sorted(path_ids) if i in by_id]
    return path, new_ids, dead_ends


def _path_matches_operators(plan: "Plan") -> bool:
    """True when the reconstructed path's operator nodes equal the plan's.

    A cheap self-check on `_reconstruct_path`: the operator nodes on the path
    should be exactly the plan's operators, in order. Reported as a note when
    it fails rather than raising, since coarse fingerprints are still useful.
    """
    from_path = [
        normalize_fact(n.get("taskName", ""))
        for n in plan.path
        if n.get("isOperator")
    ]
    from_plan = [normalize_fact(op.text) for op in plan.operators]
    return from_path == from_plan


def _ground_operator(term, term_to_string, templates, operator_owner) -> OperatorInstance:
    """Turn one planner JSON operator term into an OperatorInstance."""
    text = term_to_string(term) if not isinstance(term, str) else term
    if isinstance(term, dict):
        name = list(term.keys())[0]
        arg_terms = term[name]
        args = [term_to_string(a) for a in arg_terms]
    else:
        name, args = text, []

    signature = f"{name}/{len(args)}"
    mechanism = operator_owner.get(signature, "?")
    tmpl = templates.get(signature)

    dels: List[str] = []
    adds: List[str] = []
    resolved = True

    if tmpl is not None:
        bindings: Dict[str, str] = {}
        matched = True
        for head_arg, value in zip(tmpl.head_args, args):
            value = normalize_fact(value)
            if getattr(head_arg, "is_variable", False):
                bindings[head_arg.name] = value
            elif normalize_fact(repr(head_arg)) != value:
                # A constant in the operator head that the call did not match.
                matched = False
        if matched:
            for template_term in tmpl.dels:
                fact, ground = _term_text(template_term, bindings)
                if ground:
                    dels.append(fact)
                else:
                    resolved = False
            for template_term in tmpl.adds:
                fact, ground = _term_text(template_term, bindings)
                if ground:
                    adds.append(fact)
                else:
                    resolved = False
        else:
            resolved = False
    else:
        # No template at all: the effects are unknown, not empty.
        resolved = False

    return OperatorInstance(
        text=text, name=name, args=args, mechanism=mechanism,
        dels=dels, adds=adds, effects_resolved=resolved,
    )
