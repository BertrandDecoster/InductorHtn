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
DEPS = ("abilities/goals/neutralize", "abilities/strategies/passage",
        "abilities/primitives/ab_catalog")

# The measured matrix, unordered: each pair wins in both seat orders.
WINNING = {frozenset(p) for p in [
    # a pusher (fireball, tidal wave) with a leaper, a hook, or the blizzard
    ("fireball", "blink"), ("fireball", "lightningFlash"), ("fireball", "hook"),
    ("fireball", "blizzard"),
    ("tidalWave", "blink"), ("tidalWave", "lightningFlash"), ("tidalWave", "hook"),
    ("tidalWave", "blizzard"),
    # a hook with a leaper: drag the guard, haul the crate, grapple across
    ("hook", "blink"), ("hook", "lightningFlash"),
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


def _actor(op):
    return list(op[list(op.keys())[0]][0].keys())[0]


def _planner(extra="", strip_kit=True, replace=()):
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    for old, new in replace:
        assert old in text, old
        text = text.replace(old, new)
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


class GauntletTest(HtnTestSuite):

    def setup(self):
        for i, dep in enumerate(DEPS):
            self.load_component(dep, reset_first=(i == 0))
        self.verify_contracts()
        self._loader.load_level_htn(HERE)
        self._planner.SetMemoryBudget(256 * 1024 * 1024)

    # ---------------------------------------------------------------- examples

    def test_example_1_mist_and_drop_crate_on_the_plate_ice_on_the_lava(self):
        self.assert_state_after("win.", has=[
            "at(player,exit)", "at(mage,exit)", "at(warden,exit)", "open(exit)"],
            not_has=["onEnter(channel,lava)"])
        self.assert_plan("win.", contains=[
            "opCast(warden, turnToMist, guard)", "opForcedMove(player, guard, choke, pit)",
            "opForcedMove(player, crate, hall, alcove)", "opErase(mage, channel, lava)"])

    def test_example_2_blink_onto_the_plate_push_the_crate_in(self):
        ops = _ops(plans_with("fireball", "blink"))
        assert _op("opTeleport", "mage", "hall", "alcove") in ops, ops[:400]
        assert _op("opTeleport", "mage", "alcove", "far") in ops
        assert _op("opForcedMove", "player", "crate", "rim", "channel") in ops
        assert _op("opExploit", "player", "crate", "lava", "fell") in ops
        self._record(True, "Example 2: the mage blinks onto the plate and on; two fireballs fill the lava")

    def test_example_3_the_latch_holds_hook_the_crate_back(self):
        ops = _ops(plans_with("tidalWave", "hook"))
        assert _op("opForcedMove", "player", "crate", "hall", "alcove") in ops, ops[:400]
        assert _op("opForcedMove", "mage", "crate", "alcove", "rim") in ops
        assert _op("opDash", "mage", "rim", "far") in ops
        assert _op("opForcedMove", "mage", "crate", "rim", "channel") in ops
        self._record(True, "Example 3: the wave throws the crate on the plate; the hook takes it back, "
                           "grapples the pillar and drags the crate into the lava")

    def test_example_4_haul_the_crate_and_grapple_across(self):
        ops = _ops(plans_with("hook", "lightningFlash"))
        assert _op("opForcedMove", "player", "guard", "choke", "start") in ops, ops[:400]
        assert _op("opDash", "mage", "hall", "alcove") in ops
        assert _op("opForcedMove", "player", "crate", "hall", "rim") in ops
        assert _op("opForcedMove", "player", "crate", "rim", "channel") in ops
        self._record(True, "Example 4: the hook drags the guard out and hauls the crate; the flash "
                           "lands on the plate")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_companion_carries_a_plan_alone(self):
        plans = _solutions(self._planner, "win.")
        assert plans, "the level must be winnable"
        for plan in plans:
            allies = {_actor(op) for op in plan} & COMPANIONS
            assert len(allies) >= 2, f"one companion carries this plan alone: {plan}"
        self._record(True, f"P1: {len(plans)} plans, none by one companion")

    def test_property_p2_without_a_hook_the_crate_cannot_do_both(self):
        """With the crate on the plate and no hook to take it back, only ice
        gets the Warden across."""
        planner = _planner("knows(player, fireball).\nknows(mage, blink).\n"
                           "tag(guard, fell).\nopen(exit).\n",
                           replace=[("at(crate, hall).", "at(crate, alcove).")])
        assert not _solutions(planner, "bridge, leave(warden).")
        self._record(True, "P2: the crate on the plate strands the Warden")

    def test_property_p3_no_single_skill_wins(self):
        report = combos_report()
        assert not report.singles_winning, f"a single skill wins: {report.singles_winning}"
        self._record(True, "P3: no pool skill wins alone, even held by both")

    def test_property_p4_the_measured_pairs_win(self):
        report = combos_report()
        found = {frozenset((w["player"][0], w["mage"][0])) for w in report.winning}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        assert len(report.winning) == 2 * len(WINNING), "each pair should win in both seat orders"
        assert not report.failures, report.failures
        assert not report.dead_skills, report.dead_skills
        self._record(True, f"P4: exactly the {len(WINNING)} measured pairs win, both ways round")

    def test_property_p5_the_mist_lasts_one_cast(self):
        """Misted, the guard can be thrown by the very next cast; one cast
        later it is heavy again and the fireball only scorches it."""
        planner = _planner("knows(player, fireball).\nknows(mage, blink).\n")
        assert _solutions(planner, "cast(warden, turnToMist, guard), "
                                   "castFrom(player, fireball, guard, start), confirmStopped(guard).")
        planner = _planner("knows(player, fireball).\nknows(mage, blink).\n")
        late = _solutions(planner, "cast(warden, turnToMist, guard), cast(mage, blink, hall), "
                                   "castFrom(player, fireball, guard, start).")
        assert late and _op("opForcedMove", "player", "guard", "choke", "pit") not in _ops(late)
        self._record(True, "P5: the mist lasts through the next cast only")

    def test_property_p6_two_pushers_strand_each_other(self):
        assert not plans_with("fireball", "tidalWave")
        self._record(True, "P6: fireball + tidal wave loses - whoever is thrown on the plate stays")


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
