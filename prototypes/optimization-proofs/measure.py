#!/usr/bin/env python3
"""Proof harness for the optimization patterns in docs/reference/ruleset-writing.md.

Each pattern is a (slow, fast) pair of Prolog rulesets that compute the SAME
answer; we run the same query against both and compare Prolog resolution steps
via GetLastResolutionStepCount(). The engine must be built with resolution
tracking (INDHTN_TRACK_RESOLUTION_STEPS=ON, the default).

Run:
    source .venv/bin/activate
    python prototypes/optimization-proofs/measure.py

Each .pl ruleset lives next to this script so the gains are inspectable and
re-runnable; this file just pairs them with a query and reports the delta.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src", "Python"))

from indhtnpy import HtnPlanner  # noqa: E402


def steps_for(source: str, query: str) -> int:
    """Compile `source`, run `query`, return the resolution-step count."""
    planner = HtnPlanner(False)
    err = planner.PrologCompileCustomVariables(source)
    if err:
        raise RuntimeError(f"compile error: {err}")
    err, _ = planner.PrologQuery(query)
    if err:
        raise RuntimeError(f"query error: {err}")
    return planner.GetLastResolutionStepCount()


def load(name: str) -> str:
    with open(os.path.join(HERE, name), "r") as f:
        return f.read()


# (label, slow_file, fast_file, query)
PATTERNS = [
    ("Constraining goal first",      "goal_ordering.slow.pl", "goal_ordering.fast.pl", "findRich(?p)."),
    ("Pre-computed negation",        "negation.slow.pl",      "negation.fast.pl",      "ok(?x)."),
    ("Direct count vs findall+count","count.slow.pl",         "count.fast.pl",         "teamSize(?n)."),
    ("Cut for deterministic choice", "cut.slow.pl",           "cut.fast.pl",           "classify(5, ?c)."),
    # First-argument indexing is intentionally NOT here: measured identical
    # steps AND wall-clock (slow==fast at 8000 facts), so this engine shows no
    # gain from it. See ruleset-writing.md. Don't claim unproven optimizations.
]


def main() -> int:
    print(f"{'pattern':<32}{'slow':>7}{'fast':>7}{'improvement':>14}")
    print("-" * 60)
    ok = True
    for label, slow_f, fast_f, query in PATTERNS:
        slow = steps_for(load(slow_f), query)
        fast = steps_for(load(fast_f), query)
        pct = (slow - fast) / slow * 100 if slow else 0.0
        flag = "" if fast < slow else "   (no gain!)"
        if fast >= slow:
            ok = False
        print(f"{label:<32}{slow:>7}{fast:>7}{pct:>12.1f}%{flag}")
    print("-" * 60)
    print("All patterns improved." if ok else "WARNING: some patterns showed no gain on this build.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
