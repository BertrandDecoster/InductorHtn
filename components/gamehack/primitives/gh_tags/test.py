"""Tests for gh_tags primitive component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite

# frost (chilled), pyro (burning), volt (electrified) stand with gob in the hall (no location tag)
WORLD = [
    "location(hall)", "location(lake)", "location(kitchen)", "location(rink)",
    "locationCanApplyTag(lake, wet)", "locationCanApplyTag(kitchen, oil)", "locationCanApplyTag(rink, ice)",
    "companion(frost)", "companion(pyro)", "companion(volt)", "enemy(gob)", "enemy(orc)",
    "hasSkill(frost, frostSkill)", "skillAppliesTag(frostSkill, chilled)",
    "hasSkill(pyro, fireballSkill)", "skillAppliesTag(fireballSkill, burning)",
    "hasSkill(volt, lightningSkill)", "skillAppliesTag(lightningSkill, electrified)",
    "hasSkill(splash, waterSkill)", "skillAppliesTag(waterSkill, wet)", "skillAppliesTag(waterSkill, clean)",
]


def at(*pairs):
    return [f"at({a}, {l})" for a, l in pairs]


class GhTagsTest(HtnTestSuite):
    """Test suite for gh_tags primitive."""

    def setup(self):
        """Load the gh_tags component."""
        self.load_component("gamehack/primitives/gh_tags")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_no_combo_the_tag_just_lands(self):
        """Example 1: on an untagged location, a skill's tag just lands."""
        self.set_state(WORLD + at(("pyro", "hall"), ("gob", "hall")))
        self.assert_plan_set("useSkillOnTarget(pyro, fireballSkill, gob).",
            ["opUseSkill(pyro, fireballSkill, gob), opApplyTag(burning, gob)"])

    def test_example_2_every_tag_of_the_skill_lands(self):
        """Example 2: a skill with two tags lands both."""
        self.set_state(WORLD + at(("splash", "hall"), ("gob", "hall")))
        self.assert_plan_set("useSkillOnTarget(splash, waterSkill, gob).",
            ["opUseSkill(splash, waterSkill, gob), opApplyTag(wet, gob), opApplyTag(clean, gob)"])

    def test_example_3_wet_and_electrified(self):
        """Example 3: electrified in water: everyone there is electrified, the vulnerable enemy is defeated,
        the location stays wet."""
        self.set_state(WORLD + at(("volt", "lake"), ("gob", "lake"), ("orc", "lake"))
                       + ["vulnerableToLocationCombo(gob, wet, electrified)"])
        self.assert_plan_set("useSkillOnTarget(volt, lightningSkill, gob).",
            ["opUseSkill(volt, lightningSkill, gob), opApplyTag(electrified, volt), opApplyTag(electrified, gob), "
             "opApplyTag(electrified, orc), opApplyTag(dead, gob)"])
        self.assert_state_after("useSkillOnTarget(volt, lightningSkill, gob).",
            has=["locationCanApplyTag(lake,wet)"])

    def test_example_4_oil_and_burning(self):
        """Example 4: burning on oil: the oil becomes burning, everyone there burns, the vulnerable are defeated."""
        self.set_state(WORLD + at(("pyro", "kitchen"), ("gob", "kitchen"), ("orc", "kitchen"))
                       + ["vulnerableToLocationCombo(gob, oil, burning)", "vulnerableToLocationCombo(orc, oil, burning)"])
        self.assert_plan_set("useSkillOnTarget(pyro, fireballSkill, gob).",
            ["opUseSkill(pyro, fireballSkill, gob), opRemoveLocationTag(oil, kitchen), opAddLocationTag(burning, kitchen), "
             "opApplyTag(burning, pyro), opApplyTag(burning, gob), opApplyTag(burning, orc), "
             "opApplyTag(dead, gob), opApplyTag(dead, orc)"])
        self.assert_state_after("useSkillOnTarget(pyro, fireballSkill, gob).",
            has=["locationCanApplyTag(kitchen,burning)"], not_has=["locationCanApplyTag(kitchen,oil)"])

    def test_example_5_chilled_on_ice(self):
        """Example 5: chilled on ice: the target alone is stunned, and defeated if vulnerable."""
        self.set_state(WORLD + at(("frost", "rink"), ("gob", "rink"), ("orc", "rink"))
                       + ["vulnerableToLocationCombo(gob, ice, chilled)"])
        self.assert_plan_set("useSkillOnTarget(frost, frostSkill, gob).",
            ["opUseSkill(frost, frostSkill, gob), opApplyTag(stunned, gob), opApplyTag(dead, gob)"])

    def test_example_6_chilled_in_water_not_vulnerable(self):
        """Example 6: chilled in water stuns; an enemy not vulnerable to the combo is not defeated."""
        self.set_state(WORLD + at(("frost", "lake"), ("gob", "lake")))
        self.assert_plan_set("useSkillOnTarget(frost, frostSkill, gob).",
            ["opUseSkill(frost, frostSkill, gob), opApplyTag(stunned, gob)"])

    def test_example_7_immune_and_present_tags(self):
        """Example 7: an immune agent gets nothing; a present tag shows opTagAlreadyOnTarget."""
        self.set_state(WORLD + at(("volt", "lake"), ("gob", "lake"), ("orc", "lake"))
                       + ["immune(orc, electrified)", "hasTag(gob, electrified)"])
        self.assert_plan_set("useSkillOnTarget(volt, lightningSkill, gob).",
            ["opUseSkill(volt, lightningSkill, gob), opApplyTag(electrified, volt), "
             "opTagAlreadyOnTarget(electrified, gob)"])

    def test_example_8_skill_needs_holder_and_target_together(self):
        """Example 8: the user must hold the skill and stand with the target."""
        self.set_state(WORLD + at(("pyro", "hall"), ("gob", "lake")))
        self.assert_no_plan("useSkillOnTarget(pyro, fireballSkill, gob).")
        self.assert_no_plan("useSkillOnTarget(frost, fireballSkill, gob).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_no_duplicate_tags(self):
        """P1: a tag already present is not added twice."""
        self.set_state(WORLD + at(("pyro", "hall"), ("gob", "hall")) + ["hasTag(gob, burning)"])
        self.run_goal("useSkillOnTarget(pyro, fireballSkill, gob)")
        state = self.get_state()
        assert sum(1 for f in state if "hasTag(gob,burning)" in f) == 1, "P1 violated"

    def test_property_p2_skill_alone_never_defeats(self):
        """P2: without a location combo, even a vulnerable enemy is not defeated."""
        self.set_state(WORLD + at(("pyro", "hall"), ("gob", "hall")) + ["vulnerableToLocationCombo(gob, oil, burning)"])
        self.assert_plan("useSkillOnTarget(pyro, fireballSkill, gob).", not_contains=["opApplyTag(dead"])


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
