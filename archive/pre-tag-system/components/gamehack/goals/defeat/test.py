"""Tests for the defeat goal component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import findAllPlansResultToPrologStringList

LOCATIONS = ["location(room)", "location(inn)", "location(hut)", "location(lake)",
             "location(sea)", "location(mountain)"]
GH7_WORLD = LOCATIONS + [
    "enemy(gob)", "at(gob, hut)",
    "at(companionI, inn)", "at(companionF, inn)", "at(player, room)",
    "companion(player)", "companion(companionI)", "companion(companionF)",
    "hasSkill(companionI, iceBlastSkill)", "hasSkill(companionF, fireballSkill)",
    "skillAppliesTag(iceBlastSkill, stunned)", "skillAppliesTag(fireballSkill, burning)",
    "skillAppliesTag(lightningSkill, electrified)", "skillAppliesTag(waterSkill, wet)",
    "skillHasTag(fireballSkill, slow)",
    "object(seaShrine)", "at(seaShrine, sea)", "canGetSkillFrom(seaShrine, waterSkill)",
    "object(mountainShrine)", "at(mountainShrine, mountain)", "canGetSkillFrom(mountainShrine, iceBlastSkill)",
    "locationCanApplyTag(lake, wet)",
]
GH4_WORLD = LOCATIONS + [
    "enemy(gob)", "at(gob, hut)",
    "at(player, room)", "at(companionE, hut)", "at(companionW, inn)",
    "companion(player)", "companion(companionE)", "companion(companionW)",
    "hasSkill(companionE, lightningSkill)", "hasSkill(companionW, waterSkill)",
    "skillAppliesTag(lightningSkill, electrified)", "skillAppliesTag(waterSkill, wet)",
    "locationCanApplyTag(lake, wet)", "locationCanApplyTag(sea, wet)",
]


class DefeatTest(HtnTestSuite):
    """Test suite for the defeat goal."""

    def setup(self):
        """Load defeat and all its dependencies."""
        self.load_component("gamehack/goals/defeat")

    def _plans(self, goal):
        self._reload_file()
        error, result = self._planner.FindAllPlansCustomVariables(goal)
        assert error is None, f"Planning error: {error}"
        return findAllPlansResultToPrologStringList(result)

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_gh7_world_several_strategies(self):
        """Example 1: GH7 world - stunAndSlow and stunAndBurn give plans; nothing electrifies,
        so wetAndElectrify doesn't."""
        self.set_state(GH7_WORLD)
        self.assert_plan("defeat(gob).",
            contains=["opSynchronize", "opApplyTag(stunned, gob), opMoveTo(companionF, inn, hut)"],
            not_contains=["opApplyTag(electrified"])

    def test_example_2_gh4_world_only_wet_and_electrify(self):
        """Example 2: GH4 world - no stun or slow skill, so only wetAndElectrify."""
        self.set_state(GH4_WORLD)
        self.assert_plan("defeat(gob).",
            contains=["opApplyTag(wet, gob)", "opApplyTag(electrified, gob)"],
            not_contains=["opSynchronize", "opApplyTag(stunned"])

    def test_example_3_non_enemy_fails(self):
        """Example 3: the target must be an enemy."""
        self.set_state(GH7_WORLD)
        self.assert_no_plan("defeat(player).")

    def test_example_4_dead_enemy_needs_no_plan(self):
        """Example 4: an enemy that is already dead can't be defeated again."""
        self.set_state(GH7_WORLD + ["hasTag(gob, dead)"])
        self.assert_no_plan("defeat(gob).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_every_plan_ends_dead(self):
        """P1: Every plan ends with the target dead."""
        self.set_state(GH7_WORLD)
        plans = self._plans("defeat(gob).")
        assert plans, "P1: expected plans"
        for p in plans:
            assert p.endswith("opApplyTag(dead, gob)"), f"P1 violated: {p}"

    def test_property_p2_no_duplicate_plans(self):
        """P2: No two plans are the same."""
        self.set_state(GH7_WORLD)
        plans = self._plans("defeat(gob).")
        assert len(plans) == len(set(plans)), "P2 violated: duplicate plans"


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
