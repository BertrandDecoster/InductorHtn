"""Tests for complete_toy_level goal component."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import findAllPlansResultToPrologStringList

# Two rooms, gob1 in room2; a wet puddle is an area of its own. companion1 holds a chilled skill,
# gob1 is vulnerable to wet + chilled -> only wetAndFreeze works: companion2 lures, companion1 chills.
TOY_WORLD = [
    "location(room1)", "location(room2)", "location(puddle1)",
    "plateOpens(plate1, door1)", "plateOpens(plate2, door1)",
    "enemy(gob1)", "at(gob1, room2)",
    "companion(companion1)", "companion(companion2)",
    "at(companion1, room1)", "at(companion2, room1)",
    "locationCanApplyTag(puddle1, wet)",
    "hasSkill(companion1, frostSkill)", "skillAppliesTag(frostSkill, chilled)",
    "vulnerableToLocationCombo(gob1, wet, chilled)",
]


class CompleteToyLevelTest(HtnTestSuite):
    """Test suite for the M0 toy-level goal."""

    def setup(self):
        self.load_component("gamehack/goals/complete_toy_level")

    def _plans(self, goal):
        self._reload_file()
        error, result = self._planner.FindAllPlansCustomVariables(goal)
        assert error is None, f"Planning error: {error}"
        return findAllPlansResultToPrologStringList(result)

    def test_example_1_full_sequence(self):
        """Locked door + enemy alive -> unlock, then defeat."""
        self.set_state(TOY_WORLD + ["locked(door1)"])
        self.assert_plan("completeToyLevel().",
            contains=["opUnlock(door1)", "opAggroMoveTo(gob1, room2, puddle1)",
                      "opUseSkill(companion1, frostSkill, gob1), opApplyTag(stunned, gob1), opApplyTag(dead, gob1)"],
            min_solutions=4, max_solutions=4)

    def test_example_1b_unlock_comes_first(self):
        """In every plan, the door unlocks before any tag lands."""
        self.set_state(TOY_WORLD + ["locked(door1)"])
        plans = self._plans("completeToyLevel().")
        assert plans, "expected plans"
        for p in plans:
            assert p.index("opUnlock(door1)") < p.index("opApplyTag("), f"unlock after a tag: {p}"

    def test_example_2_door_already_unlocked(self):
        """Door unlocked -> no unlock step, still defeat."""
        self.set_state(TOY_WORLD)
        self.assert_plan("completeToyLevel().",
            contains=["opApplyTag(stunned, gob1), opApplyTag(dead, gob1)"],
            not_contains=["opUnlock", "opDoorAlreadyUnlocked", "opSynchronizeOnPlates"])

    def test_example_3_enemy_gone(self):
        """No enemy -> empty plan (level already complete)."""
        self.set_state(["locked(door1)", "plateOpens(plate1, door1)", "plateOpens(plate2, door1)",
                        "companion(companion1)", "companion(companion2)"])
        self.assert_plan_set("completeToyLevel().", [""])

    def test_property_p1_ordering(self):
        """P1: the door unlocks before any tag lands, in every plan."""
        self.set_state(TOY_WORLD + ["locked(door1)"])
        for p in self._plans("completeToyLevel()."):
            assert p.index("opUnlock(door1)") < p.index("opApplyTag("), f"P1 violated: {p}"

    def test_property_p2_graceful_completion(self):
        """P2: a beat whose state already holds is skipped, not failed: no door, no enemy -> the empty plan."""
        self.set_state(["companion(companion1)", "companion(companion2)"])
        self.assert_plan_set("completeToyLevel().", [""])


def run_tests():
    suite = CompleteToyLevelTest()
    suite.setup()
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
    success = run_tests()
    sys.exit(0 if success else 1)
