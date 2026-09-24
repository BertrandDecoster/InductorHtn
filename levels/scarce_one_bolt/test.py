"""Tests for the One Bolt level."""

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
POOL = ["lightningFlash", "hook", "taunt", "fireball", "tidalWave", "shieldBash", "vortex"]

# The measured matrix (htn_components combos): these pairs win, nothing else does.
WINNING = {
    frozenset(("lightningFlash", p))
    for p in ["hook", "taunt", "fireball", "tidalWave", "shieldBash", "vortex"]
}


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
    """The plans as operator strings, e.g. `opCast(player, hook, drone)`."""
    out = []
    for plan in plans:
        for op in plan:
            name = list(op.keys())[0]
            args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
            out.append(f"{name}({', '.join(args)})")
    return " ".join(out)


class OneBoltTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_into_the_flood(self):
        """The default kit: the player hooks the drone into the flooded nave;
        one bolt on the nave takes both machines."""
        self.assert_plan("win.", contains=[
            "opCast(player, hook, drone)", "opForcedMove(player, drone, hall, nave)",
            "opGrant(player, drone, wet)", "opCast(mage, lightningFlash, engine)",
            "opExploit(mage, engine, electrocuted, dead)", "opExploit(mage, drone, electrocuted, dead)"])

    def test_example_2_lured_into_the_flood(self):
        ops = text_of(plans_with("taunt", "lightningFlash"))
        assert "opNavigate(drone, hall, nave)" in ops and "opGrant(drone, drone, wet)" in ops, ops
        assert "opExploit(mage, drone, electrocuted, dead)" in ops, ops
        self._record(True, "Example 2: taunted from the nave, the drone wades in; one bolt")

    def test_example_3_the_shaft(self):
        ops = text_of(plans_with("fireball", "lightningFlash"))
        assert "opKnock(player, drone, shaft)" in ops and "opExploit(player, drone, chasm, fell)" in ops
        assert "opExploit(mage, engine, electrocuted, dead)" in ops, ops
        self._record(True, "Example 3: a fireball knocks the drone into the shaft; the bolt takes the engine")

    def test_example_4_off_the_balcony(self):
        ops = text_of(plans_with("hook", "lightningFlash"))
        assert "opNavigate(player, porch, gallery)" in ops, ops
        assert "opFall(player, drone, hall, gallery)" in ops, ops
        self._record(True, "Example 4: hooked from the gallery, the drone falls in the gap")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_six_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_one_bolt(self):
        """Every winning plan casts exactly one bolt: the mana buys one."""
        for a, b in [tuple(p) for p in WINNING]:
            for plan in plans_with(a, b):
                s = json.dumps(plan)
                bolts = s.count('"lightningFlash"')
                assert bolts == 1, f"{a}+{b}: {bolts} bolts in {s}"
        self._record(True, "P3: every winning plan spends exactly one bolt")

    def test_property_p4_a_bolt_on_the_dry_drone_is_wasted(self):
        """Jolting the drone first only stuns it, and the mana is gone."""
        assert not plans_with("hook", "lightningFlash",
                              "cast(mage, lightningFlash, drone), win.")
        assert not plans_with("lightningFlash", "lightningFlash")
        self._record(True, "P4: a bolt on the dry drone only stuns it; two bolts still lose")

    def test_property_p5_soaked_in_the_wrong_area(self):
        """A wave in the hall soaks the drone where it stands: wet, but not in
        the engine's area - one bolt cannot take both."""
        plans = plans_with("tidalWave", "lightningFlash")
        assert plans and all("opGrant(player, drone, fell)" in text_of([p]) for p in plans)
        self._record(True, "P5: with a wave, the drone only ever falls (the shaft or the gap)")

    def test_property_p6_each_hand_matters(self):
        assert plans_with("lightningFlash", "vortex") and plans_with("taunt", "lightningFlash")
        self._record(True, "P6: the pairs win whichever companion holds which half")


def run_tests():
    suite = OneBoltTest()
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
