#!/usr/bin/env python3
"""Drive the Taxi example domain through the new in-process MCP API.

Usage:  python play_taxi_game.py
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from indhtn_mcp.server import create_server


REPO = Path(__file__).resolve().parents[1]
TAXI = REPO / "Examples" / "Taxi.htn"


def header(msg: str) -> None:
    print()
    print("=" * 60)
    print(msg)
    print("=" * 60)


async def play() -> None:
    srv = create_server()
    sid = (await srv.call_tool_direct("indhtn_create_session", {}))["sessionId"]

    header("1. Load Taxi.htn")
    r = await srv.call_tool_direct(
        "indhtn_load_files", {"sessionId": sid, "paths": [str(TAXI)]}
    )
    print(json.dumps(r, indent=2))

    header("2. Initial state (location, cash)")
    print(await srv.call_tool_direct(
        "indhtn_query", {"sessionId": sid, "query": "at(?where)."}
    ))
    print(await srv.call_tool_direct(
        "indhtn_query", {"sessionId": sid, "query": "have-cash(?amount)."}
    ))

    header("3. Snapshot starting state")
    print(await srv.call_tool_direct(
        "indhtn_snapshot_state", {"sessionId": sid, "name": "start"}
    ))

    header("4. Find plans for travel-to(uptown)")
    plans = await srv.call_tool_direct(
        "indhtn_find_plans", {"sessionId": sid, "goal": "travel-to(uptown)"}
    )
    for plan in plans["plans"]:
        print(f"  [{plan['index']}] " + " -> ".join(plan["operators"]))

    header("5. Preview each solution's effect on state")
    for plan in plans["plans"]:
        preview = await srv.call_tool_direct(
            "indhtn_preview_solution_facts",
            {"sessionId": sid, "solutionIndex": plan["index"]},
        )
        print(
            f"  solution {plan['index']}: added={preview['added']} "
            f"removed={preview['removed']}"
        )

    header("6. Apply solution 0")
    print(await srv.call_tool_direct(
        "indhtn_apply_plan", {"sessionId": sid, "solutionIndex": 0}
    ))

    header("7. State after apply")
    print(await srv.call_tool_direct(
        "indhtn_query", {"sessionId": sid, "query": "at(?where)."}
    ))

    header("8. Restore snapshot")
    print(await srv.call_tool_direct(
        "indhtn_restore_state", {"sessionId": sid, "name": "start"}
    ))
    print(await srv.call_tool_direct(
        "indhtn_query", {"sessionId": sid, "query": "at(?where)."}
    ))

    await srv.call_tool_direct("indhtn_end_session", {"sessionId": sid})


if __name__ == "__main__":
    asyncio.run(play())
