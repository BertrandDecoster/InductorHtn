"""Tests for the Sync: Vault level."""

import functools
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
ISLAND = ["blink", "lightningFlash", "hook"]
FORGE = ["fireball", "vortex", "taunt"]
POOL = ISLAND + FORGE

# The measured matrix: each island skill with each forge skill.
WINNING = {frozenset((a, b)) for a in ISLAND for b in FORGE}


@functools.lru_cache(maxsize=None)
def plans_with(player, mage):
    """All winning plans (lists of (operator, args)) with the player knowing `player` and
    the mage `mage`, on a fresh planner (a failed search locks the rule set)."""
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
    error, result = planner.FindAllPlansCustomVariables("win.")
    assert error is None, error
    solutions = json.loads(result)
    if not solutions or (isinstance(solutions[0], dict) and "false" in solutions[0]):
        return []
    plans = []
    for sol in solutions:
        plan = []
        for op in sol:
            name = list(op.keys())[0]
            plan.append((name, tuple(list(a.keys())[0] if isinstance(a, dict) else str(a)
                                     for a in op[name])))
        plans.append(plan)
    return plans


def has(plans, name, *args):
    return any((name, tuple(args)) in plan for plan in plans)


class SyncVaultTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/strategies/passage", reset_first=False)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_blink_to_the_island_fireball_the_barrel(self):
        self.assert_plan("win.", contains=[
            "opCast(player, blink, island)", "opTeleport(player, rim, island)",
            "opStepOn(player, player, islandPlate)", "opCast(mage, fireball, barrel)",
            "opKnock(mage, barrel, forgePlate)", "opOpen(mage, vaultdoor)",
            "opNavigate(mage, hall, vault)"])

    def test_example_2_hook_the_pillar_taunt_the_warden(self):
        plans = plans_with("hook", "taunt")
        assert has(plans, "opCast", "player", "hook", "pillar"), plans[:1]
        assert has(plans, "opDash", "player", "rim", "island")
        assert has(plans, "opRemove", "mage", "warden", "taunted")
        assert has(plans, "opWindUp", "warden", "groundSlam", "forge")
        assert has(plans, "opKnock", "warden", "barrel", "forgePlate")
        assert has(plans, "opOpen", "warden", "vaultdoor")
        self._record(True, "Example 2: hooked over the rift; the walled-in warden cannot follow its "
                           "taunter, and its own slam throws the barrel onto the plate")

    def test_example_3_flash_over_vortex_the_plate(self):
        plans = plans_with("lightningFlash", "vortex")
        assert has(plans, "opDash", "player", "rim", "island"), plans[:1]
        assert has(plans, "opCast", "mage", "vortex", "forgePlate")
        assert has(plans, "opKnock", "mage", "barrel", "forgePlate")
        assert not has(plans, "opKnock", "mage", "warden", "forgePlate")
        self._record(True, "Example 3: the player flashes over; the vortex draws the barrel onto "
                           "the plate, the heavy warden stays")

    # -------------------------------------------------------------- properties

    def test_property_p1_no_single_skill_wins(self):
        winners = [s for s in POOL if plans_with(s, s)]
        assert not winners, f"a single skill wins: {winners}"
        self._record(True, "P1: no skill wins alone, even held by both companions")

    def test_property_p2_the_measured_pairs_win(self):
        found = {frozenset((a, b)) for a, b in itertools.combinations(POOL, 2) if plans_with(a, b)}
        assert found == WINNING, f"extra: {found - WINNING}, missing: {WINNING - found}"
        self._record(True, f"P2: exactly the {len(WINNING)} measured pairs win")

    def test_property_p3_either_seat(self):
        assert plans_with("taunt", "hook") and plans_with("hook", "taunt")
        self._record(True, "P3: a pair wins whichever companion holds which half")

    def test_property_p4_the_door_waits_for_both_plates(self):
        """One plate alone does not open the door; the second one pressed does."""
        self.assert_state_after("weighIsland(player).", has=["on(player,islandPlate)"],
                                not_has=["open(vaultdoor)"])
        self.assert_plan("weighIsland(player), weighForge(player).", contains=["opOpen(mage, vaultdoor)"])
        self._record(True, "P4: the door opens only when both plates are held at once")

    def test_property_p5_nobody_sets_foot_in_the_forge(self):
        """Walled and on lava: no companion ever ends up in the forge, and the
        forge plate is only ever pressed by the barrel."""
        for a in ISLAND:
            for b in FORGE:
                for plan in plans_with(a, b):
                    assert not any(n in ("opNavigate", "opTeleport", "opDash") and a2[-1] == "forge"
                                   for n, a2 in plan), (a, b)
                    presses = [a2 for n, a2 in plan if n == "opStepOn" and a2[2] == "forgePlate"]
                    assert all(p[1] == "barrel" for p in presses), presses
        self._record(True, "P5: the forge plate takes the barrel, never a companion")

    def test_property_p6_the_warden_does_not_budge(self):
        """Heavy, the warden stays off the plate whatever knocks it; only the
        barrel goes."""
        for skill in FORGE:
            for plan in plans_with("blink", skill):
                assert not any(n == "opKnock" and a[1] == "warden" for n, a in plan), skill
        self._record(True, "P6: knocks move the barrel, never the warden")

    def test_property_p7_the_island_holder_stays(self):
        """The door opens while the island holder is still on the island plate;
        the other walks into the vault."""
        for a in ISLAND:
            for plan in plans_with(a, "fireball"):
                opened = next(i for i, (n, _) in enumerate(plan) if n == "opOpen")
                assert ("opStepOff", ("player", "player", "islandPlate")) not in plan[:opened]
                assert ("opNavigate", ("mage", "hall", "vault")) in plan[opened:]
        self._record(True, "P7: both plates are held when the door opens")


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
