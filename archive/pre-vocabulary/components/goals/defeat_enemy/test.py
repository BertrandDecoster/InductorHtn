"""Tests for defeat_enemy goal component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite


class DefeatEnemyTest(HtnTestSuite):
    """Test suite for defeat_enemy goal."""

    def setup(self):
        """Load defeat_enemy goal and all its dependencies."""
        # Load primitives first
        self.load_component("primitives/locomotion", reset_first=True)
        self.load_component("primitives/tags", reset_first=False)
        self.load_component("primitives/aggro", reset_first=False)
        # Load strategies
        self.load_component("strategies/the_burn", reset_first=False)
        self.load_component("strategies/the_slipstream", reset_first=False)
        # Load the goal
        self.load_component("goals/defeat_enemy", reset_first=False)

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_fire_strategy(self):
        """Example 1: Enemy vulnerable to fire near oil

        Given: Enemy vulnerable to burning, oil room available
        When: defeatEnemy(enemy1)
        Then: Uses theBurn, enemy has burning tag
        """
        self.set_state([
            "at(enemy1, roomA)",
            "at(player, roomA)",
            "vulnerableTo(enemy1, burning)",
            "roomHasHazard(roomB, oil)",
            "canApplyTag(player, burning)",
            "connected(roomA, roomB)"
        ])

        # theBurn uses opConsumeHazard and opGetAggro
        self.assert_plan("defeatEnemy(enemy1).",
            contains=["opConsumeHazard", "opGetAggro"])

        self.assert_state_after("defeatEnemy(enemy1).",
            has=["hasTag(enemy1,burning)"])

    def test_example_2_slipstream_strategy(self):
        """Example 2: Enemy vulnerable to wounded near spikes

        Given: Enemy vulnerable to wounded, spikes room available
        When: defeatEnemy(enemy1)
        Then: Uses theSlipstream, enemy has wounded tag
        """
        self.set_state([
            "at(enemy1, roomA)",
            "vulnerableTo(enemy1, wounded)",
            "roomHasHazard(roomB, spikes)",
            "connected(roomA, roomB)",
            "canApplyTag(arcanist, frozen)"
        ])

        # theSlipstream uses opApplyRoomTag (for freezing)
        self.assert_plan("defeatEnemy(enemy1).",
            contains=["opApplyRoomTag"])

        self.assert_state_after("defeatEnemy(enemy1).",
            has=["at(enemy1,roomB)", "hasTag(enemy1,wounded)"])

    def test_example_3_no_matching_strategy(self):
        """Example 3: No matching strategy

        Given: No matching vulnerability/hazard combination
        When: defeatEnemy(enemy1)
        Then: Planning fails
        """
        self.set_state([
            "at(enemy1, roomA)",
            "vulnerableTo(enemy1, poison)"
            # No poison hazard, no oil, no freeze ability
        ])

        self.assert_no_plan("defeatEnemy(enemy1).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_enemy_affected(self):
        """P1: Enemy receives a status tag after defeat."""
        self.set_state([
            "at(enemy1, roomA)",
            "at(player, roomA)",
            "vulnerableTo(enemy1, burning)",
            "roomHasHazard(roomB, oil)",
            "canApplyTag(player, burning)",
            "connected(roomA, roomB)"
        ])

        self.run_goal("defeatEnemy(enemy1)")
        state = self.get_state()

        has_tag = any("hasTag(enemy1," in f for f in state)
        assert has_tag, "P1 violated: enemy should have a status tag"

    def test_property_p2_strategy_selection_burn(self):
        """P2: theBurn selected when burning vulnerability + oil available."""
        self.set_state([
            "at(enemy1, roomA)",
            "at(player, roomA)",
            "vulnerableTo(enemy1, burning)",
            "roomHasHazard(roomB, oil)",
            "canApplyTag(player, burning)",
            "connected(roomA, roomB)"
        ])

        # theBurn uses opConsumeHazard (consumes oil)
        self.assert_plan("defeatEnemy(enemy1).",
            contains=["opConsumeHazard"])

    def test_property_p2_strategy_selection_slipstream(self):
        """P2: theSlipstream selected for other vulnerabilities."""
        self.set_state([
            "at(enemy1, roomA)",
            "vulnerableTo(enemy1, electrified)",
            "roomHasHazard(roomB, electricity)",
            "connected(roomA, roomB)",
            "canApplyTag(arcanist, frozen)"
        ])

        # Get plan and verify it uses theSlipstream strategy
        self.assert_plan("defeatEnemy(enemy1).",
            contains=["opApplyRoomTag"])  # opApplyRoomTag is part of theSlipstream

    def test_property_p3_requires_vulnerability_match(self):
        """P3: Planning fails without matching vulnerability."""
        # Enemy vulnerable to poison but only fire hazard available
        self.set_state([
            "at(enemy1, roomA)",
            "vulnerableTo(enemy1, poison)",
            "roomHasHazard(roomB, fire)",
            "connected(roomA, roomB)"
            # No canApplyTag for freeze
        ])

        self.assert_no_plan("defeatEnemy(enemy1).")

    # =========================================================================
    # Integration Tests
    # =========================================================================

    def test_burn_priority_over_slipstream(self):
        """When both strategies are possible, theBurn is preferred."""
        self.set_state([
            "at(enemy1, roomA)",
            "at(player, roomA)",
            "vulnerableTo(enemy1, burning)",
            "roomHasHazard(roomB, oil)",
            "roomHasHazard(roomC, fire)",
            "canApplyTag(player, burning)",
            "canApplyTag(arcanist, frozen)",
            "connected(roomA, roomB)",
            "connected(roomA, roomC)"
        ])

        # theBurn should be selected first (method ordering)
        # theBurn uses opConsumeHazard (consumes oil)
        self.assert_plan("defeatEnemy(enemy1).",
            contains=["opConsumeHazard"])

    def test_slipstream_fallback_no_vulnerability(self):
        """Slipstream works as fallback even without vulnerability match."""
        self.set_state([
            "at(enemy1, roomA)",
            "roomHasHazard(roomB, spikes)",
            "connected(roomA, roomB)",
            "canApplyTag(arcanist, frozen)"
            # No vulnerableTo fact
        ])

        # Should use fallback slipstream
        self.assert_plan("defeatEnemy(enemy1).",
            contains=["opApplyRoomTag", "opMoveTo"])


def run_tests():
    """Run all tests in this file."""
    suite = DefeatEnemyTest()
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
