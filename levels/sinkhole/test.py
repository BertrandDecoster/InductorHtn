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
POOL = ["vortex", "blink", "hook", "taunt", "fireball", "turnToMist", "tidalWave"]

# The measured matrix (htn_components combos): these pairs win, nothing else does.
WINNING = {
    frozenset(p) for p in [
        ("vortex", "blink"), ("vortex", "hook"),                   # the sinkhole, and an escape
        ("hook", "taunt"),                                         # gather first
        ("vortex", "fireball"), ("vortex", "tidalWave"),           # mooks first, the vortex provokes
        ("taunt", "fireball"), ("taunt", "tidalWave"),             # mooks first, the taunt provokes
        ("turnToMist", "tidalWave"),                               # mist
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
        """The default kit: the vortex draws everything onto the rim and pins
        the golem, which stamps; the mage, drawn in too, blinks out; the rim
        takes all three."""
        self.assert_plan("clearSinkhole.", contains=[
            "opCast(player, vortex, golem)", "opForcedMove(player, mage, ledge, rim)",
            "opWindUp(golem, caveIn, rim)", "opTeleport(mage, rim, ledge)",
            "opBlow(golem, caveIn, rim, rim)", "opExploit(golem, wader, chasm, fell)",
            "opExploit(golem, tender, chasm, fell)", "opExploit(golem, golem, chasm, fell)"])
        self.assert_state_after("clearSinkhole.",
                                has=["tag(golem,fell)", "tag(wader,fell)", "tag(tender,fell)"],
                                not_has=["tag(mage,fell)", "tag(player,fell)"])

    def test_example_2_gather_first(self):
        plans = plans_with("hook", "taunt")
        ops = text_of(plans)
        assert plans, "hook both onto the rim, step off, taunt the golem"
        assert "opForcedMove(player, wader, pool, rim)" in ops
        assert "opForcedMove(player, tender, slick, rim)" in ops
        assert "opCast(mage, taunt, golem)" in ops and "opBlow(golem, caveIn, rim, rim)" in ops
        self._record(True, "Example 2: gather the mooks on the rim, then provoke the golem")

    def test_example_3_mist(self):
        plans = plans_with("turnToMist", "tidalWave")
        ops = text_of(plans)
        assert plans and "opCast(player, turnToMist, golem)" in ops
        assert "opForcedMove(mage, golem, rim, pit)" in ops
        assert "caveIn" not in ops, "the golem is washed away, never provoked"
        self._record(True, "Example 3: mist the golem, wash it and the mooks into the pit")

    def test_example_4_the_vortex_pulls_a_friend_back(self):
        """Mooks first (the mage's fireballs), then the vortex provokes the
        golem and draws the mage in with it; the player's second vortex, on
        the ledge, draws the mage back out in the window."""
        plans = plans_with("vortex", "fireball")
        ops = text_of(plans)
        assert plans and "opCast(player, vortex, golem)" in ops
        assert "opCast(player, vortex, ledge)" in ops and "opForcedMove(player, mage, rim, ledge)" in ops
        self._record(True, "Example 4: one vortex provokes, a second pulls the mage out")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_eight_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_nobody_falls_with_the_rim(self):
        for a, b in [tuple(p) for p in WINNING]:
            for plan in plans_with(a, b):
                s = text_of([plan])
                assert "player, chasm, fell" not in s and "mage, chasm, fell" not in s, s
        self._record(True, "P3: no winning plan loses a companion to the sinkhole")

    def test_property_p4_the_vortex_takes_friends(self):
        """With no way out for the drawn companion, the sinkhole method fails."""
        assert not plans_with("vortex", "turnToMist")
        assert not plans_with("vortex", "taunt")
        self._record(True, "P4: a vortex without an escape loses")

    def test_property_p5_the_golem_first_cuts_the_rim(self):
        assert plans_with("hook", "taunt")
        assert not plans_with("hook", "taunt", "collapse(golem), neutralize(wader), neutralize(tender).")
        self._record(True, "P5: bringing the golem down first leaves the mooks out of reach")

    def test_property_p6_the_golem_cannot_be_moved_as_it_stands(self):
        self.assert_no_plan("placeAs(mage, golem, pit).")


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
