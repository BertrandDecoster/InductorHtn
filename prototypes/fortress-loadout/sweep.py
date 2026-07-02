#!/usr/bin/env python3
"""fortress-loadout spike driver.

Sweeps every unordered 2-skill loadout (player + 1 companion, one skill each,
7-skill pool -> 21 loadouts) and asks the planner, per challenge: solvable, in
how many distinct ways, through which atoms? Then checks the design
properties that make the loadout a real puzzle decision:

  P1  each challenge solvable by enough loadouts (no choke point)
  P2  some but not all loadouts full-clear (the decision matters)
  P3  every skill appears in at least one full-clear loadout (no dead skill)
  P4  every declared atom is achieved by some loadout (no dead content)
  P5  every declared atom-method is seen in some plan, and every method tag
      seen in plans is declared (metadata drift, both directions)
  P6  no loadout solves an invulnerable-target challenge by fighting alone
      (combo gating is real)

Run:  source .venv/bin/activate && python prototypes/fortress-loadout/sweep.py
"""

from __future__ import annotations

import asyncio
import itertools
import re
from pathlib import Path

from indhtn_mcp.server import create_server

LEVEL = Path(__file__).resolve().parent / "level.htn"

P1_MIN_LOADOUTS_PER_CHALLENGE = 6

_RESOLVE = re.compile(r"opResolveAtom\(\s*(\w+)\s*,\s*(\w+)\s*\)")

CHALLENGE_GOALS = [
    ("enterFortress", "enterFortress()."),
    ("secureWorkshop", "secureWorkshop()."),
    ("defeatVaultBrute", "defeatVaultBrute()."),
]


def resolves(plan: dict) -> list[tuple[str, str]]:
    """(atom, method) markers a plan passes through, in order."""
    out = []
    for op in plan["operators"]:
        m = _RESOLVE.search(op)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def dedupe(plans: list[dict]) -> list[dict]:
    seen, out = set(), []
    for p in plans:
        key = tuple(p["operators"])
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


async def main() -> None:
    srv = create_server()
    sid = (await srv.call_tool_direct(
        "indhtn_create_session", {"memoryBudgetBytes": 256 * 1024 * 1024}
    ))["sessionId"]

    load = await srv.call_tool_direct(
        "indhtn_load_files", {"sessionId": sid, "paths": [str(LEVEL)]}
    )
    if not load.get("ok", False):
        print("FAILED to load level.htn:")
        print(load)
        await srv.call_tool_direct("indhtn_end_session", {"sessionId": sid})
        return

    async def query(q: str) -> list[dict]:
        res = await srv.call_tool_direct(
            "indhtn_query", {"sessionId": sid, "query": q}
        )
        return res.get("solutions", []) or []

    # --- Domain introspection (single source of truth: the level file) ---
    skills = sorted(s["?s"] for s in await query("equippableSkill(?s)."))
    grants: dict[str, list[str]] = {s: [] for s in skills}
    for sol in await query("skillGrants(?s, ?e, ?dir)."):
        grants[sol["?s"]].append(sol["?e"])

    combo_rules = [(s["?a"], s["?b"], s["?r"]) for s in await query("comboRule(?a, ?b, ?r).")]
    base_effects = sorted({e for es in grants.values() for e in es})
    for a, b, r in combo_rules:
        assert a in base_effects and b in base_effects, f"combo input {a}/{b} not skill-producible"
        assert r not in {x for ab in combo_rules for x in ab[:2]}, f"combo output {r} used as input (cycle)"

    atoms_of: dict[str, list[str]] = {}
    for sol in await query("challengeAtom(?c, ?a)."):
        atoms_of.setdefault(sol["?c"], []).append(sol["?a"])
    declared_atoms = {a for atoms in atoms_of.values() for a in atoms}
    declared_methods = {(s["?a"], s["?m"]) for s in await query("atomMethod(?a, ?m).")}

    print(f"skills ({len(skills)}): " + ", ".join(f"{s}[{'+'.join(grants[s])}]" for s in skills))
    print(f"combo rules: {combo_rules}")
    print(f"challenges: { {c: len(a) for c, a in atoms_of.items()} }, "
          f"declared methods: {len(declared_methods)}\n")

    # --- Sweep all 21 loadouts ---
    rows = []
    atoms_seen: set[str] = set()
    methods_seen: set[tuple[str, str]] = set()
    full_total = 0

    for s1, s2 in itertools.combinations(skills, 2):
        await srv.call_tool_direct("indhtn_reset_state", {"sessionId": sid})
        await srv.call_tool_direct(
            "indhtn_add_facts",
            {"sessionId": sid,
             "facts": [f"equipped(player, {s1})", f"equipped(companion, {s2})"]},
        )

        cells = {}
        loadout_atoms: set[str] = set()
        fight_only_solve = []
        for cname, goal in CHALLENGE_GOALS:
            plans = await srv.call_tool_direct(
                "indhtn_find_plans", {"sessionId": sid, "goal": goal}
            )
            if not plans.get("ok", False):
                cells[cname] = 0
                continue
            unique = dedupe(plans["plans"])
            cells[cname] = len(unique)
            for p in unique:
                tags = resolves(p)
                for atom, method in tags:
                    atoms_seen.add(atom)
                    methods_seen.add((atom, method))
                    loadout_atoms.add(atom)
                # P6: a plan for an invulnerable-target challenge that never
                # passes a resolve marker would be a bare-fight solve.
                if cname != "enterFortress" and not tags:
                    fight_only_solve.append((cname, p["operators"]))

        full = await srv.call_tool_direct(
            "indhtn_find_plans", {"sessionId": sid, "goal": "solveLevel()."}
        )
        n_full = len(dedupe(full["plans"])) if full.get("ok", False) else 0
        full_total += n_full

        rows.append({
            "loadout": (s1, s2),
            "cells": cells,
            "full": n_full,
            "atoms": loadout_atoms,
            "fight_only": fight_only_solve,
        })

    # --- Matrix ---
    names = [c for c, _ in CHALLENGE_GOALS]
    w = max(len(f"{s1}+{s2}") for s1, s2 in itertools.combinations(skills, 2)) + 2
    print("=" * (w + 46))
    print(f"{'loadout':<{w}}{names[0]:<16}{names[1]:<16}{names[2]:<18}FULL")
    print("-" * (w + 46))
    for r in rows:
        s1, s2 = r["loadout"]
        c = r["cells"]
        line = f"{s1}+{s2:<{w - len(s1) - 1}}"
        for n in names:
            line += f"{c.get(n, 0):<16}" if n != names[2] else f"{c.get(n, 0):<18}"
        line += f"{r['full']}"
        print(line)
    print("=" * (w + 46))

    # --- Cross-check: in-plan loadout root vs sum of swept FULL cells ---
    await srv.call_tool_direct("indhtn_reset_state", {"sessionId": sid})
    play = await srv.call_tool_direct(
        "indhtn_find_plans", {"sessionId": sid, "goal": "playLevel()."}
    )
    n_play = len(dedupe(play["plans"])) if play.get("ok", False) else 0
    xcheck = "PASS" if n_play == full_total else "FAIL"
    print(f"\ncross-check: playLevel() = {n_play} plans, "
          f"sum of swept FULL column = {full_total}  [{xcheck}]")

    # --- Properties ---
    print("\n" + "=" * 72)
    print("PROPERTIES")
    print("-" * 72)

    ok = True

    for n in names:
        solvers = [r for r in rows if r["cells"].get(n, 0) > 0]
        p = len(solvers) >= P1_MIN_LOADOUTS_PER_CHALLENGE
        ok &= p
        print(f"P1 {n:<22}: {'PASS' if p else 'FAIL'} — solvable by "
              f"{len(solvers)}/21 loadouts (need >= {P1_MIN_LOADOUTS_PER_CHALLENGE})")

    full_clear = [r for r in rows if r["full"] > 0]
    p2 = 0 < len(full_clear) < len(rows)
    ok &= p2
    print(f"P2 decision matters     : {'PASS' if p2 else 'FAIL'} — "
          f"{len(full_clear)}/21 loadouts full-clear the level")

    skills_in_clear = {s for r in full_clear for s in r["loadout"]}
    dead_skills = set(skills) - skills_in_clear
    p3 = not dead_skills
    ok &= p3
    print(f"P3 no dead skill        : {'PASS' if p3 else 'FAIL'}"
          + (f" — never in a full-clear loadout: {sorted(dead_skills)}" if dead_skills else
             f" — all {len(skills)} skills appear in a full-clear loadout"))

    dead_atoms = declared_atoms - atoms_seen
    p4 = not dead_atoms
    ok &= p4
    print(f"P4 no dead atom         : {'PASS' if p4 else 'FAIL'}"
          + (f" — never achieved: {sorted(dead_atoms)}" if dead_atoms else
             f" — all {len(declared_atoms)} atoms achieved by some loadout"))

    dead_methods = declared_methods - methods_seen
    undeclared = methods_seen - declared_methods
    p5 = not dead_methods and not undeclared
    ok &= p5
    print(f"P5 method metadata      : {'PASS' if p5 else 'FAIL'}"
          + (f" — declared but never seen: {sorted(dead_methods)}" if dead_methods else "")
          + (f" — seen but undeclared: {sorted(undeclared)}" if undeclared else "")
          + ("" if dead_methods or undeclared else
             f" — all {len(declared_methods)} methods seen, no drift"))

    fight_only = [(r["loadout"], f) for r in rows for f in r["fight_only"]]
    p6 = not fight_only
    ok &= p6
    print(f"P6 combos are gated     : {'PASS' if p6 else 'FAIL'}"
          + (f" — bare-fight solves: {fight_only[:3]}" if fight_only else
             " — no invulnerable target falls to fighting alone"))

    print("=" * 72)
    print(f"VERDICT: {'ALL PASS' if ok else 'FAILURES PRESENT'}")

    # --- Per-loadout atom coverage (which approaches each loadout unlocks) ---
    print("\natom coverage per loadout (full-clear loadouts marked *):")
    for r in rows:
        s1, s2 = r["loadout"]
        mark = "*" if r["full"] > 0 else " "
        print(f"  {mark} {s1}+{s2:<{w - len(s1) - 1}} {', '.join(sorted(r['atoms'])) or '-'}")

    await srv.call_tool_direct("indhtn_end_session", {"sessionId": sid})


if __name__ == "__main__":
    asyncio.run(main())
