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
POOL = ["sunder", "gust", "taunt", "magnetize", "rainCall", "zap", "pounce", "translocate"]

# The measured matrix (htn_components combos): these pairs win, whichever
# companion holds which half, and nothing else does.
WINNING = {frozenset(p) for p in [
    ("sunder", "gust"), ("sunder", "magnetize"), ("sunder", "taunt"), ("sunder", "translocate"),
    ("rainCall", "zap"),
    ("pounce", "translocate"), ("magnetize", "translocate"),
]}


def plans_with(player, mage, goal="win."):
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
    error, result = planner.FindAllPlansCustomVariables(goal)
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


class EscortScholarTest(HtnTestSuite):

    def setup(self):
        for i, dep in enumerate(Manifest.load(os.path.join(HERE, "manifest.json")).dependencies):
            self.load_component(dep, reset_first=(i == 0))
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_strip_and_lure(self):
        self.assert_plan("win.", contains=[
            "opCast(player, sunder, brute)", "opForcedMove(mage, brute, hall, balcony)",
            "opNavigate(scholar, hall, exit)"])

    def test_example_2_soak_and_jolt(self):
        plans = plans_with("rainCall", "zap")
        assert plans and all(has(p, "opCast(player,rainCall,brute)",
                                 "opExploit(mage,brute,electrocuted,dead)",
                                 "opNavigate(scholar,hall,exit)") for p in plans)
        self._record(True, "Example 2: rain, then a jolt, short-circuits the brute; the scholar walks")

    def test_example_3_swap_across(self):
        plans = plans_with("pounce", "translocate")
        assert plans and all(has(p, "opSwap(mage,player,balcony,exit)",
                                 "opSwap(mage,scholar,exit,balcony)") for p in plans)
        assert any("opDash(player,balcony,exit)" in p for p in plans)
        self._record(True, "Example 3: a pounce over the gap, a swap to follow, a swap to bring the scholar")

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

    def test_property_p3_never_lure_it_onto_the_scholar(self):
        """A taunted brute slams where it lands: taunted from the library, it
        would stun the scholar. Every taunt plan lures it onto the balcony."""
        trap = plans_with("sunder", "taunt",
                          "cast(player, sunder, brute), castFrom(mage, taunt, brute, library).")
        assert trap and "opGrant(brute,scholar,stunned)" in trap[0], trap
        plans = plans_with("sunder", "taunt")
        assert plans
        for p in plans:
            assert "opForcedMove(mage,brute,hall,balcony)" in p, p
            assert "opGrant(brute,scholar,stunned)" not in p, p
        self._record(True, "P3: the brute is always lured away from the scholar")

    def test_property_p4_the_scholar_is_never_dragged(self):
        """Dragging the scholar over the gap drops it: it walks, or it is swapped."""
        for a, b in [("magnetize", "translocate"), ("pounce", "translocate"), ("sunder", "magnetize")]:
            for p in plans_with(a, b):
                assert not any(op.startswith("opForcedMove") and ",scholar," in op for op in p), p
        self._record(True, "P4: the scholar is never moved by a push or a pull")


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
