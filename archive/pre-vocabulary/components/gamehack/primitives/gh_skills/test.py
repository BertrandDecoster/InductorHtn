"""Tests for gh_skills primitive component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


class GhSkillsTest(HtnTestSuite):
    """Test suite for gh_skills primitive."""

    def setup(self):
        """Load the gh_skills component (and its dependency gh_movement)."""
        self.load_component("gamehack/primitives/gh_skills")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_ally_already_has_skill(self):
        """Example 1: Ally already has skill - just moves to target

        Given: at(companionI, inn), at(gob, hut), hasSkill(companionI, iceBlastSkill)
        When: prepareToUseSkill(companionI, iceBlastSkill, gob)
        Then: Moves to target, no skill change
        """
        self.set_state([
            "at(companionI, inn)",
            "at(gob, hut)",
            "hasSkill(companionI, iceBlastSkill)"
        ])

        self.assert_plan("prepareToUseSkill(companionI, iceBlastSkill, gob).",
            contains=["opMoveTo(companionI, inn, hut)"],
            not_contains=["opSwapSkill", "opGetSkill"])

    def test_example_2_ally_needs_to_learn_skill(self):
        """Example 2: Ally needs to learn skill - travels, swaps, then goes to target

        Given: at(companionI, inn), at(gob, hut), hasSkill(companionI, iceBlastSkill),
               ally(companionI), canGetSkillAtLocation(sea, waterSkill)
        When: prepareToUseSkill(companionI, waterSkill, gob)
        Then: Goes to sea, swaps skill, goes to gob
        """
        self.set_state([
            "at(companionI, inn)",
            "at(gob, hut)",
            "hasSkill(companionI, iceBlastSkill)",
            "ally(companionI)",
            "canGetSkillAtLocation(sea, waterSkill)"
        ])

        self.assert_plan("prepareToUseSkill(companionI, waterSkill, gob).",
            contains=["opSwapSkill(companionI, iceBlastSkill, waterSkill)"])

        self.assert_state_after("prepareToUseSkill(companionI, waterSkill, gob).",
            has=["hasSkill(companionI,waterSkill)"],
            not_has=["hasSkill(companionI,iceBlastSkill)"])

    def test_example_3_ally_no_skill_learns(self):
        """Example 3: Ally with no skill learns one

        Given: at(player, room), at(gob, hut), ally(player),
               canGetSkillAtLocation(mountain, iceBlastSkill)
        When: prepareToUseSkill(player, iceBlastSkill, gob)
        Then: Goes to mountain, gets skill, goes to gob
        """
        self.set_state([
            "at(player, room)",
            "at(gob, hut)",
            "ally(player)",
            "canGetSkillAtLocation(mountain, iceBlastSkill)"
        ])

        self.assert_plan("prepareToUseSkill(player, iceBlastSkill, gob).",
            contains=["opGetSkill(player, iceBlastSkill)"])

        self.assert_state_after("prepareToUseSkill(player, iceBlastSkill, gob).",
            has=["hasSkill(player,iceBlastSkill)"])

    def test_example_4_non_ally_cannot_learn(self):
        """Example 4: Non-ally cannot learn skill

        Given: at(gob, hut), at(target, room), canGetSkillAtLocation(sea, waterSkill)
               No ally(gob) fact
        When: prepareToUseSkill(gob, waterSkill, target)
        Then: Planning fails
        """
        self.set_state([
            "at(gob, hut)",
            "at(target, room)",
            "canGetSkillAtLocation(sea, waterSkill)"
        ])

        self.assert_no_plan("prepareToUseSkill(gob, waterSkill, target).")

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_skill_swap_clean(self):
        """P1: After swap, old skill gone and new skill present."""
        self.set_state([
            "at(companionI, inn)",
            "at(gob, hut)",
            "hasSkill(companionI, iceBlastSkill)",
            "ally(companionI)",
            "canGetSkillAtLocation(sea, waterSkill)"
        ])

        self.run_goal("prepareToUseSkill(companionI, waterSkill, gob)")
        state = self.get_state()

        has_new = any("hasSkill(companionI,waterSkill)" in f for f in state)
        has_old = any("hasSkill(companionI,iceBlastSkill)" in f for f in state)

        assert has_new, "P1 violated: new skill not present"
        assert not has_old, "P1 violated: old skill still present"

    def test_property_p2_non_ally_blocked(self):
        """P2: Only allies can learn new skills."""
        self.set_state([
            "at(enemy1, room)",
            "at(target, hut)",
            "canGetSkillAtLocation(sea, waterSkill)"
            # No ally(enemy1) fact
        ])

        # Non-ally without the skill should fail
        result = self.run_goal("prepareToUseSkill(enemy1, waterSkill, target)")
        assert not result, "P2 violated: non-ally should not be able to learn skills"


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
