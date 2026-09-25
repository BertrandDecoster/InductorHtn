"""Tests for gh_movement primitive component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


class GhMovementTest(HtnTestSuite):
    """Test suite for gh_movement primitive."""

    def setup(self):
        """Load the gh_movement component."""
        self.load_component("gamehack/primitives/gh_movement")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_direct_movement(self):
        """Example 1: Direct movement

        Given: at(player, room)
        When: goToLocation(player, hut)
        Then: Plan contains opMoveTo, final state has at(player, hut)
        """
        self.set_state([
            "at(player, room)"
        ])

        self.assert_plan("goToLocation(player, hut).",
            contains=["opMoveTo(player, room, hut)"])

        self.assert_state_after("goToLocation(player, hut).",
            has=["at(player,hut)"],
            not_has=["at(player,room)"])

    def test_example_2_already_at_destination(self):
        """Example 2: Already at destination

        Given: at(player, room)
        When: goToLocation(player, room)
        Then: No opMoveTo, uses opStayInLocation
        """
        self.set_state([
            "at(player, room)"
        ])

        self.assert_plan("goToLocation(player, room).",
            contains=["opStayInLocation(player)"],
            not_contains=["opMoveTo"])

    def test_example_3_go_to_same_location(self):
        """Example 3: Go to same location as target

        Given: at(player, room), at(gob, hut)
        When: goToSameLocation(player, gob)
        Then: Plan contains opMoveTo(player, room, hut)
        """
        self.set_state([
            "at(player, room)",
            "at(gob, hut)"
        ])

        self.assert_plan("goToSameLocation(player, gob).",
            contains=["opMoveTo(player, room, hut)"])

        self.assert_state_after("goToSameLocation(player, gob).",
            has=["at(player,hut)"])

    def test_example_4_already_at_same_location(self):
        """Example 4: Already at same location as target

        Given: at(player, room), at(gob, room)
        When: goToSameLocation(player, gob)
        Then: opStayInLocation, no opMoveTo
        """
        self.set_state([
            "at(player, room)",
            "at(gob, room)"
        ])

        self.assert_plan("goToSameLocation(player, gob).",
            contains=["opStayInLocation(player)"],
            not_contains=["opMoveTo"])

    def test_example_5_static_entity_cannot_move(self):
        """Example 5: Static entity cannot move

        Given: at(tower, lake), at(gob, hut), static(tower)
        When: goToSameLocation(tower, gob)
        Then: Planning fails
        """
        self.set_state([
            "at(tower, lake)",
            "at(gob, hut)",
            "static(tower)"
        ])

        self.assert_no_plan("goToSameLocation(tower, gob).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_single_location(self):
        """P1: Entity at exactly one location after move."""
        self.set_state([
            "at(player, room)"
        ])

        self.run_goal("goToLocation(player, hut)")
        state = self.get_state()

        player_locations = [f for f in state if f.startswith("at(player,")]
        assert len(player_locations) == 1, \
            f"P1 violated: player at {len(player_locations)} locations: {player_locations}"

    def test_property_p2_idempotent(self):
        """P2: Moving to current location is a no-op (state unchanged except no-op operator)."""
        self.set_state([
            "at(player, room)"
        ])

        initial_state = set(self.get_state())
        self.run_goal("goToLocation(player, room)")
        final_state = set(self.get_state())

        assert initial_state == final_state, \
            f"P2 violated: state changed. Added: {final_state - initial_state}, Removed: {initial_state - final_state}"


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
