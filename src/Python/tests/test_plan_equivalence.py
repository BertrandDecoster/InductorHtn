"""Plan-equivalence: type/2 and signature/2 facts must be inert at planning time.

For each annotated assembled level, compare plans produced by the engine
with and without those facts present. Identical output proves the engine
treats them as inert.

If a level's plan output ever differs between the two versions, the
engine is somehow affected by `type/2` / `signature/2` facts — a real
bug. The TYP001 linter assumes these facts are linter-only conventions,
and this suite is the empirical guard for that assumption.
"""
import os
import re
import sys

# conftest.py adds src/Python to sys.path, but also support running this file
# directly via `python test_plan_equivalence.py` (no pytest).
_HERE = os.path.dirname(os.path.abspath(__file__))
_PYTHON_DIR = os.path.dirname(_HERE)
_PROJECT_ROOT = os.path.abspath(os.path.join(_PYTHON_DIR, '..', '..'))
if _PYTHON_DIR not in sys.path:
    sys.path.insert(0, _PYTHON_DIR)

from indhtnpy import HtnPlanner  # noqa: E402

ASSEMBLED_DIR = os.path.join(_PROJECT_ROOT, 'tests', 'fixtures', 'assembled')

LEVELS = [
    'puzzle1.htn',
    'gamehack_gh4.htn',
    'gamehack_gh7.htn',
    'gamehack_multipath.htn',
    'gamehack_mvp.htn',
]


# Strip whole-line `type(...)` or `signature(...)` facts only.
#
# A "fact line" here is a line whose entire content (modulo leading
# whitespace) is `type(...).` or `signature(...).`, with optional trailing
# whitespace. This deliberately does NOT match the same functors appearing
# inside method/operator bodies (e.g. `if(type(?x, agent))`) — those are
# calls, not facts, and we must not touch them.
FACT_LINE_RE = re.compile(r'^\s*(type|signature)\s*\(.*\)\s*\.\s*$')


def strip_type_signature_facts(source: str) -> str:
    """Remove `type/2` and `signature/2` fact lines from HTN source.

    Also drops a couple of section-comment headers for cleanliness. Those
    are comments and do not affect the engine, so this is cosmetic only.
    """
    out_lines = []
    for line in source.splitlines():
        if FACT_LINE_RE.match(line):
            continue
        s = line.strip()
        if s.startswith('% === Signatures') or s.startswith('% === Type Declarations'):
            continue
        out_lines.append(line)
    return '\n'.join(out_lines)


def _normalize_goal(goal: str) -> str:
    """Ensure goal string ends with a single period (FindAllPlans requires it)."""
    g = goal.strip()
    if not g.endswith('.'):
        g += '.'
    return g


def find_plans_json(source: str) -> str:
    """Compile + find all plans for the level's goals().

    Returns the JSON-as-string returned by FindAllPlansCustomVariables.
    Each level has a single `goals(...)` directive — we extract it via
    GetGoals() after compilation and feed it back to FindAllPlans.
    """
    planner = HtnPlanner(debug=False)
    compile_err = planner.HtnCompileCustomVariables(source)
    assert not compile_err, f"Compile failed: {compile_err}"

    err, goals = planner.GetGoals(customVariables=True)
    assert err is None, f"GetGoals failed: {err}"
    assert goals, "No goals() directive found in source"

    # Each level has exactly one goals() — match it and feed back.
    assert len(goals) == 1, f"Expected exactly 1 goal, got {len(goals)}: {goals}"
    goal_str = _normalize_goal(goals[0])

    err, plans_json = planner.FindAllPlansCustomVariables(goal_str)
    assert err is None, f"FindAllPlans failed: {err}"
    assert plans_json is not None, "FindAllPlans returned no result"
    return plans_json


def _assert_plans_equivalent(level_file: str):
    """Compare plans with and without type/signature facts."""
    path = os.path.join(ASSEMBLED_DIR, level_file)
    with open(path, 'r') as f:
        full = f.read()
    stripped = strip_type_signature_facts(full)

    # Sanity: stripping must actually remove something — otherwise the test
    # isn't proving anything.
    assert 'signature(' in full, f"{level_file}: expected signature(...) facts in source"
    assert 'type(' in full, f"{level_file}: expected type(...) facts in source"
    assert 'signature(' not in stripped, \
        f"{level_file}: stripping should have removed all signature(...) lines"
    assert 'type(' not in stripped, \
        f"{level_file}: stripping should have removed all type(...) lines"

    plans_with = find_plans_json(full)
    plans_without = find_plans_json(stripped)

    assert plans_with == plans_without, (
        f"{level_file}: plans differ with vs without type/signature facts.\n"
        f"With (first 500 chars):    {plans_with[:500]}\n"
        f"Without (first 500 chars): {plans_without[:500]}"
    )


# ------------------------- Per-level pytest cases -----------------------------

def test_puzzle1_plans_equivalent():
    _assert_plans_equivalent('puzzle1.htn')


def test_gh4_plans_equivalent():
    _assert_plans_equivalent('gamehack_gh4.htn')


def test_gh7_plans_equivalent():
    _assert_plans_equivalent('gamehack_gh7.htn')


def test_multipath_plans_equivalent():
    _assert_plans_equivalent('gamehack_multipath.htn')


def test_mvp_plans_equivalent():
    _assert_plans_equivalent('gamehack_mvp.htn')


# ------------------------- Strip-function unit tests --------------------------

def test_strip_function_works():
    """Direct unit test of strip_type_signature_facts."""
    src = (
        "% header\n"
        "type(agent, player).\n"
        "signature(moveTo, [agent, room]).\n"
        "  type(  cell, c5  ).\n"
        "op() :- if(at(?x)), do(moveTo(?x, target)).\n"
    )
    stripped = strip_type_signature_facts(src)
    assert 'type(' not in stripped
    assert 'signature(' not in stripped
    assert 'at(?x)' in stripped           # body call must NOT be stripped
    assert 'moveTo(?x, target)' in stripped  # body call must NOT be stripped


def test_type_in_method_body_not_stripped():
    """If `type/2` ever appears as a call inside a method body (not a fact),
    it must not be stripped. The regex requires the whole line to be a
    `type(...).` form — i.e. a fact, not part of a body.
    """
    src = "method(?x) :- if(type(?x, agent)), do()."
    stripped = strip_type_signature_facts(src)
    assert stripped == src  # unchanged


if __name__ == '__main__':
    test_strip_function_works()
    test_type_in_method_body_not_stripped()
    test_puzzle1_plans_equivalent()
    test_gh4_plans_equivalent()
    test_gh7_plans_equivalent()
    test_multipath_plans_equivalent()
    test_mvp_plans_equivalent()
    print("All plan-equivalence tests passed.")
