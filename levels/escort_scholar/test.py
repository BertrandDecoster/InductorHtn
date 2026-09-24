"""Tests for The Scholar (escort) level."""

import itertools
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from htn_components.combos import ComboSpec, _plan
from htn_components.manifest import Manifest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
POOL = ["turnToMist", "fireball", "shieldBash", "vortex", "hook", "lightningFlash", "blizzard"]

# The measured matrix (htn_components combos): these pairs win, whichever
# companion holds which half, and nothing else does. Mist with anything that
# moves the brute; the blizzard with anything that puts its eye out.
MOVERS = ["fireball", "shieldBash", "vortex", "hook"]
WINNING = ({frozenset(("turnToMist", m)) for m in MOVERS}
           | {frozenset(("blizzard", "shieldBash")), frozenset(("blizzard", "lightningFlash"))})


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


class EscortScholarTest(HtnTestSuite):

    def setup(self):
        for i, dep in enumerate(Manifest.load(os.path.join(HERE, "manifest.json")).dependencies):
            self.load_component(dep, reset_first=(i == 0))
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_mist_and_fireball_twice(self):
        """The fireball sets the brute alight: its slam winds up on the
        library, and the second fireball knocks it down the shaft."""
        self.assert_plan("win.", contains=[
            "opCast(player, turnToMist, brute)", "opWindUp(brute, groundSlam, library)",
            "opKnock(mage, brute, shaft)", "opExploit(mage, brute, chasm, fell)",
            "opMiss(brute, groundSlam, library)", "opNavigate(scholar, hall, exit)"],
            not_contains=["opBlow"])

    def test_example_2_mist_and_hook(self):
        plans = plans_with("turnToMist", "hook")
        assert plans and all(has(p, "opCast(player,turnToMist,brute)", "opCast(mage,hook,brute)",
                                 "opForcedMove(mage,brute,hall,library)",
                                 "opNavigate(scholar,hall,exit)") for p in plans)
        self._record(True, "Example 2: the misted brute is hooked out of the doorway")

    def test_example_3_jolt_the_eye_and_ice_the_cistern(self):
        plans = plans_with("lightningFlash", "blizzard")
        assert plans and all(has(p, "opExploit(player,brute,electrocuted,stunned)",
                                 "opDash(player,library,hall)",
                                 "opNavigate(mage,cistern,exit)", "opCast(mage,blizzard,cistern)",
                                 "opNavigate(scholar,balcony,cistern)",
                                 "opNavigate(scholar,cistern,exit)") for p in plans)
        self._record(True, "Example 3: the jolt stuns the eye; the blizzard from the exit ices the cistern")

    def test_example_4_mist_and_vortex(self):
        plans = plans_with("turnToMist", "vortex")
        assert plans and all(has(p, "opCast(mage,vortex,shaft)", "opKnock(mage,brute,shaft)")
                             for p in plans)
        self._record(True, "Example 4: a vortex on the shaft takes the misted brute")

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

    def test_property_p3_the_slam_never_lands(self):
        for a, b in WINNING:
            for p in plans_with(a, b):
                assert not any(op.startswith("opBlow") for op in p), p
        self._record(True, "P3: no winning plan lets the slam fall on the library")

    def test_property_p4_the_scholar_walks_on_ice(self):
        """On the long way round, the scholar steps into the cistern only once it
        is iced; it is never moved by force."""
        for a, b in WINNING:
            for p in plans_with(a, b):
                assert not any(op.startswith(("opForcedMove", "opFall")) and ",scholar," in op
                               for op in p), p
                if "opNavigate(scholar,balcony,cistern)" in p:
                    ice = next(i for i, op in enumerate(p) if op.endswith(",blizzard,cistern)"))
                    assert ice < p.index("opNavigate(scholar,balcony,cistern)"), p
        self._record(True, "P4: the scholar walks; it wades only on the ice")

    def test_property_p5_two_companions_cast(self):
        for a, b in WINNING:
            for p in plans_with(a, b):
                assert casters(p) == {"player", "mage"}, p
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
