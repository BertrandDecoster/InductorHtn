"""Tests for the Crossing level."""

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
DEPS = ("abilities/goals/neutralize", "abilities/primitives/ab_catalog")

# The measured matrix, unordered; each pair wins in both seat orders. The
# bramble takes fire or the wave; the sentry a jolt or a drag across.
WINNING = {frozenset((b, s)) for b in ("fireball", "tidalWave")
           for s in ("lightningFlash", "hook", "taunt", "vortex")}

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


def _planner(extra=""):
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT)
    for dep in DEPS:
        loader.load(dep)
    assert planner.HtnCompileCustomVariables(text + extra) is None
    return planner


def plans_with(player, mage, goal="clearCrossing."):
    """Plans with the player knowing `player` and the mage `mage`, on a fresh
    planner (a failed search locks the rule set)."""
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    return _solutions(_planner(kit), goal)


def _ops(plans):
    return " ".join(json.dumps(p) for p in plans).replace(" ", "")


def _op(name, *args):
    return f'"{name}":[' + ",".join('{"%s":[]}' % a for a in args) + "]"


class CrossingTest(HtnTestSuite):

    def setup(self):
        for i, dep in enumerate(DEPS):
            self.load_component(dep, reset_first=(i == 0))
        self.verify_contracts()
        self._loader.load_level_htn(HERE)
        self._planner.SetMemoryBudget(256 * 1024 * 1024)

    # ---------------------------------------------------------------- examples

    def test_example_1_jolt_burn_and_throw(self):
        self.assert_state_after("clearCrossing.", has=[
            "tag(sentry,dead)", "tag(bramble,dead)", "tag(brute,fell)"])
        self.assert_plan("clearCrossing.", contains=[
            "opExploit(mage, sentry, electrocuted, dead)", "opCast(player, fireball, crypt)",
            "opCast(warden, turnToMist, brute)", "opForcedMove(player, brute, brink, abyss)"])

    def test_example_2_provoke_the_brute_into_the_cave_in(self):
        ops = _ops(plans_with("taunt", "tidalWave"))
        assert _op("opForcedMove", "mage", "bramble", "crypt", "abyss") in ops, ops[:400]
        assert _op("opForcedMove", "player", "sentry", "ledge", "abyss") in ops
        assert _op("opBlow", "brute", "caveIn", "brink", "brink") in ops
        assert _op("opExploit", "brute", "brute", "chasm", "fell") in ops
        self._record(True, "Example 2: taunted from the hall, the brute caves the brink in under itself")

    def test_example_3_vortex_on_the_abyss(self):
        ops = _ops(plans_with("fireball", "vortex"))
        assert _op("opCast", "mage", "vortex", "abyss") in ops, ops[:400]
        assert _op("opForcedMove", "mage", "sentry", "ledge", "abyss") in ops
        self._record(True, "Example 3: the misted sentry is sucked off the ledge into the abyss")

    def test_example_4_drag_it_across(self):
        ops = _ops(plans_with("hook", "tidalWave"))
        assert _op("opCast", "warden", "turnToMist", "sentry") in ops, ops[:400]
        assert _op("opForcedMove", "player", "sentry", "ledge", "abyss") in ops
        self._record(True, "Example 4: misted, the sentry is hooked from the brink and falls on the way")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_companion_carries_a_plan_alone(self):
        plans = _solutions(self._planner, "clearCrossing.")
        assert plans, "the encounter must be solvable"
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

    def test_property_p4_the_cave_in_takes_the_brink_for_good(self):
        """Drag the sentry across first: once the brute has brought the brink
        down, nobody can stand where a pull drops it."""
        assert plans_with("taunt", "hook", "beat(sentry), regroup, provoke(brute).")
        assert not plans_with("taunt", "hook", "provoke(brute), beat(sentry).")
        self._record(True, "P4: provoke the brute first and the sentry cannot be dragged across")

    def test_property_p5_the_vortex_takes_friends_on_the_brink(self):
        planner = _planner("knows(player, vortex).\nknows(mage, fireball).\n")
        plans = _solutions(planner, "castFrom(warden, turnToMist, sentry, brink), "
                                    "cast(player, vortex, abyss).")
        assert _op("opExploit", "player", "warden", "chasm", "fell") in _ops(plans)
        self._record(True, "P5: a vortex on the abyss sucks in the Warden standing on the brink")

    def test_property_p6_the_bramble_cannot_be_aimed_at(self):
        assert not plans_with("lightningFlash", "hook", "beat(bramble).")
        self._record(True, "P6: hidden in the shadows, the bramble takes only fire or the wave")


def run_tests():
    suite = CrossingTest()
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
