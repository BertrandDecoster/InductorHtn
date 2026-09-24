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
POOL = ["lightningFlash", "blindingFlash", "taunt", "hook", "vortex", "tidalWave"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        # the keg brought to the ent, then jolted from outside
        ("lightningFlash", "hook"), ("lightningFlash", "vortex"),
        # the keg brought to the ent, then startled (the flasher may stay: disjoint)
        ("blindingFlash", "hook"), ("blindingFlash", "vortex"), ("blindingFlash", "tidalWave"),
        # goaded into the grove, and the taunter got out of the blast: the rooted ent stays
        ("taunt", "hook"), ("taunt", "vortex"), ("taunt", "tidalWave"),
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
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT, warn=lambda m: None)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, "win.")


def ops_list(plan):
    out = []
    for op in plan:
        name = list(op.keys())[0]
        args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
        out.append(f"{name}({','.join(args)})")
    return out


def ops_text(plans):
    """Every operator of every plan, as `name(a,b,...)` strings joined by spaces."""
    return " ".join(" ".join(ops_list(p)) for p in plans)


class PowderKegTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_hook_the_keg_down_and_jolt_it(self):
        ops = ops_text(plans_with("hook", "lightningFlash"))
        for op in ["opForcedMove(player,mule,ridge,grove)", "opCast(mage,lightningFlash,mule)",
                   "opProvoked(mule,electrocuted,blast)", "opWindUp(mule,blast,grove)",
                   "opSpill(mule,grove,flames)", "opExploit(mule,ent,burning,dead)"]:
            assert op in ops, f"missing {op}"
        self._record(True, "Example 1: hook the mule into the grove, jolt it from the road")

    def test_example_2_goad_it_and_wash_the_taunter_out(self):
        ops = ops_text(plans_with("taunt", "tidalWave"))
        for op in ["opCast(player,taunt,mule)", "opForcedMove(player,mule,ridge,grove)",
                   "opWindUp(mule,blast,grove)", "opCast(mage,tidalWave,mage)",
                   "opForcedMove(mage,player,grove,hollow)", "opForcedMove(mage,mule,grove,hollow)",
                   "opBlow(mule,blast,grove,grove)", "opExploit(mule,ent,burning,dead)"]:
            assert op in ops, f"missing {op}"
        self._record(True, "Example 2: taunt from the grove, the wave washes the taunter out")

    def test_example_3_wash_it_down_the_slope_and_flash_it(self):
        ops = ops_text(plans_with("tidalWave", "blindingFlash"))
        for op in ["opForcedMove(player,mule,ridge,grove)", "opCast(mage,blindingFlash,mage)",
                   "opProvoked(mule,blinded,blast)", "opExploit(mule,ent,burning,dead)"]:
            assert op in ops, f"missing {op}"
        self._record(True, "Example 3: wash the mule down from the crag, flash it")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_a_soaked_fuse(self):
        """Washed down the slope, the mule is wet: lightning only makes it seize up."""
        assert not plans_with("lightningFlash", "tidalWave")
        self._record(True, "P3: lightningFlash + tidalWave: no plan")

    def test_property_p4_the_rooted_ent_stays(self):
        """Whatever gets the taunter out, the ent never moves: it is heavy."""
        for other in ["hook", "vortex", "tidalWave"]:
            ops = ops_text(plans_with("taunt", other))
            assert ops and not re.search(r"opForcedMove\(\w+,ent,", ops), other
        self._record(True, "P4: the ent stays rooted in every taunt plan")

    def test_property_p5_the_keg_blows_once(self):
        """Two triggers and no mover: the first spends the keg on the ridge."""
        assert not plans_with("lightningFlash", "blindingFlash")
        assert not plans_with("lightningFlash", "taunt") and not plans_with("blindingFlash", "taunt")
        self._record(True, "P5: two triggers and no mover: no plan")


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
