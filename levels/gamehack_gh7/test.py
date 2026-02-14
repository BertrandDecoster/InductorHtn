"""Tests for gamehack_gh7 level."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite


class GamehackGh7Test(HtnTestSuite):
    """Test suite for gamehack_gh7 level."""

    def setup(self):
        """Load all components and level."""
        self.load_component("gamehack/primitives/gh_movement", reset_first=True)
        self.load_component("gamehack/primitives/gh_tags", reset_first=False)
        self.load_component("gamehack/primitives/gh_aggro", reset_first=False)
        self.load_component("gamehack/primitives/gh_skills", reset_first=False)
        self.load_component("gamehack/actions/gh_tag_application", reset_first=False)
        self.load_component("gamehack/strategies/stun_and_slow_skill", reset_first=False)
        self.load_component("gamehack/strategies/wet_and_electrocute", reset_first=False)
        self.load_component("gamehack/goals/plan_to_damage", reset_first=False)
        self.load_level("levels/gamehack_gh7")

    def load_level(self, level_path):
        """Load a level's HTN file."""
        base_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "../.."
        ))
        level_file = os.path.join(base_path, level_path, "level.htn")

        with open(level_file, "r") as f:
            content = f.read()

        error = self._planner.HtnCompileCustomVariables(content)
        if error:
            raise RuntimeError(f"Failed to compile level: {error}")

    # =========================================================================
    # Example Tests
    # =========================================================================

    def test_example_1_plan_to_damage_succeeds(self):
        """Example 1: planToDamage(gob) succeeds."""
        self.assert_plan("planToDamage(gob).", min_solutions=1)

    def test_example_2_stun_and_slow_skill_works(self):
        """Example 2: stunAndSlowSkill works with companionI + companionF."""
        self.assert_plan("stunAndSlowSkill(gob).",
            contains=["opSynchronize"])

    def test_example_3_wet_and_electrocute_via_skill_acquisition(self):
        """Example 3: wetAndElectrocute works via skill acquisition at sea."""
        self.assert_plan("wetAndElectrocute(gob).",
            contains=["opApplyTag(wet", "opApplyTag(electrocute"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_both_strategies(self):
        """P1: Both strategies produce plans."""
        # stunAndSlowSkill should work
        self.assert_plan("stunAndSlowSkill(gob).", min_solutions=1)

        # wetAndElectrocute should also work
        self.assert_plan("wetAndElectrocute(gob).", min_solutions=1)

    def test_property_p2_correct_tags_stun_slow(self):
        """P2: stunAndSlowSkill applies stun and fire tags."""
        self.run_goal("stunAndSlowSkill(gob)")
        state = self.get_state()

        has_stun = any("hasTag(gob,stun)" in f for f in state)
        has_fire = any("hasTag(gob,fire)" in f for f in state)

        assert has_stun, "P2 violated: gob should have stun tag"
        assert has_fire, "P2 violated: gob should have fire tag"

    def test_property_p2_correct_tags_wet_electrocute(self):
        """P2: wetAndElectrocute applies wet and electrocute tags."""
        self.run_goal("wetAndElectrocute(gob)")
        state = self.get_state()

        has_wet = any("hasTag(gob,wet)" in f for f in state)
        has_electrocute = any("hasTag(gob,electrocute)" in f for f in state)

        assert has_wet, "P2 violated: gob should have wet tag"
        assert has_electrocute, "P2 violated: gob should have electrocute tag"


def run_tests():
    """Run all tests in this file."""
    suite = GamehackGh7Test()
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
