"""Replaying a plan's del/add must see every compiled source and must say
when it could not.

`play --interactive` shows the world after each step by replaying operator
effects. That is only honest if the operator templates come from the same
sources the planner compiled - including `level.htn` - and if an operator
whose template is missing is reported rather than silently treated as a
no-op.

Run:  python -m pytest tests/test_replay_sources.py -v
"""

import json
import os

from test_fun_metrics import FIXTURES, PROJECT_ROOT  # noqa: E402

from htn_metrics.extract import (  # noqa: E402
    extract_plan_space, ground_solution, load_level_spec, replay_with_check,
)


def test_loader_records_the_level_source():
    """`load_level_htn` must append level.htn to `sources`, so operators the
    level defines can be grounded."""
    from htn_components.loader import ComponentLoader
    from indhtnpy import HtnPlanner

    planner = HtnPlanner(False)
    loader = ComponentLoader(planner, PROJECT_ROOT)
    loader.load_level_htn(os.path.join(FIXTURES, "reference_good"))
    label, text = loader.sources[-1]
    assert label == "levels/reference_good"
    assert "opStashBag" in text


def test_missing_template_is_reported_as_unresolved():
    """No template means no effects, and that must be visible."""
    ops = ground_solution([{"opNope": [{"player": []}]}], sources=[])
    assert len(ops) == 1
    assert ops[0].effects_resolved is False
    assert ops[0].dels == [] and ops[0].adds == []


def test_replay_check_matches_the_planner_and_names_unresolved_operators():
    """The replayed final state must equal `GetSolutionFacts`; when a template
    is missing the check must name the operator instead of passing."""
    from htn_metrics.extract import LevelPlanner

    path = os.path.join(FIXTURES, "reference_good")
    spec = load_level_spec(path)
    space = extract_plan_space(path, spec=spec)
    plan = space.plans[0]

    planner, _loader = LevelPlanner(spec).build()
    error, _ = planner.FindAllPlansCustomVariables(space.goal + ".")
    assert not error
    error, facts_json = planner.GetSolutionFacts(0)
    assert not error
    expected = set(json.loads(facts_json))

    states, warnings = replay_with_check(space.initial_facts, plan.operators, expected)
    assert states[-1] == expected
    assert warnings == []

    crippled = ground_solution(
        [{"opStashBag": [{"player": []}]}], sources=[]
    ) + plan.operators[1:]
    _states, warnings = replay_with_check(space.initial_facts, crippled, expected)
    assert any("opStashBag" in w for w in warnings), warnings
    assert any("differs" in w or "mismatch" in w for w in warnings), warnings
