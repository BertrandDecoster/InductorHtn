"""Tests for locomotion primitive component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite


class LocomotionTest(HtnTestSuite):
    """Test suite for locomotion primitive."""

    def setup(self):
        """Load the locomotion component (resets planner for clean state)."""
        # load_component with reset_first=True (default) creates fresh planner
        self.load_component("primitives/locomotion")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_direct_movement(self):
        """Example 1: Direct movement

        Given: at(player, roomA), connected(roomA, roomB)
        When: moveTo(player, roomB)
        Then: Plan contains opMoveTo, final state has at(player, roomB)
        """
        self.set_state([
            "at(player, roomA)",
            "connected(roomA, roomB)"
        ])

        self.assert_plan("moveTo(player, roomB).",
            contains=["opMoveTo(player, roomA, roomB)"])

        # Note: facts are stored without spaces after commas
        self.assert_state_after("moveTo(player, roomB).",
            has=["at(player,roomB)"],
            not_has=["at(player,roomA)"])

    def test_example_2_already_at_destination(self):
        """Example 2: Already at destination

        Given: at(player, roomA)
        When: moveTo(player, roomA)
        Then: Plan is empty (no operators)
        """
        self.set_state([
            "at(player, roomA)"
        ])

        # Should succeed with empty plan
        self.assert_plan("moveTo(player, roomA).",
            not_contains=["opMoveTo"])

    def test_example_3_multi_hop_path(self):
        """Example 3: Multi-hop path

        Given: at(player, roomA), connections through corridor
        When: moveTo(player, roomB)
        Then: Plan contains two opMoveTo operations
        """
        self.set_state([
            "at(player, roomA)",
            "connected(roomA, corridor)",
            "connected(corridor, roomB)",
            "pathThrough(roomA, roomB, corridor)"
        ])

        self.assert_plan("moveTo(player, roomB).",
            contains=["opMoveTo(player, roomA, corridor)",
                     "opMoveTo(player, corridor, roomB)"])

        # Note: facts are stored without spaces after commas
        self.assert_state_after("moveTo(player, roomB).",
            has=["at(player,roomB)"],
            not_has=["at(player,roomA)"])

    def test_example_4_unreachable_destination(self):
        """Example 4: Unreachable destination

        Given: at(player, roomA), no connection to roomC
        When: moveTo(player, roomC)
        Then: Planning fails
        """
        self.set_state([
            "at(player, roomA)"
            # No connections defined
        ])

        self.assert_no_plan("moveTo(player, roomC).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_single_location(self):
        """P1: An entity can only be at one location at a time.

        After moving, entity should not be at old location.
        """
        self.set_state([
            "at(player, roomA)",
            "connected(roomA, roomB)"
        ])

        # Run the goal
        self.run_goal("moveTo(player, roomB)")
        state = self.get_state()

        # Count how many at(player, ?) facts exist
        player_locations = [f for f in state if f.startswith("at(player,")]
        assert len(player_locations) == 1, \
            f"P1 violated: player at {len(player_locations)} locations: {player_locations}"

    def test_property_p2_conservation(self):
        """P2: Moving doesn't create or destroy entities.

        The entity should still exist after moving.
        """
        self.set_state([
            "at(player, roomA)",
            "connected(roomA, roomB)"
        ])

        self.run_goal("moveTo(player, roomB)")
        state = self.get_state()

        # Player should still exist somewhere
        player_exists = any(f.startswith("at(player,") for f in state)
        assert player_exists, "P2 violated: player no longer exists after move"

    def test_property_p3_idempotent(self):
        """P3: Moving to current location is a no-op.

        State should be unchanged after moving to same location.
        """
        self.set_state([
            "at(player, roomA)"
        ])

        initial_state = set(self.get_state())
        self.run_goal("moveTo(player, roomA)")
        final_state = set(self.get_state())

        # State should be identical
        assert initial_state == final_state, \
            f"P3 violated: state changed. Added: {final_state - initial_state}, Removed: {initial_state - final_state}"

    # =========================================================================
    # Additional Tests
    # =========================================================================

    def test_example_5_multiple_entities_independent(self):
        """Example 5: Multiple entities move independently."""
        self.set_state([
            "at(player, roomA)",
            "at(warden, roomB)",
            "connected(roomA, roomB)",
            "connected(roomB, roomC)"
        ])

        # Move player to roomB
        self.assert_plan("moveTo(player, roomB).",
            contains=["opMoveTo(player, roomA, roomB)"])

        # Move warden to roomC (separate test instance needed)
        # Reset and test warden
        self.setup()
        self.set_state([
            "at(player, roomA)",
            "at(warden, roomB)",
            "connected(roomA, roomB)",
            "connected(roomB, roomC)"
        ])

        self.assert_plan("moveTo(warden, roomC).",
            contains=["opMoveTo(warden, roomB, roomC)"])


def run_tests():
    """Run all tests in this file."""
    suite = LocomotionTest()
    suite.setup()

    # Run all test methods
    for method_name in dir(suite):
        if method_name.startswith("test_"):
            # Reset state for each test
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
