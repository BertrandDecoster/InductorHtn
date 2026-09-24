"""Tests for the Sinkhole level."""

import itertools
import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import HtnPlanner
from htn_components.loader import ComponentLoader

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
KIT = ["fireball", "shock", "gust", "chill", "quake", "douse"]
COMPANIONS = {"player", "mage", "warden"}


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def _actor(op):
    return list(op[list(op.keys())[0]][0].keys())[0]


def winning_kits():
    """Every pick-2 kit that clears the level, each on a fresh planner (a
    failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\(player, \w+\)\.\n", "", text, flags=re.M)
    wins = []
    for pick in itertools.combinations(KIT, 2):
        planner = HtnPlanner(False)
        ComponentLoader(planner, ROOT).load("abilities/goals/neutralize")
        kit = "".join(f"knows(player, {c}).\n" for c in pick)
        assert planner.HtnCompileCustomVariables(text + kit) is None
        if _solutions(planner, "clearSinkhole."):
            wins.append(pick)
    return wins


class SinkholeTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_the_default_kit_clears_the_sinkhole(self):
        self.assert_state_after("clearSinkhole.",
                                has=["tag(golem,fell)", "tag(wader,frozen)", "tag(tender,dead)"])

    def test_example_2_the_golem_is_frozen_then_pushed(self):
        self.assert_plan("neutralize(golem).", contains=[
            "opCast(mage, douse, golem)",
            "opReact(player, golem, wet, chilled, freezeOver)",
            "opForcedMove(warden, golem, rim, pit)"])

    def test_example_3_steam_dries_the_wader(self):
        self.assert_state_after("applyAbility(player, fireball, wader, react).",
                                not_has=["tag(wader,wet)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_no_companion_carries_a_plan_alone(self):
        plans = _solutions(self._planner, "clearSinkhole.")
        assert plans, "the encounter must be solvable"
        for plan in plans:
            allies = {_actor(op) for op in plan} & COMPANIONS
            assert len(allies) >= 2, f"one companion carries this plan alone: {plan}"
            assert "player" in allies, f"the controlled companion is idle: {plan}"
        self._record(True, "P1: no companion carries a plan alone")

    def test_property_p2_at_least_three_kits_none_mandatory(self):
        wins = winning_kits()
        assert len(wins) >= 3, f"only {len(wins)} winning kits: {wins}"
        for choice in KIT:
            assert any(choice not in w for w in wins), f"{choice} is mandatory: {wins}"
        self._record(True, f"P2: {len(wins)} winning kits, none mandatory: {wins}")

    def test_property_p3_the_golem_cannot_be_shoved_as_it_stands(self):
        self.assert_no_plan("placeAs(warden, golem, pit).")


def run_tests():
    suite = SinkholeTest()
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
    sys.exit(0 if run_tests() else 1)
