"""Tests for the Sinkhole level."""

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
POOL = ["hook", "taunt", "vortex", "lightningFlash", "fireball", "turnToMist"]

# The measured matrix (htn_components combos): these pairs win, nothing else does.
WINNING = {
    frozenset(p) for p in [
        ("hook", "vortex"), ("hook", "lightningFlash"),            # the sinkhole, the hooker walks off
        ("taunt", "vortex"), ("taunt", "lightningFlash"),          # the sinkhole, the taunter stays
        ("fireball", "vortex"), ("fireball", "lightningFlash"),    # one by one, the golem stamps
        ("fireball", "turnToMist"),                                # one by one, the golem in the hole
    ]
}


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def plans_with(player, mage, goal="clearSinkhole."):
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
    """The plans as operator strings, e.g. `opCast(player, vortex, golem)`."""
    out = []
    for plan in plans:
        for op in plan:
            name = list(op.keys())[0]
            args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
            out.append(f"{name}({', '.join(args)})")
    return " ".join(out)


class SinkholeTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_the_sinkhole(self):
        """The default kit: the player hooks both mooks onto the rim and walks
        off; the mage's vortex pins the golem, which stamps; the rim takes all
        three."""
        self.assert_plan("clearSinkhole.", contains=[
            "opForcedMove(player, wader, pool, rim)", "opForcedMove(player, tender, slick, rim)",
            "opNavigate(player, rim, ledge)", "opCast(mage, vortex, golem)",
            "opWindUp(golem, caveIn, rim)", "opBlow(golem, caveIn, rim, rim)",
            "opExploit(golem, wader, chasm, fell)", "opExploit(golem, tender, chasm, fell)",
            "opExploit(golem, golem, chasm, fell)"])

    def test_example_2_the_taunter_holds_the_rim(self):
        """Taunted from the rim, the mooks walk onto it and follow the taunter:
        it stays, and goes down with the rim when the flash jolts the golem."""
        ops = text_of(plans_with("taunt", "lightningFlash"))
        assert "opNavigate(tender, slick, rim)" in ops, ops
        assert "opCast(mage, lightningFlash, golem)" in ops and "opBlow(golem, caveIn, rim, rim)" in ops
        assert "opExploit(golem, player, chasm, fell)" in ops, ops
        self._record(True, "Example 2: the taunter holds the mooks on the rim, and falls with it")

    def test_example_3_one_by_one(self):
        """Fire burns the tender and knocks the wader into the drain; the flash
        makes the golem stamp on its empty rim, and the flasher is not there."""
        ops = text_of(plans_with("fireball", "lightningFlash"))
        assert "opReact(player, tender, oiled, burning, blaze)" in ops, ops
        assert "opKnock(player, wader, drain)" in ops, ops
        assert "opBlow(golem, caveIn, rim, rim)" in ops, ops
        self._record(True, "Example 3: fire for the mooks, the flash for the golem")

    def test_example_4_mist_and_the_hole(self):
        plans = plans_with("turnToMist", "fireball")
        ops = text_of(plans)
        assert "opCast(player, turnToMist, golem)" in ops and "opKnock(mage, golem, hole)" in ops, ops
        assert "caveIn" not in ops, "the golem is knocked into the hole, never provoked"
        self._record(True, "Example 4: mist the golem, knock it into the hole")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_seven_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_the_taunter_is_spent(self):
        """Every taunt plan loses its taunter to the rim: walking off drags the
        mooks off with it. A hooker can walk away."""
        for plan in plans_with("taunt", "vortex"):
            assert "player, fell)" in text_of([plan]), text_of([plan])
        assert any("player, fell)" not in text_of([p]) for p in plans_with("hook", "vortex"))
        self._record(True, "P3: a taunter goes down with the rim; a hooker walks off")

    def test_property_p4_the_golem_first_cuts_the_rim(self):
        assert plans_with("hook", "vortex")
        assert not plans_with("hook", "vortex",
                              "golemDown(golem), mook(wader), mook(tender), "
                              "confirmStopped(wader), confirmStopped(tender).")
        self._record(True, "P4: bringing the golem down first leaves the tender out of reach")

    def test_property_p5_the_golem_cannot_be_knocked_as_it_stands(self):
        self.assert_no_plan("knockOn(golem, feature(hole), none).")

    def test_property_p6_fire_clears_the_mooks_only(self):
        """Fire alone takes both mooks but never the golem."""
        assert plans_with("fireball", "fireball",
                          "neutralize(wader), neutralize(tender).")
        assert not plans_with("fireball", "fireball")
        self._record(True, "P6: fire clears the mooks, never the golem")


def run_tests():
    suite = SinkholeTest()
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
