"""Tests for the tags primitive component."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../src/Python")))

from htn_test_framework import HtnTestSuite

OIL = ["location(storage)", "locationCanApplyTag(storage, oily)",
       "companion(pyro)", "hasSkill(pyro, igniteSkill)", "skillAppliesTag(igniteSkill, burning)",
       "enemy(gob)", "at(gob, storage)", "companion(warden)", "at(warden, storage)", "hasTag(warden, frozen)",
       "at(barrel, storage)", "location(field)", "enemy(imp)", "at(imp, field)"]


class TagsTest(HtnTestSuite):
    """Test suite for the tags primitive."""

    def setup(self):
        self.load_component("primitives/tags")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_wet_and_burning_make_steam(self):
        """Example 1: wet + burning = steam."""
        self.set_state(["hasTag(gob, wet)", "hasTag(gob, burning)"])
        self.assert_plan_set("combineTags(gob).",
            ["opRemoveTag(wet, gob), opRemoveTag(burning, gob), opApplyTag(steam, gob)"])

    def test_example_2_frozen_and_burning_make_wet(self):
        """Example 2: frozen + burning = wet (ice melts)."""
        self.set_state(["hasTag(gob, frozen)", "hasTag(gob, burning)"])
        self.assert_state_after("combineTags(gob).", has=["hasTag(gob,wet)"],
                                not_has=["hasTag(gob,frozen)", "hasTag(gob,burning)"])

    def test_example_3_result_already_held(self):
        """Example 3: the result is already a third tag: the pair just goes."""
        self.set_state(["hasTag(gob, wet)", "hasTag(gob, burning)", "hasTag(gob, steam)"])
        self.assert_plan_set("combineTags(gob).", ["opRemoveTag(wet, gob), opRemoveTag(burning, gob)"])

    def test_example_4_result_is_one_of_the_pair(self):
        """Example 4: oily + burning = burning."""
        self.set_state(["hasTag(gob, oily)", "hasTag(gob, burning)"])
        self.assert_plan_set("combineTags(gob).",
            ["opRemoveTag(oily, gob), opRemoveTag(burning, gob), opApplyTag(burning, gob)"])

    def test_example_5_nothing_combines(self):
        """Example 5: nothing combines: the empty plan."""
        self.set_state(["hasTag(gob, wet)", "hasTag(gob, oily)"])
        self.assert_plan_set("combineTags(gob).", [""])

    def test_example_6_a_location_combines(self):
        """Example 6: an oily location that gets burning burns."""
        self.set_state(["location(storage)", "locationCanApplyTag(storage, oily)", "locationCanApplyTag(storage, burning)"])
        self.assert_plan_set("combineTags(storage).", [
            "opRemoveLocationTag(oily, storage), opRemoveLocationTag(burning, storage), opAddLocationTag(burning, storage)"])

    def test_example_7_igniting_an_oily_location(self):
        """Example 7: the location burns, and every agent there gets burning (not the barrel)."""
        self.set_state(OIL)
        self.assert_plan_set("useSkillOnLocation(pyro, igniteSkill, storage).", [
            "opUseSkill(pyro, igniteSkill, storage), opAddLocationTag(burning, storage), "
            "opRemoveLocationTag(oily, storage), opRemoveLocationTag(burning, storage), opAddLocationTag(burning, storage), "
            "opApplyTag(burning, warden), opRemoveTag(frozen, warden), opRemoveTag(burning, warden), opApplyTag(wet, warden), "
            "opApplyTag(burning, warden), opRemoveTag(wet, warden), opRemoveTag(burning, warden), opApplyTag(steam, warden), "
            "opApplyTag(burning, warden), opApplyTag(burning, gob)"])

    def test_example_8_plain_ground_does_not_burn(self):
        """Example 8: a fire spell on plain ground changes nothing."""
        self.set_state(OIL)
        self.assert_plan_set("useSkillOnLocation(pyro, igniteSkill, field).", ["opUseSkill(pyro, igniteSkill, field)"])

    def test_example_9_location_tag_lands(self):
        """Example 9: the location's tag lands on an agent standing there, and combines."""
        self.set_state(["locationCanApplyTag(lake, wet)", "at(gob, lake)", "hasTag(gob, burning)",
                        "at(imp, lake)", "hasTag(imp, wet)", "at(ox, lake)", "immune(ox, wet)"])
        self.assert_plan_set("useLocationToApplyTag(lake, wet, gob).",
            ["opApplyTag(wet, gob), opRemoveTag(burning, gob), opRemoveTag(wet, gob), opApplyTag(steam, gob)"])
        self.assert_plan_set("useLocationToApplyTag(lake, wet, imp).", ["opTagAlreadyOnTarget(wet, imp)"])
        self.assert_no_plan("useLocationToApplyTag(lake, wet, ox).")

    def test_example_10_electronics_plus_electrified_equals_disabled(self):
        """Example 10: electronics + electrified = disabled."""
        self.set_state(["hasTag(device1, electronics)", "hasTag(device1, electrified)"])
        self.assert_state_after("combineTags(device1).", has=["hasTag(device1,disabled)"],
                                not_has=["hasTag(device1,electronics)", "hasTag(device1,electrified)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_nothing_left_to_combine(self):
        """P1: after combineTags, no two tags of the agent combine."""
        self.set_state(["hasTag(gob, frozen)", "hasTag(gob, burning)", "hasTag(gob, electrified)"])
        self.run_goal("combineTags(gob)")
        tags = [f[len("hasTag(gob,"):-1] for f in self.get_state() if f.startswith("hasTag(gob,")]
        assert sorted(tags) == ["stunned"], f"P1 violated: {tags}"

    def test_property_p2_commutative_wet_electrified(self):
        """P2: wet + electrified gives stunned whichever landed first."""
        self.set_state(["locationCanApplyTag(pool, electrified)", "at(gob, pool)", "hasTag(gob, wet)",
                        "locationCanApplyTag(bog, wet)", "at(imp, bog)", "hasTag(imp, electrified)"])
        self.assert_state_after("useLocationToApplyTag(pool, electrified, gob).", has=["hasTag(gob,stunned)"])
        self.assert_state_after("useLocationToApplyTag(bog, wet, imp).", has=["hasTag(imp,stunned)"])


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
