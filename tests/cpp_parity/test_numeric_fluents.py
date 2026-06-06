"""
Python parity tests for numeric-fluent operator effects.

Mirrors the C++ TEST(...) cases in
src/Tests/Htn/HtnNumericFluentTests.cpp (Tasks 2-4) but exercises the
behaviour through the Python ctypes binding (`indhtnpy`). The point is
to pin that:

  1. The shared library loaded by Python implements the new
     `increase(F, expr)` / `decrease(F, expr)` operator effects.
  2. State observed via `GetSolutionFacts` after `FindAllPlansCustomVariables`
     matches what the C++ HtnFluentHelper tests assert at the engine level.
  3. The verbose `del/add/is`-based pattern and the concise
     `increase`/`decrease` pattern produce identical final fact sets
     when routed through the Python binding -- not just at the C++ layer.
  4. Operator-application failures (no matching fluent fact) propagate
     correctly through the binding as "no solutions" rather than crashes.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from conftest import HtnTestHelper  # noqa: E402

# Re-import HtnPlanner directly: a couple of these tests need to drive the
# planner manually (multi-goal sequences, custom equivalence comparison)
# rather than go through HtnTestHelper's single-helper-per-call lifecycle.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "Python"))
from indhtnpy import HtnPlanner  # noqa: E402


def _facts_for_solution(planner: HtnPlanner, index: int = 0):
    """Decode GetSolutionFacts JSON into a Python list of fact strings.

    Returns [] on error or no solution facts.
    """
    err, facts_json = planner.GetSolutionFacts(index)
    if err is not None or facts_json is None:
        return []
    return json.loads(facts_json)


def _facts_filtered(planner: HtnPlanner, index: int, predicate_names):
    """Get solution facts filtered to the given predicate functor names.

    Returns a set of fact strings so two final states can be compared
    by value-equality. Mirrors C++ FactsOfPredicates in HtnNumericFluentTests.cpp.
    """
    facts = _facts_for_solution(planner, index)
    keep = set()
    for f in facts:
        # facts are strings like "score(player,15)" or "mana(player,30)"
        # the functor name is the prefix up to "(" (or the whole string
        # for a 0-arity atom)
        head_end = f.find("(")
        head = f if head_end == -1 else f[:head_end]
        if head in predicate_names:
            keep.add(f)
    return keep


def _plan_and_get_facts(program_with_goals: str, goal_query: str):
    """Compile a program (rules only), find plans for `goal_query`, and
    return (planner, plan_json, facts_list).

    `plan_json` is the parsed result of FindAllPlansCustomVariables.
    `facts_list` is the parsed list of fact strings from solution 0,
    or [] if there was no successful solution.
    """
    planner = HtnPlanner(False)
    err = planner.HtnCompileCustomVariables(program_with_goals)
    if err is not None:
        raise RuntimeError(f"Compile error: {err}")

    err, plans_str = planner.FindAllPlansCustomVariables(goal_query)
    if err is not None:
        return planner, None, []

    plans = json.loads(plans_str)
    # "false" shape => no solution
    if len(plans) > 0 and isinstance(plans[0], dict) and "false" in plans[0]:
        return planner, plans, []

    return planner, plans, _facts_for_solution(planner, 0)


class TestNumericFluentsViaPython:
    """Test 5.1 / 5.2 / 5.4 from the task spec.

    Each test mirrors a specific C++ test in HtnNumericFluentTests.cpp and
    re-asserts the same invariant through the Python binding.
    """

    # Test 5.1 -- mirrors C++ TEST(IncreaseUpdatesFact)
    def test_increase_via_python(self):
        program = (
            "score(player, 10). "
            "opGain(?n) :- increase(score(player), ?n). "
        )
        planner, plans, facts = _plan_and_get_facts(program, "opGain(5).")

        # Plan must succeed and contain opGain(5)
        assert plans is not None, "FindAllPlans returned an error"
        assert len(plans) == 1, f"expected 1 plan, got {plans}"
        assert "opGain" in plans[0][0], f"expected opGain in plan: {plans}"

        # State assertions: score(player,10) gone, score(player,15) present
        assert "score(player,15)" in facts, f"facts: {facts}"
        assert "score(player,10)" not in facts, f"facts: {facts}"

    # Test 5.2 -- mirrors C++ TEST(DecreaseUpdatesFact)
    def test_decrease_via_python(self):
        program = (
            "score(player, 10). "
            "opLose(?n) :- decrease(score(player), ?n). "
        )
        planner, plans, facts = _plan_and_get_facts(program, "opLose(3).")

        assert plans is not None
        assert len(plans) == 1, f"expected 1 plan, got {plans}"

        # 10 - 3 = 7
        assert "score(player,7)" in facts, f"facts: {facts}"
        assert "score(player,10)" not in facts, f"facts: {facts}"

    # Test 5.4 -- mirrors C++ TEST(NoMatchingFactFails). The fluent
    # operator must fail to apply (and the plan must fail) when there
    # is no score(player, _) fact in state -- not crash, not silently
    # succeed with no effect.
    def test_fluent_failure_via_python(self):
        program = (
            # NB: no score(player, ...) fact at all -- the operator's
            # increase() can't bind to anything.
            "opGain(?n) :- increase(score(player), ?n). "
        )
        planner = HtnPlanner(False)
        err = planner.HtnCompileCustomVariables(program)
        assert err is None, f"Compile error: {err}"

        err, plans_str = planner.FindAllPlansCustomVariables("opGain(5).")
        # The plan call itself shouldn't be an error -- failure shows up
        # as the "false" JSON shape, same as any other failed plan.
        assert err is None, f"plan err: {err}"

        plans = json.loads(plans_str)
        # Failure shape is [{"false":[]}, {"failureIndex":[...]}].
        # Either way, no successful first solution.
        is_failure = (
            len(plans) > 0
            and isinstance(plans[0], dict)
            and "false" in plans[0]
        )
        assert is_failure, f"expected planning failure, got: {plans}"

    # Sanity follow-up to 5.4: decrease on missing fact also fails
    # cleanly. Different code path inside the helper (one uses
    # increase, the other decrease), so worth pinning separately.
    def test_fluent_failure_decrease_via_python(self):
        program = (
            "opLose(?n) :- decrease(score(player), ?n). "
        )
        planner = HtnPlanner(False)
        err = planner.HtnCompileCustomVariables(program)
        assert err is None, f"Compile error: {err}"

        err, plans_str = planner.FindAllPlansCustomVariables("opLose(3).")
        assert err is None

        plans = json.loads(plans_str)
        is_failure = (
            len(plans) > 0
            and isinstance(plans[0], dict)
            and "false" in plans[0]
        )
        assert is_failure, f"expected planning failure, got: {plans}"


class TestFluentEquivalenceViaPython:
    """Test 5.3 -- parity for the verbose-vs-concise equivalence.

    Mirrors C++ TEST(FluentEquivalentToDelAdd_BasicSpendAndGain). The
    headline guarantee is "increase/decrease is a sugar for the verbose
    is/del/add pattern" -- after running the same goal sequence on both
    rulesets, the final fact sets must be identical when restricted to
    the fluent predicates under test.

    We assert through the Python binding to make sure the equivalence
    holds end-to-end across the FFI boundary too, not just in the C++
    layer that the Tests 4.x cases pin.
    """

    def test_fluent_equivalent_via_python(self):
        verbose_program = (
            "mana(player, 50). "
            "xp(player, 0). "
            "spend(?c) :- if(mana(player, ?o), is(?n, -(?o, ?c))), "
            "             do(opVerboseSpend(?o, ?n)). "
            "opVerboseSpend(?o, ?n) :- del(mana(player, ?o)), add(mana(player, ?n)). "
            "gain(?a) :- if(xp(player, ?o), is(?n, +(?o, ?a))), "
            "            do(opVerboseGain(?o, ?n)). "
            "opVerboseGain(?o, ?n) :- del(xp(player, ?o)), add(xp(player, ?n)). "
        )
        concise_program = (
            "mana(player, 50). "
            "xp(player, 0). "
            "spend(?c) :- if(), do(opConciseSpend(?c)). "
            "opConciseSpend(?c) :- decrease(mana(player), ?c). "
            "gain(?a) :- if(), do(opConciseGain(?a)). "
            "opConciseGain(?a) :- increase(xp(player), ?a). "
        )
        goal_query = "spend(15), gain(7), spend(5)."

        p_verbose, _, _ = _plan_and_get_facts(verbose_program, goal_query)
        p_concise, _, _ = _plan_and_get_facts(concise_program, goal_query)

        preds = {"mana", "xp"}
        verbose_facts = _facts_filtered(p_verbose, 0, preds)
        concise_facts = _facts_filtered(p_concise, 0, preds)

        # The headline check: identical final state across the two forms.
        assert verbose_facts == concise_facts, (
            f"verbose: {sorted(verbose_facts)}\nconcise: {sorted(concise_facts)}"
        )

        # Belt-and-braces: both arrived at the expected final values.
        # 50 - 15 - 5 = 30 mana, 0 + 7 = 7 xp.
        assert "mana(player,30)" in verbose_facts
        assert "xp(player,7)" in verbose_facts
        assert "mana(player,30)" in concise_facts
        assert "xp(player,7)" in concise_facts

    # Smaller sanity equivalence: a single increase. If this fails but
    # the multi-step one above does too, the diagnostic is much easier
    # to read because there are only 2 fluents to inspect.
    def test_fluent_equivalent_single_step_via_python(self):
        verbose_program = (
            "score(player, 10). "
            "gain(?a) :- if(score(player, ?o), is(?n, +(?o, ?a))), "
            "            do(opVerboseGain(?o, ?n)). "
            "opVerboseGain(?o, ?n) :- del(score(player, ?o)), add(score(player, ?n)). "
        )
        concise_program = (
            "score(player, 10). "
            "gain(?a) :- if(), do(opConciseGain(?a)). "
            "opConciseGain(?a) :- increase(score(player), ?a). "
        )
        goal_query = "gain(5)."

        p_verbose, _, _ = _plan_and_get_facts(verbose_program, goal_query)
        p_concise, _, _ = _plan_and_get_facts(concise_program, goal_query)

        preds = {"score"}
        verbose_facts = _facts_filtered(p_verbose, 0, preds)
        concise_facts = _facts_filtered(p_concise, 0, preds)

        assert verbose_facts == concise_facts, (
            f"verbose: {sorted(verbose_facts)}\nconcise: {sorted(concise_facts)}"
        )
        assert verbose_facts == {"score(player,15)"}
