"""Named quality properties over a loadout sweep.

Ported checks: P1-P6 from prototypes/fortress-loadout/sweep.py, dominance
from prototypes/loadout-decision/sweep.py, plus the new depth / diversity /
minPlanLength / everyPlanUses / generativity checks (quantify-over-play:
universal properties over the enumerated plan set).

Each check: check_<name>(ctx, params) -> PropertyResult. run_properties()
dispatches from the config's properties map, skipping severity "off".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from .config import LevelConfig
from .harness import SweepContext


@dataclass
class PropertyResult:
    name: str
    ok: bool
    detail: str
    severity: str = "warn"


def _triples(row) -> Set[Tuple[str, str, str]]:
    """(challenge, atom, method) fingerprints a loadout achieves."""
    out = set()
    for cname, metas in row.plan_metas.items():
        for m in metas:
            for atom, method in m.tags:
                out.add((cname, atom, method))
    return out


def check_P1_choke(ctx: SweepContext, params: Dict) -> PropertyResult:
    need = int(params.get("minLoadoutsPerChallenge", 6))
    fails = []
    details = []
    for n in ctx.challenge_names:
        solvers = sum(1 for r in ctx.rows if r.cells.get(n, 0) > 0)
        details.append(f"{n}: {solvers}/{len(ctx.rows)}")
        if solvers < need:
            fails.append(n)
    return PropertyResult(
        "P1_choke", not fails,
        f"loadouts solving each challenge (need >= {need}): " + ", ".join(details)
        + (f" — choke points: {fails}" if fails else ""))


def check_P2_decision(ctx: SweepContext, params: Dict) -> PropertyResult:
    full_clear = sum(1 for r in ctx.rows if r.full > 0)
    ok = 0 < full_clear < len(ctx.rows)
    return PropertyResult(
        "P2_decision", ok,
        f"{full_clear}/{len(ctx.rows)} loadouts full-clear "
        + ("(some but not all — the decision matters)" if ok else
           "(want some-but-not-all)"))


def check_P3_deadSkill(ctx: SweepContext, params: Dict) -> PropertyResult:
    in_clear = {s for r in ctx.rows if r.full > 0 for s in r.loadout}
    dead = sorted(set(ctx.skills) - in_clear)
    return PropertyResult(
        "P3_deadSkill", not dead,
        f"never in a full-clear loadout: {dead}" if dead else
        f"all {len(ctx.skills)} skills appear in a full-clear loadout")


def check_P4_deadAtom(ctx: SweepContext, params: Dict) -> PropertyResult:
    dead = sorted(ctx.declared_atoms - ctx.atoms_seen)
    return PropertyResult(
        "P4_deadAtom", not dead,
        f"declared but never achieved: {dead}" if dead else
        f"all {len(ctx.declared_atoms)} declared atoms achieved by some loadout")


def check_P5_methodDrift(ctx: SweepContext, params: Dict) -> PropertyResult:
    dead = sorted(ctx.declared_methods - ctx.methods_seen)
    undeclared = sorted(ctx.methods_seen - ctx.declared_methods)
    ok = not dead and not undeclared
    detail = []
    if dead:
        detail.append(f"declared but never seen: {dead}")
    if undeclared:
        detail.append(f"seen but undeclared: {undeclared}")
    return PropertyResult(
        "P5_methodDrift", ok,
        "; ".join(detail) if detail else
        f"all {len(ctx.declared_methods)} declared methods seen, no drift")


def check_P6_comboGated(ctx: SweepContext, params: Dict) -> PropertyResult:
    leaks = [(r.loadout, c) for r in ctx.rows for c, _ops in r.fight_only]
    return PropertyResult(
        "P6_comboGated", not leaks,
        f"marker-less solves of gated challenges: {leaks[:3]}" if leaks else
        "no gated challenge falls to a marker-less (bare-fight) plan")


def check_playRootCrossCheck(ctx: SweepContext, params: Dict) -> PropertyResult:
    total = sum(r.full for r in ctx.rows)
    ok = ctx.play_count == total
    return PropertyResult(
        "playRootCrossCheck", ok,
        f"playRoot = {ctx.play_count} plans vs sum of FULL column = {total}")


def check_depth(ctx: SweepContext, params: Dict) -> PropertyResult:
    lo, hi = int(params.get("min", 3)), int(params.get("max", 5))
    fails, details = [], []
    for n in ctx.challenge_names:
        depths = [m.depth for r in ctx.rows for m in r.plan_metas.get(n, [])]
        if not depths:
            continue
        best = max(depths)
        details.append(f"{n}: max {best}, min {min(depths)}")
        if not lo <= best <= hi:
            fails.append(f"{n} ({best})")
    return PropertyResult(
        "depth", not fails,
        f"causal depth target [{lo},{hi}] — " + "; ".join(details)
        + (f" — out of range: {fails}" if fails else ""))


def check_diversity(ctx: SweepContext, params: Dict) -> PropertyResult:
    need = int(params.get("minClusters", 2))
    fails, details = [], []
    for n in ctx.challenge_names:
        clusters = {frozenset(m.tags) for r in ctx.rows
                    for m in r.plan_metas.get(n, [])}
        details.append(f"{n}: {len(clusters)}")
        if 0 < len(clusters) < need:
            fails.append(n)
    return PropertyResult(
        "diversity", not fails,
        f"solution clusters per challenge (need >= {need}): " + ", ".join(details)
        + (f" — too samey: {fails}" if fails else ""))


def check_minPlanLength(ctx: SweepContext, params: Dict) -> PropertyResult:
    need = int(params.get("min", 2))
    shortest = None
    where = ""
    for r in ctx.rows:
        for n, metas in r.plan_metas.items():
            for m in metas:
                if shortest is None or m.length < shortest:
                    shortest, where = m.length, f"{n} with {'+'.join(r.loadout)}"
    ok = shortest is None or shortest >= need
    return PropertyResult(
        "minPlanLength", ok,
        f"shortest plan: {shortest} ops ({where}); need >= {need}")


def check_everyPlanUses(ctx: SweepContext, params: Dict) -> PropertyResult:
    mechanic = params.get("mechanic")
    if not mechanic:
        return PropertyResult("everyPlanUses", True, "no mechanic configured")
    atom = str(mechanic)
    missing = [(r.loadout, n) for r in ctx.rows
               for n, metas in r.plan_metas.items()
               for m in metas
               if not any(atom in (a, meth) for a, meth in m.tags)]
    return PropertyResult(
        "everyPlanUses", not missing,
        f"plans bypassing {atom}: {missing[:3]}" if missing else
        f"every plan passes through {atom}")


def check_dominance(ctx: SweepContext, params: Dict) -> PropertyResult:
    """Loadout A dominates B when A's fingerprint set is a proper superset —
    B offers nothing A does not (Sirlin: a degenerate option)."""
    trip = {r.loadout: _triples(r) for r in ctx.rows}
    dominated = []
    for a in ctx.rows:
        for b in ctx.rows:
            if a.loadout != b.loadout and trip[b.loadout] and \
                    trip[a.loadout] > trip[b.loadout] and a.full >= b.full:
                dominated.append(("+".join(a.loadout), "+".join(b.loadout)))
    return PropertyResult(
        "dominance", not dominated,
        f"{len(dominated)} dominated pairs, e.g. " +
        "; ".join(f"{a} > {b}" for a, b in dominated[:3])
        if dominated else "no loadout strictly dominates another")


def check_generativity(ctx: SweepContext, params: Dict) -> PropertyResult:
    """A skill's exclusive contribution: fingerprints achieved ONLY by
    loadouts containing it. Zero = a skill no strategy actually needs."""
    achievers: Dict[Tuple[str, str, str], List[Tuple[str, ...]]] = {}
    for r in ctx.rows:
        for t in _triples(r):
            achievers.setdefault(t, []).append(r.loadout)
    exclusive = {s: 0 for s in ctx.skills}
    for t, loadouts in achievers.items():
        for s in ctx.skills:
            if all(s in lo for lo in loadouts):
                exclusive[s] += 1
    zeros = sorted(s for s, n in exclusive.items() if n == 0)
    ranking = ", ".join(f"{s}:{n}" for s, n in
                        sorted(exclusive.items(), key=lambda kv: -kv[1]))
    return PropertyResult(
        "generativity", not zeros,
        f"exclusive fingerprints per skill: {ranking}"
        + (f" — nothing needs: {zeros}" if zeros else ""))


_CHECKS = {
    "P1_choke": check_P1_choke,
    "P2_decision": check_P2_decision,
    "P3_deadSkill": check_P3_deadSkill,
    "P4_deadAtom": check_P4_deadAtom,
    "P5_methodDrift": check_P5_methodDrift,
    "P6_comboGated": check_P6_comboGated,
    "playRootCrossCheck": check_playRootCrossCheck,
    "depth": check_depth,
    "diversity": check_diversity,
    "minPlanLength": check_minPlanLength,
    "everyPlanUses": check_everyPlanUses,
    "dominance": check_dominance,
    "generativity": check_generativity,
}


def run_properties(ctx: SweepContext, cfg: LevelConfig) -> List[PropertyResult]:
    results: List[PropertyResult] = []
    for name, pcfg in cfg.properties.items():
        if pcfg.severity == "off":
            continue
        check = _CHECKS.get(name)
        if check is None:
            results.append(PropertyResult(
                name, False, f"unknown property {name!r} "
                f"(available: {sorted(_CHECKS)})", pcfg.severity))
            continue
        res = check(ctx, pcfg.params)
        res.severity = pcfg.severity
        results.append(res)
    return results
