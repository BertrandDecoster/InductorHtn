"""Tests for the puzzle1 level."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite

BURN_GUARD1 = ("opMoveTo(arcanist, main, generator), opAggro(guard1, arcanist), "
               "opMoveTo(arcanist, generator, storage), opAggroMoveTo(guard1, generator, storage), "
               "opMoveTo(player, main, storage), opUseSkill(player, igniteSkill, guard1), "
               "opRemoveLocationTag(oil, storage), opAddLocationTag(burning, storage), "
               "opApplyTag(burning, player), opApplyTag(burning, arcanist), opApplyTag(burning, guard1), "
               "opApplyTag(dead, guard1)")
CHILL_GUARD2 = ("opAggro(guard2, player), opMoveTo(player, generator, corridor), "
                "opAggroMoveTo(guard2, generator, corridor), opMoveTo(arcanist, storage, corridor), "
                "opUseSkill(arcanist, frostSkill, guard2), opApplyTag(stunned, guard2), opApplyTag(dead, guard2)")


class Puzzle1Test(HtnTestSuite):
    """Test suite for the puzzle1 level."""

    def setup(self):
        """Load the goals (and, through their manifests, every dependency), then the level."""
        self.load_component("goals/clear_location", reset_first=True)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        with open(os.path.join(base_path, "levels/puzzle1/level.htn"), "r") as f:
            error = self._planner.HtnCompileCustomVariables(f.read())
        if error:
            raise RuntimeError(f"Failed to compile level: {error}")

    # =========================================================================
    # Example Tests
    # =========================================================================

    def test_example_1_puzzle_can_be_completed(self):
        """Example 1: the puzzle has exactly one plan."""
        self.assert_plan_set("completePuzzle.", [
            BURN_GUARD1 + ", opMoveTo(player, storage, generator), " + CHILL_GUARD2
            + ", opMoveTo(player, corridor, exit), opMoveTo(arcanist, corridor, exit)"])

    def test_example_2_guard1_uses_oil_and_burn(self):
        """Example 2: guard1 is lured onto the oil and set burning."""
        self.assert_plan_set("defeat(guard1).", [BURN_GUARD1])
        self.assert_state_after("defeat(guard1).",
            has=["hasTag(guard1,dead)", "locationCanApplyTag(storage,burning)"])

    def test_example_3_guard2_uses_wet_and_freeze(self):
        """Example 3: guard2 is lured into the wet corridor and chilled."""
        self.assert_plan_set("defeat(guard2).", [
            "opMoveTo(player, main, generator), " + CHILL_GUARD2.replace("storage, corridor", "main, corridor")])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_all_enemies_dead(self):
        """P1: after completing the puzzle, both guards are dead."""
        self.assert_state_after("completePuzzle.", has=["hasTag(guard1,dead)", "hasTag(guard2,dead)"])

    def test_property_p2_companions_at_exit(self):
        """P2: after completing the puzzle, both companions are at the exit; the dead stay behind."""
        self.assert_state_after("completePuzzle.",
            has=["at(player,exit)", "at(arcanist,exit)", "at(guard1,storage)", "at(guard2,corridor)"])


def run_tests():
    """Run all tests in this file."""
    suite = Puzzle1Test()
    for method_name in dir(suite):
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
