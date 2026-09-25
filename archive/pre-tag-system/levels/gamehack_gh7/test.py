"""Tests for gamehack_gh7 level."""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import findAllPlansResultToPrologStringList


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

    # =========================================================================
    # Example Tests
    # =========================================================================

    def test_example_1_defeat_plans(self):
        """Example 1: defeat(gob) has 27 plans: 6 stunAndSlow, 12 wetAndElectrify, 9 stunAndBurn."""
        plans = self._assert_count("defeat(gob).", 27)
        assert all(p.endswith("opApplyTag(dead, gob)") for p in plans)

    def test_example_2_stun_and_slow_works(self):
        """Example 2: stunAndSlow: companionI stuns while companionF's slow fireball lands, among 6 plans
        (the player or a swapping companion can get either skill from its shrine)."""
        self._assert_count("stunAndSlow(gob).", 6)
        self.assert_plan("stunAndSlow(gob).", contains=[
            "opMoveTo(companionI, inn, hut), opMoveTo(companionF, inn, hut), opSynchronize(companionI, companionF)"])

    def test_example_3_wet_and_electrify_via_the_sea_shrine(self):
        """Example 3: wetAndElectrify works by getting waterSkill from the sea shrine; the tower electrifies."""
        self._assert_count("wetAndElectrify(gob).", 12)
        self.assert_plan("wetAndElectrify(gob).", contains=[
            "opMoveTo(player, room, sea), opGetSkill(player, waterSkill)",
            "opUseSkill(teslaTower, lightningSkill, gob), opApplyTag(electrified, gob)"])

    def test_example_4_stun_and_burn_works(self):
        """Example 4: stunAndBurn works: iceBlastSkill stuns, fireballSkill burns."""
        self._assert_count("stunAndBurn(gob).", 9)
        self.assert_plan("stunAndBurn(gob).", contains=[
            "opMoveTo(companionI, inn, hut), opUseSkill(companionI, iceBlastSkill, gob), opApplyTag(stunned, gob), "
            "opMoveTo(companionF, inn, hut), opUseSkill(companionF, fireballSkill, gob), opApplyTag(burning, gob)"])

    # =========================================================================
    # Property Tests
    # =========================================================================

    def test_property_p1_every_strategy(self):
        """P1: All three strategies produce plans."""
        for goal in ("stunAndSlow(gob).", "wetAndElectrify(gob).", "stunAndBurn(gob)."):
            assert self._plans(goal), f"P1 violated: no plan for {goal}"

    def test_property_p2_correct_tags_stun_slow(self):
        """P2: stunAndSlow applies stunned and burning."""
        self.run_goal("stunAndSlow(gob)")
        state = self.get_state()
        assert any("hasTag(gob,stunned)" in f for f in state), "P2 violated: gob should be stunned"
        assert any("hasTag(gob,burning)" in f for f in state), "P2 violated: gob should be burning"

    def test_property_p2_correct_tags_wet_electrify(self):
        """P2: wetAndElectrify applies wet and electrified."""
        self.run_goal("wetAndElectrify(gob)")
        state = self.get_state()
        assert any("hasTag(gob,wet)" in f for f in state), "P2 violated: gob should be wet"
        assert any("hasTag(gob,electrified)" in f for f in state), "P2 violated: gob should be electrified"


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
