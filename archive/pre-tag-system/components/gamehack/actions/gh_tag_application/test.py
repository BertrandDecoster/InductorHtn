"""Tests for gh_tag_application action component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite

WORLD = ["location(room)", "location(inn)", "location(hut)", "location(lake)", "location(sea)", "enemy(gob)"]
LURE_GOB_TO_LAKE = ("opMoveTo(player, room, hut), opAggro(gob, player), "
                    "opMoveTo(player, hut, lake), opAggroMoveTo(gob, hut, lake)")


class GhTagApplicationTest(HtnTestSuite):
    """Test suite for gh_tag_application action."""

    def setup(self):
        """Load gh_tag_application and all its dependencies."""
        self.load_component("gamehack/actions/gh_tag_application")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_way1_companion_has_skill(self):
        """Example 1: Way 1 - a companion holds a skill that applies the tag."""
        self.set_state(WORLD + ["companion(companionW)", "at(companionW, inn)", "at(gob, hut)",
                                "hasSkill(companionW, waterSkill)", "skillAppliesTag(waterSkill, wet)"])
        self.assert_plan_set("applyTagNotPresent(wet, gob).",
            ["opMoveTo(companionW, inn, hut), opUseSkill(companionW, waterSkill, gob), opApplyTag(wet, gob)"])
        self.assert_state_after("applyTagNotPresent(wet, gob).", has=["hasTag(gob,wet)"])

    def test_example_2_way1_companion_gets_skill_from_object(self):
        """Example 2: Way 1 - a companion gets the skill from an object first."""
        self.set_state(WORLD + ["companion(companionI)", "at(companionI, inn)", "at(gob, hut)",
                                "hasSkill(companionI, iceBlastSkill)", "skillAppliesTag(waterSkill, wet)",
                                "object(seaShrine)", "at(seaShrine, sea)", "canGetSkillFrom(seaShrine, waterSkill)"])
        self.assert_plan_set("applyTagNotPresent(wet, gob).",
            ["opMoveTo(companionI, inn, sea), opSwapSkill(companionI, iceBlastSkill, waterSkill), "
             "opMoveTo(companionI, sea, hut), opUseSkill(companionI, waterSkill, gob), opApplyTag(wet, gob)"])

    def test_example_3_way2_location_applies_tag(self):
        """Example 3: Way 2 - a lurer brings the target to a location that applies the tag."""
        self.set_state(WORLD + ["companion(player)", "at(gob, hut)", "at(player, room)",
                                "locationCanApplyTag(lake, wet)"])
        self.assert_plan_set("applyTagNotPresent(wet, gob).", [LURE_GOB_TO_LAKE + ", opApplyTag(wet, gob)"])
        self.assert_state_after("applyTagNotPresent(wet, gob).", has=["at(gob,lake)"])

    def test_example_4_way2_already_at_location(self):
        """Example 4: Way 2 - the target already stands there: no lurer, one plan."""
        self.set_state(WORLD + ["companion(player)", "companion(companionW)", "at(gob, lake)",
                                "at(player, room)", "at(companionW, inn)", "locationCanApplyTag(lake, wet)"])
        self.assert_plan_set("applyTagNotPresent(wet, gob).", ["opApplyTag(wet, gob)"])

    def test_example_5_way3_agent_has_skill(self):
        """Example 5: Way 3 - a lurer brings the target to a non-companion that holds the skill."""
        self.set_state(WORLD + ["companion(player)", "at(gob, hut)", "at(teslaTower, lake)", "at(player, room)",
                                "enemy(teslaTower)", "hasSkill(teslaTower, lightningSkill)",
                                "skillAppliesTag(lightningSkill, electrified)"])
        self.assert_plan_set("applyTagNotPresent(electrified, gob).",
            [LURE_GOB_TO_LAKE + ", opUseSkill(teslaTower, lightningSkill, gob), opApplyTag(electrified, gob)"])

    def test_example_6_way3_already_together(self):
        """Example 6: Way 3 - the target already stands with the non-companion: no lurer, one plan."""
        self.set_state(WORLD + ["companion(player)", "companion(companionW)", "at(gob, lake)",
                                "at(teslaTower, lake)", "at(player, room)", "at(companionW, inn)",
                                "enemy(teslaTower)", "hasSkill(teslaTower, lightningSkill)",
                                "skillAppliesTag(lightningSkill, electrified)"])
        self.assert_plan_set("applyTagNotPresent(electrified, gob).",
            ["opUseSkill(teslaTower, lightningSkill, gob), opApplyTag(electrified, gob)"])

    def test_example_7_no_way_available(self):
        """Example 7: no skill, location or agent applies the tag."""
        self.set_state(WORLD + ["companion(player)", "at(gob, hut)", "at(player, room)"])
        self.assert_no_plan("applyTagNotPresent(stunned, gob).")

    # =========================================================================
    # Additional Tests
    # =========================================================================

    def test_full_applyTag_integration(self):
        """applyTag delegates to applyTagNotPresent when the tag is missing."""
        self.set_state(WORLD + ["companion(companionE)", "at(companionE, hut)", "at(gob, hut)",
                                "hasSkill(companionE, lightningSkill)", "skillAppliesTag(lightningSkill, electrified)"])
        self.assert_plan_set("applyTag(electrified, gob).",
            ["opStayInLocation(companionE), opUseSkill(companionE, lightningSkill, gob), opApplyTag(electrified, gob)"])

    def test_applyTag_immune_target(self):
        """applyTag finds no plan for a tag the target is immune to."""
        self.set_state(WORLD + ["companion(companionE)", "at(companionE, hut)", "at(gob, hut)",
                                "hasSkill(companionE, lightningSkill)", "skillAppliesTag(lightningSkill, electrified)",
                                "immune(gob, electrified)"])
        self.assert_no_plan("applyTag(electrified, gob).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_tag_applied(self):
        """P1: After a successful plan, the target has the requested tag."""
        self.set_state(WORLD + ["companion(companionW)", "at(companionW, inn)", "at(gob, hut)",
                                "hasSkill(companionW, waterSkill)", "skillAppliesTag(waterSkill, wet)"])
        self.run_goal("applyTagNotPresent(wet, gob)")
        state = self.get_state()
        has_wet = any("hasTag(gob,wet)" in f for f in state)
        assert has_wet, "P1 violated: gob should have wet tag after applyTagNotPresent"


def run_tests():
    """Run all tests in this file."""
    suite = GhTagApplicationTest()
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
