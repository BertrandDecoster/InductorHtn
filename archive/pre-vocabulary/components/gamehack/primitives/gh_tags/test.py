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
        """Example 1: Tag already present (no-op)

        Given: hasTag(gob, wet)
        When: applyTag(wet, gob)
        Then: opTagAlreadyOnTarget, no opApplyTag
        """
        self.set_state([
            "hasTag(gob, wet)"
        ])

        self.assert_plan("applyTag(wet, gob).",
            contains=["opTagAlreadyOnTarget(wet, gob)"],
            not_contains=["opApplyTag"])

    def test_example_2_use_skill_single_tag(self):
        """Example 2: Use skill to apply single tag

        Given: skillAppliesTag(lightningSkill, electrocute)
        When: useSkillOnTarget(companionE, lightningSkill, gob)
        Then: opApplyTag(electrocute, gob), hasTag(gob, electrocute)
        """
        self.set_state([
            "skillAppliesTag(lightningSkill, electrocute)"
        ])

        self.assert_plan("useSkillOnTarget(companionE, lightningSkill, gob).",
            contains=["opApplyTag(electrocute, gob)"])

        self.assert_state_after("useSkillOnTarget(companionE, lightningSkill, gob).",
            has=["hasTag(gob,electrocute)"])

    def test_example_3_use_skill_multiple_tags(self):
        """Example 3: Use skill to apply multiple tags

        Given: skillAppliesTag(waterSkill, wet), skillAppliesTag(waterSkill, clean)
        When: useSkillOnTarget(companionW, waterSkill, gob)
        Then: Both wet and clean tags applied
        """
        self.set_state([
            "skillAppliesTag(waterSkill, wet)",
            "skillAppliesTag(waterSkill, clean)"
        ])

        self.assert_plan("useSkillOnTarget(companionW, waterSkill, gob).",
            contains=["opApplyTag(wet, gob)", "opApplyTag(clean, gob)"])

        self.assert_state_after("useSkillOnTarget(companionW, waterSkill, gob).",
            has=["hasTag(gob,wet)", "hasTag(gob,clean)"])

    def test_example_4_skill_with_no_tags(self):
        """Example 4: Skill with no tags (no-op)

        Given: No skillAppliesTag facts for emptySkill
        When: useSkillOnTarget(player, emptySkill, gob)
        Then: Plan is empty
        """
        # No skillAppliesTag facts set
        self.assert_plan("useSkillOnTarget(player, emptySkill, gob).",
            not_contains=["opApplyTag"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_no_duplicate_tags(self):
        """P1: Applying a tag already present is idempotent."""
        self.set_state([
            "hasTag(gob, wet)"
        ])

        self.run_goal("applyTag(wet, gob)")
        state = self.get_state()

        wet_count = sum(1 for f in state if "hasTag(gob,wet)" in f)
        assert wet_count == 1, f"P1 violated: expected 1 wet tag, got {wet_count}"

    def test_property_p2_multi_tag_complete(self):
        """P2: All tags from a multi-tag skill are applied."""
        self.set_state([
            "skillAppliesTag(waterSkill, wet)",
            "skillAppliesTag(waterSkill, clean)"
        ])

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
