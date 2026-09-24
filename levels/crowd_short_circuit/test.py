"""Tests for the Short Circuit level (crowd control)."""

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
POOL = ["tidalWave", "vortex", "taunt", "hook", "lightningFlash", "blindingFlash"]

# The measured matrix (htn_components combos: 12 of 36).
#   short: a soak (wave, or a herd into the flooded sump) and one lightning flash down the hall;
#   drop:  the ogre's cave-in on the drones - taunt it into the yard and be hooked out, or
#          vortex drones and ogre into the sump and dazzle it.
SHORT = {frozenset((s, "lightningFlash")) for s in ["tidalWave", "vortex", "taunt", "hook"]}
DROP = {frozenset(("taunt", "hook")), frozenset(("vortex", "blindingFlash"))}
WINNING = SHORT | DROP
START = {"player": "gate", "mage": "gate"}


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


def op_list(plan):
    """[(name, [args])] for one plan."""
    out = []
    for op in plan:
        name = list(op.keys())[0]
        out.append((name, [list(a.keys())[0] if isinstance(a, dict) else str(a) for a in op[name]]))
    return out


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


class ShortCircuitTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_vortex_into_the_sump_then_one_flash(self):
        self.assert_plan("win.", contains=[
            "opCast(player, vortex, sump)", "opForcedMove(player, cog1, yard, sump)",
            "opGrant(player, cog3, wet)", "opCast(mage, lightningFlash, forge)",
            "opExploit(mage, cog1, electrocuted, dead)", "opExploit(mage, cog3, electrocuted, dead)",
            "opDash(mage, gate, forge)"])

    def test_example_2_a_wave_in_place_or_into_the_sump(self):
        plans = plans_with("tidalWave", "lightningFlash")
        ops = [op_list(p) for p in plans]
        washed = [o for o in ops if ("opForcedMove", ["player", "cog1", "yard", "sump"]) in o]
        in_place = [o for o in ops if not any(n == "opForcedMove" for n, _ in o)]
        assert washed and in_place, "the wave from the gate washes them in; from the yard it soaks in place"
        self._record(True, "Example 2: soak in place or wash into the sump; one flash takes all three")

    def test_example_3_taunt_the_ogre_and_be_hooked_out(self):
        plans = plans_with("taunt", "hook")
        assert plans
        ops = op_list(plans[0])
        assert ("opWindUp", ["ogre", "caveIn", "yard"]) in ops
        assert ("opForcedMove", ["mage", "player", "yard", "gate"]) in ops
        assert ("opSpill", ["ogre", "yard", "chasm"]) in ops
        assert all(("opExploit", ["ogre", c, "chasm", "fell"]) in ops for c in ("cog1", "cog2", "cog3"))
        self._record(True, "Example 3: the ogre stamps the yard through; the taunter is hooked out")

    def test_example_4_gather_and_dazzle(self):
        plans = plans_with("vortex", "blindingFlash")
        spots = set()
        for plan in plans:
            ops = op_list(plan)
            assert ("opForcedMove", ["player", "ogre", "forge", "sump"]) in ops
            i = next(i for i, (n, _) in enumerate(ops) if n == "opCast" and _[1] == "blindingFlash")
            spots.add(where(ops[:i], START)[0]["mage"])
        assert spots == {"yard", "forge"}, f"the flash comes from next door, never the sump: {spots}"
        self._record(True, "Example 4: the vortex draws drones and ogre into the sump; flash from next door")

    def test_example_5_traps(self):
        assert not plans_with("lightningFlash", "lightningFlash"), "dry drones are only stunned"
        assert not plans_with("taunt", "taunt"), "companions cannot be taunted out"
        assert not plans_with("taunt", "tidalWave"), "the wave washes the drones out with the taunter"
        assert not plans_with("hook", "blindingFlash"), "the hooker is caught in the cave-in"
        self._record(True, "Example 5: two bolts, two taunts, wave rescue, hook + flash")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_six_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_each_hand_matters(self):
        for a, b in [tuple(p) for p in WINNING]:
            assert plans_with(a, b) and plans_with(b, a), f"{a}+{b}"
        self._record(True, "P3: the pairs win whichever companion holds which half")

    def test_property_p4_one_blow(self):
        """Every winning plan takes all three drones with one blow - one flash, or one
        cave-in - and nobody on the team is under the cave-in, stunned or fallen."""
        for a, b in [tuple(p) for p in WINNING]:
            for plan in plans_with(a, b):
                ops = op_list(plan)
                bolts = [1 for n, args in ops if n == "opCast" and args[1] == "lightningFlash"]
                blows = [args for n, args in ops if n == "opBlow"]
                assert len(bolts) + len(blows) == 1, f"{a}+{b}"
                for i, (n, args) in enumerate(ops):
                    if n == "opBlow":
                        pos, phased = where(ops[:i], START)
                        assert not [c for c in pos if pos[c] == args[3] and c not in phased], f"{a}+{b}"
                hurt = [args for n, args in ops if n == "opGrant" and args[1] in START
                        and args[2] in ("stunned", "fell", "dead")]
                assert not hurt, f"{a}+{b}: {hurt}"
        self._record(True, "P4: one flash or one cave-in takes the crowd; the team walks away")


def run_tests():
    suite = ShortCircuitTest()
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
