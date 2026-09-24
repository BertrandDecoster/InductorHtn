"""Tests for the Two Hands level."""

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
POOL = ["turnToMist", "fireball", "tidalWave", "shieldBash", "vortex", "hook", "taunt",
        "lightningFlash"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        ("turnToMist", "fireball"), ("turnToMist", "tidalWave"), ("turnToMist", "shieldBash"),
        ("turnToMist", "vortex"), ("turnToMist", "hook"),                     # drop it
        ("tidalWave", "lightningFlash"), ("taunt", "lightningFlash"),         # short it
    ]
}


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def plans_with(player, mage):
    """All winning plans with the player knowing `player` and the mage `mage`, on a fresh
    planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    loader = ComponentLoader(planner, ROOT)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, "win.")


def text_of(plans):
    """The plans as operator strings, e.g. `opCast(player, taunt, sentinel)`."""
    out = []
    for plan in plans:
        for op in plan:
            name = list(op.keys())[0]
            args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
            out.append(f"{name}({', '.join(args)})")
    return " ".join(out)


class TwoHandsTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_mist_then_knock(self):
        self.assert_plan("win.", contains=[
            "opCast(player, turnToMist, sentinel)", "opCast(mage, fireball, sentinel)",
            "opKnock(mage, sentinel, abyss)", "opExploit(mage, sentinel, chasm, fell)"])

    def test_example_2_mist_then_hook_across_the_gap(self):
        ops = text_of(plans_with("turnToMist", "hook"))
        assert "opNavigate(mage, ledge, overlook)" in ops, ops
        assert "opFall(mage, sentinel, bridge, overlook)" in ops, ops
        self._record(True, "Example 2: mist, then a hook from the overlook drops it in the gap")

    def test_example_3_soak_then_jolt(self):
        ops = text_of(plans_with("tidalWave", "lightningFlash"))
        assert "opCast(player, tidalWave, player)" in ops and "opGrant(player, sentinel, wet)" in ops
        assert "opExploit(mage, sentinel, electrocuted, dead)" in ops, ops
        self._record(True, "Example 3: a wave on the bridge soaks it, the flash short-circuits it")

    def test_example_4_lure_it_into_the_ford(self):
        ops = text_of(plans_with("taunt", "lightningFlash"))
        assert "opCast(player, taunt, sentinel)" in ops
        assert "opNavigate(sentinel, ledge, ford)" in ops and "opGrant(sentinel, sentinel, wet)" in ops
        assert "opExploit(mage, sentinel, electrocuted, dead)" in ops, ops
        self._record(True, "Example 4: taunted from the ford, it walks in soaked; the flash kills it")

    def test_example_5_mist_then_vortex(self):
        ops = text_of(plans_with("turnToMist", "vortex"))
        assert "opCast(mage, vortex, abyss)" in ops and "opKnock(mage, sentinel, abyss)" in ops, ops
        self._record(True, "Example 5: mist, then a vortex on the abyss draws it in")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_seven_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        """Swapping who holds which skill still wins: the combo is about the
        pair, not the seat."""
        assert plans_with("fireball", "turnToMist") and plans_with("lightningFlash", "taunt")
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_the_mist_is_a_moment(self):
        """The mist lasts through one more cast: a knock then lands. With the
        sentinel heavy again, nothing moves it."""
        assert not plans_with("fireball", "fireball")
        assert not plans_with("turnToMist", "turnToMist")
        self._record(True, "P4: mist alone or a knock alone leaves the sentinel standing")

    def test_property_p5_heavy_and_dry(self):
        """A hook on the heavy sentinel drags the caster onto the bridge; a
        flash on the dry machine only stuns it."""
        assert not plans_with("hook", "lightningFlash")
        self.assert_state_after("cast(mage, fireball, sentinel), cast(player, turnToMist, sentinel).",
                                has=["at(sentinel,bridge)"], not_has=["tag(sentinel,fell)"])
        self._record(True, "P5: a hook and a flash leave it standing; a knock before the mist too")


def run_tests():
    suite = TwoHandsTest()
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
