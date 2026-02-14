"""Tests for gamehack_gh4 level."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite


class GamehackGh4Test(HtnTestSuite):
    """Test suite for gamehack_gh4 level."""

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
        self.load_level("levels/gamehack_gh4")

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

    def test_example_2_wet_via_ally_skill(self):
        """Example 2: companionW applies wet via waterSkill."""
        self.assert_plan("applyTag(wet, gob).",
            contains=["opApplyTag(wet, gob)"])

    def test_example_3_electrocute_via_ally_skill(self):
        """Example 3: companionE applies electrocute via lightningSkill."""
        self.assert_plan("applyTag(electrocute, gob).",
            contains=["opApplyTag(electrocute, gob)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_only_wet_and_electrocute(self):
        """P1: Only wetAndElectrocute plans (no stunAndSlowSkill)."""
        # stunAndSlowSkill requires skillHasTag(?s, slow) which doesn't exist in GH4
        self.assert_plan("planToDamage(gob).",
            not_contains=["opSynchronize"])

    def test_property_p2_both_tags_applied(self):
        """P2: Target has both wet and electrocute after plan."""
        self.run_goal("planToDamage(gob)")
        state = self.get_state()

        has_wet = any("hasTag(gob,wet)" in f for f in state)
        has_electrocute = any("hasTag(gob,electrocute)" in f for f in state)

        assert has_wet, "P2 violated: gob should have wet tag"
        assert has_electrocute, "P2 violated: gob should have electrocute tag"


def run_tests():
    """Run all tests in this file."""
    suite = GamehackGh4Test()
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
