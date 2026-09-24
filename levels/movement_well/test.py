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

# The measured matrix, unordered: a way down with the hook for the way out.
WINNING = {frozenset(("hook", s)) for s in
           ("lightningFlash", "fireball", "shieldBash", "tidalWave")}

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


def _casters(plan):
    """The companions who cast in a plan (walking is not a second pair of hands)."""
    out = set()
    for op in plan:
        name = list(op.keys())[0]
        if name == "opCast":
            out.add(list(op[name][0].keys())[0])
    return out & COMPANIONS


def _planner(extra="", strip_kit=True):
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    if strip_kit:
        text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
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
        self._planner.SetMemoryBudget(256 * 1024 * 1024)

    # ---------------------------------------------------------------- examples

    def test_example_1_flash_down_and_be_hauled_out(self):
        self.assert_state_after("win.", has=[
            "at(player,exit)", "at(mage,exit)", "at(golem,exit)", "open(lock)",
            "tag(player,rooted)"])
        self.assert_plan("win.", contains=[
            "opStepOn(golem, golem, step)", "opDash(player, brink, well)",
            "opStepOn(player, player, floor)", "opOpen(player, lock)",
            "opForcedMove(mage, player, well, exit)"])

    def test_example_2_fill_the_shaft_and_climb_out_on_the_golem(self):
        ops = _ops(plans_with("fireball", "hook"))
        assert _op("opBridge", "player", "brink", "well") in ops, ops[:400]
        assert _op("opNavigate", "mage", "brink", "well") in ops
        assert _op("opCast", "mage", "hook", "golem") in ops
        assert _op("opDash", "mage", "well", "exit") in ops
        # ... or the player goes down and the mage hauls him out.
        assert _op("opForcedMove", "mage", "player", "well", "exit") in ops
        self._record(True, "Example 2: the fireball fills the shaft; whoever walks down is hauled "
                           "out, or hooks the golem at the exit and swings up")

    def test_example_3_bash_the_crate_in(self):
        ops = _ops(plans_with("shieldBash", "hook"))
        assert _op("opCast", "player", "shieldBash", "crate") in ops, ops[:400]
        assert _op("opBridge", "player", "brink", "well") in ops
        self._record(True, "Example 3: the bash knocks the crate into the shaft")

    def test_example_4_a_wave_on_the_brink(self):
        ops = _ops(plans_with("tidalWave", "hook"))
        assert _op("opCast", "player", "tidalWave", "player") in ops, ops[:400]
        assert _op("opFall", "player", "crate", "brink", "well") in ops
        self._record(True, "Example 4: the wave washes the crate into the shaft")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_companion_carries_a_plan_alone(self):
        plans = _solutions(self._planner, "win.")
        assert plans, "the level must be winnable"
        for plan in plans:
            assert len(_casters(plan)) >= 2, f"one companion carries this plan alone: {plan}"
        self._record(True, f"P1: {len(plans)} plans, each with two or more casters")

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
        assert report.dead_skills == ["vortex"], report.dead_skills
        self._record(True, f"P3: exactly the {len(WINNING)} measured pairs win; vortex is the trap")

    def test_property_p4_whoever_goes_down_is_stuck(self):
        """The mud roots whoever lands: one flash down, and nobody can bring
        the flasher up without a hook - not even over a filled shaft."""
        assert not plans_with("lightningFlash", "fireball")
        assert not plans_with("fireball", "shieldBash")
        self._record(True, "P4: without a hook, the one in the well stays there")

    def test_property_p5_the_puddle_takes_the_shield(self):
        """The bash's shield would take the mud; the water in the well takes the
        shield first, and the mud roots the basher."""
        planner = _planner("knows(player, shieldBash).\nknows(mage, hook).\n")
        plans = _solutions(planner, "cast(player, shieldBash, crate), walkTo(player, well).")
        ops = _ops(plans)
        assert _op("opRemove", "player", "player", "shielded") in ops, ops[:400]
        assert _op("opGrant", "player", "player", "rooted") in ops
        self._record(True, "P5: the puddle breaks the shield; the mud roots the basher")

    def test_property_p6_the_well_is_empty(self):
        """A vortex on the floor has nothing to draw onto it."""
        assert not plans_with("vortex", "hook")
        planner = _planner("knows(player, vortex).\nknows(mage, hook).\n")
        plans = _solutions(planner, "cast(player, vortex, floor).")
        assert plans and "opKnock" not in _ops(plans)
        self._record(True, "P6: the vortex on the floor draws nothing")


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
