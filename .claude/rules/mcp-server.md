---
description: MCP server for AI assistant integration
globs: mcp-server/**
---

# MCP Server

Model Context Protocol server that lets AI assistants drive an in-process
`HtnPlanner`. Each session owns one C++ planner instance via the
`indhtnpy` bindings — no subprocess, no stdio REPL parsing.

## Architecture

```
┌─────────────┐     MCP Protocol      ┌─────────────────────┐
│ AI Assistant│ ◄──────────────────► │  MCP Server (Python)│
└─────────────┘   (stdio JSON-RPC)    │                     │
                                      │  ┌───────────────┐  │
                                      │  │ SessionManager│  │
                                      │  │   ┌─────────┐ │  │
                                      │  │   │ Session │←┼──┼── indhtnpy → libindhtnpy
                                      │  │   │  +lock  │ │  │   (ctypes / C++)
                                      │  │   └─────────┘ │  │
                                      │  └───────────────┘  │
                                      └─────────────────────┘
```

The previous draft of this server shelled out to `indhtn` over stdio and
parsed REPL prompts. That design is gone — see `mcp-server/README.md` for
the migration note and full tool surface.

## File Structure

```
mcp-server/
├── indhtn_mcp/
│   ├── server.py           # MCP protocol implementation + tool dispatch
│   ├── session.py          # HtnSession + SessionManager (in-process)
│   ├── snapshots.py        # Named state snapshots
│   ├── bindings_loader.py  # Resolves the libindhtnpy path
│   └── result_format.py    # JSON parsing helpers
├── mcp.json                # MCP host wiring (claude_desktop_config.json snippet)
└── setup.py                # Package installation
```

## MCP Tools (29 total)

Authoritative list lives in `mcp-server/README.md`. The headline tools:

| Tool | Purpose |
|------|---------|
| `indhtn_create_session` | Create a session, returns `sessionId` |
| `indhtn_end_session` | End a session |
| `indhtn_load_files` / `indhtn_load_source` / `indhtn_append_source` | Compile rulesets |
| `indhtn_query` | Prolog query (no `do()`) |
| `indhtn_find_plans` | HTN planning; caches solutions |
| `indhtn_apply_plan` | Apply a cached solution by index |
| `indhtn_apply_operator` | Apply a single primitive operator |
| `indhtn_list_facts` / `indhtn_add_facts` / `indhtn_remove_facts` | State manipulation |
| `indhtn_snapshot_state` / `indhtn_restore_state` | Checkpoint / undo |
| `indhtn_set_trace` / `indhtn_get_traces` | Capture planner trace |
| `indhtn_lint` / `indhtn_introspect` | Static analysis (no session) |
| `indhtn_get_decomposition_tree` / `indhtn_preview_solution_facts` / `indhtn_get_parallelized_plan` | Plan inspection |
| `indhtn_method_failures` | Per-method failure histogram — where each method's decomposition blocks (gate vs body subtask). Needs an `INDHTN_CHOICE_TRACKING` build |

## Response convention: `ok`, partial failures, and `errors[]`

Every handler returns JSON with an `ok` boolean. The convention is:

- `ok: true` means the call was **dispatched without raising**. The handler
  reached the bindings and returned a structured response.
- `ok: true` does **not** mean every item in a batch succeeded. Tools that
  take a list of inputs (`indhtn_add_facts`, `indhtn_load_files`,
  `indhtn_reset_state`, `indhtn_restore_state`) return per-item status in
  an `errors[]` or `replay[]` array alongside the success list.
- `ok: false` is reserved for errors that prevented dispatch entirely:
  invalid arguments, unknown session, the bindings raised, etc. The
  payload always carries a `code` discriminant (`preconditions_failed`,
  `expanded_to_multiple_ops`, `ambiguous_unification`,
  `compile_error`, `runtime_error`, `not_found`, `invalid_argument`, ...).

**Implication for callers**: never branch only on `ok` for batch tools.
Always inspect `errors[]` / `replay[]` for partial failure. A typical
check looks like:

```python
r = await call("indhtn_add_facts", {...})
if not r["ok"]:
    raise RuntimeError(r["error"])
if r.get("errors"):
    # Partial failure — some facts compiled, some did not.
    raise RuntimeError(f"add_facts had partial failure: {r['errors']}")
```

## Session Management (`session.py`)

- One `HtnSession` per `sessionId`, owning one `HtnPlanner` C++ instance.
- Per-session `asyncio.Lock` serialises calls into the same planner.
- `SessionManager` evicts the oldest session when `max_sessions` is hit.
- A process-wide `trace_lock` serialises planner work whenever trace
  capture is active (because the C++ trace buffer is global).

### Concurrency caveats

- The C++ bindings calls are synchronous from Python. The server wraps
  long-running calls (`find_plans`, `query`, `apply_*`) in
  `asyncio.to_thread` and `asyncio.wait_for`, controlled by
  `$INDHTN_CALL_TIMEOUT_S` (default 60s). On timeout, the caller gets a
  `runtime_error` with code `call_timeout`; the C++ call itself cannot
  be hard-cancelled and will continue to run until it completes naturally.
- Trace state (`g_traceBuffer`, `g_captureActive`, `g_traceCallback`) is
  process-global in the engine. The server holds `trace_lock` across
  every planner-driving call while any session is capturing, so traces
  from other sessions don't bleed into the capture buffer.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `INDHTN_LIB_PATH` | (resolved) | Override path to `libindhtnpy.{so,dylib}` / `indhtnpy.dll` |
| `INDHTN_REPO_ROOT` | (auto)     | Where to look for `build/`, `src/Python/` |
| `INDHTN_MAX_SESSIONS` | 10      | Maximum concurrent sessions |
| `INDHTN_CALL_TIMEOUT_S` | 60     | Per-call timeout for planner-driving tools |
| `INDHTN_LOG_LEVEL` | INFO       | Logging level |

## Adding New Tools

1. Add a `Tool(name=..., description=..., inputSchema=...)` entry in
   `IndHTNMCPServer._tools()`.
2. Implement `async def _h_<tool_name>(srv, args) -> List[TextContent]:`
   in `server.py`. Use `_ok_dict(...)` for success and `_err_dict(...)`
   for errors. Wrap planner-driving calls in
   `srv._run_planner_call(session, lambda: ...)` to inherit the
   to_thread + trace_lock + timeout wrapping.
3. Register in `_HANDLERS`.
4. Add a parity test in `mcp-server/tests/test_parity.py`.

## Testing

```bash
cd /Users/polycea/Projects/InductorHtn/mcp-server
python -m pytest tests/ -v
```

Tests run the bindings in-process — no subprocess setup. `test_parity.py`
asserts the MCP path produces the same plans and final state as
`htn_test_framework.HtnTestSuite` (which the C++ component tests use).
