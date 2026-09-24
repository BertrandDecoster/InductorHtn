"""Tests for the Sync: Decoy level."""

import itertools
import json
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from indhtnpy import HtnPlanner
from htn_components.loader import ComponentLoader
from htn_components.manifest import Manifest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
LURES = ["taunt", "magnetize", "gust", "tidalWave"]
VEILS = ["vanish", "flashbang", "net", "smokeBomb"]
POOL = LURES + VEILS

# The measured matrix: every lure with every veil, and nothing else.
WINNING = {frozenset((a, b)) for a in LURES for b in VEILS}


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
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT, warn=lambda m: None)
    for dep in Manifest.load(os.path.join(HERE, "manifest.json")).dependencies:
        loader.load(dep)
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, "win.")


def ops(plans):
    return " ".join(json.dumps(p) for p in plans).replace(" ", "")


def op(name, *args):
    return json.dumps({name: [{a: []} for a in args]}).replace(" ", "")


class SyncDecoyTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_the_decoy_is_slammed_the_slipper_walks(self):
        self.assert_plan("win.", contains=[
            "opNavigate(mage, camp, nook)", "opCast(player, taunt, golem)",
            "opGrant(golem, player, stunned)", "opCast(mage, flashbang, golem)",
            "opNavigate(mage, arch, switch)", "opOpen(mage, portcullis)"])

    def test_example_2_shoved_into_the_alcove_then_sneak(self):
        text = ops(plans_with("vanish", "gust"))
        assert op("opForcedMove", "mage", "golem", "arch", "alcove") in text, text[:400]
        assert op("opCast", "player", "vanish", "player") in text
        assert op("opOpen", "player", "portcullis") in text
        self._record(True, "Example 2: the mage shoves the golem aside; the stealthed player slips through")

    def test_example_3_hooked_away_then_netted(self):
        text = ops(plans_with("magnetize", "net"))
        assert op("opCast", "player", "magnetize", "golem") in text
        assert op("opCast", "mage", "net", "golem") in text
        self._record(True, "Example 3: the hook drags the golem off the arch; the net blinds it")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_sixteen_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_either_seat(self):
        assert plans_with("net", "tidalWave") and plans_with("tidalWave", "net")
        self._record(True, "P3: a pair wins whichever companion holds which half")

    def test_property_p4_the_taunter_never_slips(self):
        """A taunted golem slams its taunter: in every taunt plan, the one
        who reaches the switch is the other companion."""
        for p, m, slipper in [("taunt", "flashbang", "mage"), ("flashbang", "taunt", "player"),
                              ("taunt", "net", "mage")]:
            text = ops(plans_with(p, m))
            assert text and op("opOpen", slipper, "portcullis") in text, (p, m)
            other = "player" if slipper == "mage" else "mage"
            assert op("opOpen", other, "portcullis") not in text, (p, m)
        self._record(True, "P4: the taunter is stunned; the other one slips")

    def test_property_p5_blinding_does_not_clear_the_arch(self):
        self.assert_no_plan("veil(player), walkTo(player, switch).")
        self._record(True, "P5: a blinded golem still holds the arch")


def run_tests():
    suite = SyncDecoyTest()
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
