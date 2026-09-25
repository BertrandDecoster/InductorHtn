"""Tests for wet_and_electrify strategy component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite

GH4_WORLD = [
    "location(room)", "location(inn)", "location(hut)", "location(lake)",
    "enemy(gob)", "at(gob, hut)", "at(companionW, inn)", "at(companionE, hut)",
    "companion(companionW)", "companion(companionE)",
    "hasSkill(companionW, waterSkill)", "hasSkill(companionE, lightningSkill)",
    "skillAppliesTag(waterSkill, wet)", "skillAppliesTag(lightningSkill, electrified)",
]
GH4_PLAN = ("opMoveTo(companionW, inn, hut), opUseSkill(companionW, waterSkill, gob), opApplyTag(wet, gob), "
            "opStayInLocation(companionE), opUseSkill(companionE, lightningSkill, gob), opApplyTag(electrified, gob)")


class WetAndElectrifyTest(HtnTestSuite):
    """Test suite for wet_and_electrify strategy."""

    def setup(self):
        """Load wet_and_electrify and all dependencies."""
        self.load_component("gamehack/strategies/wet_and_electrify")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_both_tags_via_companion_skills(self):
        """Example 1: companionW wets gob, companionE electrifies it."""
        self.set_state(GH4_WORLD)
        self.assert_plan_set("wetAndElectrify(gob).", [GH4_PLAN])

    def test_example_2_wet_via_location(self):
        """Example 2: gob is lured to the lake (either companion lures), then electrified."""
        self.set_state([
            "location(room)", "location(hut)", "location(lake)",
            "enemy(gob)", "at(gob, hut)", "at(player, room)", "at(companionE, hut)",
            "companion(player)", "companion(companionE)", "hasSkill(companionE, lightningSkill)",
            "locationCanApplyTag(lake, wet)", "skillAppliesTag(lightningSkill, electrified)",
        ])
        self.assert_plan_set("wetAndElectrify(gob).", [
            "opMoveTo(player, room, hut), opAggro(gob, player), opMoveTo(player, hut, lake), "
            "opAggroMoveTo(gob, hut, lake), opApplyTag(wet, gob), opMoveTo(companionE, hut, lake), "
            "opUseSkill(companionE, lightningSkill, gob), opApplyTag(electrified, gob)",
            "opStayInLocation(companionE), opAggro(gob, companionE), opMoveTo(companionE, hut, lake), "
            "opAggroMoveTo(gob, hut, lake), opApplyTag(wet, gob), opStayInLocation(companionE), "
            "opUseSkill(companionE, lightningSkill, gob), opApplyTag(electrified, gob)",
        ])

    def test_example_3_non_enemy_fails(self):
        """Example 3: the target must be an enemy."""
        self.set_state(["companion(player)", "at(player, room)"])
        self.assert_no_plan("wetAndElectrify(player).")

    def test_example_4_immune_target(self):
        """Example 4: a target immune to electrified rules the strategy out."""
        self.set_state(GH4_WORLD + ["immune(gob, electrified)"])
        self.assert_no_plan("wetAndElectrify(gob).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_both_tags(self):
        """P1: Target has both wet and electrified after the plan."""
        self.set_state(GH4_WORLD)
        self.run_goal("wetAndElectrify(gob)")
        state = self.get_state()
        assert any("hasTag(gob,wet)" in f for f in state), "P1 violated: gob should have wet tag"
        assert any("hasTag(gob,electrified)" in f for f in state), "P1 violated: gob should be electrified"

    def test_property_p2_sequential_ordering(self):
        """P2: Wet lands before electrified (the plan set of Example 1 fixes the order)."""
        self.set_state(GH4_WORLD)
        self.assert_plan_set("wetAndElectrify(gob).", [GH4_PLAN])
        assert GH4_PLAN.index("opApplyTag(wet") < GH4_PLAN.index("opApplyTag(electrified")


def run_tests():
    """Run all tests in this file."""
    suite = WetAndElectrifyTest()
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
