"""Two-unification head: 20 scenarios that vary per-(method, grounding) results.

    head() :- if(uni(?u)), do(t1(?u), t2(?u)).     % uni(g1). uni(g2). -> 2 groundings

t1/t2 each have two methods; each method body is two maybeFail() subtasks. The
result of every (method, grounding) pair is selected purely by facts, so a single
method can succeed in one grounding and fail in another — which is what makes the
head histogram a *mixed* distribution such as [0,1,1] (one grounding succeeds, one
blocks at t2).

Result encoding for (method, grounding):
    0 gate-fail   -> no gate(method,u) fact
    1 fail@sub1   -> gate present, subtaskOk(method,s1,u) absent
    2 fail@sub2   -> gate present, subtaskOk s1 present, subtaskOk s2 absent
    3 success     -> gate present, both subtaskOk present
"""
import json
import pytest

from indhtnpy import HtnPlanner

METHODS = ["t1m1", "t1m2", "t2m1", "t2m2"]
GROUNDINGS = ["g1", "g2"]


def _available() -> bool:
    p = HtnPlanner(False)
    p.HtnCompileCustomVariables("a() :- if(), do(o()). o() :- del(), add().")
    p.FindAllPlansCustomVariables("a().")
    try:
        p.GetChoiceStats()
        return True
    except RuntimeError:
        return False


pytestmark = pytest.mark.skipif(not _available(),
                                reason="library built without INDHTN_CHOICE_TRACKING")


# --------------------------------------------------------------------------- #

def scn(t1m1, t1m2, t2m1, t2m2):
    """Each arg is a (g1_result, g2_result) pair."""
    d = {}
    for name, pair in [("t1m1", t1m1), ("t1m2", t1m2), ("t2m1", t2m1), ("t2m2", t2m2)]:
        d[(name, "g1")], d[(name, "g2")] = pair
    return d


def make_ruleset(s):
    facts = ["uni(g1). uni(g2).", "m(t1m1). m(t1m2). m(t2m1). m(t2m2)."]
    for m in METHODS:
        for u in GROUNDINGS:
            r = s.get((m, u), 0)
            if r >= 1: facts.append("gate(%s, %s)." % (m, u))
            if r >= 2: facts.append("subtaskOk(%s, s1, %s)." % (m, u))
            if r >= 3: facts.append("subtaskOk(%s, s2, %s)." % (m, u))
    clauses = [
        "head() :- if(uni(?u)), do(t1(?u), t2(?u)).",
        "t1(?u) :- if(m(t1m1), gate(t1m1, ?u)), do(maybeFail(t1m1, s1, ?u), maybeFail(t1m1, s2, ?u)).",
        "t1(?u) :- if(m(t1m2), gate(t1m2, ?u)), do(maybeFail(t1m2, s1, ?u), maybeFail(t1m2, s2, ?u)).",
        "t2(?u) :- if(m(t2m1), gate(t2m1, ?u)), do(maybeFail(t2m1, s1, ?u), maybeFail(t2m1, s2, ?u)).",
        "t2(?u) :- if(m(t2m2), gate(t2m2, ?u)), do(maybeFail(t2m2, s1, ?u), maybeFail(t2m2, s2, ?u)).",
        "maybeFail(?mth, ?pos, ?u) :- if(subtaskOk(?mth, ?pos, ?u)), do(ok_leaf()).",
        "ok_leaf() :- del(), add().",
    ]
    return " ".join(facts + clauses)


def expected(s):
    def r(m, u): return s.get((m, u), 0)
    t1c = {u: (r("t1m1", u) == 3) + (r("t1m2", u) == 3) for u in GROUNDINGS}
    t2c = {u: (r("t2m1", u) == 3) + (r("t2m2", u) == 3) for u in GROUNDINGS}

    head = [0, 0, 0]
    sols = 0
    for u in GROUNDINGS:
        if t1c[u] == 0:
            head[0] += 1
        elif t2c[u] == 0:
            head[1] += 1
        else:
            head[2] += 1
        sols += t1c[u] * t2c[u]

    out = {"head": dict(groundingsN=2, successS=head[2], gateFailCount=0,
                        furthestCompleted=head, subtaskCount=2)}

    def agg(method, mult):
        gN = gF = 0
        hist = [0, 0, 0]
        reached = False
        for u in GROUNDINGS:
            k = mult[u]
            if k == 0:
                continue
            rr = r(method, u)
            if rr == 0:
                gF += k
            else:
                gN += k
                hist[rr - 1] += k
                reached = True
        if gN + gF == 0:
            return None
        if not reached:
            return dict(groundingsN=0, successS=0, gateFailCount=gF,
                        furthestCompleted=[], subtaskCount=0)
        return dict(groundingsN=gN, successS=hist[2], gateFailCount=gF,
                    furthestCompleted=hist, subtaskCount=2)

    out["t1m1"] = agg("t1m1", {u: 1 for u in GROUNDINGS})
    out["t1m2"] = agg("t1m2", {u: 1 for u in GROUNDINGS})
    out["t2m1"] = agg("t2m1", {u: t1c[u] for u in GROUNDINGS})
    out["t2m2"] = agg("t2m2", {u: t1c[u] for u in GROUNDINGS})
    return out, sols


_FIELDS = ["groundingsN", "successS", "gateFailCount", "furthestCompleted", "subtaskCount"]


def engine(s):
    p = HtnPlanner(False)
    assert p.HtnCompileCustomVariables(make_ruleset(s)) is None
    _e, sols = p.FindAllPlansCustomVariables("head().")
    nsol = 0
    if sols:
        parsed = json.loads(sols)
        if isinstance(parsed, list) and (not parsed or isinstance(parsed[0], list)):
            nsol = len(parsed)
    bm = p.GetChoiceStats()["byMethod"]
    g = {"head": next((m for m in bm if m["clauseSignature"].startswith("head")), None)}
    for mk in METHODS:
        g[mk] = next((m for m in bm if ("m(%s)" % mk) in m["clauseSignature"]), None)
    return g, nsol


def _match(e, got):
    if e is None:
        return got is None
    if got is None:
        return False
    return all(e[f] == got.get(f) for f in _FIELDS)


# --------------------------------------------------------------------------- #
# 20 scenarios spanning: both subtask methods fail / both succeed / one of each,
# and head furthest reaching t1 / t2 / success (including mixed per-grounding).
# --------------------------------------------------------------------------- #

SCENARIOS = [
    ("t1 both methods fail -> fail@t1 x2",      scn((1, 1), (2, 2), (3, 3), (3, 3))),
    ("t1 one-each, t2 both fail -> fail@t2 x2", scn((3, 3), (0, 0), (1, 1), (2, 2))),
    ("all succeed -> success x2",               scn((3, 3), (3, 3), (3, 3), (3, 3))),
    ("t1 both gate-fail -> fail@t1 x2",         scn((0, 0), (0, 0), (3, 3), (3, 3))),
    ("t2 both methods succeed",                 scn((3, 3), (0, 0), (3, 3), (3, 3))),
    ("t2 both fail (mixed modes)",              scn((3, 3), (0, 0), (1, 2), (2, 1))),
    ("t1 both succeed (t2 resolved 2x/grnd)",   scn((3, 3), (3, 3), (3, 1), (1, 3))),
    ("[0,1,1] g1 success / g2 fail@t2",         scn((3, 3), (1, 1), (3, 1), (1, 1))),
    ("[1,0,1] g1 fail@t1 / g2 success",         scn((1, 3), (2, 1), (1, 3), (2, 1))),
    ("[1,1,0] g1 fail@t1 / g2 fail@t2",         scn((0, 3), (0, 1), (1, 1), (1, 2))),
    ("success via different methods/grounding", scn((3, 1), (1, 3), (3, 1), (1, 3))),
    ("[2,0,0] t1 fail mixed modes",             scn((1, 2), (0, 1), (3, 3), (3, 3))),
    ("everything gate-fails",                   scn((0, 0), (0, 0), (0, 0), (0, 0))),
    ("all fail@sub2 -> fail@t1 x2",             scn((2, 2), (2, 2), (2, 2), (2, 2))),
    ("all fail@sub1, t2 unreached",             scn((1, 1), (1, 1), (3, 3), (3, 3))),
    ("t2 one-each per grounding",               scn((3, 3), (0, 0), (3, 0), (0, 3))),
    ("asymmetric t1 completions (2 vs 1)",      scn((3, 3), (3, 0), (2, 3), (1, 1))),
    ("mixed everything",                        scn((3, 1), (0, 3), (2, 3), (1, 0))),
    ("[0,1,1] both t1 methods complete g1",     scn((3, 3), (3, 1), (2, 3), (1, 1))),
    ("[0,2,0] t1 ok, t2 fails both (diff)",     scn((3, 3), (1, 1), (2, 1), (1, 2))),
]


@pytest.mark.parametrize("label,s", SCENARIOS, ids=[x[0] for x in SCENARIOS])
def test_scenario_matches_model(label, s):
    exp, exp_sol = expected(s)
    got, got_sol = engine(s)
    assert got_sol == exp_sol, f"{label}: solutions exp={exp_sol} got={got_sol}"
    for k in ["head"] + METHODS:
        assert _match(exp[k], got[k]), f"{label} [{k}]: exp={exp[k]} got={got[k]}"


def test_scenarios_cover_all_head_outcomes():
    """The 20 scenarios collectively exercise fail@t1, fail@t2, and success
    buckets of the head histogram (including mixed groundings)."""
    seen = set()
    for _label, s in SCENARIOS:
        exp, _ = expected(s)
        h = tuple(exp["head"]["furthestCompleted"])
        seen.add(h)
    # at least one pure-t1, one pure-t2, one pure-success, and the mixed [0,1,1]
    assert (2, 0, 0) in seen
    assert (0, 2, 0) in seen
    assert (0, 0, 2) in seen
    assert (0, 1, 1) in seen


def test_target_0_1_1_exact_table():
    """The [0,1,1] reference case, with the full per-method table asserted."""
    s = scn((3, 3), (1, 1), (3, 1), (1, 1))
    got, nsol = engine(s)
    assert nsol == 1
    assert got["head"]["furthestCompleted"] == [0, 1, 1]
    assert got["head"]["successS"] == 1 and got["head"]["groundingsN"] == 2
    assert got["t1m1"]["furthestCompleted"] == [0, 0, 2]
    assert got["t1m2"]["furthestCompleted"] == [2, 0, 0]
    assert got["t2m1"]["furthestCompleted"] == [1, 0, 1]
    assert got["t2m2"]["furthestCompleted"] == [2, 0, 0]
