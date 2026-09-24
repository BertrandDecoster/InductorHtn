"""Tests for the Ring-Out level."""

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
COMPANIONS = {"player", "mage"}
DEPS = ("abilities/goals/neutralize", "abilities/strategies/passage",
        "abilities/primitives/ab_catalog")

# The measured matrix, unordered; each pair wins in both seat orders.
WINNING = {frozenset(p) for p in [
    # onto the brink: hook it there or suck it in, then push it over; or taunt
    # it there and fireball it over before its slam lands
    ("fireball", "hook"), ("fireball", "vortex"), ("fireball", "taunt"),
    ("tidalWave", "hook"), ("tidalWave", "vortex"),
    # from behind: land on the perch, walk round, push
    ("fireball", "blink"), ("fireball", "lightningFlash"),
    ("tidalWave", "blink"), ("tidalWave", "lightningFlash"),
    # across: a vortex lifts the puller onto the perch
    ("vortex", "hook"), ("vortex", "taunt"),
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


def plans_with(player, mage, goal="win."):
    """Plans with the player knowing `player` and the mage `mage`, on a fresh
    planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT)
    for dep in DEPS:
        loader.load(dep)
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, goal)


def _ops(plans):
    return " ".join(json.dumps(p) for p in plans).replace(" ", "")


def _op(name, *args):
    return f'"{name}":[' + ",".join('{"%s":[]}' % a for a in args) + "]"


class RingOutTest(HtnTestSuite):

    def setup(self):
        for i, dep in enumerate(DEPS):
            self.load_component(dep, reset_first=(i == 0))
        self.verify_contracts()
        self._loader.load_level_htn(HERE)
        self._planner.SetMemoryBudget(256 * 1024 * 1024)

    # ---------------------------------------------------------------- examples

    def test_example_1_hook_it_onto_the_brink_then_push(self):
        self.assert_plan("win.", contains=[
            "opForcedMove(mage, ogre, plinth, brink)", "opForcedMove(player, ogre, brink, void)",
            "opExploit(player, ogre, chasm, fell)"])

    def test_example_2_land_on_the_perch_push_from_behind(self):
        ops = _ops(plans_with("tidalWave", "blink"))
        assert _op("opTeleport", "mage", "gate", "perch") in ops, ops[:300]
        assert _op("opOpen", "mage", "grate") in ops
        assert _op("opForcedMove", "player", "ogre", "plinth", "void") in ops
        self._record(True, "Example 2: the mage blinks onto the perch; the player's wave from the "
                           "ledge rings it out")

    def test_example_3_taunt_it_and_knock_it_over_before_the_slam(self):
        ops = _ops(plans_with("fireball", "taunt"))
        assert _op("opWindUp", "ogre", "groundSlam", "brink") in ops, ops[:300]
        assert _op("opForcedMove", "player", "ogre", "brink", "void") in ops
        assert _op("opMiss", "ogre", "groundSlam", "brink") in ops
        self._record(True, "Example 3: taunted onto the brink it winds up; the fireball in the "
                           "window rings it out and the slam never lands")

    def test_example_4_a_vortex_lifts_the_puller(self):
        ops = _ops(plans_with("vortex", "hook"))
        assert _op("opForcedMove", "player", "mage", "yard", "perch") in ops, ops[:300]
        assert _op("opForcedMove", "mage", "ogre", "plinth", "void") in ops
        self._record(True, "Example 4: the player's vortex sucks the mage onto the perch; her hook "
                           "drags it across the void")

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
        assert not report.dead_skills, report.dead_skills
        self._record(True, f"P3: exactly the {len(WINNING)} measured pairs win, both ways round")

    def test_property_p4_two_pushers_only_shove_it_about(self):
        assert not plans_with("fireball", "tidalWave")
        self._record(True, "P4: fireball + tidal wave never find a line into the void")

    def test_property_p5_the_slam_must_be_answered(self):
        """Taunted onto the brink, the ogre slams the taunter into the void
        unless the partner knocks it over in the window: a blinker cannot."""
        assert plans_with("taunt", "fireball", "lure(ogre), standing.")
        assert not plans_with("taunt", "blink", "lure(ogre), standing.")
        self._record(True, "P5: a taunt lure needs a fireball ready; with a blinker it kills the taunter")


def run_tests():
    suite = RingOutTest()
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
