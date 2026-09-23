"""Level-shape regressions: `funExpect` facts checked against a scorecard.

A design hypothesis written with numbers ("the player makes at least two
decisions") is worth more once it outlives the iteration that produced it.
Components are shared across levels, so a change made for one level can
quietly flatten another; declared expectations turn each level's intended
shape into a regression test that `verify` runs every time.

    funExpect(strategy_classes, atLeast, 2).
    funExpect(f6_player, player_decision_points, atLeast, 2).
    funExpect(f7_intent, verdict, pass).
    funExpect(plan_length_median, atMost, 8).

Metric names are the scorecard's, with nested values flattened by `_`
(`plan_length.median` -> `plan_length_median`). The three-argument form
searches every family and is refused when the name is ambiguous; the
four-argument form names the family. `funExpect(family, verdict, v)` is
shorthand for `funExpect(family, verdict, equals, v)`.
"""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .structure import declared_args

OPERATORS = ("atLeast", "atMost", "equals")


def flatten_metrics(families: Iterable[Any]) -> Dict[Tuple[str, str], Any]:
    """`(family_key, flat_metric_name) -> scalar` for every family.

    Lists and deeper structures are skipped: an expectation compares a
    number, a boolean or a word, never a collection.
    """
    out: Dict[Tuple[str, str], Any] = {}

    def visit(family: str, prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for key, sub in value.items():
                visit(family, f"{prefix}_{key}" if prefix else str(key), sub)
        elif isinstance(value, (int, float, str, bool)) or value is None:
            out[(family, prefix)] = value

    for family in families:
        out[(family.key, "verdict")] = family.verdict
        for key, value in family.metrics.items():
            visit(family.key, key, value)
    return out


def _parse_value(text: str) -> Any:
    text = text.strip().strip("'\"")
    if text in ("true", "false"):
        return text == "true"
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        return text


@dataclass
class Expectation:
    family: Optional[str]
    metric: str
    op: str
    expected: Any
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return {"family": self.family, "metric": self.metric, "op": self.op,
                "expected": self.expected, "source": self.source}


def read_expectations(facts: Iterable[str]) -> List[Expectation]:
    out: List[Expectation] = []
    for args in declared_args(facts, "funExpect"):
        if len(args) == 3 and args[1] == "verdict":
            # funExpect(f7_intent, verdict, pass): a family's verdict.
            family, metric, op, value = args[0], "verdict", "equals", args[2]
        elif len(args) == 3:
            family, (metric, op, value) = None, args
        elif len(args) == 4:
            family, metric, op, value = args
        else:
            continue
        out.append(Expectation(
            family=family, metric=metric, op=op, expected=_parse_value(value),
            source=f"funExpect({', '.join(args)})",
        ))
    return out


def check_expectations(
    expectations: Iterable[Expectation], families: Iterable[Any]
) -> List[Dict[str, Any]]:
    """One result per expectation: `ok`, the actual value, and why not."""
    flat = flatten_metrics(families)
    results: List[Dict[str, Any]] = []
    for exp in expectations:
        result = dict(exp.to_dict(), ok=False, actual=None, reason="")
        results.append(result)
        if exp.op not in OPERATORS:
            result["reason"] = f"unknown operator '{exp.op}' (use {', '.join(OPERATORS)})"
            continue
        matches = [
            (fam, value) for (fam, name), value in flat.items()
            if name == exp.metric and (exp.family is None or fam == exp.family)
        ]
        if not matches:
            result["reason"] = (
                "no such metric on this scorecard (ablation and loadout metrics "
                "exist only under fun --ablate / --loadouts; verify runs neither)"
            )
            continue
        if len(matches) > 1:
            result["reason"] = (
                "ambiguous - name the family: "
                + ", ".join(sorted(fam for fam, _ in matches))
            )
            continue
        actual = matches[0][1]
        result["actual"] = actual
        if actual is None:
            result["reason"] = "metric not measured in this run"
            continue
        try:
            if exp.op == "equals":
                ok = actual == exp.expected
            elif exp.op == "atLeast":
                ok = actual >= exp.expected
            else:
                ok = actual <= exp.expected
        except TypeError:
            result["reason"] = f"cannot compare {actual!r} with {exp.expected!r}"
            continue
        result["ok"] = bool(ok)
        if not ok:
            result["reason"] = f"got {actual!r}"
    return results
