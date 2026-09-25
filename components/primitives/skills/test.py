"""Tests for the skills primitive component."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite

WORLD = [
    "location(camp)", "location(hut)", "location(forge)",
    "companion(pyro)", "companion(frost)", "companion(page)",
    "at(pyro, camp)", "at(frost, camp)", "at(page, camp)",
    "hasSkill(pyro, fireballSkill)", "skillAppliesTag(fireballSkill, burning)",
    "hasSkill(frost, frostSkill)", "skillAppliesTag(frostSkill, chilled)",
    "object(shrine)", "at(shrine, forge)", "canGetSkillFrom(shrine, fireballSkill)",
    "enemy(gob)", "at(gob, hut)", "at(imp, camp)", "enemy(imp)",
    "hasSkill(pyro, stormSkill)", "skillAppliesTag(stormSkill, burning)", "skillAppliesTag(stormSkill, electrified)",
]


class SkillsTest(HtnTestSuite):
    """Test suite for the skills primitive."""

    def setup(self):
        self.load_component("primitives/skills")
        self.set_state(WORLD)

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_holds_the_skill(self):
        """Example 1: holds the skill: walks to the target."""
        self.assert_plan_set("prepareToUseSkill(pyro, fireballSkill, gob).", ["opMoveTo(pyro, camp, hut)"])

    def test_example_2_swaps_at_the_object(self):
        """Example 2: gets it from the shrine, replacing its skill, then walks to the target."""
        self.assert_plan_set("prepareToUseSkill(frost, fireballSkill, gob).", [
            "opMoveTo(frost, camp, forge), opSwapSkill(frost, frostSkill, fireballSkill), opMoveTo(frost, forge, hut)"])

    def test_example_3_learns_a_first_skill(self):
        """Example 3: a companion with no skill learns one."""
        self.assert_plan_set("prepareToUseSkill(page, fireballSkill, gob).", [
            "opMoveTo(page, camp, forge), opGetSkill(page, fireballSkill), opMoveTo(page, forge, hut)"])

    def test_example_4_use_needs_the_same_location(self):
        """Example 4: a skill is used on a target standing in the same location."""
        self.assert_no_plan("useSkillOnTarget(pyro, fireballSkill, gob).")
        self.assert_plan_set("useSkillOnTarget(pyro, fireballSkill, imp).",
            ["opUseSkill(pyro, fireballSkill, imp), opApplyTag(burning, imp)"])

    def test_example_5_every_tag_lands(self):
        """Example 5: each of the skill's tags lands."""
        self.assert_plan_set("useSkillOnTarget(pyro, stormSkill, imp).",
            ["opUseSkill(pyro, stormSkill, imp), opApplyTag(burning, imp), opApplyTag(electrified, imp)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_one_skill_learned(self):
        """P1: learning replaces the companion's skill."""
        self.assert_state_after("prepareToUseSkill(frost, fireballSkill, gob).",
            has=["hasSkill(frost,fireballSkill)"], not_has=["hasSkill(frost,frostSkill)"])


def run_tests():
    """Run all tests in this file."""
    suite = SkillsTest()
    for method_name in dir(suite):
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
