"""Tests for the Sync: Decoy level."""

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
LURES = ["hook", "fireball", "vortex"]
BLINDERS = ["blindingFlash", "shieldBash"]
RESCUERS = ["hook", "fireball", "vortex", "tidalWave"]
POOL = ["taunt", "hook", "fireball", "vortex", "tidalWave", "blindingFlash", "shieldBash"]

# The measured matrix: the taunt with each rescuer; each lure with each blinder.
WINNING = ({frozenset(("taunt", r)) for r in RESCUERS}
           | {frozenset((a, b)) for a in LURES for b in BLINDERS})


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


def index(plan, name, *args):
    return plan.index((name, tuple(args)))


class SyncDecoyTest(HtnTestSuite):

    def setup(self):
        self.load_component("abilities/goals/neutralize", reset_first=True)
        self.load_component("abilities/primitives/ab_catalog", reset_first=False)
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_bait_the_slam_and_hook_the_decoy_out(self):
        self.assert_plan("win.", contains=[
            "opNavigate(player, nook, balcony)", "opCast(player, taunt, golem)",
            "opForcedMove(player, golem, arch, balcony)", "opWindUp(golem, groundSlam, balcony)",
            "opCast(mage, hook, player)", "opForcedMove(mage, player, balcony, camp)",
            "opBlow(golem, groundSlam, balcony, balcony)", "opGrant(golem, eye, stunned)",
            "opNavigate(mage, arch, switch)", "opOpen(mage, portcullis)"])

    def test_example_2_the_vortex_takes_the_decoy_and_the_golem(self):
        plans = plans_with("vortex", "taunt")
        assert has(plans, "opCast", "player", "vortex", "nook"), plans[:1]
        assert has(plans, "opForcedMove", "player", "mage", "balcony", "nook")
        assert has(plans, "opForcedMove", "player", "golem", "balcony", "nook")
        assert has(plans, "opGrant", "golem", "eye", "stunned")
        assert has(plans, "opOpen", "player", "portcullis")
        self._record(True, "Example 2: the vortex sucks the decoy and the golem off the balcony; "
                           "the eye takes the slam")

    def test_example_3_thrown_into_the_alcove_then_bashed(self):
        plans = plans_with("fireball", "shieldBash")
        assert has(plans, "opForcedMove", "player", "golem", "arch", "alcove"), plans[:1]
        assert has(plans, "opCast", "mage", "shieldBash", "eye")
        assert not has(plans, "opWindUp", "golem", "groundSlam", "balcony")
        self._record(True, "Example 3: the fireball throws the golem aside; the bash stuns the eye")

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
        assert plans_with("tidalWave", "taunt") and plans_with("taunt", "tidalWave")
        assert plans_with("shieldBash", "vortex") and plans_with("vortex", "shieldBash")
        self._record(True, "P3: a pair wins whichever companion holds which half")

    def test_property_p4_the_rescue_is_the_one_cast_in_the_window(self):
        """In every taunt plan the slam is wound up on the balcony, and the
        other companion's cast falls between the wind-up and the blow."""
        for rescuer in RESCUERS:
            plans = plans_with("taunt", rescuer)
            assert plans, rescuer
            for plan in plans:
                up = index(plan, "opWindUp", "golem", "groundSlam", "balcony")
                blow = index(plan, "opBlow", "golem", "groundSlam", "balcony", "balcony")
                window = [args for name, args in plan[up:blow] if name == "opCast"]
                assert window and window[0][0] == "mage" and window[0][1] == rescuer, (rescuer, window)
        self._record(True, "P4: the slam lands on the eye; the friend's one cast saves the decoy")

    def test_property_p5_a_flash_saves_only_its_caster(self):
        """blindingFlash is disjoint for its caster alone: it cannot pull the
        decoy out of the slam, so taunt + blindingFlash has no plan."""
        assert not plans_with("taunt", "blindingFlash")
        assert not plans_with("taunt", "shieldBash")
        self._record(True, "P5: a flash or a bash cannot save the decoy from a physical slam")

    def test_property_p6_companions_cannot_be_taunted(self):
        self.assert_query("receptive(mage, taunted).", min_solutions=0, max_solutions=0)
        self._record(True, "P6: a taunt never drags a friend out of the blast")


def run_tests():
    suite = SyncDecoyTest()
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
