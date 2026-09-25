"""Tests for the defeat goal component."""

import json
import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import findAllPlansResultToPrologStringList

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

VULNERABLE = ["vulnerableToLocationCombo(gob, wet, chilled)", "vulnerableToLocationCombo(gob, oil, burning)"]


class DefeatTest(HtnTestSuite):
    """Test suite for the defeat goal."""

    def setup(self):
        """Load defeat and all its dependencies."""
        self.load_component("gamehack/goals/defeat")

    def _plans(self, goal):
        self._reload_file()
        error, result = self._planner.FindAllPlansCustomVariables(goal)
        assert error is None, f"Planning error: {error}"
        solutions = json.loads(result)
        if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
            return []
        return findAllPlansResultToPrologStringList(result)

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_all_three_strategies(self):
        """Example 1: 5 plans: wetAndFreeze (2 lurers), oilAndBurn (2 lurers), stunAndSlow (1)."""
        self.set_state(WORLD + VULNERABLE)
        plans = self._plans("defeat(gob).")
        assert len(plans) == 5, f"expected 5 plans, got {len(plans)}"
        assert sum("opUseSkill(frost, frostSkill, gob)" in p for p in plans) == 2
        assert sum("opAddLocationTag(burning, kitchen)" in p for p in plans) == 2
        assert sum("opSynchronize(player, pyro)" in p for p in plans) == 1

    def test_example_2_only_stun_and_slow(self):
        """Example 2: gob vulnerable to nothing: only stunAndSlow, which adds dead itself."""
        self.set_state(WORLD)
        self.assert_plan_set("defeat(gob).", [
            "opMoveTo(player, camp, hut), opMoveTo(pyro, camp, hut), opSynchronize(player, pyro), "
            "opUseSkill(player, iceBlastSkill, gob), opApplyTag(stunned, gob), "
            "opUseSkill(pyro, fireballSkill, gob), opApplyTag(burning, gob), opApplyTag(dead, gob)"])

    def test_example_3_non_enemy_fails(self):
        """Example 3: the target must be an enemy."""
        self.set_state(WORLD + VULNERABLE)
        self.assert_no_plan("defeat(player).")

    def test_example_4_dead_enemy_needs_no_plan(self):
        """Example 4: an enemy that is already dead can't be defeated again."""
        self.set_state(WORLD + VULNERABLE + ["hasTag(gob, dead)"])
        self.assert_no_plan("defeat(gob).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_every_plan_ends_dead(self):
        """P1: Every plan ends with the target dead."""
        self.set_state(WORLD + VULNERABLE)
        plans = self._plans("defeat(gob).")
        assert plans, "P1: expected plans"
        for p in plans:
            assert p.endswith("opApplyTag(dead, gob)"), f"P1 violated: {p}"

    def test_property_p2_two_companions_act(self):
        """P2: in every plan, two different companions act (move or use a skill)."""
        self.set_state(WORLD + VULNERABLE)
        for p in self._plans("defeat(gob)."):
            actors = {c for c in ("player", "frost", "pyro")
                      if f"opMoveTo({c}," in p or f"opUseSkill({c}," in p}
            assert len(actors) >= 2, f"P2 violated: {p}"


def run_tests():
    """Run all tests in this file."""
    suite = DefeatTest()
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
