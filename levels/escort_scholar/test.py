"""Tests for The Scholar (escort) level."""

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
POOL = ["hook", "vortex", "tidalWave", "lightningFlash", "turnToMist", "blizzard", "shieldBash",
        "blindingFlash"]

# The measured matrix (htn_components combos): these pairs win, whichever
# companion holds which half, and nothing else does.
WINNING = {frozenset(p) for p in [
    ("hook", "turnToMist"), ("vortex", "turnToMist"), ("tidalWave", "lightningFlash"),
    ("lightningFlash", "blizzard"), ("blizzard", "shieldBash"), ("blizzard", "blindingFlash")]}


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


def index(plan, prefix):
    return min(i for i, op in enumerate(plan) if op.startswith(prefix))


class EscortScholarTest(HtnTestSuite):

    def setup(self):
        for i, dep in enumerate(Manifest.load(os.path.join(HERE, "manifest.json")).dependencies):
            self.load_component(dep, reset_first=(i == 0))
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_soak_and_jolt_in_the_window(self):
        self.assert_plan("win.", contains=[
            "opCast(player, tidalWave, player)", "opWindUp(brute, groundSlam, player)",
            "opCast(mage, lightningFlash, brute)", "opExploit(mage, brute, electrocuted, dead)",
            "opMiss(brute, groundSlam, player)", "opNavigate(scholar, hall, exit)"],
            not_contains=["opBlow"])

    def test_example_2_mist_and_vortex(self):
        plans = plans_with("turnToMist", "vortex")
        assert plans and all(has(p, "opCast(player,turnToMist,brute)", "opCast(mage,vortex,pit)",
                                 "opForcedMove(mage,brute,hall,pit)",
                                 "opNavigate(scholar,hall,exit)") for p in plans)
        self._record(True, "Example 2: the brute turns to mist and the vortex sucks it into the pit")

    def test_example_3_ice_the_cistern(self):
        plans = plans_with("shieldBash", "blizzard")
        assert plans and all(has(p, "opGrant(player,brute,stunned)", "opCast(mage,blizzard,cistern)",
                                 "opNavigate(scholar,balcony,cistern)",
                                 "opNavigate(scholar,cistern,exit)") for p in plans)
        self._record(True, "Example 3: the brute is bashed blind, the cistern ices over, the scholar walks across")

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

    def test_property_p3_the_traps_have_no_plan(self):
        """A wave from the library soaks the scholar too; walking onto the ice
        it would freeze. A soaked brute swings at the soaker unless it dies in
        the window: a bash cannot stop a physical blow, and mist does not move
        it. A dry jolt stuns the brute, but it still fills the doorway."""
        for a, b in [("tidalWave", "blizzard"), ("tidalWave", "shieldBash"),
                     ("tidalWave", "turnToMist"), ("lightningFlash", "lightningFlash")]:
            assert not plans_with(a, b), (a, b)
        self._record(True, "P3: wave + blizzard, wave + bash, wave + mist and a dry jolt alone have no plan")

    def test_property_p4_the_slam_never_lands(self):
        """Whenever the brute winds up, the blow misses: it is dead before it
        lands, and the scholar is never struck."""
        for a, b in WINNING:
            for p in plans_with(a, b):
                assert not any(op.startswith("opBlow") for op in p), p
                if any(op.startswith("opWindUp") for op in p):
                    assert index(p, "opWindUp") < index(p, "opExploit") < index(p, "opMiss"), p
        self._record(True, "P4: the slam is always outrun; no blow lands")

    def test_property_p5_two_companions_cast(self):
        for a, b in WINNING:
            for p in plans_with(a, b):
                casters = {op.split("(")[1].split(",")[0] for op in p if op.startswith("opCast")}
                assert casters == {"player", "mage"}, p
        self._record(True, "P5: both companions cast in every winning plan")


def run_tests():
    suite = EscortScholarTest()
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
