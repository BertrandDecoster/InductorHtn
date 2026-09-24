"""Tests for the Cold Shoulder level."""

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
POOL = ["hook", "taunt", "blindingFlash", "lightningFlash", "fireball", "tidalWave", "shieldBash"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        # lure the troll to imp1 with a taunt, then lead it on to the kiln
        # and set it off again: a flash from inside, a jolt from next door
        ("taunt", "blindingFlash"), ("taunt", "lightningFlash"),
        # lure it to imp1; imp2 goes over the lip: knocked in, or hooked across
        ("taunt", "fireball"), ("taunt", "tidalWave"), ("taunt", "shieldBash"), ("taunt", "hook"),
        # hook imp1 into the cave (or onto its ice), set the troll off where it
        # stands, hook imp2 across the lip
        ("hook", "blindingFlash"), ("hook", "lightningFlash"),
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


class ColdShoulderTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_lure_it_then_lead_it_on(self):
        ops = ops_list(plans_with("taunt", "blindingFlash")[0])
        for op in ["opCast(player,taunt,troll)", "opNavigate(troll,hall,forge)",
                   "opExploit(troll,imp1,chilled,dead)", "opNavigate(player,forge,kiln)",
                   "opNavigate(troll,forge,kiln)", "opCast(mage,blindingFlash,mage)",
                   "opExploit(troll,imp2,chilled,dead)"]:
            assert op in ops, f"missing {op}"
        assert ops.index("opNavigate(troll,forge,kiln)") < ops.index("opCast(mage,blindingFlash,mage)")
        self._record(True, "Example 1: taunt it to the forge, lead it to the kiln, flash it")

    def test_example_2_gather_then_jolt(self):
        ops = ops_text(plans_with("hook", "lightningFlash"))
        for op in ["opForcedMove(player,imp1,forge,hall)", "opForcedMove(player,imp1,hall,cave)",
                   "opCast(mage,lightningFlash,troll)", "opExploit(troll,imp1,chilled,dead)",
                   "opFall(player,imp2,kiln,cave)", "opExploit(player,imp2,gap,fell)"]:
            assert op in ops, f"missing {op}"
        self._record(True, "Example 2: hook imp1 into the cave, jolt the troll, hook imp2 over the lip")

    def test_example_3_breathe_first_then_hook_onto_the_ice(self):
        late = [ops_list(p) for p in plans_with("hook", "blindingFlash")
                if "opExploit(player,imp1,chilled,dead)" in ops_list(p)]
        assert late, "no plan hooks imp1 onto the ice"
        ops = late[0]
        assert ops.index("opSpill(troll,cave,iceSheet)") < ops.index("opForcedMove(player,imp1,hall,cave)")
        self._record(True, "Example 3: flash the troll in its cave, then hook the imp onto the ice")

    def test_example_4_over_the_lip(self):
        ops = ops_text(plans_with("taunt", "fireball"))
        for op in ["opExploit(troll,imp1,chilled,dead)", "opCast(mage,fireball,imp2)",
                   "opFall(mage,imp2,kiln,cave)"]:
            assert op in ops, f"missing {op}"
        self._record(True, "Example 4: taunt the troll to the forge, fireball imp2 into the gap")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_mood_once(self):
        """The troll answers a taunt once: two taunts cannot reach both imps."""
        assert not plans_with("taunt", "taunt")
        self._record(True, "P3: a second taunt does nothing")

    def test_property_p4_a_stunned_troll_never_breathes(self):
        assert not plans_with("taunt", "blindingFlash", "tag(troll, stunned).\n")
        self._record(True, "P4: stunned (silenced), the troll breathes no more")

    def test_property_p5_a_soaked_imp_only_freezes_on_the_ice(self):
        """Soaked, an imp that arrives on the ice freezes over (stunned) instead of dying: only
        the breath itself (raw) kills it."""
        plans = plans_with("hook", "blindingFlash", "tag(imp1, wet).\n")
        assert plans
        text = ops_text(plans)
        assert "opExploit(player,imp1,chilled,dead)" not in text
        assert "opExploit(troll,imp1,chilled,dead)" in text
        self._record(True, "P5: a soaked imp must be caught in the breath itself")

    def test_property_p6_fire_melts_the_ice(self):
        plans = plans_with("hook", "fireball", "onEnter(forge, iceSheet).\n",
                           goal="cast(mage, fireball, imp1).")
        assert plans and "opReshape(mage,forge,iceSheet,puddle)" in ops_text(plans)
        self._record(True, "P6: a fireball on an iced room leaves a puddle")


def run_tests():
    suite = ColdShoulderTest()
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
