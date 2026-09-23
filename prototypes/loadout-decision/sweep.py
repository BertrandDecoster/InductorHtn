#!/usr/bin/env python3
"""loadout-decision spike driver.

NOTE (2026-07-02): frozen as a dated spike record — its outputs are cited in
README.md. The dominance-as-proper-subset check lives on as the ``dominance``
property of the shared harness (``mcp-server/indhtn_quality/properties.py``);
use that for new levels.

The companion model from `prototypes/decision-dag/` was tautological: decisions
were free, independent capability tokens swept by Python. Here the decision is a
*constrained loadout* (one skill per companion, distinct skills) and it is chosen
INSIDE the HTN plan: `defeatWithLoadout(gob)` binds two skills over
`equippableSkill`, commits them with `loadSkill` operators, then decomposes the
real combat goal against whatever got equipped. A single `find_plans` call
therefore enumerates every (loadout x strategy) as a distinct plan.

This driver does the analysis the planner can't: it groups the plans by the
*set of equipped skills* and reports

  - which strategies each loadout unlocks (the "decisions unlock combos" matrix),
  - which loadouts unlock NOTHING (proves the decision is load-bearing, not free),
  - which loadouts are dominated (unlock a subset of another's strategies),
  - the multipurpose payoff: a single multi-tag skill unlocking >=2 combos.

Run:  source .venv/bin/activate && PYTHONPATH=mcp-server python prototypes/loadout-decision/sweep.py
"""

from __future__ import annotations

import asyncio
import itertools
import re
from pathlib import Path

from indhtn_mcp.server import create_server

LEVEL = Path(__file__).resolve().parent / "level.htn"
GOAL = "defeatWithLoadout(gob)."

# loadSkill(companion, skill) — tolerant of optional whitespace.
_LOADSKILL = re.compile(r"loadSkill\(\s*(\w+)\s*,\s*(\w+)\s*\)")

# Strategy fingerprints: each (name, predicate-over-the-operator-string) is tried
# in order; the FIRST match classifies the plan. opSynchronize is unique to the
# simultaneous strategy; electrocute / fire then separate the two sequential ones.
_STRATEGY_MARKERS = [
    ("stunAndSlowSkill", lambda ops: "opSynchronize(" in ops),
    ("wetAndElectrocute", lambda ops: "opApplyTag(electrocute" in ops),
    ("stunAndBurn", lambda ops: "opApplyTag(fire" in ops),
]


def loadout_of(plan: dict) -> frozenset[str]:
    """The SET of skills this plan equipped (companion assignment collapsed)."""
    skills = set()
    for op in plan["operators"]:
        m = _LOADSKILL.search(op)
        if m:
            skills.add(m.group(2))
    return frozenset(skills)


def strategy_of(plan: dict) -> str:
    ops = " ".join(plan["operators"])
    for name, matches in _STRATEGY_MARKERS:
        if matches(ops):
            return name
    return "(unclassified)"


def fmt_set(s: frozenset[str]) -> str:
    return "{" + ", ".join(sorted(s)) + "}"


async def main() -> None:
    srv = create_server()
    sid = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]

    load = await srv.call_tool_direct(
        "indhtn_load_files", {"sessionId": sid, "paths": [str(LEVEL)]}
    )
    if not load.get("ok", False):
        print("FAILED to load level.htn:")
        print(load)
        await srv.call_tool_direct("indhtn_end_session", {"sessionId": sid})
        return

    # --- Pull the decision space straight from the domain (single source of truth) ---
    pool_q = await srv.call_tool_direct(
        "indhtn_query", {"sessionId": sid, "query": "equippableSkill(?s)."}
    )
    pool = sorted({s["?s"] for s in pool_q.get("solutions", [])})

    tag_q = await srv.call_tool_direct(
        "indhtn_query", {"sessionId": sid, "query": "skillAppliesTag(?s, ?tag)."}
    )
    skill_tags: dict[str, set[str]] = {}
    for s in tag_q.get("solutions", []):
        skill_tags.setdefault(s["?s"], set()).add(s["?tag"])
    multi_tag = {sk: ts for sk, ts in skill_tags.items() if len(ts) >= 2}

    print(f"equippable skills (the decision pool): {pool}")
    print(f"slots: 2 (one skill per companion, distinct)")
    print(f"multi-tag (multipurpose) skills: "
          f"{ {sk: sorted(ts) for sk, ts in multi_tag.items()} }\n")

    # --- One call: the planner chooses the loadout in-plan and enumerates all plans ---
    plans = await srv.call_tool_direct(
        "indhtn_find_plans", {"sessionId": sid, "goal": GOAL}
    )
    n_total = plans.get("planCount", 0)

    # --- Group plans by equipped skill-set ---
    enabled: dict[frozenset[str], set[str]] = {}
    plan_counts: dict[frozenset[str], int] = {}
    for plan in plans.get("plans", []):
        lo = loadout_of(plan)
        enabled.setdefault(lo, set()).add(strategy_of(plan))
        plan_counts[lo] = plan_counts.get(lo, 0) + 1

    # --- Every possible loadout, including the ones that unlock nothing ---
    all_loadouts = [frozenset(c) for c in itertools.combinations(pool, 2)]

    print("=" * 82)
    print(f"{'loadout (skill-set)':<40}{'#plans':<8}{'unlocked strategies'}")
    print("-" * 82)
    for lo in sorted(all_loadouts, key=lambda s: sorted(s)):
        strats = sorted(enabled.get(lo, set()))
        cnt = plan_counts.get(lo, 0)
        shown = ", ".join(strats) if strats else "-- nothing --"
        print(f"{fmt_set(lo):<40}{cnt:<8}{shown}")
    print("=" * 82)
    print(f"total plans returned by FindAllPlans: {n_total}\n")

    # --- Dominance: a loadout dominated if its strategy-set is a subset of another's ---
    nonempty = {lo: enabled[lo] for lo in all_loadouts if enabled.get(lo)}
    dominated = []
    for lo, strats in nonempty.items():
        for other, ostrats in nonempty.items():
            if other != lo and strats < ostrats:  # proper subset
                dominated.append((lo, other))
                break

    # --- Multipurpose payoff: loadouts unlocking >=2 strategies, and the skill behind it ---
    rich = {lo: strats for lo, strats in nonempty.items() if len(strats) >= 2}
    dead = [lo for lo in all_loadouts if not enabled.get(lo)]

    print("=" * 72)
    print("ANALYSIS")
    print("-" * 72)
    print(f"(1) Load-bearing: {len(dead)}/{len(all_loadouts)} loadouts unlock NOTHING")
    for lo in sorted(dead, key=lambda s: sorted(s)):
        print(f"      {fmt_set(lo)}  -> the decision genuinely gates capability")
    print(f"\n(2) Multipurpose payoff: {len(rich)} loadout(s) unlock >=2 distinct combos")
    for lo, strats in sorted(rich.items(), key=lambda kv: sorted(kv[0])):
        culprits = sorted(sk for sk in lo if sk in multi_tag)
        print(f"      {fmt_set(lo)}  -> {sorted(strats)}")
        for sk in culprits:
            print(f"          via multipurpose {sk} = {sorted(multi_tag[sk])} "
                  f"(one equip, multiple combos)")
    if not rich:
        print("      (none -- no single loadout unlocked more than one strategy)")
    print(f"\n(3) Dominated loadouts (strategy-set is a strict subset of another's):")
    if dominated:
        for lo, by in dominated:
            print(f"      {fmt_set(lo)}  dominated by {fmt_set(by)}")
    else:
        print("      (none -- every viable loadout unlocks a unique strategy-set)")
    print("=" * 72)

    # --- Verdict ---
    print("\nVERDICT")
    print("-" * 72)
    print(f"  decision is load-bearing : {'PASS' if dead else 'FAIL'} "
          f"({len(dead)} loadout(s) unlock nothing)")
    print(f"  multipurpose unlocks set : {'PASS' if rich else 'FAIL'} "
          f"({len(rich)} loadout(s) unlock >=2 combos via a multi-tag skill)")
    print(f"  loadouts genuinely differ: "
          f"{'PASS' if len({frozenset(s) for s in nonempty.values()}) > 1 else 'FAIL'} "
          f"(distinct loadouts unlock distinct strategy-sets)")
    print("-" * 72)

    await srv.call_tool_direct("indhtn_end_session", {"sessionId": sid})


if __name__ == "__main__":
    asyncio.run(main())
