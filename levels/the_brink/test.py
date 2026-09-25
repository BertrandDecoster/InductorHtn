"""Tests for The Brink level."""

import itertools
import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite

LEVEL_DIR = os.path.dirname(os.path.abspath(__file__))
COMPANIONS = {"player", "warden"}

# The plan set the level header states, per kit (P1). Every other kit: no plan.
EXPECTED = {
    ("gust", "ignite"): 2,
    ("gust", "dash"): 1,
    ("dash", "ignite"): 1,
}


def _plans(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def _actors(plan):
    return {list(op[list(op.keys())[0]][0].keys())[0] for op in plan}


class TheBrinkTest(HtnTestSuite):

    def setup(self):
        self.load_component("core/goals/exploit_weakness", reset_first=True)
        self.verify_contracts()
        self._loader.load_level_htn(LEVEL_DIR)

    def _kit_plans(self, kit):
        """Every plan for the encounter with the player's kit replaced by
        `kit`, on a fresh planner (a failed search locks the rule set)."""
        source = open(os.path.join(LEVEL_DIR, "level.htn")).read()
        picks = dict(re.findall(r"funChoiceFact\((\w+), (hasSkill\(player, \w+\))\)", source))
        lines = [line for line in source.splitlines() if line.strip().rstrip(".") not in picks.values()]
        lines += [picks[p] + "." for p in kit]
        fresh = HtnTestSuite()
        fresh.load_component("core/goals/exploit_weakness", reset_first=True)
        error = fresh._planner.HtnCompileCustomVariables("\n".join(lines) + "\n")
        assert error is None, error
        return _plans(fresh._planner, "clearTheBrink.")

    def _pool(self):
        source = open(os.path.join(LEVEL_DIR, "level.htn")).read()
        return re.findall(r"funChoice\(kit, (\w+)\)", source)

    # ---------------------------------------------------------------- examples

    def test_example_1_rung_out_then_burned(self):
        self.assert_plan("clearTheBrink.", contains=[
            "opPush(player, ogre, keep, brink)",
            "opPush(player, ogre, brink, void)",
            "opLure(warden, bearer, tower, bridge)",
            "opCastRegion(player, ignite, bridge, rope, abyss)",
        ])

    def test_example_2_one_burn_takes_both(self):
        self.assert_plan("clearTheBrink.", contains=[
            "opPush(player, ogre, keep, bridge)",
            "opLure(warden, bearer, tower, bridge)",
            "opCastRegion(player, ignite, bridge, rope, abyss)",
        ])
        plans = _plans(self._planner, "clearTheBrink.")
        both = [p for p in plans if '"void"' not in json.dumps(p)]
        assert len(both) == 1, f"expected one plan with no ring-out, got {len(both)}"
        self._record(True, "Example 2: one plan burns both")

    def test_example_3_taunted_to_the_edge_pulled_from_the_far_side(self):
        plans = self._kit_plans(("gust", "dash"))
        assert len(plans) == 1, plans
        text = json.dumps(plans[0]).replace(" ", "")
        for op in ['{"opTaunt":[{"player":[]},{"bearer":[]},{"tower":[]},{"brink":[]}]}',
                   '{"opNavigate":[{"warden":[]},{"gate":[]},{"ledge":[]}]}',
                   '{"opLure":[{"warden":[]},{"bearer":[]},{"brink":[]},{"void":[]}]}']:
            assert op in text, f"{op} not in {text}"
        self._record(True, "Example 3: taunted to the edge, pulled from the far side")

    # -------------------------------------------------------------- properties

    def test_property_p1_the_plan_set_is_the_stated_one(self):
        for kit in itertools.combinations(self._pool(), 2):
            count = len(self._kit_plans(kit))
            want = EXPECTED.get(kit, EXPECTED.get(kit[::-1], 0))
            assert count == want, f"kit {kit}: {count} plans, the header says {want}"
        self._record(True, "P1: the plan set is the stated one")

    def test_property_p2_no_companion_carries_a_plan_alone(self):
        for kit in itertools.combinations(self._pool(), 2):
            for plan in self._kit_plans(kit):
                allies = _actors(plan) & COMPANIONS
                assert allies == COMPANIONS, f"kit {kit}: carried by {allies} alone: {plan}"
        self._record(True, "P2: no companion carries a plan alone")

    def test_property_p3_the_bearer_resists_a_push(self):
        self.assert_no_plan("push(bearer, bridge).")


def run_tests():
    suite = TheBrinkTest()
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
