"""Tests for tags primitive component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite


class TagsTest(HtnTestSuite):
    """Test suite for tags primitive."""

    def setup(self):
        """Load the tags component (resets planner for clean state)."""
        self.load_component("primitives/tags")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_simple_tag_application(self):
        """Example 1: Simple tag application

        Given: Entity has no tags
        When: applyTag(entity1, burning)
        Then: Plan contains opApplyTag, final state has hasTag(entity1, burning)
        """
        # No initial state needed (entity has no tags)
        self.assert_plan("applyTag(entity1, burning).",
            contains=["opApplyTag(entity1, burning)"])

        self.assert_state_after("applyTag(entity1, burning).",
            has=["hasTag(entity1,burning)"])

    def test_example_2_tag_combination(self):
        """Example 2: Tag combination (burning + wet = steam)

        Given: hasTag(entity1, wet)
        When: applyTag(entity1, burning)
        Then: Entity has steam, not wet or burning
        """
        self.set_state([
            "hasTag(entity1, wet)"
        ])

        self.assert_plan("applyTag(entity1, burning).",
            contains=["opRemoveTag(entity1, wet)", "opApplyTag(entity1, steam)"])

        self.assert_state_after("applyTag(entity1, burning).",
            has=["hasTag(entity1,steam)"],
            not_has=["hasTag(entity1,wet)", "hasTag(entity1,burning)"])

    def test_example_3_same_tag_noop(self):
        """Example 3: Applying same tag (no-op)

        Given: hasTag(entity1, burning)
        When: applyTag(entity1, burning)
        Then: No operators, still has burning
        """
        self.set_state([
            "hasTag(entity1, burning)"
        ])

        self.assert_plan("applyTag(entity1, burning).",
            not_contains=["opApplyTag", "opRemoveTag"])

    def test_example_4_remove_tag(self):
        """Example 4: Remove tag

        Given: hasTag(entity1, burning)
        When: removeTag(entity1, burning)
        Then: Tag is removed
        """
        self.set_state([
            "hasTag(entity1, burning)"
        ])

        self.assert_plan("removeTag(entity1, burning).",
            contains=["opRemoveTag(entity1, burning)"])

        self.assert_state_after("removeTag(entity1, burning).",
            not_has=["hasTag(entity1,burning)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p2_combination_replaces(self):
        """P2: After combination, neither original tag exists.

        Test all defined combinations.
        """
        # Test burning + wet = steam
        self.set_state([
            "hasTag(entity1, wet)"
        ])
        self.run_goal("applyTag(entity1, burning)")
        state = self.get_state()

        # Should have steam, not wet or burning
        has_steam = any("hasTag(entity1,steam)" in f for f in state)
        has_wet = any("hasTag(entity1,wet)" in f for f in state)
        has_burning = any("hasTag(entity1,burning)" in f for f in state)

        assert has_steam, "P2 violated: should have steam"
        assert not has_wet, "P2 violated: should not have wet"
        assert not has_burning, "P2 violated: should not have burning"

    def test_property_p3_commutative_wet_electrified(self):
        """P3: Commutative combinations - wet + electrified and electrified + wet

        Both should produce stunned.
        """
        # Test wet + electrified
        self.setup()  # Reset
        self.set_state([
            "hasTag(entity1, wet)"
        ])
        self.run_goal("applyTag(entity1, electrified)")
        state1 = self.get_state()

        # Test electrified + wet
        self.setup()  # Reset
        self.set_state([
            "hasTag(entity1, electrified)"
        ])
        self.run_goal("applyTag(entity1, wet)")
        state2 = self.get_state()

        # Both should result in stunned
        has_stunned1 = any("hasTag(entity1,stunned)" in f for f in state1)
        has_stunned2 = any("hasTag(entity1,stunned)" in f for f in state2)

        assert has_stunned1, "P3 violated: wet + electrified should produce stunned"
        assert has_stunned2, "P3 violated: electrified + wet should produce stunned"

    # =========================================================================
    # Additional Tests
    # =========================================================================

    def test_frozen_plus_burning_equals_wet(self):
        """Frozen + burning produces wet (ice melts)."""
        self.set_state([
            "hasTag(entity1, frozen)"
        ])

        self.assert_state_after("applyTag(entity1, burning).",
            has=["hasTag(entity1,wet)"],
            not_has=["hasTag(entity1,frozen)", "hasTag(entity1,burning)"])

    def test_remove_nonexistent_tag_noop(self):
        """Removing a tag that doesn't exist is a no-op."""
        # No initial tags
        self.assert_plan("removeTag(entity1, burning).",
            not_contains=["opRemoveTag"])

    def test_multiple_entities_independent(self):
        """Tags on different entities are independent."""
        self.set_state([
            "hasTag(entity1, burning)",
            "hasTag(entity2, wet)"
        ])

        # Apply wet to entity1 (should combine with burning -> steam)
        self.assert_plan("applyTag(entity1, wet).",
            contains=["opRemoveTag(entity1, burning)", "opApplyTag(entity1, steam)"])


def run_tests():
    """Run all tests in this file."""
    suite = TagsTest()
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
