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
    # something for the guard and the crate (vortex) with something for the barrel
    ("vortex", "fireball"), ("vortex", "shieldBash"), ("vortex", "hook"), ("vortex", "tidalWave"),
    # the fireball throws the crate through the grate; the other moves guard and barrel
    ("fireball", "shieldBash"), ("fireball", "hook"),
    # a blinker on the lever, with someone for the guard and the barrel
    ("blink", "shieldBash"), ("blink", "hook"),
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


def plans_with(player, mage, goal="win.", **kw):
    """Plans with the player knowing `player` and the mage `mage`, on a fresh
    planner (a failed search locks the rule set)."""
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    return _solutions(_planner(kit, **kw), goal)


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

    def test_example_1_drag_the_guard_throw_the_crate_swing_over(self):
        self.assert_state_after("win.", has=[
            "at(player,exit)", "at(mage,exit)", "at(warden,exit)", "open(gate)",
            "at(guard,start)", "bridged(rim,far)"])
        self.assert_plan("win.", contains=[
            "opCast(warden, turnToMist, guard)", "opForcedMove(mage, guard, choke, start)",
            "opKnock(player, crate, lever)", "opDash(mage, rim, far)",
            "opFall(mage, barrel, rim, far)"])

    def test_example_2_drag_the_guard_blink_on_the_lever_swing_over(self):
        ops = _ops(plans_with("blink", "hook"))
        assert _op("opForcedMove", "mage", "guard", "choke", "start") in ops, ops[:400]
        assert _op("opTeleport", "player", "hall", "alcove") in ops
        assert _op("opStepOn", "player", "player", "lever") in ops
        assert _op("opDash", "mage", "rim", "far") in ops
        assert _op("opFall", "mage", "barrel", "rim", "far") in ops
        assert _op("opTeleport", "player", "alcove", "far") in ops
        self._record(True, "Example 2: the hook drags the misted guard out, swings over on the "
                           "pillar and drags the barrel in; the blinker works the lever")

    def test_example_3_bash_the_guard_and_the_barrel(self):
        ops = _ops(plans_with("shieldBash", "blink"))
        assert _op("opKnock", "player", "guard", "trapdoor") in ops, ops[:400]
        assert _op("opFall", "player", "barrel", "rim", "far") in ops
        assert _op("opTeleport", "mage", "hall", "alcove") in ops
        self._record(True, "Example 3: the bash drops the misted guard and knocks the barrel in")

    def test_example_4_a_wave_from_the_rim(self):
        ops = _ops(plans_with("tidalWave", "vortex"))
        assert _op("opKnock", "mage", "guard", "trapdoor") in ops, ops[:400]
        assert _op("opKnock", "mage", "crate", "lever") in ops
        assert _op("opCast", "player", "tidalWave", "player") in ops
        assert _op("opFall", "player", "barrel", "rim", "far") in ops
        self._record(True, "Example 4: one vortex for the guard, one for the lever; the wave from "
                           "the rim washes the barrel into the channel")

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
        assert not report.dead_skills, report.dead_skills
        self._record(True, f"P3: exactly the {len(WINNING)} measured pairs win, both ways round")

    def test_property_p4_the_mist_lasts_one_cast(self):
        """Misted, the guard drops through the trapdoor on the very next cast;
        one cast later it is heavy again and the fireball only scorches it."""
        planner = _planner("knows(player, fireball).\nknows(mage, blink).\n")
        assert _solutions(planner, "cast(warden, turnToMist, guard), "
                                   "castFrom(player, fireball, guard, start), confirmStopped(guard).")
        planner = _planner("knows(player, fireball).\nknows(mage, blink).\n")
        late = _solutions(planner, "cast(warden, turnToMist, guard), cast(mage, blink, choke), "
                                   "castFrom(player, fireball, guard, start).")
        assert late and _op("opKnock", "player", "guard", "trapdoor") not in _ops(late)
        self._record(True, "P4: the mist lasts through the next cast only")

    def test_property_p5_one_fireball_each_is_not_enough(self):
        """Two fireballs cannot do three jobs; with mana for four they can."""
        assert not plans_with("fireball", "fireball")
        rich = [("mana(player, 2).", "mana(player, 4).")]
        assert plans_with("fireball", "fireball", replace=rich)
        self._record(True, "P5: fireball + fireball loses on mana alone")

    def test_property_p6_a_hook_on_the_heavy_guard_drags_the_hooker(self):
        """Unmisted, the guard is an anchor: the hook swings the hooker into
        the choke, and the guard still holds it."""
        planner = _planner("knows(player, hook).\nknows(mage, blink).\n")
        plans = _solutions(planner, "castFrom(player, hook, guard, start).")
        ops = _ops(plans)
        assert _op("opDash", "player", "start", "choke") in ops, ops[:300]
        assert _op("opForcedMove", "player", "guard", "choke", "start") not in ops
        self._record(True, "P6: the heavy guard pulls the hooker in; it does not budge")

    def test_property_p7_the_grate_stops_melee_and_dashes(self):
        """Nothing melee reaches the crate through the grate: shield bash and
        hook both need a leaper or the vortex for the lever."""
        assert not plans_with("shieldBash", "hook")
        self._record(True, "P7: shield bash + hook cannot work the lever")


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
