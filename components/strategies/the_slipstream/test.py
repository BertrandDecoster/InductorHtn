"""Tests for the_slipstream strategy component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite


class TheSlipstreamTest(HtnTestSuite):
    """Test suite for the_slipstream strategy."""

    def setup(self):
        """Load the_slipstream strategy and its dependencies."""
        # Load dependencies first
        self.load_component("primitives/locomotion", reset_first=True)
        self.load_component("primitives/tags", reset_first=False)
        # Load the strategy
        self.load_component("strategies/the_slipstream", reset_first=False)

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_slide_through_corridor(self):
        """Example 1: Slide through corridor into hazard

        Given: Enemy in roomA, fire hazard in roomC, path through corridor
        When: theSlipstream(enemy1)
        Then: Enemy in roomC with burning tag
        """
        self.set_state([
            "at(enemy1, roomA)",
            "roomHasHazard(roomC, fire)",
            "pathThrough(roomA, roomC, corridor)",
            "canApplyTag(arcanist, frozen)"
        ])

        self.assert_plan("theSlipstream(enemy1).",
            contains=["opApplyRoomTag", "opMoveTo"])

        self.assert_state_after("theSlipstream(enemy1).",
            has=["at(enemy1,roomC)", "hasTag(enemy1,burning)"])

    def test_example_2_direct_push(self):
        """Example 2: Direct push into adjacent hazard

        Given: Enemy adjacent to electricity hazard room
        When: theSlipstream(enemy1)
        Then: Enemy electrified
        """
        self.set_state([
            "at(enemy1, roomA)",
            "roomHasHazard(roomB, electricity)",
            "connected(roomA, roomB)",
            "canApplyTag(arcanist, frozen)"
        ])

        self.assert_state_after("theSlipstream(enemy1).",
            has=["at(enemy1,roomB)", "hasTag(enemy1,electrified)"])

    def test_example_3_no_path_to_hazard(self):
        """Example 3: No path to hazard

        Given: No connection between enemy and hazard room
        When: theSlipstream(enemy1)
        Then: Planning fails
        """
        self.set_state([
            "at(enemy1, roomA)",
            "roomHasHazard(roomC, fire)",
            # No path or connection
            "canApplyTag(arcanist, frozen)"
        ])

        self.assert_no_plan("theSlipstream(enemy1).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_enemy_relocated(self):
        """P1: Enemy ends up in hazard room."""
        self.set_state([
            "at(enemy1, roomA)",
            "roomHasHazard(roomB, spikes)",
            "connected(roomA, roomB)",
            "canApplyTag(arcanist, frozen)"
        ])

        self.run_goal("theSlipstream(enemy1)")
        state = self.get_state()

        in_hazard_room = any("at(enemy1,roomB)" in f for f in state)
        assert in_hazard_room, "P1 violated: enemy should be in hazard room"

    def test_property_p2_hazard_effect_applied(self):
        """P2: Enemy receives tag from hazard."""
        self.set_state([
            "at(enemy1, roomA)",
            "roomHasHazard(roomB, acid)",
            "connected(roomA, roomB)",
            "canApplyTag(arcanist, frozen)"
        ])

        self.run_goal("theSlipstream(enemy1)")
        state = self.get_state()

        has_dissolved = any("hasTag(enemy1,dissolved)" in f for f in state)
        assert has_dissolved, "P2 violated: enemy should have dissolved tag"

    def test_property_p3_requires_freeze(self):
        """P3: Requires freeze ability."""
        self.set_state([
            "at(enemy1, roomA)",
            "roomHasHazard(roomB, fire)",
            "connected(roomA, roomB)"
            # Missing: canApplyTag(arcanist, frozen)
        ])

        self.assert_no_plan("theSlipstream(enemy1).")


def run_tests():
    """Run all tests in this file."""
    suite = TheSlipstreamTest()
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
