"""Tests for gh_aggro primitive component."""

import os
import sys

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../src/Python")))

from htn_test_framework import HtnTestSuite

WORLD = ["location(room)", "location(hut)", "location(lake)", "companion(player)", "enemy(gob)"]
LURE_GOB_TO_LAKE = ("opMoveTo(player, room, hut), opAggro(gob, player), "
                    "opMoveTo(player, hut, lake), opAggroMoveTo(gob, hut, lake)")


class GhAggroTest(HtnTestSuite):
    """Test suite for gh_aggro primitive."""

    def setup(self):
        """Load the gh_aggro component (and its dependency gh_movement)."""
        self.load_component("gamehack/primitives/gh_aggro")

    # =========================================================================
    # Example Tests (from design.md)
    # =========================================================================

    def test_example_1_new_aggro(self):
        """Example 1: an enemy with no target takes the companion."""
        self.set_state(WORLD + ["at(gob, hut)", "at(player, room)"])
        self.assert_plan_set("getAggro(gob, player).", ["opAggro(gob, player)"])
        self.assert_state_after("getAggro(gob, player).", has=["hasAggro(gob,player)"])

    def test_example_2_swap_aggro(self):
        """Example 2: an enemy after someone else switches target."""
        self.set_state(WORLD + ["hasAggro(gob, companionE)"])
        self.assert_plan_set("getAggro(gob, player).",
            ["opRemoveAggro(gob, companionE), opAggro(gob, player)"])

    def test_example_3_already_aggroed(self):
        """Example 3: already after the companion."""
        self.set_state(WORLD + ["hasAggro(gob, player)"])
        self.assert_plan_set("getAggro(gob, player).", ["opTargetAlreadyAggroed(gob, player)"])

    def test_example_4_bring_enemy_to_location(self):
        """Example 4: the lurer walks to the enemy, takes its aggro, walks to the location."""
        self.set_state(WORLD + ["at(gob, hut)", "at(player, room)"])
        self.assert_plan_set("bringEnemyTo(player, gob, lake).", [LURE_GOB_TO_LAKE])
        self.assert_state_after("bringEnemyTo(player, gob, lake).", has=["at(gob,lake)"])

    def test_example_5_enemy_already_at_location(self):
        """Example 5: the enemy already stands there."""
        self.set_state(WORLD + ["at(gob, lake)", "at(player, room)"])
        self.assert_plan_set("bringEnemyTo(player, gob, lake).", ["opEnemyAlreadyAtLocation(gob, lake)"])

    def test_example_6_static_enemy_cannot_be_lured(self):
        """Example 6: a static enemy never moves."""
        self.set_state(WORLD + ["enemy(tower)", "at(tower, lake)", "static(tower)", "at(player, room)"])
        self.assert_no_plan("bringEnemyTo(player, tower, hut).")

    def test_example_7_agents_already_together(self):
        """Example 7: the two agents already share a location."""
        self.set_state(WORLD + ["at(gob, hut)", "at(teslaTower, hut)"])
        self.assert_plan_set("bringAgentsTogether(player, gob, teslaTower).",
            ["opAgentsAlreadyTogether(gob, teslaTower)"])

    def test_example_8_lure_to_a_static_agent(self):
        """Example 8: the movable enemy is lured to the static one, whichever is named first."""
        self.set_state(WORLD + ["at(gob, hut)", "at(teslaTower, lake)", "static(teslaTower)", "at(player, room)"])
        self.assert_plan_set("bringAgentsTogether(player, gob, teslaTower).", [LURE_GOB_TO_LAKE])
        self.assert_plan_set("bringAgentsTogether(player, teslaTower, gob).", [LURE_GOB_TO_LAKE])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_single_aggro(self):
        """P1: After an aggro swap, the enemy has exactly one target."""
        self.set_state(WORLD + ["hasAggro(gob, companionE)"])
        self.run_goal("getAggro(gob, player)")
        state = self.get_state()
        aggro_targets = [f for f in state if f.startswith("hasAggro(gob,")]
        assert len(aggro_targets) == 1, \
            f"P1 violated: gob has {len(aggro_targets)} aggro targets: {aggro_targets}"
        assert "hasAggro(gob,player)" in aggro_targets[0], \
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
