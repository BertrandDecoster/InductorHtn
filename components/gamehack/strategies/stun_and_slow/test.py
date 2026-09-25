"""Tests for stun_and_slow strategy component."""

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


PLAN = ("opMoveTo(player, camp, hut), opMoveTo(pyro, camp, hut), opSynchronize(player, pyro), "
        "opUseSkill(player, iceBlastSkill, gob), opApplyTag(stunned, gob), "
        "opUseSkill(pyro, fireballSkill, gob), opApplyTag(burning, gob)")


class StunAndSlowTest(HtnTestSuite):
    """Test suite for stun_and_slow strategy."""

    def setup(self):
        """Load stun_and_slow and all dependencies."""
        self.load_component("gamehack/strategies/stun_and_slow")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_both_companions_have_skills(self):
        """Example 1: the player stuns while pyro's slow fireball lands. Frost holds neither skill: one plan."""
        self.set_state(WORLD)
        self.assert_plan_set("stunAndSlow(gob).", [PLAN])

    def test_example_2_only_one_companion(self):
        """Example 2: one companion can't do both parts."""
        self.set_state(["location(camp)", "location(hut)", "enemy(gob)", "at(gob, hut)",
                        "companion(player)", "at(player, camp)",
                        "hasSkill(player, iceBlastSkill)", "skillAppliesTag(iceBlastSkill, stunned)",
                        "skillHasTag(fireballSkill, slow)", "skillAppliesTag(fireballSkill, burning)"])
        self.assert_no_plan("stunAndSlow(gob).")

    def test_example_3_target_immune_to_stunned(self):
        """Example 3: a target immune to stunned rules the strategy out."""
        self.set_state(WORLD + ["immune(gob, stunned)"])
        self.assert_no_plan("stunAndSlow(gob).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_two_companions(self):
        """P1: two different companions take part, synchronized before either skill is used."""
        self.set_state(WORLD)
        self.assert_plan("stunAndSlow(gob).", contains=["opSynchronize(player, pyro), opUseSkill"])

    def test_property_p2_both_effects(self):
        """P2: gob ends stunned and burning (not dead: the goal adds that)."""
        self.set_state(WORLD)
        self.assert_state_after("stunAndSlow(gob).", has=["hasTag(gob,stunned)", "hasTag(gob,burning)"],
            not_has=["hasTag(gob,dead)"])


def run_tests():
    """Run all tests in this file."""
    suite = StunAndSlowTest()
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
