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
POOL = ["taunt", "blindingFlash", "hook", "vortex", "tidalWave", "fireball"]

# The measured matrix: the pairs that win, and nothing else does.
WINNING = {
    frozenset(p) for p in [
        # a taunt lures the troll into a room with both imps; a friend gets the
        # taunter out: a hook, a fireball that knocks it clear, or a vortex
        # that draws everyone out and then back onto the ice
        ("taunt", "hook"), ("taunt", "fireball"), ("taunt", "vortex"),
        # gather (or breathe first and deliver onto the ice), then a flash
        ("blindingFlash", "hook"), ("blindingFlash", "vortex"), ("blindingFlash", "tidalWave"),
        ("blindingFlash", "fireball"),
    ]
}


def _solutions(planner, goal):
    error, result = planner.FindAllPlansCustomVariables(goal)
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    return solutions


def plans_with(player, mage, extra=""):
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
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n" + extra
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


class ColdShoulderTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_breathe_first_then_hook_the_other_imp_onto_the_ice(self):
        plans = plans_with("hook", "blindingFlash")
        late = [p for p in plans if "opBlow(troll,frostBreath,cave,cave)" in ops_list(p)
                and any(o.startswith("opExploit(player,imp") for o in ops_list(p))]
        assert late, "no plan delivers an imp onto the ice after the breath"
        ops = ops_list(late[0])
        assert ops.index("opCast(mage,blindingFlash,mage)") < ops.index("opSpill(troll,cave,iceSheet)")
        self._record(True, "Example 1: flash the troll in its cave, hook the second imp onto the ice")

    def test_example_2_fireball_the_imp_over_taunt_knock_the_taunter_clear(self):
        ops = ops_text(plans_with("fireball", "taunt"))
        for op in ["opForcedMove(player,imp1,forge,kiln)", "opCast(mage,taunt,troll)",
                   "opForcedMove(mage,troll,cave,kiln)", "opWindUp(troll,frostBreath,kiln)",
                   "opCast(player,fireball,mage)", "opForcedMove(player,mage,kiln,cave)",
                   "opExploit(troll,imp1,chilled,dead)", "opExploit(troll,imp2,chilled,dead)",
                   "opReshape(troll,kiln,flames,puddle)"]:
            assert op in ops, f"missing {op}"
        self._record(True, "Example 2: fireball imp1 into the kiln, taunt, fireball the taunter clear")

    def test_example_3_vortex_out_and_back_onto_the_ice(self):
        ops = ops_text(plans_with("taunt", "vortex"))
        for op in ["opCast(player,taunt,troll)", "opWindUp(troll,frostBreath,hall)",
                   "opCast(mage,vortex,gate)", "opForcedMove(mage,player,hall,gate)",
                   "opBlow(troll,frostBreath,hall,hall)", "opCast(mage,vortex,hall)",
                   "opExploit(mage,imp1,chilled,dead)", "opExploit(mage,imp2,chilled,dead)"]:
            assert op in ops, f"missing {op}"
        self._record(True, "Example 3: vortex everyone out of the breath, then the imps back onto the ice")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_the_taunter_is_always_answered(self):
        """In every taunt plan, the other companion casts between the wind-up and the breath."""
        for other in ["hook", "fireball", "vortex"]:
            for p in plans_with("taunt", other):
                ops = ops_list(p)
                w = next(i for i, o in enumerate(ops) if o.startswith("opWindUp(troll"))
                b = next(i for i, o in enumerate(ops) if o.startswith("opBlow(troll"))
                assert any(o.startswith(f"opCast(mage,{other},") for o in ops[w:b]), ops
        self._record(True, "P3: a taunter is always got out in the window")

    def test_property_p4_the_ice_stays(self):
        """Some winning plans kill an imp by delivering it onto the ice after the breath."""
        ops = ops_text(plans_with("fireball", "blindingFlash"))
        assert "opExploit(player,imp1,chilled,dead)" in ops
        self._record(True, "P4: an imp sent onto the ice later dies there")

    def test_property_p5_a_soaked_imp_only_freezes_on_the_ice(self):
        """Soaked, an imp that arrives on the ice freezes over (water meets cold) instead of
        dying: no plan kills it by arrival any more; only the breath itself does."""
        plans = plans_with("hook", "blindingFlash", "tag(imp1, wet).\n")
        assert plans
        assert "opExploit(player,imp1," not in ops_text(plans)
        self._record(True, "P5: a soaked imp must be in the breath itself")

    def test_property_p6_taunt_alone_is_a_trap(self):
        """With a flash, a taunt cannot be answered: the taunter stays in the breath."""
        assert not plans_with("taunt", "blindingFlash") and not plans_with("taunt", "tidalWave")
        self._record(True, "P6: taunt with a flash or a wave: no plan")


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
