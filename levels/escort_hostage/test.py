"""Tests for The Hostage (escort) level."""

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
SEATS = ("player", "mage")
POOL = ["net", "flashbang", "sleepDart", "flameWall", "magnetize", "gust", "cleanse", "terrify"]

# The measured matrix (htn_components combos): these pairs win, whichever
# companion holds which half, and nothing else does.
SILENCERS = ["net", "flashbang", "sleepDart", "terrify", "flameWall"]
MOVERS = ["magnetize", "gust", "cleanse"]
WINNING = {frozenset((s, m)) for s in SILENCERS for m in MOVERS}


def plans_with(player, mage):
    """All winning plans (as operator strings) with the player knowing `player`
    and the mage `mage`, on a fresh planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT, warn=lambda m: None)
    for dep in Manifest.load(os.path.join(HERE, "manifest.json")).dependencies:
        loader.load(dep)
    assert planner.HtnCompileCustomVariables(
        text + f"knows(player, {player}).\nknows(mage, {mage}).\n") is None
    error, result = planner.FindAllPlansCustomVariables("win.")
    assert error is None, error
    sols = json.loads(result)
    if not sols or (isinstance(sols[0], dict) and "false" in sols[0]):
        return []
    plans = []
    for sol in sols:
        ops = []
        for op in sol:
            name = list(op.keys())[0]
            args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
            ops.append(f"{name}({','.join(args)})")
        plans.append(ops)
    return plans


def has(plan, *ops):
    return all(op in plan for op in ops)


class EscortHostageTest(HtnTestSuite):

    def setup(self):
        for i, dep in enumerate(Manifest.load(os.path.join(HERE, "manifest.json")).dependencies):
            self.load_component(dep, reset_first=(i == 0))
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_blind_and_drag(self):
        self.assert_plan("win.", contains=[
            "opCast(player, net, hound)", "opForcedMove(mage, hostage, cell, corridor)",
            "opForcedMove(mage, hostage, corridor, gate)"])

    def test_example_2_unshackle(self):
        plans = plans_with("terrify", "cleanse")
        assert plans and all(has(p, "opCast(player,terrify,hound)", "opCast(mage,cleanse,hostage)",
                                 "opNavigate(hostage,corridor,gate)") for p in plans)
        self._record(True, "Example 2: the hound is frightened, the shackles come off, the hostage walks")

    def test_example_3_burn_and_shove(self):
        plans = plans_with("flameWall", "gust")
        assert plans and all(has(p, "opExploit(player,hound,burning,dead)",
                                 "opForcedMove(mage,hostage,cell,corridor)",
                                 "opForcedMove(mage,hostage,corridor,gate)") for p in plans)
        self._record(True, "Example 3: the hound burns; two gusts from behind shove the hostage out")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_pairs_win_either_way(self):
        found = {}
        for a, b in itertools.permutations(POOL, 2):
            found.setdefault(frozenset((a, b)), []).append(bool(plans_with(a, b)))
        winning = {k for k, v in found.items() if all(v)}
        one_way = {k for k, v in found.items() if any(v) and not all(v)}
        assert not one_way, f"win only one way round: {one_way}"
        assert winning == WINNING, f"extra: {winning - WINNING}, missing: {WINNING - winning}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win, either way round")

    def test_property_p3_the_hostage_is_spared(self):
        """Fire goes on the kennel, never the cell; the hostage is never pulled
        from the kennel side over the fire pit."""
        for a, b in [("flameWall", "magnetize"), ("flameWall", "cleanse"), ("flameWall", "gust")]:
            for p in plans_with(a, b):
                assert "opSpill(player,kennel,flames)" in p, p
                assert not any("hostage" in op and ("burning" in op or "firepit" in op) for op in p), p
        self._record(True, "P3: fire only on the kennel; the hostage never burns or falls")

    def test_property_p4_the_hound_first(self):
        """Nobody enters the corridor before the hound is silenced."""
        for a, b in [("net", "magnetize"), ("sleepDart", "gust"), ("flashbang", "cleanse")]:
            for p in plans_with(a, b):
                first_in = min(i for i, op in enumerate(p) if op.startswith("opNavigate") and ",corridor)" in op)
                silenced = min(i for i, op in enumerate(p) if op.startswith("opCast(player,"))
                assert silenced < first_in, p
        self._record(True, "P4: the hound is silenced before anyone walks the corridor")


def run_tests():
    suite = EscortHostageTest()
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
