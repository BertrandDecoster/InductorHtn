"""Tests for gh_skills primitive component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite

WORLD = ["location(room)", "location(inn)", "location(hut)", "location(sea)", "location(mountain)",
         "object(seaShrine)", "at(seaShrine, sea)", "canGetSkillFrom(seaShrine, waterSkill)",
         "object(mountainShrine)", "at(mountainShrine, mountain)", "canGetSkillFrom(mountainShrine, iceBlastSkill)"]


class GhSkillsTest(HtnTestSuite):
    """Test suite for gh_skills primitive."""

    def setup(self):
        """Load the gh_skills component (and its dependency gh_movement)."""
        self.load_component("gamehack/primitives/gh_skills")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_companion_already_has_skill(self):
        """Example 1: already holds the skill, just goes to the target."""
        self.set_state(WORLD + ["companion(companionI)", "at(companionI, inn)", "at(gob, hut)",
                                "hasSkill(companionI, iceBlastSkill)"])
        self.assert_plan_set("prepareToUseSkill(companionI, iceBlastSkill, gob).",
            ["opMoveTo(companionI, inn, hut)"])

    def test_example_2_companion_swaps_skill_at_object(self):
        """Example 2: goes to the object, swaps the skill, goes to the target."""
        self.set_state(WORLD + ["companion(companionI)", "at(companionI, inn)", "at(gob, hut)",
                                "hasSkill(companionI, iceBlastSkill)"])
        self.assert_plan_set("prepareToUseSkill(companionI, waterSkill, gob).",
            ["opMoveTo(companionI, inn, sea), opSwapSkill(companionI, iceBlastSkill, waterSkill), "
             "opMoveTo(companionI, sea, hut)"])
        self.assert_state_after("prepareToUseSkill(companionI, waterSkill, gob).",
            has=["hasSkill(companionI,waterSkill)"], not_has=["hasSkill(companionI,iceBlastSkill)"])

    def test_example_3_companion_with_no_skill_learns(self):
        """Example 3: a companion with no skill gets one."""
        self.set_state(WORLD + ["companion(player)", "at(player, room)", "at(gob, hut)"])
        self.assert_plan_set("prepareToUseSkill(player, iceBlastSkill, gob).",
            ["opMoveTo(player, room, mountain), opGetSkill(player, iceBlastSkill), opMoveTo(player, mountain, hut)"])

    def test_example_4_non_companion_cannot_learn(self):
        """Example 4: only companions get skills from objects."""
        self.set_state(WORLD + ["at(gob, hut)", "at(target, room)"])
        self.assert_no_plan("prepareToUseSkill(gob, waterSkill, target).")

    def test_example_5_the_object_stays(self):
        """Example 5: after one companion learns from it, the object still grants the skill."""
        self.set_state(WORLD + ["companion(player)", "at(player, room)", "at(gob, hut)"])
        self.assert_state_after("prepareToUseSkill(player, iceBlastSkill, gob).",
            has=["canGetSkillFrom(mountainShrine,iceBlastSkill)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_skill_swap_clean(self):
        """P1: After a swap, the old skill is gone and the new one is held."""
        self.set_state(WORLD + ["companion(companionI)", "at(companionI, inn)", "at(gob, hut)",
                                "hasSkill(companionI, iceBlastSkill)"])
        self.run_goal("prepareToUseSkill(companionI, waterSkill, gob)")
        state = self.get_state()
        has_new = any("hasSkill(companionI,waterSkill)" in f for f in state)
        has_old = any("hasSkill(companionI,iceBlastSkill)" in f for f in state)
        assert has_new, "P1 violated: new skill not present"
        assert not has_old, "P1 violated: old skill still present"

    def test_property_p2_non_companion_blocked(self):
        """P2: Only companions can learn new skills."""
        self.set_state(WORLD + ["at(enemy1, room)", "at(target, hut)"])
        result = self.run_goal("prepareToUseSkill(enemy1, waterSkill, target)")
        assert not result, "P2 violated: a non-companion should not be able to learn skills"


def run_tests():
    """Run all tests in this file."""
    suite = GhSkillsTest()
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
