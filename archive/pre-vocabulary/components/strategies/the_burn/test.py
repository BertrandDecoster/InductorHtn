"""Tests for the_burn strategy component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite


class TheBurnTest(HtnTestSuite):
    """Test suite for the_burn strategy."""

    def setup(self):
        """Load the_burn strategy and its dependencies."""
        # Load dependencies first
        self.load_component("primitives/locomotion", reset_first=True)
        self.load_component("primitives/tags", reset_first=False)
        self.load_component("primitives/aggro", reset_first=False)
        # Load the strategy
        self.load_component("strategies/the_burn", reset_first=False)

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_basic_burn(self):
        """Example 1: Basic burn strategy

        Given: Player and enemy in roomA, oil in roomB
        When: theBurn(enemy1)
        Then: Enemy gets burned, oil consumed
        """
        self.set_state([
            "at(player, roomA)",
            "at(enemy1, roomA)",
            "roomHasHazard(roomB, oil)",
            "canApplyTag(player, burning)",
            "connected(roomA, roomB)"
        ])

        # Plan should include movement and burning
        self.assert_plan("theBurn(enemy1).",
            contains=["opMoveTo", "opApplyTag"])

        self.assert_state_after("theBurn(enemy1).",
            has=["hasTag(enemy1,burning)", "hazardConsumed(roomB,oil)"],
            not_has=["roomHasHazard(roomB,oil)"])

    def test_example_2_enemy_already_in_oil_room(self):
        """Example 2: Enemy already in oil room

        Given: Enemy already in roomB with oil
        When: theBurn(enemy1)
        Then: Just need to ignite
        """
        self.set_state([
            "at(player, roomA)",
            "at(enemy1, roomB)",
            "roomHasHazard(roomB, oil)",
            "canApplyTag(player, burning)",
            "connected(roomA, roomB)"
        ])

        self.assert_state_after("theBurn(enemy1).",
            has=["hasTag(enemy1,burning)"])

    def test_example_3_no_oil_room(self):
        """Example 3: No oil room available

        Given: No room with oil hazard
        When: theBurn(enemy1)
        Then: Planning fails
        """
        self.set_state([
            "at(player, roomA)",
            "at(enemy1, roomA)",
            "canApplyTag(player, burning)"
            # No roomHasHazard with oil
        ])

        self.assert_no_plan("theBurn(enemy1).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_consumes_hazard(self):
        """P1: Oil is consumed after ignition."""
        self.set_state([
            "at(player, roomA)",
            "at(enemy1, roomA)",
            "roomHasHazard(roomB, oil)",
            "canApplyTag(player, burning)",
            "connected(roomA, roomB)"
        ])

        self.run_goal("theBurn(enemy1)")
        state = self.get_state()

        # Oil should be consumed
        has_oil = any("roomHasHazard(roomB,oil)" in f for f in state)
        oil_consumed = any("hazardConsumed(roomB,oil)" in f for f in state)

        assert not has_oil, "P1 violated: oil should be consumed"
        assert oil_consumed, "P1 violated: hazardConsumed should be added"

    def test_property_p2_requires_ability(self):
        """P2: Player must have canApplyTag ability."""
        self.set_state([
            "at(player, roomA)",
            "at(enemy1, roomA)",
            "roomHasHazard(roomB, oil)",
            # Missing: canApplyTag(player, burning)
            "connected(roomA, roomB)"
        ])

        self.assert_no_plan("theBurn(enemy1).")

    def test_property_p3_enemy_gets_burned(self):
        """P3: Target enemy receives burning tag."""
        self.set_state([
            "at(player, roomA)",
            "at(enemy1, roomA)",
            "roomHasHazard(roomB, oil)",
            "canApplyTag(player, burning)",
            "connected(roomA, roomB)"
        ])

        self.run_goal("theBurn(enemy1)")
        state = self.get_state()

        has_burning = any("hasTag(enemy1,burning)" in f for f in state)
        assert has_burning, "P3 violated: enemy should have burning tag"


def run_tests():
    """Run all tests in this file."""
    suite = TheBurnTest()
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
