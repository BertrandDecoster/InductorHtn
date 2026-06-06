"""Convert indhtnpy JSON term shapes into stable MCP-shaped payloads.

The C++ side serialises Prolog terms into JSON dicts of the form
``{"functor": [arg_term1, arg_term2, ...]}``. Tools using the bindings (the
test framework, this MCP server) re-stringify those for display via the
``termToString`` helper in ``indhtnpy``. This module centralises the
conversion so every tool returns the same shape.
"""

from __future__ import annotations

import json
from typing import Any

from .bindings_loader import _ensure_indhtnpy_importable

_ensure_indhtnpy_importable()

from indhtnpy import termToString  # type: ignore  # noqa: E402


def _safe_load(text: str) -> Any:
    if not text:
        return []
    return json.loads(text)


def _is_failure_solutions(solutions: Any) -> bool:
    return (
        isinstance(solutions, list)
        and len(solutions) > 0
        and isinstance(solutions[0], dict)
        and "false" in solutions[0]
    )


def parse_plans(raw_json: str) -> dict:
    """Parse a ``FindAllPlans*`` raw JSON result.

    Returns a dict with shape::

        {
          "ok": True,
          "planCount": N,
          "plans": [
            {"index": 0, "operators": ["walk(downtown, park)", ...],
             "operatorsRaw": [{"walk": [...]}, ...]},
            ...
          ]
        }

    or on failure::

        {"ok": False, "planCount": 0, "plans": [],
         "failureContext": [...stringified terms...]}
    """
    solutions = _safe_load(raw_json)
    if not isinstance(solutions, list) or len(solutions) == 0:
        return {"ok": False, "planCount": 0, "plans": [], "failureContext": []}

    if _is_failure_solutions(solutions):
        return {
            "ok": False,
            "planCount": 0,
            "plans": [],
            "failureContext": _stringify_failure(solutions),
            "rawFailure": solutions,
        }

    plans = []
    for idx, solution in enumerate(solutions):
        ops_raw = solution if isinstance(solution, list) else [solution]
        ops_str = [termToString(t) for t in ops_raw]
        plans.append({"index": idx, "operators": ops_str, "operatorsRaw": ops_raw})

    return {"ok": True, "planCount": len(plans), "plans": plans}


def parse_query_solutions(raw_json: str) -> dict:
    """Parse a ``PrologQuery`` raw JSON result.

    Query solutions are dicts of variable bindings, e.g.
    ``{"?X": {"value": []}}``. Returns::

        {"ok": True, "solutionCount": N,
         "solutions": [{"?X": "value", ...}, ...]}

    On no-solutions::

        {"ok": False, "solutionCount": 0, "solutions": [],
         "failureContext": [...]}
    """
    solutions = _safe_load(raw_json)
    if not isinstance(solutions, list) or len(solutions) == 0:
        return {"ok": False, "solutionCount": 0, "solutions": []}

    if _is_failure_solutions(solutions):
        return {
            "ok": False,
            "solutionCount": 0,
            "solutions": [],
            "failureContext": _stringify_failure(solutions),
            "rawFailure": solutions,
        }

    bindings = []
    for solution in solutions:
        # Each solution is a dict mapping variable names to terms.
        out = {}
        if isinstance(solution, dict):
            for var, value in solution.items():
                if isinstance(value, (dict, list)):
                    out[var] = termToString(value)
                else:
                    out[var] = str(value)
        bindings.append(out)

    return {"ok": True, "solutionCount": len(bindings), "solutions": bindings}


def parse_facts(raw_json: str) -> list[str]:
    """Parse a JSON array of fact strings (from GetStateFacts / GetSolutionFacts)."""
    if not raw_json:
        return []
    data = json.loads(raw_json)
    if not isinstance(data, list):
        return []
    return [str(f) for f in data]


def diff_facts(before: list[str], after: list[str]) -> dict:
    """Return ``{added, removed, unchanged_count}`` between two fact lists."""
    before_set = set(before)
    after_set = set(after)
    added = sorted(after_set - before_set)
    removed = sorted(before_set - after_set)
    unchanged = before_set & after_set
    return {
        "added": added,
        "removed": removed,
        "unchangedCount": len(unchanged),
    }


def _stringify_failure(solutions: list) -> list[str]:
    """Convert the failure-context term list to a list of strings."""
    out = []
    for term in solutions:
        try:
            out.append(termToString(term))
        except Exception:
            out.append(json.dumps(term))
    return out


def extract_failed_precondition(solutions: list) -> str | None:
    """Best-effort: find the first non-bookkeeping term in a failure result.

    Failure shape: ``[{"false":[]}, {"failureIndex":[{"-1":[]}]}, <context>...]``.
    The context terms (if any) are the partial unifications when the planner
    gave up — typically the precondition that couldn't be satisfied.
    """
    if not _is_failure_solutions(solutions):
        return None
    for term in solutions:
        if not isinstance(term, dict):
            continue
        name = next(iter(term.keys()), "")
        if name in ("false", "failureIndex"):
            continue
        try:
            return termToString(term)
        except Exception:
            return None
    return None
