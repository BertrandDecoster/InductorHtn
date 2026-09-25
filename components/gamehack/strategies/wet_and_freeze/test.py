"""Tests for wet_and_freeze strategy component."""

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


FREEZE = "opUseSkill(frost, frostSkill, gob), opApplyTag(stunned, gob), opApplyTag(dead, gob)"


class WetAndFreezeTest(HtnTestSuite):
    """Test suite for wet_and_freeze strategy."""

    def setup(self):
        """Load wet_and_freeze and all dependencies."""
        self.load_component("gamehack/strategies/wet_and_freeze")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_lured_into_water_and_chilled(self):
        """Example 1: gob is vulnerable to wet + chilled. Player or pyro lures it into the lake;
        frost, the only one with a chilled skill, chills it there."""
        self.set_state(WORLD + ["vulnerableToLocationCombo(gob, wet, chilled)"])
        self.assert_plan_set("wetAndFreeze(gob).", [
            lure("player", "lake") + ", opMoveTo(frost, camp, lake), " + FREEZE,
            lure("pyro", "lake") + ", opMoveTo(frost, camp, lake), " + FREEZE,
        ])

    def test_example_2_water_or_ice(self):
        """Example 2: vulnerable to both wet + chilled and ice + chilled: the lake and the rink both work."""
        self.set_state(WORLD + ["vulnerableToLocationCombo(gob, wet, chilled)",
                                "vulnerableToLocationCombo(gob, ice, chilled)"])
        self.assert_plan("wetAndFreeze(gob).", min_solutions=4, max_solutions=4,
            contains=["opAggroMoveTo(gob, hut, lake)", "opAggroMoveTo(gob, hut, rink)"])

    def test_example_3_not_vulnerable(self):
        """Example 3: an enemy not vulnerable to a chilled combo rules the strategy out."""
        self.set_state(WORLD)
        self.assert_no_plan("wetAndFreeze(gob).")

    def test_example_4_one_companion_is_not_enough(self):
        """Example 4: the lurer and the caster are two companions."""
        self.set_state(["location(camp)", "location(hut)", "location(lake)", "locationCanApplyTag(lake, wet)",
                        "enemy(gob)", "at(gob, hut)", "companion(frost)", "at(frost, camp)",
                        "hasSkill(frost, frostSkill)", "skillAppliesTag(frostSkill, chilled)",
                        "vulnerableToLocationCombo(gob, wet, chilled)"])
        self.assert_no_plan("wetAndFreeze(gob).")

    def test_example_5_already_standing_in_water(self):
        """Example 5: gob already stands in the lake: no lurer, frost alone chills it."""
        self.set_state([f for f in WORLD if f != "at(gob, hut)"] + ["at(gob, lake)", "vulnerableToLocationCombo(gob, wet, chilled)"])
        self.assert_plan_set("wetAndFreeze(gob).", ["opMoveTo(frost, camp, lake), " + FREEZE])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_defeated(self):
        """P1: the enemy ends stunned and dead."""
        self.set_state(WORLD + ["vulnerableToLocationCombo(gob, wet, chilled)"])
        self.run_goal("wetAndFreeze(gob)")
        state = self.get_state()
        assert any("hasTag(gob,stunned)" in f for f in state), "P1 violated: gob should be stunned"
        assert any("hasTag(gob,dead)" in f for f in state), "P1 violated: gob should be dead"


def run_tests():
    """Run all tests in this file."""
    suite = WetAndFreezeTest()
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
