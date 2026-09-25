"""Tests for gh_tags primitive component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


class GhTagsTest(HtnTestSuite):
    """Test suite for gh_tags primitive."""

    def setup(self):
        """Load the gh_tags component."""
        self.load_component("gamehack/primitives/gh_tags")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_tag_already_present(self):
        """Example 1: the tag is already there, the plan shows opTagAlreadyOnTarget."""
        self.set_state(["hasTag(gob, wet)"])
        self.assert_plan_set("applyTag(wet, gob).", ["opTagAlreadyOnTarget(wet, gob)"])

    def test_example_2_use_skill_single_tag(self):
        """Example 2: the skill is used and its tag lands."""
        self.set_state(["at(gob, lake)", "at(companionE, lake)", "hasSkill(companionE, lightningSkill)",
                        "skillAppliesTag(lightningSkill, electrified)"])
        self.assert_plan_set("useSkillOnTarget(companionE, lightningSkill, gob).",
            ["opUseSkill(companionE, lightningSkill, gob), opApplyTag(electrified, gob)"])
        self.assert_state_after("useSkillOnTarget(companionE, lightningSkill, gob).",
            has=["hasTag(gob,electrified)"])

    def test_example_3_use_skill_multiple_tags(self):
        """Example 3: every tag of the skill lands."""
        self.set_state(["at(gob, lake)", "at(companionW, lake)", "hasSkill(companionW, waterSkill)",
                        "skillAppliesTag(waterSkill, wet)", "skillAppliesTag(waterSkill, clean)"])
        self.assert_plan_set("useSkillOnTarget(companionW, waterSkill, gob).",
            ["opUseSkill(companionW, waterSkill, gob), opApplyTag(wet, gob), opApplyTag(clean, gob)"])
        self.assert_state_after("useSkillOnTarget(companionW, waterSkill, gob).",
            has=["hasTag(gob,wet)", "hasTag(gob,clean)"])

    def test_example_2b_caster_must_hold_the_skill_and_stand_with_the_target(self):
        """Example 2b: no plan when the caster lacks the skill or stands elsewhere."""
        self.set_state(["at(gob, lake)", "at(companionE, inn)", "hasSkill(companionE, lightningSkill)",
                        "skillAppliesTag(lightningSkill, electrified)"])
        self.assert_no_plan("useSkillOnTarget(companionE, lightningSkill, gob).")
        self.assert_no_plan("useSkillOnTarget(companionW, lightningSkill, gob).")

    def test_example_4_skill_with_no_tags(self):
        """Example 4: a skill with no tags is still used; no tag lands."""
        self.set_state(["at(gob, lake)", "at(player, lake)", "hasSkill(player, emptySkill)"])
        self.assert_plan_set("useSkillOnTarget(player, emptySkill, gob).",
            ["opUseSkill(player, emptySkill, gob)"])

    def test_example_5_immune_and_present_tags_do_not_land(self):
        """Example 5: a tag the target is immune to, or already has, doesn't land."""
        self.set_state(["at(gob, lake)", "at(companionW, lake)", "hasSkill(companionW, waterSkill)",
                        "skillAppliesTag(waterSkill, wet)", "skillAppliesTag(waterSkill, clean)",
                        "immune(gob, wet)", "hasTag(gob, clean)"])
        self.assert_plan_set("useSkillOnTarget(companionW, waterSkill, gob).",
            ["opUseSkill(companionW, waterSkill, gob)"])

    def test_example_6_location_applies_tag(self):
        """Example 6: the location's tag lands on the target standing there."""
        self.set_state(["at(gob, lake)"])
        self.assert_plan_set("useLocationToApplyTag(lake, wet, gob).", ["opApplyTag(wet, gob)"])
        self.assert_no_plan("useLocationToApplyTag(sea, wet, gob).")

    def test_example_7_agent_skill_applies_tag(self):
        """Example 7: a non-companion standing with the target uses its skill on it."""
        self.set_state(["at(gob, lake)", "at(teslaTower, lake)", "hasSkill(teslaTower, lightningSkill)",
                        "skillAppliesTag(lightningSkill, electrified)"])
        self.assert_plan_set("useAgentSkillToApplyTag(teslaTower, lightningSkill, gob).",
            ["opUseSkill(teslaTower, lightningSkill, gob), opApplyTag(electrified, gob)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_no_duplicate_tags(self):
        """P1: Applying a tag already present is idempotent."""
        self.set_state(["hasTag(gob, wet)"])
        self.run_goal("applyTag(wet, gob)")
        state = self.get_state()
        wet_count = sum(1 for f in state if "hasTag(gob,wet)" in f)
        assert wet_count == 1, f"P1 violated: expected 1 wet tag, got {wet_count}"

    def test_property_p2_multi_tag_complete(self):
        """P2: All tags from a multi-tag skill are applied."""
        self.set_state(["at(gob, lake)", "at(companionW, lake)", "hasSkill(companionW, waterSkill)",
                        "skillAppliesTag(waterSkill, wet)", "skillAppliesTag(waterSkill, clean)"])
        self.run_goal("useSkillOnTarget(companionW, waterSkill, gob)")
        state = self.get_state()
        has_wet = any("hasTag(gob,wet)" in f for f in state)
        has_clean = any("hasTag(gob,clean)" in f for f in state)
        assert has_wet, "P2 violated: wet tag not applied"
        assert has_clean, "P2 violated: clean tag not applied"


def run_tests():
    """Run all tests in this file."""
    suite = GhTagsTest()
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
