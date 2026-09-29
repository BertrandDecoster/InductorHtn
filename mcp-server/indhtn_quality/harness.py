"""Config-driven loadout sweep: the generalization of the three prototype
sweep.py scripts (fortress-loadout P1-P6 + cross-check, loadout-decision
dominance, decision-dag capability sweeps).

Sweeps every unordered skill loadout, runs every challenge goal plus the
full/playRoot goals, replays each plan for causal depth / length / atom-tag
metadata, prints the classic matrix, then runs the named property checks
from the config (see properties.py).

CLI:
    PYTHONPATH=mcp-server python -m indhtn_quality.harness <quality.json> \
        [--json out.json] [--only P1_choke,depth]
Exit code is non-zero iff an error-severity property fails.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

from .config import LevelConfig, load_config
from .plan_replay import replay_plan
from .session_util import open_session, run
from .static_model import build_static_model


@dataclass
class PlanMeta:
    depth: int
    length: int
    tags: List[Tuple[str, str]]


@dataclass
class Row:
    loadout: Tuple[str, ...]
    cells: Dict[str, int]
    full: int
    atoms: Set[str]
    fight_only: List[Tuple[str, List[str]]]
    plan_metas: Dict[str, List[PlanMeta]] = field(default_factory=dict)


@dataclass
class SweepContext:
    skills: List[str]
    challenge_names: List[str]
    rows: List[Row]
    declared_atoms: Set[str]
    declared_methods: Set[Tuple[str, str]]
    atoms_seen: Set[str]
    methods_seen: Set[Tuple[str, str]]
    play_count: int
    marker_required_for: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _dedupe(plans: List[dict]) -> List[dict]:
    seen, out = set(), []
    for p in plans:
        key = tuple(p["operators"])
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


async def run_sweep(cfg: LevelConfig) -> SweepContext:
    async with open_session(paths=[str(cfg.level)],
                            memory_budget=cfg.memory_budget) as qs:
        model = build_static_model(qs.source_text)
        marker = cfg.metadata.resolve_marker

        skills = sorted(s["?s"] for s in await qs.query_all(cfg.choice.pool_query))
        declared_atoms: Set[str] = set()
        declared_methods: Set[Tuple[str, str]] = set()
        if cfg.metadata.challenge_atoms:
            declared_atoms = {s["?a"] for s in
                              await qs.query_all(cfg.metadata.challenge_atoms)}
        if cfg.metadata.atom_methods:
            declared_methods = {(s["?a"], s["?m"]) for s in
                                await qs.query_all(cfg.metadata.atom_methods)}

        rows: List[Row] = []
        atoms_seen: Set[str] = set()
        methods_seen: Set[Tuple[str, str]] = set()
        warnings: List[str] = []

        for loadout in itertools.combinations(skills, cfg.choice.slots):
            await qs.reset_state()
            await qs.add_facts(t.format(*loadout) for t in cfg.choice.inject_facts)
            initial = await qs.state_facts()

            cells: Dict[str, int] = {}
            plan_metas: Dict[str, List[PlanMeta]] = {}
            loadout_atoms: Set[str] = set()
            fight_only: List[Tuple[str, List[str]]] = []

            for cname, goal in cfg.challenges:
                res = await qs.find_plans(goal)
                if not res.get("ok", False):
                    cells[cname] = 0
                    continue
                unique = _dedupe(res["plans"])
                cells[cname] = len(unique)
                # Trees must be fetched before the next find_plans clobbers
                # the session's stored solutions.
                trees = [await qs.tree(p["index"]) for p in unique]
                metas: List[PlanMeta] = []
                for plan, tree in zip(unique, trees):
                    replay = replay_plan(model, initial, plan, tree, marker=marker)
                    warnings.extend(replay.warnings)
                    tags = [s.atom_tag for s in replay.steps if s.atom_tag]
                    metas.append(PlanMeta(depth=replay.causal_depth,
                                          length=len(replay.steps), tags=tags))
                    for atom, method in tags:
                        atoms_seen.add(atom)
                        methods_seen.add((atom, method))
                        loadout_atoms.add(atom)
                    if cname in cfg.metadata.marker_required_for and not tags:
                        fight_only.append((cname, plan["operators"]))
                plan_metas[cname] = metas

            full = 0
            if cfg.full_goal:
                res = await qs.find_plans(cfg.full_goal)
                full = len(_dedupe(res["plans"])) if res.get("ok", False) else 0

            rows.append(Row(loadout=loadout, cells=cells, full=full,
                            atoms=loadout_atoms, fight_only=fight_only,
                            plan_metas=plan_metas))

        play_count = 0
        if cfg.play_root:
            await qs.reset_state()
            res = await qs.find_plans(cfg.play_root)
            play_count = len(_dedupe(res["plans"])) if res.get("ok", False) else 0

    return SweepContext(
        skills=skills,
        challenge_names=[c for c, _ in cfg.challenges],
        rows=rows,
        declared_atoms=declared_atoms, declared_methods=declared_methods,
        atoms_seen=atoms_seen, methods_seen=methods_seen,
        play_count=play_count,
        marker_required_for=list(cfg.metadata.marker_required_for),
        warnings=warnings,
    )


# ----------------------------------------------------------------------
# Reporting (matrix format lifted from prototypes/fortress-loadout/sweep.py)
# ----------------------------------------------------------------------

def format_matrix(ctx: SweepContext) -> str:
    names = ctx.challenge_names
    w = max(len("+".join(r.loadout)) for r in ctx.rows) + 2
    lines = ["=" * (w + 46),
             f"{'loadout':<{w}}" + "".join(
                 f"{n:<16}" if i < len(names) - 1 else f"{n:<18}"
                 for i, n in enumerate(names)) + "FULL",
             "-" * (w + 46)]
    for r in ctx.rows:
        s1, rest = r.loadout[0], "+".join(r.loadout[1:])
        line = f"{s1}+{rest:<{w - len(s1) - 1}}"
        for i, n in enumerate(names):
            width = 16 if i < len(names) - 1 else 18
            line += f"{r.cells.get(n, 0):<{width}}"
        line += f"{r.full}"
        lines.append(line)
    lines.append("=" * (w + 46))
    return "\n".join(lines)


def format_coverage(ctx: SweepContext) -> str:
    w = max(len("+".join(r.loadout)) for r in ctx.rows) + 2
    lines = ["atom coverage per loadout (full-clear loadouts marked *):"]
    for r in ctx.rows:
        s1, rest = r.loadout[0], "+".join(r.loadout[1:])
        mark = "*" if r.full > 0 else " "
        lines.append(f"  {mark} {s1}+{rest:<{w - len(s1) - 1}} "
                     f"{', '.join(sorted(r.atoms)) or '-'}")
    return "\n".join(lines)


def to_report(ctx: SweepContext, results) -> dict:
    return {
        "skills": ctx.skills,
        "rows": [{
            "loadout": list(r.loadout), "cells": r.cells, "full": r.full,
            "atoms": sorted(r.atoms),
            "planMetas": {c: [{"depth": m.depth, "length": m.length,
                               "tags": [list(t) for t in m.tags]}
                              for m in metas]
                          for c, metas in r.plan_metas.items()},
        } for r in ctx.rows],
        "playCount": ctx.play_count,
        "properties": [{"name": p.name, "ok": p.ok, "severity": p.severity,
                        "detail": p.detail} for p in results],
        "warnings": sorted(set(ctx.warnings)),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    from .properties import run_properties

    ap = argparse.ArgumentParser(
        prog="indhtn_quality.harness",
        description="Run the loadout-sweep quality battery from a quality.json.")
    ap.add_argument("config", help="path to the level's quality.json")
    ap.add_argument("--json", dest="json_out",
                    help="also write a machine-readable report to this file")
    ap.add_argument("--only", help="comma-separated property names to run")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    if args.only:
        keep = {n.strip() for n in args.only.split(",")}
        cfg.properties = {k: v for k, v in cfg.properties.items() if k in keep}

    ctx = run(run_sweep(cfg))

    print(f"skills ({len(ctx.skills)}): " + ", ".join(ctx.skills))
    print(f"challenges: {ctx.challenge_names}, "
          f"declared atoms: {len(ctx.declared_atoms)}, "
          f"declared methods: {len(ctx.declared_methods)}\n")
    print(format_matrix(ctx))

    if ctx.play_count or any(r.full for r in ctx.rows):
        total = sum(r.full for r in ctx.rows)
        verdict = "PASS" if ctx.play_count == total else "FAIL"
        print(f"\ncross-check: playRoot = {ctx.play_count} plans, "
              f"sum of swept FULL column = {total}  [{verdict}]")

    results = run_properties(ctx, cfg)
    print("\n" + "=" * 72)
    print("PROPERTIES")
    print("-" * 72)
    hard_fail = False
    for res in results:
        status = "PASS" if res.ok else ("FAIL" if res.severity == "error" else "WARN")
        hard_fail |= (not res.ok and res.severity == "error")
        print(f"{res.name:<22}[{res.severity:<5}] {status} — {res.detail}")
    print("=" * 72)
    print(f"VERDICT: {'ALL PASS' if not hard_fail else 'FAILURES PRESENT'} "
          f"(error-severity gates)")

    print("\n" + format_coverage(ctx))

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(to_report(ctx, results), fh, indent=2)
        print(f"\nreport written to {args.json_out}")

    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
