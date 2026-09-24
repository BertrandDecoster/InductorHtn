"""Tests for the Ring-Out level."""

import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import HtnPlanner
from htn_components.loader import ComponentLoader
from htn_components.combos import run_combos

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
COMPANIONS = {"player", "mage"}
PUSHERS = ["gust", "shieldBash"]
OTHERS = ["magnetize", "taunt", "translocate", "shadowStep", "pounce"]

# The measured matrix, unordered: every pusher with every non-pusher, and the
# swapper with either puller. Both seat orders win.
WINNING = {frozenset((p, o)) for p in PUSHERS for o in OTHERS} | {
    frozenset(("translocate", "magnetize")), frozenset(("translocate", "taunt"))}

_REPORT = []


def combos_report():
    if not _REPORT:
        _REPORT.append(run_combos(HERE, ROOT))
    return _REPORT[0]


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def _actor(op):
    return list(op[list(op.keys())[0]][0].keys())[0]


def plans_with(player, mage, goal="win."):
    """Plans with the player knowing `player` and the mage `mage`, on a fresh
    planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    loader = ComponentLoader(planner, ROOT)
    for dep in ("abilities/goals/neutralize", "abilities/strategies/passage",
                "abilities/primitives/ab_catalog"):
        loader.load(dep)
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, goal)


def _ops(plans):
    return " ".join(json.dumps(p) for p in plans).replace(" ", "")


def _op(name, *args):
    return f'"{name}":[' + ",".join('{"%s":[]}' % a for a in args) + "]"


class RingOutTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/strategies/passage", reset_first=False)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_lure_onto_the_brink_then_push(self):
        self.assert_plan("win.", contains=[
            "opForcedMove(mage, ogre, plinth, brink)", "opForcedMove(player, ogre, brink, void)",
            "opExploit(player, ogre, chasm, fell)"])

    def test_example_2_open_the_grate_push_from_behind(self):
        ops = _ops(plans_with("gust", "shadowStep"))
        assert _op("opDash", "mage", "gate", "perch") in ops or \
            _op("opDash", "mage", "yard", "perch") in ops, ops[:300]
        assert _op("opForcedMove", "player", "ogre", "plinth", "void") in ops
        self._record(True, "Example 2: the mage blinks onto the perch; the player shoves from the ledge")

    def test_example_3_ferry_the_puller_across_the_void(self):
        ops = _ops(plans_with("translocate", "taunt"))
        assert _op("opSwap", "player", "mage", "perch", "gate") in ops, ops[:300]
        assert _op("opForcedMove", "mage", "ogre", "plinth", "void") in ops
        self._record(True, "Example 3: the player swaps up, swaps the mage up; her taunt drags it in")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_companion_carries_a_plan_alone(self):
        plans = _solutions(self._planner, "win.")
        assert plans, "the level must be winnable"
        for plan in plans:
            allies = {_actor(op) for op in plan} & COMPANIONS
            assert len(allies) >= 2, f"one companion carries this plan alone: {plan}"
        self._record(True, f"P1: {len(plans)} plans, none by one companion")

    def test_property_p2_no_single_skill_wins(self):
        report = combos_report()
        assert not report.singles_winning, f"a single skill wins: {report.singles_winning}"
        self._record(True, "P2: no pool skill wins alone, even held by both")

    def test_property_p3_the_measured_pairs_win(self):
        report = combos_report()
        found = {frozenset((w["player"][0], w["mage"][0])) for w in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert len(report.winning) == 2 * len(WINNING), "each pair should win in both seat orders"
        assert not report.failures, report.failures
        self._record(True, f"P3: exactly the {len(WINNING)} measured pairs win, both ways round")

    def test_property_p4_a_push_from_the_yard_is_not_enough(self):
        """The ogre does not start on a line into the void: a push from the
        yard only moves it onto the ledge."""
        plans = plans_with("gust", "shieldBash")
        assert not plans, "two pushers should not ring it out"
        self._record(True, "P4: two pushers only shove it back and forth")


def run_tests():
    suite = RingOutTest()
    for method_name in sorted(dir(suite)):
        if method_name.startswith("test_"):
            suite.setup()
            method = getattr(suite, method_name)
            try:
                method()
            except AssertionError as e:
                suite._record(False, method_name, str(e))
            except Exception as e:
                suite._record(False, method_name, f"Error: {e}")
    print(suite.summary())
    return suite.all_passed()


if __name__ == "__main__":
    sys.exit(0 if run_tests() else 1)
