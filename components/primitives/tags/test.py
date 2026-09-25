"""Tests for the tags primitive component."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite

WORLD = [
    "location(pond)", "location(pit)", "location(rink)", "location(field)",
    "locationCanApplyTag(pond, wet)", "locationCanApplyTag(pit, oil)", "locationCanApplyTag(rink, ice)",
    # the pond: a companion and two enemies, one vulnerable to wet + electrified
    "companion(ward)", "enemy(gob)", "enemy(imp)", "at(ward, pond)", "at(gob, pond)", "at(imp, pond)",
    "vulnerableToLocationCombo(imp, wet, electrified)", "vulnerableToLocationCombo(gob, wet, chilled)",
    # the oil pit: a companion, two enemies (orc vulnerable to oil + burning) and a barrel
    "companion(sol)", "enemy(orc)", "enemy(rat)", "at(sol, pit)", "at(orc, pit)", "at(rat, pit)", "at(barrel, pit)",
    "vulnerableToLocationCombo(orc, oil, burning)",
    # the ice rink
    "enemy(yak)", "enemy(elk)", "at(yak, rink)", "at(elk, rink)", "vulnerableToLocationCombo(yak, ice, chilled)",
    # plain ground
    "enemy(ant)", "at(ant, field)", "immune(ant, burning)",
]


class TagsTest(HtnTestSuite):
    """Test suite for the tags primitive."""

    def setup(self):
        self.load_component("primitives/tags")
        self.set_state(WORLD)

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_electrified_in_water(self):
        """Example 1: electrified in water: everyone there is electrified; the vulnerable is defeated."""
        self.assert_plan_set("landSkillTag(electrified, gob).", [
            "opApplyTag(electrified, ward), opApplyTag(electrified, gob), opApplyTag(electrified, imp), "
            "opApplyTag(dead, imp)"])

    def test_example_2_burning_on_oil(self):
        """Example 2: burning on oil: the oil catches fire, every agent there burns (not the barrel)."""
        self.assert_plan_set("landSkillTag(burning, orc).", [
            "opRemoveLocationTag(oil, pit), opAddLocationTag(burning, pit), "
            "opApplyTag(burning, sol), opApplyTag(burning, orc), opApplyTag(burning, rat), opApplyTag(dead, orc)"])

    def test_example_3_chilled_in_water(self):
        """Example 3: chilled in water: the target alone is stunned, and defeated if vulnerable."""
        self.assert_plan_set("landSkillTag(chilled, gob).", ["opApplyTag(stunned, gob), opApplyTag(dead, gob)"])

    def test_example_4_chilled_on_ice(self):
        """Example 4: chilled on ice: stunned; only the vulnerable one is defeated."""
        self.assert_plan_set("landSkillTag(chilled, yak).", ["opApplyTag(stunned, yak), opApplyTag(dead, yak)"])
        self.assert_plan_set("landSkillTag(chilled, elk).", ["opApplyTag(stunned, elk)"])

    def test_example_5_no_combo(self):
        """Example 5: no combo where the target stands: the tag just lands."""
        self.assert_plan_set("landSkillTag(electrified, orc).", ["opApplyTag(electrified, orc)"])

    def test_example_6_immune(self):
        """Example 6: an immune target: nothing lands."""
        self.assert_plan_set("landSkillTag(burning, ant).", [""])

    def test_example_7_already_there(self):
        """Example 7: the target already has the tag."""
        self.set_state(["hasTag(elk, burning)"])
        self.assert_plan_set("landTag(burning, elk).", ["opTagAlreadyOnTarget(burning, elk)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_the_skill_alone_never_defeats(self):
        """P1: a tag with no combo never defeats, even an enemy vulnerable to a combo with it."""
        self.assert_state_after("landSkillTag(burning, imp).", has=["hasTag(imp,burning)"],
                                not_has=["hasTag(imp,dead)"])

    def test_property_p2_only_oil_changes(self):
        """P2: electrified in water leaves the location wet."""
        self.assert_state_after("landSkillTag(electrified, gob).", has=["locationCanApplyTag(pond,wet)"])


def run_tests():
    """Run all tests in this file."""
    suite = TagsTest()
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
