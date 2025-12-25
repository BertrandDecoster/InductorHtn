"""Tests for clear_room goal component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite


class ClearRoomTest(HtnTestSuite):
    """Test suite for clear_room goal."""

    def setup(self):
        """Load clear_room goal and all its dependencies."""
        # Load primitives first
        self.load_component("primitives/locomotion", reset_first=True)
        self.load_component("primitives/tags", reset_first=False)
        self.load_component("primitives/aggro", reset_first=False)
        # Load strategies
        self.load_component("strategies/the_burn", reset_first=False)
        self.load_component("strategies/the_slipstream", reset_first=False)
        # Load goals
        self.load_component("goals/defeat_enemy", reset_first=False)
        self.load_component("goals/clear_room", reset_first=False)

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_single_enemy(self):
        """Example 1: Room with single enemy

        Given: One enemy in room with available strategy
        When: clearRoom(roomA)
        Then: Enemy defeated
        """
        self.set_state([
            "at(enemy1, roomA)",
            "isEnemy(enemy1)",
            "at(player, roomA)",
            "roomHasHazard(roomB, oil)",
            "canApplyTag(player, burning)",
            "connected(roomA, roomB)",
            "vulnerableTo(enemy1, burning)"
        ])

        self.assert_plan("clearRoom(roomA).",
            contains=["opApplyTag"])

        self.assert_state_after("clearRoom(roomA).",
            has=["hasTag(enemy1,burning)"])

    def test_example_2_multiple_enemies(self):
        """Example 2: Room with multiple enemies

        Given: Two enemies in room with different vulnerabilities
        When: clearRoom(roomA)
        Then: Both enemies defeated (using different strategies)
        """
        self.set_state([
            "at(enemy1, roomA)",
            "at(enemy2, roomA)",
            "isEnemy(enemy1)",
            "isEnemy(enemy2)",
            "at(player, roomA)",
            # First enemy uses theBurn (oil + burning)
            "roomHasHazard(roomB, oil)",
            "canApplyTag(player, burning)",
            "connected(roomA, roomB)",
            "vulnerableTo(enemy1, burning)",
            # Second enemy uses theSlipstream (spikes + freeze)
            "roomHasHazard(roomC, spikes)",
            "canApplyTag(arcanist, frozen)",
            "connected(roomA, roomC)",
            "vulnerableTo(enemy2, wounded)"
        ])

        self.run_goal("clearRoom(roomA)")
        state = self.get_state()

        # Both enemies should have tags
        enemy1_tagged = any("hasTag(enemy1," in f for f in state)
        enemy2_tagged = any("hasTag(enemy2," in f for f in state)
        assert enemy1_tagged, "Enemy1 should have a tag"
        assert enemy2_tagged, "Enemy2 should have a tag"

    def test_example_3_empty_room(self):
        """Example 3: Empty room

        Given: No enemies in room
        When: clearRoom(roomA)
        Then: Empty plan succeeds
        """
        self.set_state([
            "at(player, roomA)"
            # No enemies
        ])

        # Should produce empty plan
        self.assert_plan("clearRoom(roomA).")

    def test_example_4_undefeatable_enemy(self):
        """Example 4: Undefeatable enemy

        Given: Enemy with no available strategy
        When: clearRoom(roomA)
        Then: Planning fails
        """
        self.set_state([
            "at(enemy1, roomA)",
            "isEnemy(enemy1)"
            # No hazards, no abilities
        ])

        self.assert_no_plan("clearRoom(roomA).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_all_enemies_affected(self):
        """P1: Every enemy in room receives a status tag."""
        self.set_state([
            "at(enemy1, roomA)",
            "at(enemy2, roomA)",
            "at(enemy3, roomA)",
            "isEnemy(enemy1)",
            "isEnemy(enemy2)",
            "isEnemy(enemy3)",
            "at(player, roomA)",
            # Each enemy can use theSlipstream with different hazards
            "roomHasHazard(roomB, fire)",
            "roomHasHazard(roomC, spikes)",
            "roomHasHazard(roomD, electricity)",
            "canApplyTag(arcanist, frozen)",
            "connected(roomA, roomB)",
            "connected(roomA, roomC)",
            "connected(roomA, roomD)",
            "vulnerableTo(enemy1, burning)",
            "vulnerableTo(enemy2, wounded)",
            "vulnerableTo(enemy3, electrified)"
        ])

        self.run_goal("clearRoom(roomA)")
        state = self.get_state()

        for enemy in ["enemy1", "enemy2", "enemy3"]:
            has_tag = any(f"hasTag({enemy}," in f for f in state)
            assert has_tag, f"P1 violated: {enemy} should have a tag"

    def test_property_p2_uses_defeat_enemy(self):
        """P2: Delegates to defeat_enemy for each enemy."""
        self.set_state([
            "at(enemy1, roomA)",
            "isEnemy(enemy1)",
            "at(player, roomA)",
            "roomHasHazard(roomB, oil)",
            "canApplyTag(player, burning)",
            "connected(roomA, roomB)",
            "vulnerableTo(enemy1, burning)"
        ])

        # Plan should contain defeat_enemy's characteristic operators
        self.assert_plan("clearRoom(roomA).",
            contains=["opConsumeHazard"])  # From theBurn strategy

    def test_property_p3_empty_room_succeeds(self):
        """P3: Room with no enemies returns empty plan."""
        self.set_state([
            "at(player, roomA)",
            "at(civilian1, roomA)"  # Non-enemy in room
            # No isEnemy facts
        ])

        # Should succeed with empty or minimal plan
        self.assert_plan("clearRoom(roomA).")

    # =========================================================================
    # Integration Tests
    # =========================================================================

    def test_mixed_strategies(self):
        """Different enemies can be defeated with different strategies."""
        self.set_state([
            "at(enemy1, roomA)",
            "at(enemy2, roomA)",
            "isEnemy(enemy1)",
            "isEnemy(enemy2)",
            "at(player, roomA)",
            "roomHasHazard(roomB, oil)",
            "roomHasHazard(roomC, spikes)",
            "canApplyTag(player, burning)",
            "canApplyTag(arcanist, frozen)",
            "connected(roomA, roomB)",
            "connected(roomA, roomC)",
            "vulnerableTo(enemy1, burning)",
            "vulnerableTo(enemy2, wounded)"
        ])

        self.run_goal("clearRoom(roomA)")
        state = self.get_state()

        # enemy1 should have burning, enemy2 should have wounded
        enemy1_burning = any("hasTag(enemy1,burning)" in f for f in state)
        enemy2_wounded = any("hasTag(enemy2,wounded)" in f for f in state)

        assert enemy1_burning, "Enemy1 should be burning"
        assert enemy2_wounded, "Enemy2 should be wounded"

    def test_enemies_in_different_rooms(self):
        """Only enemies in target room are affected."""
        self.set_state([
            "at(enemy1, roomA)",
            "at(enemy2, roomB)",  # Different room
            "isEnemy(enemy1)",
            "isEnemy(enemy2)",
            "at(player, roomA)",
            "roomHasHazard(roomC, oil)",
            "canApplyTag(player, burning)",
            "connected(roomA, roomC)",
            "vulnerableTo(enemy1, burning)",
            "vulnerableTo(enemy2, burning)"
        ])

        self.run_goal("clearRoom(roomA)")
        state = self.get_state()

        # Only enemy1 should be tagged
        enemy1_tagged = any("hasTag(enemy1," in f for f in state)
        enemy2_tagged = any("hasTag(enemy2," in f for f in state)

        assert enemy1_tagged, "Enemy1 should be affected"
        assert not enemy2_tagged, "Enemy2 should NOT be affected (different room)"


def run_tests():
    """Run all tests in this file."""
    suite = ClearRoomTest()
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
