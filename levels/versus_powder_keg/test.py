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
POOL = ["hook", "taunt", "lightningFlash", "blindingFlash", "vortex", "turnToMist", "tidalWave",
        "shieldBash"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        # bring the mule to the ent (hook, taunt) and light it (a jolt, a flash, a snare)
        ("hook", "lightningFlash"), ("hook", "blindingFlash"), ("hook", "vortex"),
        ("taunt", "lightningFlash"), ("taunt", "blindingFlash"), ("taunt", "vortex"),
        # or turn the ent to mist and knock it into the hollow
        ("turnToMist", "tidalWave"), ("turnToMist", "shieldBash"), ("turnToMist", "vortex"),
    ]
}


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def plans_with(player, mage, extra="", goal="win."):
    """All plans of `goal` with the player knowing `player` and the mage `mage`, on a fresh
    planner (a failed search locks the rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(256 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT, warn=lambda m: None)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n" + extra
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, goal)


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

    def test_example_1_hook_it_down_the_road_jolt_it(self):
        ops = ops_text(plans_with("hook", "lightningFlash"))
        for op in ["opForcedMove(player,mule,ridge,road)", "opForcedMove(player,mule,road,grove)",
                   "opCast(mage,lightningFlash,mule)", "opBlow(mule,blast,mule,grove)",
                   "opExploit(mule,ent,burning,dead)"]:
            assert op in ops, f"missing {op}"
        self._record(True, "Example 1: two hooks along the road, a jolt: the keg blows on the ent")

    def test_example_2_flash_it_on_the_ridge_taunt_it_down_in_the_window(self):
        late = []
        for p in plans_with("taunt", "blindingFlash"):
            ops = ops_list(p)
            if "opWindUp(mule,blast,mule)" in ops:
                w = ops.index("opWindUp(mule,blast,mule)")
                if "opCast(player,taunt,mule)" in ops[w:] and "opNavigate(mule,ridge,road)" in ops[w:]:
                    late.append(ops)
        assert late, "no plan taunts the mule down in the window"
        assert "opBlow(mule,blast,mule,grove)" in late[0] and "opExploit(mule,ent,burning,dead)" in late[0]
        self._record(True, "Example 2: flash it on the ridge; in the window, taunt it down to the grove")

    def test_example_3_snare_it_with_a_vortex(self):
        ops = ops_text(plans_with("taunt", "vortex"))
        for op in ["opCast(mage,vortex,sap)", "opProvoked(mule,rooted,blast)",
                   "opExploit(mule,ent,burning,dead)"]:
            assert op in ops, f"missing {op}"
        self._record(True, "Example 3: taunt it into the grove, vortex on the sap pool snares it")

    def test_example_4_mist_and_the_hollow(self):
        ops = ops_text(plans_with("turnToMist", "tidalWave"))
        for op in ["opCast(player,turnToMist,ent)", "opCast(mage,tidalWave,mage)",
                   "opExploit(mage,ent,chasm,fell)"]:
            assert op in ops, f"missing {op}"
        self._record(True, "Example 4: turn the ent to mist, wash it into the hollow")

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
        """Soaked, the mule only seizes up under lightning (stunned: silenced, no blast); a
        blinding flash still lights it."""
        assert not plans_with("hook", "lightningFlash", "tag(mule, wet).\n")
        assert plans_with("hook", "blindingFlash", "tag(mule, wet).\n")
        self._record(True, "P3: a wet mule seizes up under lightning; a flash still lights it")

    def test_property_p4_over_the_ravine_it_falls(self):
        plans = plans_with("hook", "hook", goal="walkTo(player, grove), cast(player, hook, mule).")
        assert "opFall(player,mule,ridge,grove)" in ops_text(plans)
        self._record(True, "P4: hooked straight across the ravine, the mule falls, keg and all")

    def test_property_p5_the_keg_blows_once(self):
        plans = plans_with("lightningFlash", "hook", goal="walkTo(player, road), cast(player, lightningFlash, mule).")
        ops = ops_text(plans)
        assert "opBlow(mule,blast,mule,ridge)" in ops and "opGrant(mule,mule,silenced)" in ops
        self._record(True, "P5: lit on the ridge, the keg is spent")

    def test_property_p6_the_ent_never_walks_or_flies(self):
        for a, b in [("hook", "blindingFlash"), ("taunt", "lightningFlash"), ("turnToMist", "vortex")]:
            assert "opForcedMove(player,ent" not in ops_text(plans_with(a, b))
            assert "opForcedMove(mage,ent" not in ops_text(plans_with(a, b))
        self._record(True, "P6: the ent is never moved to another area")


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
