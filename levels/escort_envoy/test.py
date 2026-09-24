"""Tests for The Envoy (escort) level."""

import itertools
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src/Python")))

from htn_test_framework import HtnTestSuite
from htn_components.combos import ComboSpec, _plan
from htn_components.manifest import Manifest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
POOL = ["fireball", "shieldBash", "tidalWave", "hook", "taunt", "turnToMist"]

# The measured matrix (htn_components combos): these pairs win, whichever
# companion holds which half, and nothing else does. Any bridger with the
# taunt; mist with a knock that also bridges.
BRIDGERS = ["fireball", "shieldBash", "tidalWave", "hook"]
WINNING = ({frozenset((b, "taunt")) for b in BRIDGERS}
           | {frozenset(("turnToMist", "fireball")), frozenset(("turnToMist", "shieldBash"))})


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


class EscortEnvoyTest(HtnTestSuite):

    def setup(self):
        for i, dep in enumerate(Manifest.load(os.path.join(HERE, "manifest.json")).dependencies):
            self.load_component(dep, reset_first=(i == 0))
        self.verify_contracts()
        self._loader.load_level_htn(HERE)

    # ---------------------------------------------------------------- examples

    def test_example_1_blast_the_crate_and_lure_the_sentry(self):
        self.assert_plan("win.", contains=[
            "opCast(player, fireball, crate)", "opBridge(player, yard, lawn)",
            "opCast(mage, taunt, sentry)", "opNavigate(sentry, lawn, tower)",
            "opNavigate(envoy, gatehouse, road)"])

    def test_example_2_grapple_over_and_drag_the_crate(self):
        plans = plans_with("hook", "taunt")
        assert plans and all(has(p, "opCast(player,hook,statue)", "opDash(player,yard,lawn)",
                                 "opCast(player,hook,crate)", "opFall(player,crate,yard,lawn)",
                                 "opBridge(player,yard,lawn)") for p in plans)
        self._record(True, "Example 2: the hook grapples to the statue, then drags the crate into the briars")

    def test_example_3_mist_and_bash(self):
        plans = plans_with("turnToMist", "shieldBash")
        assert plans and all(has(p, "opCast(mage,shieldBash,crate)", "opBridge(mage,yard,lawn)",
                                 "opCast(player,turnToMist,sentry)",
                                 "opKnock(mage,sentry,trapdoor)",
                                 "opExploit(mage,sentry,chasm,fell)") for p in plans)
        self._record(True, "Example 3: one bash bridges the briars, a second drops the misted sentry")

    def test_example_4_wash_the_crate_in(self):
        plans = plans_with("tidalWave", "taunt")
        assert plans and all(has(p, "opCast(player,tidalWave,player)",
                                 "opFall(player,crate,yard,lawn)") for p in plans)
        self._record(True, "Example 4: a wave in the yard washes the crate into the briars")

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

    def test_property_p3_envoy_is_never_dragged(self):
        """Pulled over the briars it would fall: no winning plan moves it by
        force - it always walks out."""
        for a, b in WINNING:
            for p in plans_with(a, b):
                assert not any(op.startswith(("opForcedMove", "opFall")) and ",envoy," in op
                               for op in p), p
                assert "opNavigate(envoy,gatehouse,road)" in p
        self._record(True, "P3: the envoy walks out; nobody drags it over the briars")

    def test_property_p4_mist_is_a_moment(self):
        """The knock that drops the misted sentry is the very next cast."""
        for a in ("fireball", "shieldBash"):
            for p in plans_with("turnToMist", a):
                casts = [op for op in p if op.startswith("opCast(")]
                i = casts.index("opCast(player,turnToMist,sentry)")
                assert casts[i + 1] == f"opCast(mage,{a},sentry)", p
        self._record(True, "P4: the sentry drops on the cast right after the mist")

    def test_property_p5_two_companions_cast(self):
        for a, b in WINNING:
            for p in plans_with(a, b):
                assert casters(p) == {"player", "mage"}, p
        self._record(True, "P5: both companions cast in every winning plan")


def run_tests():
    suite = EscortEnvoyTest()
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
