"""Tests for the Gauntlet level."""

import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import HtnPlanner
from htn_components.loader import ComponentLoader
from htn_components.combos import run_combos

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
COMPANIONS = {"player", "mage", "warden"}

# The measured matrix (player's pick, mage's pick): these win, nothing else does.
WINNING = {
    ("gust", "magnetize"), ("gust", "translocate"), ("gust", "shadowStep"), ("gust", "pounce"),
    ("shieldBash", "shadowStep"), ("shieldBash", "pounce"),
    ("magnetize", "gust"), ("magnetize", "shadowStep"), ("magnetize", "pounce"),
    ("translocate", "gust"),
    ("shadowStep", "gust"), ("shadowStep", "shieldBash"), ("shadowStep", "magnetize"),
    ("pounce", "gust"), ("pounce", "shieldBash"), ("pounce", "magnetize"),
}

_REPORT = []


def combos_report():
    """One parallel `combos` run, shared by the properties that read it."""
    if not _REPORT:
        _REPORT.append(run_combos(HERE, ROOT))
    return _REPORT[0]


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def _actor(op):
    return list(op[list(op.keys())[0]][0].keys())[0]


def plans_with(player, mage, goal="win."):
    """Plans with the player knowing `player` and the mage `mage`, on a fresh
    planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT)
    loader.load("abilities/strategies/passage")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, goal)


def _ops(plans):
    return " ".join(json.dumps(p) for p in plans).replace(" ", "")


class GauntletTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/strategies/passage", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_dash_onto_the_plate_push_the_crate(self):
        self.assert_state_after("win.", has=[
            "at(player,exit)", "at(mage,exit)", "at(warden,exit)", "open(gate)"])
        self.assert_plan("win.", contains=[
            "opCast(warden, sunder, guard)", "opForcedMove(player, guard, choke, pit)",
            "opDash(mage, hall, alcove)", "opExploit(player, crate, chasm, fell)"])

    def test_example_2_throw_a_friend_who_grapples_out(self):
        ops = _ops(plans_with("gust", "magnetize"))
        assert '"opForcedMove":[{"player":[]},{"mage":[]},{"hall":[]},{"alcove":[]}]' in ops, ops[:400]
        assert '"opCast":[{"mage":[]},{"magnetize":[]},{"pillar":[]}]' in ops
        self._record(True, "Example 2: gust throws the mage onto the plate; she hooks the pillar out")

    def test_example_3_throw_a_friend_who_swaps_out(self):
        ops = _ops(plans_with("gust", "translocate"))
        assert '"opSwap":[{"mage":[]},{"idol":[]},{"alcove":[]},{"far":[]}]' in ops, ops[:400]
        self._record(True, "Example 3: thrown onto the plate, the mage swaps places with the idol")

    def test_example_4_haul_the_crate_to_the_rim(self):
        ops = _ops(plans_with("magnetize", "shadowStep"))
        assert '"opForcedMove":[{"player":[]},{"crate":[]},{"hall":[]},{"rim":[]}]' in ops
        assert '"opForcedMove":[{"player":[]},{"crate":[]},{"rim":[]},{"chasm":[]}]' in ops
        self._record(True, "Example 4: the player hooks the crate to the rim, crosses, drags it in")

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
        with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
            text = f.read()
        planner = HtnPlanner(False)
        loader = ComponentLoader(planner, ROOT)
        loader.load("abilities/strategies/passage")
        loader.load("abilities/primitives/ab_catalog")
        assert planner.HtnCompileCustomVariables(
            text + "tag(guard, fell).\nopen(gate).\nat(crate, alcove).\n") is None
        assert not _solutions(planner, "reach(warden, exit).")
        self._record(True, "P2: the crate on the plate strands the Warden")

    def test_property_p3_no_single_skill_wins(self):
        report = combos_report()
        assert not report.singles_winning, f"a single skill wins: {report.singles_winning}"
        self._record(True, "P3: no pool skill wins alone, even held by both")

    def test_property_p4_the_measured_pairs_win(self):
        report = combos_report()
        found = {(w["player"][0], w["mage"][0]) for w in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert not report.failures, report.failures
        self._record(True, f"P4: exactly the {len(WINNING)} measured assignments win; combos passes")

    def test_property_p5_a_bashed_friend_is_stunned(self):
        """shieldBash throws a friend onto the plate stunned: silenced, she
        cannot grapple out."""
        assert not plans_with("shieldBash", "magnetize")
        self._record(True, "P5: shieldBash + magnetize loses - the thrown mage is stunned")


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
