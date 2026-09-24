"""Tests for the Powder Keg level."""

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
GATHERERS = ["tidalWave", "hook", "taunt", "vortex"]
LIGHTERS = ["fireball", "lightningFlash"]
POOL = GATHERERS + LIGHTERS

# The measured matrix (htn_components combos): one gatherer and one lighter
# win, nothing else does.
WINNING = {frozenset((g, l)) for g in GATHERERS for l in LIGHTERS}


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def plans_with(player, mage, goal="win."):
    """All plans for `goal` with the player knowing `player` and the mage `mage`, on a
    fresh planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, goal)


def text_of(plans):
    """The plans as operator strings, e.g. `opCast(player, gust, drone)`."""
    out = []
    for plan in plans:
        for op in plan:
            name = list(op.keys())[0]
            args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
            out.append(f"{name}({', '.join(args)})")
    return " ".join(out)


class PowderKegTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_wash_down_then_burn(self):
        """The default kit: a wave from the landing washes the lurker into the
        yard, a fireball lights the keg, the floor takes both."""
        self.assert_plan("win.", contains=[
            "opForcedMove(player, lurker, stair, yard)", "opCast(mage, fireball, keg)",
            "opWindUp(keg, caveIn, yard)", "opBlow(keg, caveIn, yard, yard)",
            "opExploit(keg, bruiser, chasm, fell)", "opExploit(keg, lurker, chasm, fell)"])

    def test_example_2_drag_down_then_step_out(self):
        plans = plans_with("taunt", "fireball")
        ops = text_of(plans)
        assert plans, "a taunt from the yard, then fire on the keg, should take both"
        assert "opForcedMove(player, lurker, stair, yard)" in ops
        assert "opNavigate(player, yard," in ops, "the taunter walks out before the fuse"
        assert "opExploit(keg, lurker, chasm, fell)" in ops
        self._record(True, "Example 2: drag the lurker into the yard, step out, set the keg alight")

    def test_example_3_spark_through_the_yard(self):
        plans = plans_with("vortex", "lightningFlash")
        ops = text_of(plans)
        assert plans and "opCast(mage, lightningFlash, gate)" in ops
        assert "opDash(mage, stair, gate)" in ops
        assert "opExploit(keg, lurker, chasm, fell)" in ops
        self._record(True, "Example 3: draw the lurker in, flash through the yard from the stair")

    def test_example_4_light_first_then_into_the_crater(self):
        plans = plans_with("tidalWave", "fireball")
        ops = text_of(plans)
        assert "opExploit(player, lurker, chasm, fell)" in ops, "washed into the crater"
        self._record(True, "Example 4: light the keg first, then wash the lurker into the crater")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_gatherer_and_lighter_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_one_blast(self):
        """Every winning plan sets the keg off exactly once, and nobody of the
        team falls."""
        for g, l in [("tidalWave", "fireball"), ("hook", "lightningFlash"), ("vortex", "fireball")]:
            for plan in plans_with(g, l):
                s = text_of([plan])
                assert s.count("opProvoked(") == 1, f"{g}+{l}: not one blast in {s}"
                assert "player, chasm, fell" not in s and "mage, chasm, fell" not in s, s
        self._record(True, "P3: the keg blows once per plan, and the team stays out of it")

    def test_property_p4_wrong_order_loses(self):
        """Light the keg first: a puller can no longer take the lurker."""
        assert plans_with("taunt", "fireball")
        assert not plans_with("taunt", "fireball", "detonate(keg), neutralize(lurker).")
        assert not plans_with("hook", "fireball",
                              "detonate(keg), herd(lurker, yard), confirmStopped(lurker).")
        # Spent means spent: the keg is gone with the floor.
        assert not plans_with("tidalWave", "fireball", "detonate(keg), detonate(keg).")
        self._record(True, "P4: lighting the keg before the lurker is down loses for a puller")

    def test_property_p5_a_spark_on_the_keg_buries_its_caster(self):
        """Aimed at the keg, the flash carries its caster into the crater: only
        the shot through the yard, from the stair, wins."""
        for plan in plans_with("hook", "lightningFlash"):
            s = text_of([plan])
            assert "opCast(mage, lightningFlash, keg)" not in s, s
        self._record(True, "P5: no winning plan flashes the keg itself")

    def test_property_p6_each_hand_matters(self):
        assert plans_with("fireball", "tidalWave") and plans_with("lightningFlash", "hook")
        self._record(True, "P6: the pairs win whichever companion holds which half")


def run_tests():
    suite = PowderKegTest()
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
