"""Tests for oil_and_burn strategy component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite

# Three companions at camp: player (iceBlastSkill: stunned), frost (frostSkill: chilled),
# pyro (fireballSkill: burning, slow). Gob at the hut. A wet lake, an ice rink, a kitchen with oil.
WORLD = [
    "location(camp)", "location(hut)", "location(lake)", "location(rink)", "location(kitchen)",
    "locationCanApplyTag(lake, wet)", "locationCanApplyTag(rink, ice)", "locationCanApplyTag(kitchen, oil)",
    "enemy(gob)", "at(gob, hut)",
    "companion(player)", "companion(frost)", "companion(pyro)",
    "at(player, camp)", "at(frost, camp)", "at(pyro, camp)",
    "hasSkill(player, iceBlastSkill)", "skillAppliesTag(iceBlastSkill, stunned)",
    "hasSkill(frost, frostSkill)", "skillAppliesTag(frostSkill, chilled)",
    "hasSkill(pyro, fireballSkill)", "skillAppliesTag(fireballSkill, burning)", "skillHasTag(fireballSkill, slow)",
]


def lure(lurer, to):
    return (f"opMoveTo({lurer}, camp, hut), opAggro(gob, {lurer}), "
            f"opMoveTo({lurer}, hut, {to}), opAggroMoveTo(gob, hut, {to})")



def burn(lurer):
    return (lure(lurer, "kitchen") + ", opMoveTo(pyro, camp, kitchen), opUseSkill(pyro, fireballSkill, gob), "
            "opRemoveLocationTag(oil, kitchen), opAddLocationTag(burning, kitchen), "
            f"opApplyTag(burning, {lurer}), opApplyTag(burning, pyro), opApplyTag(burning, gob), opApplyTag(dead, gob)")


class OilAndBurnTest(HtnTestSuite):
    """Test suite for oil_and_burn strategy."""

    def setup(self):
        """Load oil_and_burn and all dependencies."""
        self.load_component("gamehack/strategies/oil_and_burn")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_lured_onto_oil_and_burned(self):
        """Example 1: player or frost lures gob into the kitchen, which holds oil; pyro sets it burning.
        The oil catches fire and everyone there burns, the lurer and pyro included."""
        self.set_state(WORLD + ["vulnerableToLocationCombo(gob, oil, burning)"])
        self.assert_plan_set("oilAndBurn(gob).", [burn("player"), burn("frost")])

    def test_example_2_not_vulnerable(self):
        """Example 2: an enemy not vulnerable to oil + burning rules the strategy out."""
        self.set_state(WORLD + ["vulnerableToLocationCombo(gob, wet, chilled)"])
        self.assert_no_plan("oilAndBurn(gob).")

    def test_example_3_no_oil(self):
        """Example 3: no oil location, no plan."""
        self.set_state(["location(camp)", "location(hut)", "enemy(gob)", "at(gob, hut)",
                        "companion(player)", "companion(pyro)", "at(player, camp)", "at(pyro, camp)",
                        "hasSkill(pyro, fireballSkill)", "skillAppliesTag(fireballSkill, burning)",
                        "vulnerableToLocationCombo(gob, oil, burning)"])
        self.assert_no_plan("oilAndBurn(gob).")

    def test_example_4_already_standing_on_oil(self):
        """Example 4: gob already stands in the kitchen: no lurer, pyro alone sets it burning."""
        self.set_state([f for f in WORLD if f != "at(gob, hut)"] + ["at(gob, kitchen)", "vulnerableToLocationCombo(gob, oil, burning)"])
        self.assert_plan_set("oilAndBurn(gob).", [
            "opMoveTo(pyro, camp, kitchen), opUseSkill(pyro, fireballSkill, gob), "
            "opRemoveLocationTag(oil, kitchen), opAddLocationTag(burning, kitchen), "
            "opApplyTag(burning, pyro), opApplyTag(burning, gob), opApplyTag(dead, gob)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_oil_becomes_burning(self):
        """P1: after the plan, the kitchen is burning, no longer oil, and gob is dead."""
        self.set_state(WORLD + ["vulnerableToLocationCombo(gob, oil, burning)"])
        self.assert_state_after("oilAndBurn(gob).",
            has=["locationCanApplyTag(kitchen,burning)", "hasTag(gob,dead)"],
            not_has=["locationCanApplyTag(kitchen,oil)"])


def run_tests():
    """Run all tests in this file."""
    suite = OilAndBurnTest()
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
