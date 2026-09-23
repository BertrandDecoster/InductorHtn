"""Exhaustive 256-combination verification of choice-tracking method stats.

Topology (5 methods):

    head() :- if(), do(t1(), t2()).
    t1 is an atom with two methods (t1m1, t1m2).
    t2 is an atom with two methods (t2m1, t2m2).
    Each of the four sub-methods has a two-subtask body so it can land in one of
    four RESULT states:
        0 = fail at its own precondition gate
        1 = fail at body subtask 1
        2 = fail at body subtask 2
        3 = success (both body subtasks complete)

Each ruleset is a base-4 number  n = 64*a + 16*b + 4*c + d  where
(a,b,c,d) = (t1m1, t1m2, t2m1, t2m2) results. All 256 are checked against an
independent predictive model derived from the planner's documented local
furthest-completion semantics.
"""
import json
import pytest

# conftest.py inserts src/Python on sys.path.
from indhtnpy import HtnPlanner


def _choice_tracking_available() -> bool:
    p = HtnPlanner(False)
    p.HtnCompileCustomVariables("a() :- if(), do(o()). o() :- del(), add().")
    p.FindAllPlansCustomVariables("a().")
    try:
        p.GetChoiceStats()
        return True
    except RuntimeError:
        return False


pytestmark = pytest.mark.skipif(
    not _choice_tracking_available(),
    reason="library built without INDHTN_CHOICE_TRACKING",
)


# --------------------------------------------------------------------------- #
# Ruleset generator
# --------------------------------------------------------------------------- #

def _method_clause(head: str, marker: str, result: int) -> str:
    if result == 0:
        # Gate fail: precondition references the absent fact `never`.
        return "%s() :- if(m(%s), never), do(ok_leaf(), ok_leaf())." % (head, marker)
    body = {
        1: "fail_leaf(), ok_leaf()",   # blocks at body subtask 1
        2: "ok_leaf(), fail_leaf()",   # blocks at body subtask 2
        3: "ok_leaf(), ok_leaf()",     # full success
    }[result]
    # `m(marker)` is an always-true marker that keeps each clause signature unique.
    return "%s() :- if(m(%s)), do(%s)." % (head, marker, body)


def make_ruleset(a: int, b: int, c: int, d: int) -> str:
    return " ".join([
        "m(t1m1). m(t1m2). m(t2m1). m(t2m2).",
        "head() :- if(), do(t1(), t2()).",
        _method_clause("t1", "t1m1", a),
        _method_clause("t1", "t1m2", b),
        _method_clause("t2", "t2m1", c),
        _method_clause("t2", "t2m2", d),
        "ok_leaf() :- del(), add().",
        "fail_leaf() :- if(never), do(ok_leaf()).",
    ])


def decode(n: int):
    return (n >> 6) & 3, (n >> 4) & 3, (n >> 2) & 3, n & 3


# --------------------------------------------------------------------------- #
# Predictive model (independent of the engine)
# --------------------------------------------------------------------------- #

def _sub_method(result: int, tried: int):
    """Expected stats for one sub-method given its result and how many times its
    parent atom was resolved (tried). None means the clause never appears."""
    if tried == 0:
        return None
    if result == 0:
        return dict(groundingsN=0, successS=0, gateFailCount=tried,
                    furthestCompleted=[], subtaskCount=0)
    hist = {1: [tried, 0, 0], 2: [0, tried, 0], 3: [0, 0, tried]}[result]
    return dict(groundingsN=tried, successS=(tried if result == 3 else 0),
                gateFailCount=0, furthestCompleted=hist, subtaskCount=2)


def expected_stats(a: int, b: int, c: int, d: int):
    """Returns ({label: stats|None}, expected_solution_count)."""
    t1_completions = (a == 3) + (b == 3)   # only result-3 methods complete locally
    t2_resolutions = t1_completions        # t2 re-resolved once per completing t1
    t1_succeeds = t1_completions > 0
    t2_succeeds = (c == 3) or (d == 3)

    if not t1_succeeds:
        head_hist = [1, 0, 0]              # head blocked at t1
    elif not t2_succeeds:
        head_hist = [0, 1, 0]              # reached t2, blocked there
    else:
        head_hist = [0, 0, 1]              # full success

    stats = {
        "head": dict(groundingsN=1, successS=head_hist[2], gateFailCount=0,
                     furthestCompleted=head_hist, subtaskCount=2),
        "t1m1": _sub_method(a, 1),
        "t1m2": _sub_method(b, 1),
        "t2m1": _sub_method(c, t2_resolutions),
        "t2m2": _sub_method(d, t2_resolutions),
    }
    solution_count = t1_completions * ((c == 3) + (d == 3))
    return stats, solution_count


# --------------------------------------------------------------------------- #
# Engine harness
# --------------------------------------------------------------------------- #

_FIELDS = ["groundingsN", "successS", "gateFailCount", "furthestCompleted", "subtaskCount"]


def engine_stats(a: int, b: int, c: int, d: int):
    p = HtnPlanner(False)
    assert p.HtnCompileCustomVariables(make_ruleset(a, b, c, d)) is None
    _err, sols = p.FindAllPlansCustomVariables("head().")
    n_sol = 0
    if sols:
        parsed = json.loads(sols)
        if isinstance(parsed, list) and (not parsed or isinstance(parsed[0], list)):
            n_sol = len(parsed)
    by_method = p.GetChoiceStats()["byMethod"]

    def by_marker(marker):
        return next((m for m in by_method if marker in m["clauseSignature"]), None)

    stats = {
        "head": next((m for m in by_method if m["clauseSignature"].startswith("head")), None),
        "t1m1": by_marker("m(t1m1)"),
        "t1m2": by_marker("m(t1m2)"),
        "t2m1": by_marker("m(t2m1)"),
        "t2m2": by_marker("m(t2m2)"),
    }
    return stats, n_sol


def _matches(exp, got) -> bool:
    if exp is None:
        return got is None
    if got is None:
        return False
    return all(exp[f] == got.get(f) for f in _FIELDS)


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

def test_all_256_combinations_match_model():
    """Every one of the 256 result-combinations: engine stats == model, for all
    5 methods, plus the solution count."""
    failures = []
    for n in range(256):
        a, b, c, d = decode(n)
        exp, exp_sol = expected_stats(a, b, c, d)
        got, got_sol = engine_stats(a, b, c, d)
        for label in ("head", "t1m1", "t1m2", "t2m1", "t2m2"):
            if not _matches(exp[label], got[label]):
                failures.append((n, label, exp[label], got[label]))
        if exp_sol != got_sol:
            failures.append((n, "solutions", exp_sol, got_sol))
    assert not failures, "First few mismatches:\n" + "\n".join(
        f"  n={n} {label}: exp={e} got={g}" for n, label, e, g in failures[:10]
    )


@pytest.mark.parametrize("n", [17, 73, 221])
def test_specific_rulesets_match_model(n):
    a, b, c, d = decode(n)
    exp, exp_sol = expected_stats(a, b, c, d)
    got, got_sol = engine_stats(a, b, c, d)
    assert got_sol == exp_sol
    for label in ("head", "t1m1", "t1m2", "t2m1", "t2m2"):
        assert _matches(exp[label], got[label]), (
            f"n={n} {label}: exp={exp[label]} got={got[label]}")
