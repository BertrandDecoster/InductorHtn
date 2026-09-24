"""Tests for The Hostage (escort) level."""

import itertools
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from htn_components.combos import ComboSpec, _plan
from htn_components.manifest import Manifest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
POOL = ["hook", "taunt", "shieldBash", "vortex", "tidalWave", "blindingFlash", "fireball"]

# The measured matrix (htn_components combos): these pairs win, whichever
# companion holds which half, and nothing else does. A mover (hook, taunt)
# with a warlock-stopper; the blinding flash only with a hook to break the
# meteor.
QUIET = ["shieldBash", "vortex", "tidalWave", "fireball"]
WINNING = ({frozenset((m, q)) for m in ("hook", "taunt") for q in QUIET}
           | {frozenset(("hook", "blindingFlash"))})


def plans_with(player, mage):
    """All winning plans (as operator strings, no spaces) with the player knowing
    `player` and the mage `mage`, on a fresh planner (a failed search locks the
    rule set)."""
    spec = ComboSpec.load(HERE)
    res = _plan(ROOT, HERE, spec.stripped(), f"knows(player, {player}).\nknows(mage, {mage}).\n",
                spec.goal)
    assert "error" not in res, res.get("error")
    return [[f"{n}({','.join(a)})" for n, a in plan] for plan in res["plans"]]


def has(plan, *ops):
    return all(op in plan for op in ops)


def casters(plan):
    return {op[len("opCast("):].split(",")[0] for op in plan if op.startswith("opCast(")}


class EscortHostageTest(HtnTestSuite):

    def setup(self):
        for i, dep in enumerate(Manifest.load(os.path.join(HERE, "manifest.json")).dependencies):
            self.load_component(dep, reset_first=(i == 0))
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_bash_and_hook(self):
        self.assert_plan("win.", contains=[
            "opCast(player, shieldBash, warlock)",
            "opCast(mage, hook, hostage)", "opForcedMove(mage, hostage, cell, corridor)",
            "opForcedMove(mage, hostage, corridor, gate)"],
            not_contains=["opWindUp"])

    def test_example_2_blind_him_and_break_the_meteor(self):
        plans = plans_with("blindingFlash", "hook")
        assert plans and all(has(p, "opCast(player,blindingFlash,player)",
                                 "opWindUp(warlock,meteor,cell)",
                                 "opInterrupt(mage,warlock,meteor,cell)",
                                 "opForcedMove(mage,hostage,corridor,gate)") for p in plans)
        self._record(True, "Example 2: the flash raises the alarm; the hook breaks the meteor")

    def test_example_3_burn_him_twice_and_call_it_out(self):
        plans = plans_with("fireball", "taunt")
        assert plans and all(has(p, "opWindUp(warlock,meteor,cell)",
                                 "opExploit(player,warlock,lava,fell)",
                                 "opMiss(warlock,meteor,cell)",
                                 "opCast(mage,taunt,hostage)", "opFollow(mage,hostage)",
                                 "opNavigate(hostage,corridor,gate)") for p in plans)
        for p in plans:
            fires = [i for i, op in enumerate(p) if op == "opCast(player,fireball,warlock)"]
            assert len(fires) == 2 and fires[0] < p.index("opWindUp(warlock,meteor,cell)") < fires[1], p
        self._record(True, "Example 3: the second fireball, in the window, drops him; the hostage follows its caller")

    def test_example_4_the_vortex_drops_him(self):
        plans = plans_with("vortex", "taunt")
        assert plans and all(has(p, "opCast(player,vortex,firepit)",
                                 "opExploit(player,warlock,lava,fell)") for p in plans)
        self._record(True, "Example 4: a vortex on the fire pit from the gate, quietly")

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

    def test_property_p3_an_unanswered_alarm_has_no_plan(self):
        for a, b in [("blindingFlash", "taunt"), ("taunt", "hook"), ("blindingFlash", "shieldBash")]:
            assert not plans_with(a, b), (a, b)
        self._record(True, "P3: a flash with a caller, a taunted warlock: no plan")

    def test_property_p4_the_meteor_never_lands(self):
        for a, b in WINNING:
            for p in plans_with(a, b):
                assert not any(op.startswith("opBlow") for op in p), p
        self._record(True, "P4: no winning plan lets the meteor fall")

    def test_property_p5_the_warlock_first_and_two_hands(self):
        for a, b in WINNING:
            for p in plans_with(a, b):
                assert casters(p) == {"player", "mage"}, p
                enter = [i for i, op in enumerate(p) if op.startswith("opNavigate(") and op.endswith(",gate,corridor)")
                         and "hostage" not in op]
                first_cast = next(i for i, op in enumerate(p) if op.startswith("opCast("))
                assert enter and enter[0] > first_cast, p
        self._record(True, "P5: both companions cast; nobody walks into the corridor before the warlock is dealt with")


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
