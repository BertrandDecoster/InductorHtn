"""Tests for the Powder Keg level (crowd control)."""

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
POOL = ["tidalWave", "vortex", "hook", "taunt", "fireball", "blindingFlash"]

# The measured matrix (htn_components combos: 14 of 36).
#   keg:    a mover brings the keg down to the rooted crowd, and a fireball lights it;
#   meteor: taunt the priest from the grove and be pulled out in the wind-up (hook,
#           vortex), or gather the priest into the grove and dazzle it (vortex + flash).
KEG = {frozenset((m, "fireball")) for m in ["tidalWave", "vortex", "hook", "taunt"]}
METEOR = {frozenset(p) for p in [("taunt", "hook"), ("taunt", "vortex"), ("vortex", "blindingFlash")]}
WINNING = KEG | METEOR


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


def ops_text(plans):
    return " ".join(json.dumps(p) for p in plans)


START = {"player": "camp", "mage": "camp"}


def where(ops, start):
    """Each companion's region after `ops`, and who is disjoint right then."""
    pos, phased = dict(start), set()
    for n, args in ops:
        if n in ("opNavigate", "opDash", "opTeleport") and args[0] in pos:
            pos[args[0]] = args[2]
        elif n == "opForcedMove" and args[1] in pos:
            pos[args[1]] = args[3]
        elif n == "opGrant" and args[2] == "disjoint":
            phased.add(args[1])
        elif n == "opRemove" and args[2] == "disjoint":
            phased.discard(args[1])
    return pos, phased


def op_list(plan):
    """[(name, [args])] for one plan."""
    out = []
    for op in plan:
        name = list(op.keys())[0]
        out.append((name, [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]))
    return out


class PowderKegTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_roll_the_keg_down_then_light_it(self):
        self.assert_plan("win.", contains=[
            "opCast(player, tidalWave, player)", "opForcedMove(player, keg, ramp, grove)",
            "opCast(mage, fireball, grove)", "opReact(mage, keg, oiled, burning, blaze)",
            "opExploit(mage, t1, burning, dead)", "opExploit(mage, t3, burning, dead)"])

    def test_example_2_taunt_the_priest_and_be_hooked_out(self):
        plans = plans_with("taunt", "hook")
        assert plans
        ops = op_list(plans[0])
        assert ("opWindUp", ["priest", "meteor", "grove"]) in ops
        assert ("opCast", ["mage", "hook", "player"]) in ops
        assert ("opForcedMove", ["mage", "player", "grove", "camp"]) in ops
        assert ("opBlow", ["priest", "meteor", "grove", "grove"]) in ops
        assert ("opExploit", ["priest", "t2", "burning", "dead"]) in ops
        self._record(True, "Example 2: the priest winds up on the grove; the hook pulls the taunter out")

    def test_example_3_gather_and_dazzle(self):
        plans = plans_with("vortex", "blindingFlash")
        ops = ops_text(plans)
        assert plans and '"priest"' in ops and "opMiss" not in ops
        for plan in plans:
            o = op_list(plan)
            assert ("opForcedMove", ["player", "priest", "shrine", "grove"]) in o
            assert ("opProvoked", ["priest", "blinded", "meteor"]) in o
        self._record(True, "Example 3: the vortex draws keg and priest in; a flash sets the meteor off")

    def test_example_4_traps(self):
        assert not plans_with("fireball", "fireball"), "fire lights the keg on the ramp, or steams"
        assert not plans_with("taunt", "taunt"), "companions cannot be taunted out"
        assert not plans_with("hook", "blindingFlash"), "the hooker is caught under the meteor"
        assert not plans_with("tidalWave", "vortex"), "two movers light nothing"
        self._record(True, "Example 4: two fires, two taunts, hook + flash, two movers")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_seven_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        for a, b in [tuple(p) for p in WINNING]:
            assert plans_with(a, b) and plans_with(b, a), f"{a}+{b}"
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_one_fire_takes_the_crowd(self):
        """Every winning plan burns the whole crowd in one go - a blaze or a meteor - and no
        meteor lands on a companion."""
        for a, b in [tuple(p) for p in WINNING]:
            for plan in plans_with(a, b):
                ops = op_list(plan)
                fires = [n for n, args in ops if (n == "opReact" and args[-1] == "blaze") or n == "opBlow"]
                deaths = [args[1] for n, args in ops if n == "opExploit" and args[-1] == "dead"]
                assert len(fires) == 1 and sorted(deaths) == ["t1", "t2", "t3"], f"{a}+{b}"
                for i, (n, args) in enumerate(ops):
                    if n == "opBlow":
                        pos, phased = where(ops[:i], START)
                        caught = [c for c in ("player", "mage") if pos[c] == args[3] and c not in phased]
                        assert not caught, f"{a}+{b}: {caught} under the blow"
        self._record(True, "P4: one blaze or one meteor burns all three; nobody is left under it")

    def test_property_p5_the_meteor_needs_a_second_hand(self):
        """The meteor route always has a wind-up answered, or a flash, by the companion who
        did not bring the priest."""
        for a, b in [tuple(p) for p in METEOR]:
            for plan in plans_with(a, b):
                ops = op_list(plan)
                assert any(n == "opWindUp" for n, _ in ops), f"{a}+{b}"
                casters = {args[0] for n, args in ops if n == "opCast"}
                assert casters == {"player", "mage"}, f"{a}+{b}: {casters}"
        self._record(True, "P5: every meteor plan needs both companions")


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
