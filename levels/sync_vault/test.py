"""Tests for the Sync: Vault level."""

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
ISLAND = ["pounce", "charge", "magnetize", "translocate"]
CLOSET = ["vanish", "flashbang", "net", "gust"]
POOL = ISLAND + CLOSET

# The measured matrix: every island skill with every closet skill, and nothing else.
WINNING = {frozenset((a, b)) for a in ISLAND for b in CLOSET}


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
    for dep in Manifest.load(os.path.join(HERE, "manifest.json")).dependencies:
        loader.load(dep)
    kit = f"knows(player, {player}).\nknows(mage, {mage}).\n"
    assert planner.HtnCompileCustomVariables(text + kit) is None
    return _solutions(planner, "win.")


def ops(plans):
    return " ".join(json.dumps(p) for p in plans).replace(" ", "")


class SyncVaultTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/strategies/passage", reset_first=False)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_pounce_over_blind_the_sentry(self):
        self.assert_plan("win.", contains=[
            "opDash(player, rim, outcrop)", "opCast(mage, flashbang, sentry)",
            "opNavigate(mage, post, closet)", "opOpen(mage, vaultdoor)"])

    def test_example_2_hook_over_shove_the_sentry_onto_the_plate(self):
        text = ops(plans_with("magnetize", "gust"))
        assert '{"opCast":[{"player":[]},{"magnetize":[]},{"pillar":[]}]}' in text, text[:400]
        assert '{"opForcedMove":[{"mage":[]},{"sentry":[]},{"post":[]},{"closet":[]}]}' in text
        self._record(True, "Example 2: the hook drags the player over; the gust puts the sentry on the plate")

    def test_example_3_swap_over_sneak_in(self):
        text = ops(plans_with("vanish", "translocate"))
        assert '{"opSwap":[{"mage":[]},{"barrel":[]},{"rim":[]},{"outcrop":[]}]}' in text
        assert '{"opNavigate":[{"player":[]},{"post":[]},{"closet":[]}]}' in text
        self._record(True, "Example 3: the mage swaps with the barrel; the stealthed player walks in")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_sixteen_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_either_seat(self):
        assert plans_with("gust", "charge") and plans_with("charge", "gust")
        self._record(True, "P3: a pair wins whichever companion holds which half")

    def test_property_p4_the_boss_sentry_is_not_blinded_by_hard_control(self):
        assert not plans_with("charge", "translocate")
        self._record(True, "P4: a stun or a confusion does not blind the boss sentry")

    def test_property_p5_the_door_needs_both_plates(self):
        self.assert_state_after("weighIsland.", not_has=["open(vaultdoor)"])
        self._record(True, "P5: one plate alone leaves the vault shut")


def run_tests():
    suite = SyncVaultTest()
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
