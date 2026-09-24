"""Tests for the Drowned Knight level."""

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
POOL = ["taunt", "turnToMist", "fireball", "shieldBash", "vortex", "hook", "blink",
        "lightningFlash"]

# The measured matrix (htn_components combos): the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        # drown it: taunt it into the lock, and open the sluice
        ("taunt", "fireball"), ("taunt", "shieldBash"), ("taunt", "vortex"),
        ("taunt", "blink"), ("taunt", "lightningFlash"),
        # drop it: mist, then knock it into the moat or the drop
        ("turnToMist", "fireball"), ("turnToMist", "shieldBash"), ("turnToMist", "vortex"),
        ("turnToMist", "hook"),
    ]
}


def _op_text(op):
    name = list(op.keys())[0]
    args = [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]
    return f"{name}({','.join(args)})"


def plans_with(player, mage):
    """Every winning plan, as lists of operator strings, with the player knowing
    `player` and the mage `mage` - on a fresh planner (a failed search locks the
    rule set)."""
    with open(os.path.join(HERE, "level.htn"), encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^knows\((player|mage), \w+\)\.\n", "", text, flags=re.M)
    planner = HtnPlanner(False)
    planner.SetMemoryBudget(512 * 1024 * 1024)
    loader = ComponentLoader(planner, ROOT)
    loader.load("abilities/goals/neutralize")
    loader.load("abilities/primitives/ab_catalog")
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    error, result = planner.FindAllPlansCustomVariables("win.")
    assert error is None, error
    sols = json.loads(result)
    if not sols or (isinstance(sols[0], dict) and "false" in sols[0]):
        return []
    return [[_op_text(op) for op in sol] for sol in sols]


def before(plan, first, then):
    return first in plan and then in plan and plan.index(first) < plan.index(then)


class DrownedKnightTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_lure_then_knock_the_counterweight(self):
        plans = plans_with("taunt", "fireball")
        ok = any(before(p, "opNavigate(knight,causeway,lock)", "opKnock(mage,counterweight,sluiceGate)")
                 and "opExploit(mage,knight,deepWater,fell)" in p for p in plans)
        assert ok, "the knight should walk into the lock, and the fireball knock the counterweight onto the sluice"
        self._record(True, "Example 1: taunted into the lock, the sluice opened by a fireball: it sinks")

    def test_example_2_lure_then_blink_to_the_sluice(self):
        plans = plans_with("taunt", "blink")
        ok = any("opTeleport(mage,gate,sluice)" in p and "opStepOn(mage,mage,sluiceGate)" in p
                 and "opExploit(mage,knight,deepWater,fell)" in p for p in plans)
        assert ok, "the mage should blink through the wall and step on the sluice"
        self._record(True, "Example 2: a blink through the gatehouse wall, a step on the sluice")

    def test_example_3_mist_then_hook_across_the_drop(self):
        plans = plans_with("turnToMist", "hook")
        ok = any(before(p, "opCast(player,turnToMist,knight)", "opFall(mage,knight,keep,tower)")
                 for p in plans)
        assert ok, "the mage should hook the misted knight across the drop from the tower"
        self._record(True, "Example 3: mist the knight, hook it across the drop from the tower")

    def test_example_4_open_the_sluice_in_the_wind_up(self):
        """Taunted, the knight walks into the lock and winds up a slam on its
        taunter: the sluice opened in that window sinks it before the blow."""
        plans = plans_with("taunt", "fireball")
        ok = any(before(p, "opWindUp(knight,groundSlam,player)", "opKnock(mage,counterweight,sluiceGate)")
                 and "opMiss(knight,groundSlam,player)" in p for p in plans)
        assert ok, "a plan should open the sluice in the slam's wind-up"
        self._record(True, "Example 4: the sluice opened in the slam's wind-up; the blow never lands")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_nine_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        assert plans_with("taunt", "vortex") and plans_with("vortex", "taunt")
        assert plans_with("turnToMist", "shieldBash") and plans_with("shieldBash", "turnToMist")
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_misted_it_does_not_drown(self):
        plans = plans_with("turnToMist", "fireball")
        assert plans and not any("deepWater" in " ".join(p) for p in plans)
        self._record(True, "P4: once misted, only the moat or the drop takes the knight")

    def test_property_p5_heavy_it_cannot_be_moved(self):
        """Hooked while heavy, the knight drags the hooker onto the keep; a
        taunt alone only walks it about: neither drops it."""
        assert not plans_with("hook", "fireball") and not plans_with("hook", "taunt")
        self._record(True, "P5: heavy, the knight is neither hooked nor knocked anywhere")

    def test_property_p6_the_flood_needs_the_knight_in_the_lock(self):
        """Every drowning floods the lock after the knight walked in."""
        for kit in [("taunt", "fireball"), ("taunt", "lightningFlash"), ("vortex", "taunt")]:
            for p in plans_with(*kit):
                if "opSpill(" in " ".join(p) and "deepWater" in " ".join(p):
                    spill = next(o for o in p if o.startswith("opSpill(") and "deepWater" in o)
                    assert before(p, "opNavigate(knight,causeway,lock)", spill), p
        self._record(True, "P6: the sluice is opened only once the knight stands in the lock")


def run_tests():
    suite = DrownedKnightTest()
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
