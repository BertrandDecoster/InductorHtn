"""Tests for puzzle1 level."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite


class Puzzle1Test(HtnTestSuite):
    """Test suite for puzzle1 level."""

    def setup(self):
        """Load all components needed for puzzle1."""
        # Load primitives
        self.load_component("primitives/locomotion", reset_first=True)
        self.load_component("primitives/tags", reset_first=False)
        self.load_component("primitives/aggro", reset_first=False)
        # Load strategies
        self.load_component("strategies/the_burn", reset_first=False)
        self.load_component("strategies/the_slipstream", reset_first=False)
        # Load goals
        self.load_component("goals/defeat_enemy", reset_first=False)
        self.load_component("goals/clear_room", reset_first=False)
        # Load level
        self.load_level("levels/puzzle1")

    def load_level(self, level_path: str):
        """Load a level's HTN file."""
        base_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "../.."
        ))
        level_file = os.path.join(base_path, level_path, "level.htn")

        with open(level_file, "r") as f:
            content = f.read()

        error = self._planner.HtnCompile(content)
        if error:
            raise RuntimeError(f"Failed to compile level: {error}")

    # =========================================================================
    # Level Completion Tests
    # =========================================================================

    def test_puzzle_can_be_completed(self):
        """The puzzle has at least one valid solution."""
        self.assert_plan("completePuzzle.")

    def test_all_enemies_defeated_after_completion(self):
        """After completing the puzzle, all enemies have status tags."""
        self.run_goal("completePuzzle")
        state = self.get_state()

        # Both guards should have tags
        guard1_tagged = any("hasTag(guard1," in f for f in state)
        guard2_tagged = any("hasTag(guard2," in f for f in state)

        assert guard1_tagged, "guard1 should have a status tag"
        assert guard2_tagged, "guard2 should have a status tag"

    def test_player_at_exit_after_completion(self):
        """After completing the puzzle, player is at exit."""
        self.run_goal("completePuzzle")
        state = self.get_state()

        player_at_exit = any("at(player,exit)" in f for f in state)
        assert player_at_exit, "Player should be at exit after completion"

    # =========================================================================
    # Strategy Selection Tests
    # =========================================================================

    def test_guard1_uses_burn_strategy(self):
        """guard1 in storage should be defeated with theBurn (oil room)."""
        # guard1 is vulnerable to burning and storage has oil
        self.run_goal("defeatEnemy(guard1)")
        state = self.get_state()

        has_burning = any("hasTag(guard1,burning)" in f for f in state)
        assert has_burning, "guard1 should have burning tag from theBurn strategy"

    def test_guard2_uses_slipstream_strategy(self):
        """guard2 in corridor should be defeated with theSlipstream (push to generator)."""
        # guard2 is vulnerable to electrified, generator has electricity
        self.run_goal("defeatEnemy(guard2)")
        state = self.get_state()

        has_electrified = any("hasTag(guard2,electrified)" in f for f in state)
        assert has_electrified, "guard2 should have electrified tag from theSlipstream strategy"

    # =========================================================================
    # Partial Progress Tests
    # =========================================================================

    def test_can_clear_storage(self):
        """Storage room can be cleared of guard1."""
        self.assert_plan("clearRoom(storage).")

    def test_can_clear_corridor(self):
        """Corridor can be cleared of guard2."""
        self.assert_plan("clearRoom(corridor).")

    def test_can_reach_exit(self):
        """Player can navigate to exit (after guards are defeated)."""
        # First clear the path by defeating guards
        self.run_goal("defeatAllGuards")

        # Then verify player can move to exit
        self.assert_plan("moveTo(player, exit).")

    # =========================================================================
    # Plan Content Tests
    # =========================================================================

    def test_complete_plan_contains_expected_operators(self):
        """The solution plan should contain key operators."""
        # Get the plan for completing the puzzle
        self.assert_plan("completePuzzle.",
            contains=["opApplyTag"])  # Must tag enemies

    def test_plan_uses_hazards(self):
        """The solution should utilize environmental hazards."""
        self.assert_plan("completePuzzle.",
            contains=["opConsumeHazard"])  # theBurn consumes oil


def run_tests():
    """Run all tests in this file."""
    suite = Puzzle1Test()
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
