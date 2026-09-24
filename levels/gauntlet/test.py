"""Tests for the Gauntlet level."""

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


def _planner(extra="", strip_kit=False):
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    if strip_kit:
        text = re.sub(r"^knows\(player, \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    loader = ComponentLoader(planner, ROOT)
    loader.load("abilities/strategies/passage")
    loader.load("abilities/primitives/ab_catalog")
    assert planner.HtnCompileCustomVariables(text + extra) is None
    return planner


def clears(pick):
    """Whether the kit wins, on a fresh planner (a failed search locks the
    rule set)."""
    kit = "".join(f"knows(player, {c}).\n" for c in pick)
    return bool(_solutions(_planner(kit, strip_kit=True), "win."))


class GauntletTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/strategies/passage", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_everyone_escapes(self):
        self.assert_state_after("escape.", has=[
            "at(player,exit)", "at(mage,exit)", "at(warden,exit)", "open(gate)"])

    def test_example_2_the_crate_bridges_the_chasm(self):
        self.assert_plan("escape.", contains=[
            "opForcedMove(warden, crate, hall, rim)", "opExploit(player, crate, chasm, fell)"])

    def test_example_3_the_rout(self):
        self.assert_plan("rout.", contains=[
            "opCast(warden, sunder, archer)", "opForcedMove(player, archer, far, cliff)"])

    # -------------------------------------------------------------- properties

    def test_property_p1_no_companion_carries_a_plan_alone(self):
        plans = _solutions(self._planner, "win.")
        assert plans, "the level must be winnable"
        for plan in plans:
            allies = {_actor(op) for op in plan} & COMPANIONS
            assert len(allies) >= 2, f"one companion carries this plan alone: {plan}"
        self._record(True, f"P1: {len(plans)} plans, none by one companion")

    def test_property_p2_the_crate_cannot_do_both(self):
        """Pushed onto the plate, the crate no longer bridges the chasm: the
        Warden, who cannot leap, is left behind."""
        planner = _planner("tag(guard, fell).\n")
        assert _solutions(planner, "placeAs(player, crate, alcove).")
        planner = _planner("tag(guard, fell).\n")
        assert not _solutions(planner, "placeAs(player, crate, alcove), reach(warden, exit).")
        self._record(True, "P2: the crate on the plate strands the Warden")

    def test_property_p3_the_companions_carry_it(self):
        """Known flaw, pinned so the rework notices: with no player skill at
        all, the Warden and the Mage still win. `combos` fails this level."""
        assert _solutions(_planner("", strip_kit=True), "win.")
        self._record(True, "P3 (known flaw): the level is won without any player skill")

def run_tests():
    suite = GauntletTest()
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
