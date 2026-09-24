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
GATHERERS = ["hook", "taunt"]
LIGHTERS = ["fireball", "lightningFlash", "shieldBash", "vortex", "blindingFlash"]
POOL = GATHERERS + LIGHTERS

# The measured matrix (htn_components combos): every gatherer with every lighter.
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
    """The plans as operator strings, e.g. `opCast(player, hook, lurker)`."""
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

    def test_example_1_hook_then_fire(self):
        """The default kit: the player hooks the lurker down into the yard and
        walks out; the mage's fireball lights the keg; the cave-in takes both."""
        self.assert_plan("win.", contains=[
            "opForcedMove(player, lurker, stair, yard)", "opNavigate(player, gate, landing)",
            "opCast(mage, fireball", "opWindUp(keg, caveIn, yard)",
            "opExploit(keg, bruiser, chasm, fell)", "opExploit(keg, lurker, chasm, fell)"])
        assert any("player, fell)" not in text_of([p]) and "mage, fell)" not in text_of([p])
                   for p in plans_with("hook", "fireball")), "a hook plan keeps the whole team"

    def test_example_2_the_tripwire(self):
        """A shield bash from the stair knocks the bruiser onto the tripwire:
        the yard catches fire, and the keg with it."""
        ops = text_of(plans_with("hook", "shieldBash"))
        assert "opKnock(mage, bruiser, tripwire)" in ops and "opSpill(mage, yard, flames)" in ops, ops
        assert "opProvoked(keg, burning, caveIn)" in ops, ops
        self._record(True, "Example 2: bashed onto the tripwire, the bruiser sets the yard alight")

    def test_example_3_the_taunter_holds_the_yard(self):
        """Taunted, the lurker walks down after the player and follows it: the
        player stays in the yard and goes down with it."""
        plans = plans_with("taunt", "lightningFlash")
        assert plans
        for plan in plans:
            s = text_of([plan])
            assert "opNavigate(lurker, stair, yard)" in s and "opExploit(keg, player, chasm, fell)" in s, s
        self._record(True, "Example 3: the taunter holds the lurker in the yard, and falls with it")

    def test_example_4_the_flash_from_the_stair(self):
        """A flash from the stair lights the keg; its dash does not land in the
        new chasm."""
        ops = text_of(plans_with("hook", "lightningFlash"))
        assert "opCast(mage, lightningFlash" in ops and "opProvoked(keg, electrocuted, caveIn)" in ops
        assert "opDash(mage" not in ops, ops
        self._record(True, "Example 4: the flash lights the keg and its caster stays out")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_ten_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} gatherer-lighter pairs win")

    def test_property_p3_the_keg_blows_once(self):
        """Light the keg first: the bruiser falls, and the lurker is out of
        reach for good."""
        assert not plans_with("hook", "fireball",
                              "detonate(keg), bringTo(lurker, yard, none), confirmStopped(lurker).")
        self._record(True, "P3: the keg blows once; lit first, the lurker is lost")

    def test_property_p4_a_blinding_flash_spends_its_caster(self):
        """The blinding flash lights the keg from inside the yard: disjoint
        passes the blow, but the chasm takes its caster."""
        for plan in plans_with("hook", "blindingFlash"):
            assert "opExploit(keg, mage, chasm, fell)" in text_of([plan])
        self._record(True, "P4: every blinding-flash plan loses its caster")

    def test_property_p5_the_wave_drowns_the_fuse(self):
        """A tidal wave in the yard soaks the keg: the tripwire's fire then
        only makes steam, and the keg does not blow."""
        wave = plans_with("tidalWave", "shieldBash", "cast(player, tidalWave, bruiser).")
        assert any("opKnock(player, bruiser, tripwire)" in text_of([p]) for p in wave)
        assert all("opReact(player, keg, wet, burning, steam)" in text_of([p]) or
                   "tripwire" not in text_of([p]) for p in wave)
        assert not plans_with("tidalWave", "shieldBash",
                              "cast(player, tidalWave, bruiser), confirmStopped(keg).")
        self._record(True, "P5: a wave onto the tripwire only steams the soaked keg")


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
