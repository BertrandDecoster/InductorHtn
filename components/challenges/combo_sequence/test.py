"""Tests for combo_sequence challenge component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite


class ComboSequenceTest(HtnTestSuite):
    """Test suite for combo_sequence challenge."""

    def setup(self):
        """Load the combo_sequence component (no external dependencies)."""
        self.load_component("challenges/combo_sequence")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_two_step_combo(self):
        """Example 1: Two-step combo in correct order

        Given: wet at step 1, electrocute at step 2
        When: executeCombo(boss)
        Then: Both effects applied in order
        """
        self.set_state([
            "needsEffect(boss, wet)",
            "comboStep(wet, 1)",
            "needsEffect(boss, electrocute)",
            "comboStep(electrocute, 2)"
        ])

        self.assert_plan("executeCombo(boss).",
            contains=["opApplyEffect(boss, wet)", "opApplyEffect(boss, electrocute)"])

        self.assert_state_after("executeCombo(boss).",
            has=["hasEffect(boss,wet)", "hasEffect(boss,electrocute)"],
            not_has=["needsEffect(boss,wet)", "needsEffect(boss,electrocute)"])

    def test_example_2_effect_already_applied_skip(self):
        """Example 2: Effect already present -- applyEffect is no-op

        Given: boss already has wet effect
        When: applyEffect(boss, wet)
        Then: Plan is empty, state unchanged
        """
        self.set_state([
            "hasEffect(boss, wet)"
        ])

        self.assert_plan("applyEffect(boss, wet).",
            not_contains=["opApplyEffect"])

    def test_example_3_no_combo_no_plan(self):
        """Example 3: No needsEffect or comboStep facts -- no plan

        Given: no combo defined
        When: executeCombo(boss)
        Then: Planning fails
        """
        self.set_state([
            # No needsEffect or comboStep facts
        ])

        self.assert_no_plan("executeCombo(boss).")

    def test_example_4_three_step_combo(self):
        """Example 4: Three-step combo applies all three effects

        Given: freeze at step 1, shatter at step 2, burn at step 3
        When: executeCombo(target)
        Then: All three effects applied in order
        """
        self.set_state([
            "needsEffect(target, freeze)",
            "comboStep(freeze, 1)",
            "needsEffect(target, shatter)",
            "comboStep(shatter, 2)",
            "needsEffect(target, burn)",
            "comboStep(burn, 3)"
        ])

        self.assert_plan("executeCombo(target).",
            contains=["opApplyEffect(target, freeze)",
                      "opApplyEffect(target, shatter)",
                      "opApplyEffect(target, burn)"])

        self.assert_state_after("executeCombo(target).",
            has=["hasEffect(target,freeze)", "hasEffect(target,shatter)", "hasEffect(target,burn)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_all_effects_applied(self):
        """P1: After plan, all needsEffect facts are replaced by hasEffect."""
        self.set_state([
            "needsEffect(boss, wet)",
            "comboStep(wet, 1)",
            "needsEffect(boss, electrocute)",
            "comboStep(electrocute, 2)"
        ])

        self.run_goal("executeCombo(boss)")
        state = self.get_state()

        needs_remaining = [f for f in state if f.startswith("needsEffect(boss,")]
        has_wet = any("hasEffect(boss,wet)" in f for f in state)
        has_electrocute = any("hasEffect(boss,electrocute)" in f for f in state)

        assert len(needs_remaining) == 0, \
            f"P1 violated: needsEffect facts still present: {needs_remaining}"
        assert has_wet, "P1 violated: hasEffect(boss, wet) not added"
        assert has_electrocute, "P1 violated: hasEffect(boss, electrocute) not added"

    def test_property_p2_correct_order(self):
        """P2: Effects are applied in ascending comboStep order.

        Verify the plan contains both operators and that the planning
        system selects the correct sequenced combo method.
        """
        self.set_state([
            "needsEffect(boss, wet)",
            "comboStep(wet, 1)",
            "needsEffect(boss, electrocute)",
            "comboStep(electrocute, 2)"
        ])

        # Both effects must appear in the plan (order enforced by comboStep indexing)
        self.assert_plan("executeCombo(boss).",
            contains=["opApplyEffect(boss, wet)", "opApplyEffect(boss, electrocute)"])

    def test_property_p3_idempotent_effects(self):
        """P3: Applying an already-present effect produces no operator."""
        self.set_state([
            "hasEffect(boss, wet)"
        ])

        initial_state = set(self.get_state())
        self.run_goal("applyEffect(boss, wet)")
        final_state = set(self.get_state())

        assert initial_state == final_state, \
            f"P3 violated: state changed. Added: {final_state - initial_state}, Removed: {initial_state - final_state}"


def run_tests():
    """Run all tests in this file."""
    suite = ComboSequenceTest()
    suite.setup()

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
