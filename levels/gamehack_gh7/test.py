"""Tests for gamehack_gh7 level."""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import findAllPlansResultToPrologStringList

COMPANIONS = ("player", "companionI", "companionF")


class GamehackGh7Test(HtnTestSuite):
    """Test suite for gamehack_gh7 level."""

    def setup(self):
        """Load the defeat goal (and every component it depends on), then the level."""
        self.load_component("gamehack/goals/defeat")
        self.load_level("levels/gamehack_gh7")

    def load_level(self, level_path):
        """Load a level's HTN file."""
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        level_file = os.path.join(base_path, level_path, "level.htn")
        with open(level_file, "r", encoding="utf-8") as f:
            content = f.read()
        error = self._planner.HtnCompileCustomVariables(content)
        if error:
            raise RuntimeError(f"Failed to compile level: {error}")

    def _plans(self, goal):
        """Every plan for the goal, as strings (empty if none)."""
        self._reload_file()
        error, result = self._planner.FindAllPlansCustomVariables(goal)
        assert error is None, f"Planning error: {error}"
        solutions = json.loads(result)
        if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
            return []
        return findAllPlansResultToPrologStringList(result)

    def _assert_count(self, goal, n):
        plans = self._plans(goal)
        assert len(plans) == n, f"{goal}: expected {n} plans, got {len(plans)}"
        assert len(plans) == len(set(plans)), f"{goal}: duplicate plans"
        return plans

    def test_property_p3_two_companions(self):
        """Every plan ends with gob dead, and two different companions act in it."""
        plans = self._plans("defeat(gob).")
        assert plans, "expected plans"
        for p in plans:
            assert p.endswith("opApplyTag(dead, gob)"), p
            actors = {c for c in COMPANIONS
                      if f"opMoveTo({c}," in p or f"opUseSkill({c}," in p or f"opAggro(gob, {c})" in p
                      or f"opStayInLocation({c})" in p}
            assert len(actors) >= 2, f"one companion only: {p}"

    # =========================================================================
    # Example Tests
    # =========================================================================

    def test_example_1_defeat_plans(self):
        """Example 1: defeat(gob) has 18 plans: 6 per strategy."""
        self._assert_count("defeat(gob).", 18)

    def test_example_2_wet_and_freeze_through_the_sea_shrine(self):
        """Example 2: nobody holds a chilled skill; the caster gets frostSkill at the sea shrine
        while another companion lures gob into the lake: 3 lurers x 2 casters."""
        self._assert_count("wetAndFreeze(gob).", 6)
        self.assert_plan("wetAndFreeze(gob).", contains=[
            "opMoveTo(companionI, inn, hut), opAggro(gob, companionI), opMoveTo(companionI, hut, lake), "
            "opAggroMoveTo(gob, hut, lake), opMoveTo(player, room, sea), opGetSkill(player, frostSkill), "
            "opMoveTo(player, sea, lake), opUseSkill(player, frostSkill, gob), opApplyTag(stunned, gob), opApplyTag(dead, gob)"])

    def test_example_3_oil_and_burn(self):
        """Example 3: gob lured into the kitchen, set burning by companionF (or a fireball learned at the volcano)."""
        self._assert_count("oilAndBurn(gob).", 6)
        self.assert_plan("oilAndBurn(gob).", contains=[
            "opMoveTo(player, room, hut), opAggro(gob, player), opMoveTo(player, hut, kitchen), "
            "opAggroMoveTo(gob, hut, kitchen), opMoveTo(companionF, inn, kitchen), opUseSkill(companionF, fireballSkill, gob), "
            "opRemoveLocationTag(oil, kitchen), opAddLocationTag(burning, kitchen), "
            "opApplyTag(burning, player), opApplyTag(burning, companionF), opApplyTag(burning, gob), opApplyTag(dead, gob)"])

    def test_example_4_stun_and_slow(self):
        """Example 4: companionI stuns while companionF's slow fireball lands, among 6 plans."""
        self._assert_count("stunAndSlow(gob).", 6)
        self.assert_plan("stunAndSlow(gob).", contains=[
            "opMoveTo(companionI, inn, hut), opMoveTo(companionF, inn, hut), opSynchronize(companionI, companionF), "
            "opUseSkill(companionI, iceBlastSkill, gob), opApplyTag(stunned, gob), "
            "opUseSkill(companionF, fireballSkill, gob), opApplyTag(burning, gob)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_every_strategy(self):
        """P1: All three strategies produce plans."""
        for goal in ("wetAndFreeze(gob).", "oilAndBurn(gob).", "stunAndSlow(gob)."):
            assert self._plans(goal), f"P1 violated: no plan for {goal}"

    def test_property_p2_oil_becomes_burning(self):
        """P2: oilAndBurn leaves the kitchen burning and gob dead."""
        self.run_goal("oilAndBurn(gob)")
        state = self.get_state()
        assert any("locationCanApplyTag(kitchen,burning)" in f for f in state), "P2 violated: kitchen should burn"
        assert any("hasTag(gob,dead)" in f for f in state), "P2 violated: gob should be dead"


def run_tests():
    """Run all tests in this file."""
    suite = GamehackGh7Test()
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
