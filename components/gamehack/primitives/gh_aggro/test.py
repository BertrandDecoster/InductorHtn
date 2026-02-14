"""Tests for gh_aggro primitive component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite


class GhAggroTest(HtnTestSuite):
    """Test suite for gh_aggro primitive."""

    def setup(self):
        """Load the gh_aggro component (and its dependency gh_movement)."""
        self.load_component("gamehack/primitives/gh_aggro")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_new_aggro(self):
        """Example 1: New aggro (no prior)

        Given: at(gob, hut), at(player, room), ally(player)
        When: aggroTarget(gob, player)
        Then: opAggro(gob, player), aggro(gob, player) in state
        """
        self.set_state([
            "at(gob, hut)",
            "at(player, room)",
            "ally(player)"
        ])

        self.assert_plan("aggroTarget(gob, player).",
            contains=["opAggro(gob, player)"])

        self.assert_state_after("aggroTarget(gob, player).",
            has=["aggro(gob,player)"])

    def test_example_2_swap_aggro(self):
        """Example 2: Swap aggro

        Given: aggro(gob, companionE), ally(player)
        When: aggroTarget(gob, player)
        Then: opRemoveAggro then opAggro
        """
        self.set_state([
            "aggro(gob, companionE)",
            "ally(player)"
        ])

        self.assert_plan("aggroTarget(gob, player).",
            contains=["opRemoveAggro(gob, companionE)", "opAggro(gob, player)"])

    def test_example_3_already_aggroed(self):
        """Example 3: Already aggroed

        Given: aggro(gob, player)
        When: aggroTarget(gob, player)
        Then: opTargetAlreadyAggroed
        """
        self.set_state([
            "aggro(gob, player)"
        ])

        self.assert_plan("aggroTarget(gob, player).",
            contains=["opTargetAlreadyAggroed"])

    def test_example_4_bring_mob_to_location(self):
        """Example 4: Bring mob to location via aggro chain

        Given: at(gob, hut), at(player, room), ally(player)
        When: bringMobToLocation(gob, lake)
        Then: Plan has aggro chain, gob ends at lake
        """
        self.set_state([
            "at(gob, hut)",
            "at(player, room)",
            "ally(player)"
        ])

        self.assert_plan("bringMobToLocation(gob, lake).",
            contains=["opAggroMoveTo(gob, hut, lake)"])

        self.assert_state_after("bringMobToLocation(gob, lake).",
            has=["at(gob,lake)"])

    def test_example_5_bring_mob_already_at_location(self):
        """Example 5: Mob already at target location

        Given: at(gob, lake)
        When: bringMobToLocation(gob, lake)
        Then: Plan is empty
        """
        self.set_state([
            "at(gob, lake)"
        ])

        self.assert_plan("bringMobToLocation(gob, lake).",
            not_contains=["opMoveTo", "opAggroMoveTo", "opAggro"])

    def test_example_6_static_mob_cannot_be_moved(self):
        """Example 6: Static mob cannot be moved

        Given: at(tower, lake), static(tower), at(player, room), ally(player)
        When: bringMobToLocation(tower, hut)
        Then: Planning fails
        """
        self.set_state([
            "at(tower, lake)",
            "static(tower)",
            "at(player, room)",
            "ally(player)"
        ])

        self.assert_no_plan("bringMobToLocation(tower, hut).")

    def test_example_7_bring_mobs_together_already(self):
        """Example 7: Mobs already together

        Given: at(gob, hut), at(teslaTower, hut)
        When: bringMobsTogether(gob, teslaTower)
        Then: Plan is empty
        """
        self.set_state([
            "at(gob, hut)",
            "at(teslaTower, hut)"
        ])

        self.assert_plan("bringMobsTogether(gob, teslaTower).",
            not_contains=["opMoveTo", "opAggroMoveTo"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_single_aggro(self):
        """P1: After aggro swap, mob has exactly one aggro target."""
        self.set_state([
            "aggro(gob, companionE)",
            "ally(player)"
        ])

        self.run_goal("aggroTarget(gob, player)")
        state = self.get_state()

        aggro_targets = [f for f in state if f.startswith("aggro(gob,")]
        assert len(aggro_targets) == 1, \
            f"P1 violated: gob has {len(aggro_targets)} aggro targets: {aggro_targets}"
        assert "aggro(gob,player)" in aggro_targets[0], \
            f"P1 violated: expected aggro on player, got {aggro_targets}"


def run_tests():
    """Run all tests in this file."""
    suite = GhAggroTest()
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
