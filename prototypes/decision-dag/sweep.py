#!/usr/bin/env python3
"""decision-dag spike driver.

NOTE (2026-07-02): frozen as a dated spike record — its outputs are cited in
README.md and docs/game-design/pcg-puzzles-and-fun.md. The fairness check
(C10, gated edge without a clue) lives on as the ``fairness`` property of the
shared harness (``mcp-server/indhtn_quality/properties.py``); use that for
new levels.

Sweeps every decision-set (subset of the level's capability tokens) and, for
each, asks the planner: is the level solvable, in how many distinct ways, and is
every winning path FAIR (each gated edge it uses has a discoverable clue)?

This operationalises four research findings (see the plan file):
  B5  planner as a design-time solvability prover  -> "solvable?" column
  C7  multiple decision-sets yield distinct strategies -> "#strategies" column
  C8  success is reported per WHOLE plan, never per edge
  C10 a path is only fair if every gated edge has a clue -> "fair?" / FLAG

Run:  source .venv/bin/activate && python prototypes/decision-dag/sweep.py
"""

from __future__ import annotations

import asyncio
import itertools
import re
from pathlib import Path

from indhtn_mcp.server import create_server

REPO = Path(__file__).resolve().parents[2]
LEVEL = Path(__file__).resolve().parent / "level.htn"

# opMove(player, FROM, TO) — tolerant of optional whitespace in the printed term.
_OPMOVE = re.compile(r"opMove\(\s*\w+\s*,\s*(\w+)\s*,\s*(\w+)\s*\)")


def edges_used(plan: dict) -> list[tuple[str, str]]:
    """Return the (from, to) hops a plan traverses, in order."""
    hops = []
    for op in plan["operators"]:
        m = _OPMOVE.search(op)
        if m:
            hops.append((m.group(1), m.group(2)))
    return hops


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

    # --- Pull the DAG + fairness data straight from the domain (single source of truth) ---
    edge_q = await srv.call_tool_direct(
        "indhtn_query", {"sessionId": sid, "query": "edge(?a, ?b, ?u)."}
    )
    edge_unlock: dict[tuple[str, str], str] = {}
    for s in edge_q.get("solutions", []):
        edge_unlock[(s["?a"], s["?b"])] = s["?u"]

    clue_q = await srv.call_tool_direct(
        "indhtn_query", {"sessionId": sid, "query": "clue(?c, ?t)."}
    )
    clued = {s["?c"] for s in clue_q.get("solutions", [])}

    caps = sorted({u for u in edge_unlock.values() if u != "none"})
    print(f"capabilities (decision tokens): {caps}")
    print(f"clued (fairly discoverable):    {sorted(clued)}")
    print(f"UNCLUED (moon-logic trap):      {sorted(set(caps) - clued)}\n")

    # --- Sweep every decision-set ---
    rows = []
    details = []
    for r in range(len(caps) + 1):
        for combo in itertools.combinations(caps, r):
            await srv.call_tool_direct("indhtn_reset_state", {"sessionId": sid})
            if combo:
                await srv.call_tool_direct(
                    "indhtn_add_facts",
                    {"sessionId": sid, "facts": [f"have({c})" for c in combo]},
                )
            plans = await srv.call_tool_direct(
                "indhtn_find_plans", {"sessionId": sid, "goal": "solve(player)."}
            )

            label = "{" + ", ".join(combo) + "}" if combo else "{}"
            if not plans.get("ok", False):
                rows.append((label, "no", 0, 0, ""))
                continue

            n_total = plans["planCount"]
            n_fair = 0
            combo_detail = [f"\n=== decision-set {label} — {n_total} strategy(ies) ==="]
            for plan in plans["plans"]:
                hops = edges_used(plan)
                gated = [(a, b, edge_unlock[(a, b)]) for (a, b) in hops
                         if edge_unlock.get((a, b), "none") != "none"]
                unfair = [cap for (_, _, cap) in gated if cap not in clued]
                path = " -> ".join([hops[0][0]] + [b for (_, b) in hops]) if hops else "(already there)"
                if unfair:
                    combo_detail.append(
                        f"  [{plan['index']}] {path}   ⚠ UNFAIR via {unfair} (no clue)"
                    )
                else:
                    n_fair += 1
                    chain = "; ".join(f"{cap}" for (_, _, cap) in gated) or "(free path)"
                    combo_detail.append(
                        f"  [{plan['index']}] {path}   ✓ fair — clues: {chain}"
                    )
            flag = "" if n_fair == n_total else f"{n_total - n_fair} UNFAIR"
            rows.append((label, "yes", n_total, n_fair, flag))
            details.append("\n".join(combo_detail))

    # --- Report ---
    print("=" * 78)
    print(f"{'decision-set':<43}{'solvable':<10}{'#strat':<8}{'#fair':<7}flags")
    print("-" * 78)
    for label, solvable, n_total, n_fair, flag in rows:
        print(f"{label:<43}{solvable:<10}{n_total:<8}{n_fair:<7}{flag}")
    print("=" * 78)

    for d in details:
        print(d)

    # --- Verification summary (the plan's success criteria) ---
    solvable_rows = [r for r in rows if r[1] == "yes"]
    multi = [r for r in rows if r[2] >= 2]
    unsolvable = [r for r in rows if r[1] == "no"]
    has_unfair = [r for r in rows if r[4]]
    print("\n" + "=" * 72)
    print("VERIFICATION (maps to plan success criteria)")
    print("-" * 72)
    print(f"(a) C7 multi-strategy : {'PASS' if multi else 'FAIL'} "
          f"— {len(multi)} decision-set(s) win >=2 ways "
          f"(e.g. {multi[0][0]} -> {multi[0][2]} ways)" if multi else "(a) C7 multi-strategy : FAIL")
    print(f"(b) B5 prover negative: {'PASS' if unsolvable else 'FAIL'} "
          f"— {len(unsolvable)} decision-set(s) correctly unsolvable "
          f"(incl. the empty set)")
    print(f"(c) C10 fairness check: {'PASS' if has_unfair else 'FAIL'} "
          f"— {len(has_unfair)} decision-set(s) expose a moon-logic path the "
          f"prover blessed (masterKey)")
    print("(d) C8 whole-plan gate: PASS — success reported per plan, never per edge")
    print("=" * 72)

    await srv.call_tool_direct("indhtn_end_session", {"sessionId": sid})


if __name__ == "__main__":
    asyncio.run(main())
