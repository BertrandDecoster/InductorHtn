"""Tests for gamehack_multipath level.

Proves the decomposed gamehack stack supports multiple concurrent strategies
and all three dispatcher paths of `applyTagNotPresent`, producing many distinct
plans for a single top-level goal.
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import findAllPlansResultToPrologStringList


class GamehackMultipathTest(HtnTestSuite):
    """Test suite for gamehack_multipath level."""

    def setup(self):
        """Load all multipath components + level."""
        self.load_component("gamehack/primitives/gh_movement", reset_first=True)
        self.load_component("gamehack/primitives/gh_tags", reset_first=False)
        self.load_component("gamehack/primitives/gh_aggro", reset_first=False)
        self.load_component("gamehack/primitives/gh_skills", reset_first=False)
        self.load_component("gamehack/actions/gh_tag_application", reset_first=False)
        self.load_component("gamehack/strategies/wet_and_electrocute", reset_first=False)
        self.load_component("gamehack/strategies/stun_and_slow_skill", reset_first=False)
        self.load_component("gamehack/strategies/stun_and_burn", reset_first=False)
        self.load_component("gamehack/goals/plan_to_damage", reset_first=False)
        self.verify_contracts()
        self.load_level("levels/gamehack_multipath")

    def load_level(self, level_path):
        """Compile the level.htn into the running planner."""
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        level_file = os.path.join(base_path, level_path, "level.htn")
        with open(level_file, "r") as f:
            content = f.read()
        error = self._planner.HtnCompileCustomVariables(content)
        if error:
            raise RuntimeError(f"Failed to compile level: {error}")

    # =========================================================================
    # Example Tests
    # =========================================================================

    def test_example_1_wet_and_electrocute_viable(self):
        """Example 1: at least one plan applies wet + electrocute to gob."""
        self.assert_plan("planToDamage(gob).",
            contains=["opApplyTag(wet, gob)", "opApplyTag(electrocute, gob)"])

    def test_example_2_stun_and_slow_viable(self):
        """Example 2: at least one plan uses the synchronized two-ally strategy."""
        self.assert_plan("planToDamage(gob).", contains=["opSynchronize"])

    def test_example_3_stun_and_burn_viable(self):
        """Example 3: at least one plan applies ice + fire to gob."""
        self.assert_plan("planToDamage(gob).",
            contains=["opApplyTag(ice, gob)", "opApplyTag(fire, gob)"])

    def test_example_4_multiple_plans(self):
        """Example 4: FindAllPlans returns many distinct plans (>= 10)."""
        error, result = self._planner.FindAllPlansCustomVariables("planToDamage(gob).")
        assert error is None, f"Planning error: {error}"
        plans = json.loads(result)
        # Filter out the {"false": ...} failure marker if present
        real_plans = [p for p in plans if not (isinstance(p, dict) and "false" in p)]
        assert len(real_plans) >= 10, f"Expected >= 10 plans, got {len(real_plans)}"
        self._record(True, f"Example 4: found {len(real_plans)} plans")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_ally_skill_path_for_wet(self):
        """P1: at least one plan applies wet via ally waterSkill.

        Discriminator: `opApplyTag(clean, gob)` only appears when `waterSkill`
        is fired by an ally (it carries both `wet` and `clean`); the location
        and mob-skill dispatcher paths for `wet` don't produce it.
        """
        self.assert_plan_matches_any("planToDamage(gob).", [
            {"contains": ["opApplyTag(clean, gob)"]},
        ])

    def test_property_p2_location_path_for_wet(self):
        """P2: at least one plan applies wet by luring gob to lakeShore or sea."""
        self.assert_plan_matches_any("planToDamage(gob).", [
            {"contains": ["opAggroMoveTo(gob, arena, lakeShore), opApplyTag(wet, gob)"]},
            {"contains": ["opAggroMoveTo(gob, arena, sea), opApplyTag(wet, gob)"]},
        ])

    def test_property_p3_mob_skill_path_for_electrocute(self):
        """P3: at least one plan electrocutes gob by luring it to teslaTower's location."""
        self.assert_plan_matches_any("planToDamage(gob).", [
            {"contains": ["opAggroMoveTo(gob, arena, lakeShore), opApplyTag(electrocute, gob)"]},
        ])

    def test_property_p4_mob_skill_path_for_ice(self):
        """P4: at least one plan applies ice by luring gob to glacier."""
        self.assert_plan_matches_any("planToDamage(gob).", [
            {"contains": ["opAggroMoveTo(gob, arena, glacier), opApplyTag(ice, gob)"]},
        ])

    def test_property_p5_state_after_wet_and_electrocute(self):
        """P5: running wetAndElectrocute(gob) tags gob with wet and electrocute."""
        self.run_goal("wetAndElectrocute(gob)")
        state = self.get_state()
        has_wet = any("hasTag(gob,wet)" in f for f in state)
        has_elec = any("hasTag(gob,electrocute)" in f for f in state)
        assert has_wet, f"P5 violated: gob should have wet. State: {state}"
        assert has_elec, f"P5 violated: gob should have electrocute. State: {state}"
        self._record(True, "P5: gob has wet and electrocute after wetAndElectrocute")

    def test_property_p6_state_after_stun_and_burn(self):
        """P6: running stunAndBurn(gob) tags gob with ice and fire."""
        self.run_goal("stunAndBurn(gob)")
        state = self.get_state()
        has_ice = any("hasTag(gob,ice)" in f for f in state)
        has_fire = any("hasTag(gob,fire)" in f for f in state)
        assert has_ice, f"P6 violated: gob should have ice. State: {state}"
        assert has_fire, f"P6 violated: gob should have fire. State: {state}"
        self._record(True, "P6: gob has ice and fire after stunAndBurn")

    def test_property_p7_skill_learning_in_stun_and_slow(self):
        """P7: at least one stunAndSlowSkill plan requires learning a skill."""
        self.assert_plan_matches_any("stunAndSlowSkill(gob).", [
            {"contains": ["opSwapSkill", "opSynchronize"]},
            {"contains": ["opGetSkill", "opSynchronize"]},
        ])


def run_tests():
    suite = GamehackMultipathTest()

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
