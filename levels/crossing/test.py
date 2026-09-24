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
DEPS = ("abilities/goals/neutralize", "abilities/strategies/passage",
        "abilities/primitives/ab_catalog")

# The measured matrix, unordered: each pair wins in both seat orders.
WINNING = {frozenset(p) for p in [
    # the fireball burns the crypt; the other drops the sentry and the brute (free casts)
    ("fireball", "hook"), ("fireball", "shieldBash"),
    # the vortex takes the bramble and the brute; the fireball the sentry
    ("fireball", "vortex"),
    # the wave takes the bramble; the other the sentry and the brute
    ("tidalWave", "hook"), ("tidalWave", "shieldBash"),
    # the vortex takes the bramble and the brute; the other the sentry
    ("vortex", "lightningFlash"), ("vortex", "hook"), ("vortex", "shieldBash"),
]}

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

    def test_example_1_bash_over_the_abyss_burn_the_crypt(self):
        self.assert_state_after("clearCrossing.", has=[
            "tag(sentry,fell)", "tag(bramble,dead)", "tag(brute,fell)"])
        self.assert_plan("clearCrossing.", contains=[
            "opCast(warden, turnToMist, sentry)", "opCast(mage, shieldBash, sentry)",
            "opFall(mage, sentry, ledge, brink)", "opCast(player, fireball, crypt)",
            "opExploit(player, bramble, burning, dead)", "opCast(warden, turnToMist, brute)",
            "opCast(mage, shieldBash, brute)"])

    def test_example_2_jolt_the_sentry_vortex_the_rest(self):
        ops = _ops(plans_with("vortex", "lightningFlash"))
        assert _op("opExploit", "mage", "sentry", "electrocuted", "dead") in ops, ops[:400]
        assert _op("opDash", "mage", "brink", "ledge") in ops
        assert _op("opKnock", "player", "bramble", "rift") in ops
        assert _op("opKnock", "player", "brute", "sinkhole") in ops
        self._record(True, "Example 2: the flash short-circuits the soaked sentry; the vortex draws "
                           "the bramble into the rift and the misted brute into the sinkhole")

    def test_example_3_swing_over_and_haul_the_brute(self):
        ops = _ops(plans_with("tidalWave", "hook"))
        assert _op("opFall", "mage", "sentry", "ledge", "brink") in ops, ops[:400]
        assert _op("opCast", "player", "tidalWave", "player") in ops
        assert _op("opKnock", "player", "bramble", "rift") in ops
        assert _op("opDash", "mage", "brink", "ledge") in ops
        assert _op("opFall", "mage", "brute", "brink", "ledge") in ops
        self._record(True, "Example 3: the hook drops the sentry, swings over on the pillar and "
                           "hauls the misted brute into the abyss; the wave takes the bramble")

    def test_example_4_fire_on_the_crypt(self):
        ops = _ops(plans_with("fireball", "hook"))
        assert _op("opCast", "player", "fireball", "crypt") in ops, ops[:400]
        assert _op("opExploit", "player", "bramble", "burning", "dead") in ops
        self._record(True, "Example 4: the fireball on the crypt burns the hidden bramble")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_companion_carries_a_plan_alone(self):
        plans = _solutions(self._planner, "clearCrossing.")
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
        assert not report.dead_skills, report.dead_skills
        self._record(True, f"P3: exactly the {len(WINNING)} measured pairs win, both ways round")

    def test_property_p4_the_bramble_cannot_be_aimed_at(self):
        assert not plans_with("lightningFlash", "hook")
        assert not plans_with("shieldBash", "hook")
        self._record(True, "P4: without fire, a wave or a vortex, the bramble stands")

    def test_property_p5_set_alight_the_brute_caves_in_the_brink(self):
        """Fire on the brute makes it stamp: the brink becomes a chasm under it
        - and nobody reaches the sentry from there any more."""
        planner = _planner("knows(player, fireball).\nknows(mage, hook).\n")
        plans = _solutions(planner, "castFrom(player, fireball, brute, hall).")
        ops = _ops(plans)
        assert _op("opWindUp", "brute", "caveIn", "brink") in ops, ops[:400]
        assert _op("opSpill", "brute", "brink", "chasm") in ops
        assert _op("opExploit", "brute", "brute", "chasm", "fell") in ops
        planner = _planner("knows(player, fireball).\nknows(mage, hook).\n")
        assert not _solutions(planner, "castFrom(player, fireball, brute, hall), beat(sentry).")
        self._record(True, "P5: the fire brings the brink down on the brute, and cuts off the ledge")

    def test_property_p6_one_costly_cast_each(self):
        """Three enemies, two costly casts: the fireball and the flash cannot
        also take the brute."""
        assert not plans_with("fireball", "lightningFlash")
        assert not plans_with("fireball", "fireball")
        self._record(True, "P6: fireball + lightningFlash and fireball + fireball lose on mana")


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
