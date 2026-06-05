"""
HTN Evaluator - Evaluates the "richness" of an HTN challenge's plan space.

Assesses whether a challenge is too easy (too many undifferentiated plans),
too hard (no plans), or well-designed (a few structurally distinct plans
using different methods).

`evaluate_level()` also returns `choice_stats` (when the engine is built with
INDHTN_CHOICE_TRACKING): the in-flight, whole-search record of WHERE each method
succeeds or fails. Per method it reports a `furthestCompleted` histogram —
[fail@subtask0, ..., fail@subtask(N-1), full-success] — that pinpoints whether a
method dies at its precondition gate or at a specific body subtask. Use it to
debug/tune rulesets: if a method's mass sits at subtask k, add the facts that
subtask k needs. Full diagnostic workflow: see `docs/method-failure-analysis.md`.
The by-atom / by-method views are built by `_build_by_atom_view` /
`_build_by_method_view`.
"""

import json
import logging
import math
import os
import subprocess
import sys
from typing import Optional

_log = logging.getLogger(__name__)

# Add the directory containing this file to sys.path so indhtnpy is importable
# regardless of where the caller imports from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from indhtnpy import HtnPlanner


def _find_project_root() -> str:
    """Return the project root (the directory that contains 'Examples/')."""
    current = os.path.dirname(os.path.abspath(__file__))
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, "Examples")):
            return current
        current = os.path.dirname(current)
    # Fallback: two levels up from src/Python
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


def _extract_operator_name(op_dict: dict) -> str:
    """Return the functor name of a single operator dict, e.g. 'opMoveTo'."""
    return list(op_dict.keys())[0]


def _parse_solutions(solutions_json: str) -> Optional[list]:
    """
    Parse the JSON string from FindAllPlansCustomVariables.

    Returns a list of solutions (each is a list of operator dicts), or None
    if planning failed (i.e. the JSON represents a failure term list).
    """
    data = json.loads(solutions_json)
    if not data:
        return None
    # A failure result has a dict with "false" as its only key.
    first = data[0]
    if isinstance(first, dict) and "false" in first:
        return None
    return data


def _operator_group(op_name: str) -> str:
    """
    Return the 'group' of an operator name: the prefix before the first uppercase
    letter after position 0 (the full name if there is no such letter).

    This is a coarse but cheap structural metric — it groups e.g. opMoveTo /
    opMoveAway / opApplyTag all into 'op'.
    """
    if not op_name:
        return op_name
    # Find first uppercase after position 0
    for i in range(1, len(op_name)):
        if op_name[i].isupper():
            return op_name[:i]
    return op_name


def _context_switch_cost(op_names: list) -> float:
    """
    Compute the number of transitions between distinct operator-functor groups
    in one plan (list of operator names).
    """
    if len(op_names) < 2:
        return 0.0
    transitions = 0
    prev_group = _operator_group(op_names[0])
    for name in op_names[1:]:
        group = _operator_group(name)
        if group != prev_group:
            transitions += 1
        prev_group = group
    return float(transitions)


def _difficulty_estimate(plan_count: int, operator_variety: list) -> str:
    """Simple difficulty heuristic based on plan count and operator variety."""
    variety = len(operator_variety)
    if plan_count == 0:
        return "unsolvable"
    if plan_count == 1:
        return "trivial"
    if plan_count <= 3 and variety <= 4:
        return "easy"
    if plan_count <= 5:
        return "medium"
    return "hard"


def _build_activation_distribution(choice_data: Optional[list]) -> Optional[dict]:
    """
    Build a per-functor activation distribution from raw GetChoiceData() records.

    C++ emits camelCase keys: "taskFunctor", "depth", "unifyingMethods" (list),
    "viableMethods" (list).  Returns None when choice_data is None (feature not
    compiled in), or a dict keyed by functor name when data is available.
    """
    if choice_data is None:
        return None
    dist: dict = {}
    for record in choice_data:
        functor = record.get("taskFunctor", "")
        if not functor:
            continue
        if functor not in dist:
            dist[functor] = {
                "depth": record.get("depth", 0),
                "unifying_count": 0,
                "viable_count": 0,
                "activation_count": 0,
            }
        entry = dist[functor]
        entry["depth"] = min(entry["depth"], record.get("depth", entry["depth"]))
        entry["unifying_count"] += len(record.get("unifyingMethods", []))
        entry["viable_count"] += len(record.get("viableMethods", []))
        entry["activation_count"] += 1
    return dist


def _build_by_atom_view(choice_stats: Optional[dict]) -> Optional[list]:
    """
    Project the "by atom" report view from raw GetChoiceStats() output.

    Each entry: {atomFunctor, isOperator, tested, fail, clears:[{method, count}]}.
    Sorted by tested-count descending, then functor name. Returns None when the
    feature is not compiled in.
    """
    if choice_stats is None:
        return None
    atoms = list(choice_stats.get("byAtom", []))
    atoms.sort(key=lambda a: (-a.get("tested", 0), a.get("atomFunctor", "")))
    return atoms


def _build_by_method_view(choice_stats: Optional[dict]) -> Optional[list]:
    """
    Project the "by method" report view from raw GetChoiceStats() output.

    Each entry keys the parent clause and lists its do() positions with the
    grounding partition (successS + sum(positions.fail) == groundingsN for
    normal methods). Sorted by clause documentOrder (the synthetic goal clause,
    -1, sorts first); positions sorted by index. Returns None when the feature
    is not compiled in.

    MUTATES ITS INPUT: this sorts each clause's "positions" list in place, so the
    same dicts stored under the caller's choice_stats["byMethod"] come back in
    positionIndex order. The sort is idempotent (stable target order), so calling
    this more than once is harmless, but a caller that needs the original
    C++/document position order should snapshot it before calling.
    """
    if choice_stats is None:
        return None
    clauses = list(choice_stats.get("byMethod", []))
    for clause in clauses:
        # In-place sort: deliberately normalizes the shared dicts (see docstring).
        clause.get("positions", []).sort(key=lambda p: p.get("positionIndex", 0))
    clauses.sort(key=lambda c: c.get("clauseDocOrder", 0))
    return clauses


def _unsolvable_result() -> dict:
    """The evaluate_level() result for a level that produced no plan (compile/
    runtime error, or zero solutions)."""
    return {
        "solvable": False,
        "plan_count": 0,
        "plan_lengths": [],
        "operator_variety": [],
        "context_switch_cost": 0.0,
        "difficulty_estimate": "unsolvable",
        "choice_data": None,
        "activation_distribution": None,
        "choice_stats": None,
    }


def evaluate_level(planner: HtnPlanner, goal: str) -> dict:
    """
    Evaluate the plan-space richness of an HTN level.

    Args:
        planner: An HtnPlanner instance with the level's ruleset already compiled.
        goal:    The HTN goal string (e.g. "completePuzzle.").

    Returns:
        A dict with the following keys:
            solvable (bool)
            plan_count (int)
            plan_lengths (list[int])
            operator_variety (list[str])
            context_switch_cost (float)
            difficulty_estimate (str)
            choice_data (list | None)
            activation_distribution (dict | None)
            choice_stats (dict | None) — {"byAtom": [...], "byMethod": [...]}
    """
    # Ensure goal ends with a period
    goal_str = goal.strip()
    if not goal_str.endswith("."):
        goal_str += "."

    error, solutions_json = planner.FindAllPlansCustomVariables(goal_str)

    if error is not None:
        # Planning returned a compile/runtime error — treat as unsolvable
        return _unsolvable_result()

    solutions = _parse_solutions(solutions_json)

    if not solutions:
        return _unsolvable_result()

    # Build per-solution operator name lists
    per_solution_ops: list[list[str]] = []
    for solution in solutions:
        op_names = [_extract_operator_name(op) for op in solution if isinstance(op, dict)]
        per_solution_ops.append(op_names)

    plan_lengths = [len(ops) for ops in per_solution_ops]

    # Unique operator names across all solutions
    all_op_names: list[str] = []
    for ops in per_solution_ops:
        all_op_names.extend(ops)
    operator_variety = sorted(set(all_op_names))

    # Mean context-switch cost across all solutions
    if per_solution_ops:
        total_csc = sum(_context_switch_cost(ops) for ops in per_solution_ops)
        mean_csc = total_csc / len(per_solution_ops)
    else:
        mean_csc = 0.0

    plan_count = len(solutions)
    difficulty = _difficulty_estimate(plan_count, operator_variety)

    # Try to get choice data; gracefully degrade if not compiled in (RuntimeError)
    # or if the payload is malformed (ValueError/JSONDecodeError from json.loads).
    choice_data = None
    try:
        choice_data = planner.GetChoiceData()
    except (RuntimeError, ValueError):
        pass

    activation_distribution = _build_activation_distribution(choice_data)

    # Cross-search choice-count stats (richer than choice_data); gracefully
    # degrade to None if not compiled in or if the payload is malformed.
    choice_stats = None
    try:
        choice_stats = planner.GetChoiceStats()
    except (RuntimeError, ValueError):
        pass

    return {
        "solvable": True,
        "plan_count": plan_count,
        "plan_lengths": plan_lengths,
        "operator_variety": operator_variety,
        "context_switch_cost": mean_csc,
        "difficulty_estimate": difficulty,
        "choice_data": choice_data,
        "activation_distribution": activation_distribution,
        "choice_stats": choice_stats,
    }


def library_coverage(levels_dir: str, layer_filter: Optional[str] = None) -> dict:
    """
    Aggregate plan-space metrics across all levels in a directory.

    Args:
        levels_dir:   Root directory containing level subdirectories, each
                      with a manifest.json and (optionally) level.htn.
        layer_filter: If given, only include levels whose path contains this
                      string (e.g. "puzzle" or "gamehack").

    Returns:
        A dict with:
            total_levels (int)               — all levels counted (solvable + not)
            unsolvable_levels (int)          — subset that produced no plan
            method_activation_counts (dict[str, int])
            dead_methods (list[str])         — defined by a solvable level, never fired
            unsolvable_only_operators (list[str]) — only ever seen in unsolvable levels
            over_concentrated (list[str])
            uniformity_entropy (float)
    """
    project_root = _find_project_root()

    # Try to import parse_htn for dead-operator detection (lives in gui/backend/).
    _parse_htn = None
    try:
        sys.path.insert(0, os.path.join(project_root, "gui", "backend"))
        from htn_parser import parse_htn as _parse_htn_import  # type: ignore
        _parse_htn = _parse_htn_import
    except Exception:
        pass

    # Resolve levels_dir to an absolute path
    if not os.path.isabs(levels_dir):
        levels_dir = os.path.join(project_root, levels_dir)

    # Gather level paths: directories containing a manifest.json
    level_paths: list[str] = []
    for dirpath, dirnames, filenames in os.walk(levels_dir):
        if "manifest.json" in filenames:
            if layer_filter is None or layer_filter in dirpath:
                level_paths.append(dirpath)

    method_activation_counts: dict[str, int] = {}
    all_known_operators: set = set()       # operators defined by SOLVABLE levels
    unsolvable_operators: set = set()      # operators defined by unsolvable levels
    total_levels = 0
    unsolvable_levels = 0

    for level_path in level_paths:
        try:
            htn_source = _load_level_source(level_path, project_root)
        except RuntimeError as exc:
            _log.warning("Skipping %s: %s", level_path, exc)
            continue
        if htn_source is None:
            continue

        # Enumerate the operators this level defines (before planning). They are
        # merged into all_known_operators only if the level turns out solvable —
        # an operator that appears only in an unsolvable level is not "dead", it
        # just never got a chance to fire (see dead_methods below).
        level_operators: set = set()
        if _parse_htn is not None:
            try:
                rules, _ = _parse_htn(htn_source)
                for rule in rules:
                    if rule.is_operator:
                        level_operators.add(rule.head.name)
            except Exception:
                pass

        planner = HtnPlanner(False)
        compile_error = planner.HtnCompileCustomVariables(htn_source)
        if compile_error is not None:
            continue

        # Determine the level goal from goals() directive (first one found)
        goal = _extract_level_goal(planner)
        if goal is None:
            continue

        report = evaluate_level(planner, goal)
        total_levels += 1
        if not report["solvable"]:
            unsolvable_levels += 1
            unsolvable_operators |= level_operators
            continue

        all_known_operators |= level_operators
        for op_name in report["operator_variety"]:
            method_activation_counts[op_name] = (
                method_activation_counts.get(op_name, 0) + 1
            )

    # Compute derived statistics.
    # dead_methods: operators defined by at least one SOLVABLE level that still
    # never appear in any plan solution.  Operators that appear only in unsolvable
    # levels are excluded here and reported under unsolvable_operators instead, so
    # an unsolvable-but-correct level does not get its operators flagged as dead.
    # Requires parse_htn to enumerate defined operators; empty when unavailable.
    dead_methods = sorted(
        m for m in all_known_operators if m not in method_activation_counts
    )
    # Operators seen ONLY in unsolvable levels (never defined by a solvable level).
    unsolvable_only_operators = sorted(unsolvable_operators - all_known_operators)
    over_concentrated = [
        m for m, cnt in method_activation_counts.items()
        if total_levels > 0 and cnt / total_levels > 0.5
    ]

    # Shannon entropy of the activation distribution
    uniformity_entropy = 0.0
    if method_activation_counts:
        total_activations = sum(method_activation_counts.values())
        if total_activations > 0:
            for cnt in method_activation_counts.values():
                p = cnt / total_activations
                if p > 0:
                    uniformity_entropy -= p * math.log2(p)

    return {
        "total_levels": total_levels,
        "unsolvable_levels": unsolvable_levels,
        "method_activation_counts": method_activation_counts,
        "dead_methods": dead_methods,
        "unsolvable_only_operators": unsolvable_only_operators,
        "over_concentrated": over_concentrated,
        "uniformity_entropy": uniformity_entropy,
    }


def _load_level_source(level_path: str, project_root: str) -> Optional[str]:
    """
    Try to load the assembled HTN source for a level.

    Preference order:
    1. assembled/<level_name>/latest.htn (pre-assembled)
    2. Run `htn_components assemble <level_path> --no-verify` via subprocess
    3. Read level.htn directly (no dependency resolution)
    """
    level_name = os.path.basename(level_path)
    assembled_latest = os.path.join(
        project_root, "assembled", level_name, "latest.htn"
    )
    if os.path.exists(assembled_latest):
        with open(assembled_latest, "r", encoding="utf-8") as f:
            return f.read()

    # Try assembling via the CLI tool
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "htn_components",
                "assemble", level_path, "--no-verify",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_root,
            env={**os.environ, "PYTHONPATH": os.path.join(project_root, "src", "Python")},
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"assemble failed (exit {result.returncode}): {result.stderr.strip()}"
            )
        # After assemble, latest.htn should exist now
        if os.path.exists(assembled_latest):
            with open(assembled_latest, "r", encoding="utf-8") as f:
                return f.read()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    # level.htn contains only world-state facts and a goals() directive — no
    # method/operator definitions.  Loading it alone produces a planner that
    # compiles but finds no plans (silent false-negative).  Raise so callers
    # can log and skip rather than recording a spurious "unsolvable" result.
    level_htn = os.path.join(level_path, "level.htn")
    if os.path.exists(level_htn):
        raise RuntimeError(
            f"Cannot load '{level_name}': bare level.htn has no method/operator "
            f"definitions. Run 'htn_components assemble {level_name}' first to "
            f"produce assembled/{level_name}/latest.htn."
        )

    return None


def _extract_level_goal(planner: HtnPlanner) -> Optional[str]:
    """
    Return the first goal string from the goals() directive, or None if
    no goals are defined.
    """
    error, goals = planner.GetGoals(customVariables=True)
    if error is not None or not goals:
        return None
    # goals is a list of goal strings e.g. ["completePuzzle"]
    goal = goals[0]
    if not goal.endswith("."):
        goal += "."
    return goal
