"""Tests for aggro primitive component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite


class AggroTest(HtnTestSuite):
    """Test suite for aggro primitive."""

    def setup(self):
        """Load the aggro component and its dependencies."""
        # aggro depends on locomotion, so load both
        # reset_first=True on first load, False on subsequent
        self.load_component("primitives/locomotion", reset_first=True)
        self.load_component("primitives/aggro", reset_first=False)

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_gain_aggro(self):
        """Example 1: Gain aggro

        Given: Enemy has no aggro
        When: getAggro(enemy1)
        Then: Plan contains opGetAggro, has hasAggro(enemy1, player)
        """
        # No initial aggro
        self.assert_plan("getAggro(enemy1).",
            contains=["opGetAggro(enemy1)"])

        self.assert_state_after("getAggro(enemy1).",
            has=["hasAggro(enemy1,player)"])

    def test_example_2_already_has_aggro(self):
        """Example 2: Already has aggro (no-op)

        Given: hasAggro(enemy1, player)
        When: getAggro(enemy1)
        Then: No operators
        """
        self.set_state([
            "hasAggro(enemy1, player)"
        ])

        self.assert_plan("getAggro(enemy1).",
            not_contains=["opGetAggro"])

    def test_example_3_enemy_follows(self):
        """Example 3: Enemy follows to different room

        Given: Enemy has aggro, player in roomB, enemy in roomA
        When: enemyFollows(enemy1, player)
        Then: Enemy moves to roomB
        """
        self.set_state([
            "hasAggro(enemy1, player)",
            "at(player, roomB)",
            "at(enemy1, roomA)",
            "connected(roomA, roomB)"
        ])

        self.assert_plan("enemyFollows(enemy1, player).",
            contains=["opMoveTo(enemy1, roomA, roomB)"])

        self.assert_state_after("enemyFollows(enemy1, player).",
            has=["at(enemy1,roomB)"],
            not_has=["at(enemy1,roomA)"])

    def test_example_4_lure_to_room(self):
        """Example 4: Lure enemy to room

        Given: Player and enemy both in roomA
        When: lureToRoom(enemy1, roomB)
        Then: Both end up in roomB with aggro
        """
        self.set_state([
            "at(player, roomA)",
            "at(enemy1, roomA)",
            "connected(roomA, roomB)"
        ])

        # Lure should move player, get aggro, move enemy
        self.assert_plan("lureToRoom(enemy1, roomB).",
            contains=["opMoveTo(player, roomA, roomB)", "opGetAggro(enemy1)"])

        self.assert_state_after("lureToRoom(enemy1, roomB).",
            has=["at(player,roomB)", "at(enemy1,roomB)", "hasAggro(enemy1,player)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p2_following_requires_aggro(self):
        """P2: enemyFollows only moves if hasAggro exists.

        Without aggro, enemy should not move.
        """
        self.set_state([
            "at(player, roomB)",
            "at(enemy1, roomA)",
            "connected(roomA, roomB)"
            # No hasAggro!
        ])

        # Should be no-op (no movement)
        self.assert_plan("enemyFollows(enemy1, player).",
            not_contains=["opMoveTo"])

    # =========================================================================
    # Additional Tests
    # =========================================================================

    def test_lose_aggro(self):
        """Lose aggro removes the hasAggro fact."""
        self.set_state([
            "hasAggro(enemy1, player)"
        ])

        self.assert_plan("loseAggro(enemy1).",
            contains=["opLoseAggro(enemy1)"])

        self.assert_state_after("loseAggro(enemy1).",
            not_has=["hasAggro(enemy1,player)"])

    def test_lose_aggro_when_none(self):
        """Lose aggro when no aggro is a no-op."""
        # No initial aggro
        self.assert_plan("loseAggro(enemy1).",
            not_contains=["opLoseAggro"])

    def test_enemy_already_in_same_room(self):
        """Enemy in same room as player - no movement needed."""
        self.set_state([
            "hasAggro(enemy1, player)",
            "at(player, roomA)",
            "at(enemy1, roomA)"
        ])

        self.assert_plan("enemyFollows(enemy1, player).",
            not_contains=["opMoveTo"])


def run_tests():
    """Run all tests in this file."""
    suite = AggroTest()
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
