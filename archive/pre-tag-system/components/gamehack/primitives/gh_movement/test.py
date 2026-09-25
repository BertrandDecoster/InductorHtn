"""Tests for gh_movement primitive component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite

WORLD = ["location(room)", "location(hut)", "location(lake)"]


class GhMovementTest(HtnTestSuite):
    """Test suite for gh_movement primitive."""

    def setup(self):
        """Load the gh_movement component."""
        self.load_component("gamehack/primitives/gh_movement")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_direct_movement(self):
        """Example 1: one step to any location."""
        self.set_state(WORLD + ["at(player, room)"])
        self.assert_plan_set("goToLocation(player, hut).", ["opMoveTo(player, room, hut)"])
        self.assert_state_after("goToLocation(player, hut).",
            has=["at(player,hut)"], not_has=["at(player,room)"])

    def test_example_2_already_at_destination(self):
        """Example 2: already there, the plan shows opStayInLocation."""
        self.set_state(WORLD + ["at(player, room)"])
        self.assert_plan_set("goToLocation(player, room).", ["opStayInLocation(player)"])

    def test_example_3_go_to_same_location(self):
        """Example 3: go where the target stands."""
        self.set_state(WORLD + ["at(player, room)", "at(gob, hut)"])
        self.assert_plan_set("goToSameLocation(player, gob).", ["opMoveTo(player, room, hut)"])

    def test_example_4_already_at_same_location(self):
        """Example 4: already with the target."""
        self.set_state(WORLD + ["at(player, room)", "at(gob, room)"])
        self.assert_plan_set("goToSameLocation(player, gob).", ["opStayInLocation(player)"])

    def test_example_5_enemies_after_the_mover_follow(self):
        """Example 5: an enemy after the mover follows it; a static one stays."""
        self.set_state(WORLD + ["at(player, room)", "at(gob, room)", "at(tower, room)",
                                "hasAggro(gob, player)", "hasAggro(tower, player)", "static(tower)"])
        self.assert_plan_set("goToLocation(player, lake).",
            ["opMoveTo(player, room, lake), opAggroMoveTo(gob, room, lake)"])

    def test_example_6_not_a_location(self):
        """Example 6: the destination must be a location."""
        self.set_state(WORLD + ["at(player, room)"])
        self.assert_no_plan("goToLocation(player, nowhere).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_single_location(self):
        """P1: Entity at exactly one location after move."""
        self.set_state(WORLD + ["at(player, room)"])
        self.run_goal("goToLocation(player, hut)")
        state = self.get_state()
        player_locations = [f for f in state if f.startswith("at(player,")]
        assert len(player_locations) == 1,             f"P1 violated: player at {len(player_locations)} locations: {player_locations}"

    def test_property_p2_idempotent(self):
        """P2: Moving to current location changes no state."""
        self.set_state(WORLD + ["at(player, room)"])
        initial_state = set(self.get_state())
        self.run_goal("goToLocation(player, room)")
        final_state = set(self.get_state())
        assert initial_state == final_state,             f"P2 violated: state changed. Added: {final_state - initial_state}, Removed: {initial_state - final_state}"


def run_tests():
    """Run all tests in this file."""
    suite = GhMovementTest()
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
