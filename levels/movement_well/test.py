"""Tests for the Well level."""

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
COMPANIONS = {"player", "mage", "golem"}
DEPS = ("abilities/goals/neutralize", "abilities/strategies/passage",
        "abilities/primitives/ab_catalog")

# The measured matrix, unordered; each pair wins in both seat orders.
WINNING = {frozenset(p) for p in [
    # a drawer brings the crate to the brink, a pusher throws it in
    ("gust", "magnetize"), ("gust", "taunt"), ("gust", "translocate"),
    ("shieldBash", "magnetize"), ("shieldBash", "taunt"), ("shieldBash", "translocate"),
    # someone goes down, a puller hauls them out
    ("translocate", "magnetize"), ("translocate", "taunt"),
    ("pounce", "magnetize"), ("pounce", "taunt"),
]}

_REPORT = []


def combos_report():
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


def _planner(extra="", strip_kit=True):
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    if strip_kit:
        text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    loader = ComponentLoader(planner, ROOT)
    for dep in DEPS:
        loader.load(dep)
    assert planner.HtnCompileCustomVariables(text + extra) is None
    return planner


def plans_with(player, mage, goal="win."):
    """Plans with the player knowing `player` and the mage `mage`, on a fresh
    planner (a failed search locks the rule set)."""
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    return _solutions(_planner(kit), goal)


def _ops(plans):
    return " ".join(json.dumps(p) for p in plans).replace(" ", "")


def _op(name, *args):
    return f'"{name}":[' + ",".join('{"%s":[]}' % a for a in args) + "]"


class WellTest(HtnTestSuite):

    def setup(self):
        for i, dep in enumerate(DEPS):
            self.load_component(dep, reset_first=(i == 0))
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_go_down_and_be_pulled_out(self):
        self.assert_state_after("win.", has=[
            "at(player,exit)", "at(mage,exit)", "at(golem,exit)", "open(lock)"])
        self.assert_plan("win.", contains=[
            "opDash(player, quay, well)", "opOpen(golem, lock)",
            "opForcedMove(mage, player, well, exit)"])

    def test_example_2_fetch_the_crate_and_throw_it(self):
        ops = _ops(plans_with("gust", "taunt"))
        assert _op("opForcedMove", "mage", "crate", "nook", "brink") in ops, ops[:300]
        assert _op("opForcedMove", "player", "crate", "brink", "well") in ops
        self._record(True, "Example 2: the mage taunts the crate onto the brink; the player gusts it in")

    def test_example_3_swap_with_the_crate(self):
        ops = _ops(plans_with("translocate", "shieldBash"))
        assert _op("opSwap", "player", "crate", "brink", "nook") in ops, ops[:300]
        assert _op("opForcedMove", "mage", "crate", "brink", "well") in ops
        self._record(True, "Example 3: the player swaps the crate onto the brink; the mage bashes it in")

    def test_example_4_swap_with_the_wisp_and_be_taunted_out(self):
        ops = _ops(plans_with("translocate", "taunt"))
        assert _op("opSwap", "player", "wisp", "quay", "well") in ops, ops[:300]
        assert _op("opForcedMove", "mage", "player", "well", "exit") in ops
        self._record(True, "Example 4: the player swaps down with the wisp; the mage's taunt drags her up")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_companion_carries_a_plan_alone(self):
        plans = _solutions(self._planner, "win.")
        assert plans, "the level must be winnable"
        for plan in plans:
            allies = {_actor(op) for op in plan} & COMPANIONS
            assert len(allies) >= 2, f"one companion carries this plan alone: {plan}"
        self._record(True, f"P1: {len(plans)} plans, none by one companion")

    def test_property_p2_no_single_skill_wins(self):
        report = combos_report()
        assert not report.singles_winning, f"a single skill wins: {report.singles_winning}"
        self._record(True, "P2: no pool skill wins alone, even held by both")

    def test_property_p3_the_measured_pairs_win(self):
        report = combos_report()
        found = {frozenset((w["player"][0], w["mage"][0])) for w in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert len(report.winning) == 2 * len(WINNING), "each pair should win in both seat orders"
        assert not report.failures, report.failures
        self._record(True, f"P3: exactly the {len(WINNING)} measured pairs win, both ways round")

    def test_property_p4_the_wisp_does_not_weigh_the_plate(self):
        planner = _planner("knows(player, pounce).\nknows(mage, magnetize).\n")
        assert _solutions(planner, "walkTo(golem, step).")
        planner = _planner("knows(player, pounce).\nknows(mage, magnetize).\n")
        assert not _solutions(planner, "walkTo(golem, step), confirmOpen(lock).")
        self._record(True, "P4: the Golem on the step alone does not open the lock")

    def test_property_p5_the_stealthed_cannot_be_hauled_out(self):
        assert not plans_with("shadowStep", "magnetize")
        self._record(True, "P5: shadow-stepped down, the player cannot be aimed at, so not hauled out")

    def test_property_p6_a_thrown_friend_is_stranded(self):
        """The throw works and the lock opens, but the only puller is down the
        well."""
        kit = "knows(player, gust).\nknows(mage, magnetize).\n"
        throw = "walkTo(mage, brink), castFrom(player, gust, mage, quay), walkTo(golem, step)"
        assert _solutions(_planner(kit), throw + ", confirmOpen(lock).")
        assert not _solutions(_planner(kit), throw + ", getOut(mage).")
        self._record(True, "P6: gust throws the mage down and the lock opens; nobody hauls her out")


def run_tests():
    suite = WellTest()
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
