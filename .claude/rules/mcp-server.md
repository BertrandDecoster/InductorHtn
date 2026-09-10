# MCP Server

Model Context Protocol server exposing InductorHTN to AI assistants. Two
families of tools:

- **Level play** (`indhtn_load_level` ...): a player-perspective playtest over
  a level directory, on the Python bindings. Needs no executable.
- **REPL** (`indhtn_start_session` ...): a raw `indhtn` REPL subprocess for
  Prolog queries and ad-hoc `.htn` files. Needs `build/Release/indhtn.exe`.

## Architecture

```
┌─────────────┐   MCP (stdio)   ┌──────────────────────────────┐
│ AI Assistant│ ◄─────────────► │ indhtn_mcp.server            │
└─────────────┘                 │  ├─ level_tools.LevelSession │──► indhtnpy + htn_metrics
                                │  └─ session.SessionManager   │──► indhtn.exe (subprocess)
                                └──────────────────────────────┘
```

## Files

```
.mcp.json                       # {"command": "python", "args": ["mcp-server/launch.py"]}
mcp-server/
├── launch.py                   # resolves .venv python, the exe, PYTHONPATH; --check
├── indhtn_mcp/
│   ├── server.py               # tool registry (name -> coroutine), stdio transport
│   ├── level_tools.py          # LevelSession: observe / actions / act / undo / explain
│   └── session.py              # REPL subprocess management
├── tests/test_level_tools.py   # the LevelSession spec
├── setup.py, requirements.txt  # mcp>=1.2,<2 (2.x dropped the decorator API)
└── README.md
```

## Launching

`.mcp.json` runs `python mcp-server/launch.py`, which re-executes the server
with `.venv/Scripts/python.exe` (or `.venv/bin/python`), the first executable
found under `build/`, and `PYTHONPATH` joined with `os.pathsep` over
`mcp-server`, `gui/backend`, `src/Python`. Check it without starting:

```bash
python mcp-server/launch.py --check
```

The executable is optional: the server starts without it and only the REPL
tools fail, with a message saying so.

## Level play tools

All take `levelSessionId` except `indhtn_load_level` and `indhtn_fun`.

| Tool | What it returns |
|------|-----------------|
| `indhtn_load_level(level)` | `levelSessionId`, first observation, first actions. Plans the whole level once. |
| `indhtn_observe` | The player's view: location, skills, charges, companions with **intentions** ("Warden: I'll drag bearer from exit into corridor"), enemies, region features. No strategy names. |
| `indhtn_actions` | The player's own legal moves with narration and consequences. Companion-only steps are auto-advanced by planner preference first. `wait` is offered when a companion could act instead. |
| `indhtn_act(action, force=false)` | Takes the move. Off-plan moves are refused with the legal list, unless `force=true`: then the operator's grounded del/add is applied and the level is **re-planned from the new world**. `plans_remaining` may drop to 0. |
| `indhtn_undo` | Back to the previous decision. |
| `indhtn_explain` | Afterwards: class reached, classes missed, and per decision the alternatives and the classes each led to. |
| `indhtn_state` | Full fact set, operators taken, `plans_remaining`. |
| `indhtn_fun(level, ablate, loadouts)` | The scorecard JSON (`docs/FUN_METRICS.md`). Ablate/loadouts can take minutes; cached under `.htn_metrics_cache/`. |

Every session writes `.playthroughs/<level>/<timestamp>.json`. See
`.claude/rules/level-design-loop.md` for how to play honestly.

`indhtn_state_diff` and `indhtn_step` are **deprecated**: they return plan
text and apply raw operators without preconditions. Use the level tools.

## REPL tools

| Tool | Description |
|------|-------------|
| `indhtn_start_session(files)` | Start a REPL with `.htn`/`.pl` files loaded |
| `indhtn_query(sessionId, query)` | Prolog query |
| `indhtn_find_plans(sessionId, goal)` | `goals(goal)` |
| `indhtn_apply_plan(sessionId, goal)` | `apply(goal)` |
| `indhtn_reset`, `indhtn_toggle_trace`, `indhtn_end_session` | `/r`, `/t`, cleanup |
| `indhtn_lint(source)`, `indhtn_introspect(source)` | Diagnostics / structure of HTN source (no session) |

## Adding a tool

1. Add a `Tool(...)` entry in `handle_list_tools` (`server.py`).
2. Write `async def _my_tool(self, args: dict) -> List[TextContent]`.
3. Register it in the `self._handlers` dict in `__init__`. Dispatch is by name; there is no if/elif chain to extend.
4. Run anything slow through `asyncio.to_thread` so the event loop stays responsive.

## Testing

```bash
PYTHONPATH=src/Python python -m pytest mcp-server/tests/test_level_tools.py -q
python -m pytest mcp-server/tests -q       # REPL tests skip when the exe is missing
```
