# InductorHTN MCP Server

MCP server that lets an AI assistant (Claude Code, Cursor, etc.) "play HTN
games": load rulesets, query state, find plans, apply operators, and
checkpoint/restore the world. The server wraps the in-process Python
bindings (`src/Python/indhtnpy.py`) so its behaviour matches the unit-test
framework in `src/Python/htn_test_framework.py`.

## Quick start

```bash
# 1. Build the bindings shared library.
cmake --build /path/to/InductorHtn/build --config Release

# 2. Install the MCP server.
cd /path/to/InductorHtn/mcp-server
pip install -e .

# 3. Launch.
indhtn-mcp
```

When invoked under `claude_desktop_config.json` (or another MCP host), the
`mcp.json` in this directory shows the recommended wiring.

## Library discovery

The server uses these locations to find `libindhtnpy.{dylib,so}` /
`indhtnpy.dll`, in order:

1. `$INDHTN_LIB_PATH` — full path to the library file (set this if the
   library lives somewhere unusual).
2. Path relative to the package: `<repo>/build`, `<repo>/build/Release`,
   `<repo>/build/Debug`, `<repo>/src/Python`. Works when the MCP server is
   installed in-place inside the InductorHTN checkout.
3. `$INDHTN_REPO_ROOT` + the same subpaths. Use this when the server is
   installed elsewhere but the build outputs live in a known repo.
4. Whatever `ctypes.util.find_library("indhtnpy")` finds (system library
   paths).

The first location that resolves wins. The server also pre-loads the
library and augments the OS library search path so subsequent `ctypes.CDLL`
calls inside `indhtnpy.py` find an already-mapped image.

## Tool surface (29 tools)

### Session lifecycle
- `indhtn_create_session(debug?, memoryBudgetBytes?)` → `{sessionId}`
- `indhtn_end_session(sessionId)`
- `indhtn_list_sessions()`
- `indhtn_reset_state(sessionId)` — drop planner, replay loaded sources
- `indhtn_clear_ruleset(sessionId)` — drop everything (sources, snapshots)

### Loading
- `indhtn_load_files(sessionId, paths, dialect?)`
- `indhtn_load_source(sessionId, source, dialect?, label?)`
- `indhtn_append_source(sessionId, source, dialect?, label?)` — incremental

Dialects: `htn`, `htn_custom_vars` (default — `?var` prefix),
`prolog`, `prolog_custom_vars`, `auto`.

### Introspection
- `indhtn_list_facts(sessionId, filterPredicate?)`
- `indhtn_list_goals(sessionId)` — `goals(...)` directives in the ruleset
- `indhtn_introspect(source)` — static parse: methods, operators, facts
- `indhtn_lint(source)` — diagnostics from the GUI linter

### Query / Plan
- `indhtn_query(sessionId, query)` — Prolog query (no `do()`)
- `indhtn_find_plans(sessionId, goal, maxPlans?)` — HTN planning
- `indhtn_get_decomposition_tree(sessionId, solutionIndex?)`
- `indhtn_method_failures(sessionId, goal)` — per-method failure histogram:
  where each method's decomposition blocks (precondition gate vs body subtask).
  Returns `code: "choice_tracking_unavailable"` unless the engine was built with
  `INDHTN_CHOICE_TRACKING`. See `docs/method-failure-analysis.md`.
- `indhtn_preview_solution_facts(sessionId, solutionIndex?)`
- `indhtn_get_parallelized_plan(sessionId, solutionIndex?)`

### Application
- `indhtn_apply_plan(sessionId, solutionIndex?)` — apply a cached solution
- `indhtn_apply_operator(sessionId, operator)` — apply one primitive op;
  fails with `code: "preconditions_failed"` if `del()` clauses don't match
  current state, or `code: "expanded_to_multiple_ops"` if the call is a
  method that decomposes into multiple operators.

### Snapshots
- `indhtn_snapshot_state(sessionId, name)`
- `indhtn_restore_state(sessionId, name)`
- `indhtn_list_snapshots(sessionId)`
- `indhtn_delete_snapshot(sessionId, name)`

Snapshots capture state and the number of loaded sources at capture time.
Restore drops the planner, replays the kept sources, then reconciles facts
back to the snapshot. Sources appended after a snapshot are unwound on
restore.

### State manipulation
- `indhtn_add_facts(sessionId, facts: string[])`
- `indhtn_remove_facts(sessionId, facts: string[])`

### Tracing / metrics
- `indhtn_set_trace(sessionId, enabled, alsoStdout?, traceType?, traceDetail?)`
- `indhtn_get_traces(sessionId, clearAfter?)`
- `indhtn_get_resolution_steps(sessionId)`

Trace state in the C++ engine is process-global. The server enforces "at
most one session capturing at a time" via a process-wide lock.

## Response shape: `ok`, partial failures, and `errors[]`

Every handler returns JSON with an `ok` boolean. The convention:

- `ok: true` means **the call was dispatched without raising**. It does
  *not* mean every item in a batch succeeded.
- `ok: false` is reserved for errors that prevented dispatch entirely
  (invalid arguments, unknown session, bindings raised, call timeout,
  etc.). The payload always carries a `code` discriminant —
  `invalid_argument`, `not_found`, `runtime_error`, `call_timeout`,
  `preconditions_failed`, `expanded_to_multiple_ops`,
  `ambiguous_unification`, `compile_error`, ...
- Tools that take a list of inputs (`indhtn_add_facts`,
  `indhtn_load_files`, `indhtn_remove_facts`) and tools that replay
  multiple sources (`indhtn_reset_state`, `indhtn_restore_state`)
  return per-item status in `errors[]` / `replay[]` alongside the
  success list, with `ok: true` even on partial failure.

**Implication for callers**: never branch only on `ok` for batch tools.
Always inspect `errors[]` / `replay[]` afterwards. Example:

```python
r = await call("indhtn_add_facts", {"sessionId": sid, "facts": facts})
if not r["ok"]:
    raise RuntimeError(r["error"])           # dispatch failure
if r.get("errors"):
    # Some facts compiled, some did not — partial failure.
    handle_partial(r["added"], r["errors"])
```

| Tool                       | `ok=true` payload keys to inspect |
| -------------------------- | ---------------------------------- |
| `indhtn_add_facts`         | `added`, `errors`                  |
| `indhtn_load_files`        | `loaded`, `errors`                 |
| `indhtn_reset_state`       | `replay[].error`                   |
| `indhtn_restore_state`     | `replay[].error`                   |
| `indhtn_remove_facts`      | `removed`, `notPresent`            |

## Parity with the test framework

`tests/test_parity.py` proves the MCP produces the same plans and final
state as the `htn_test_framework.HtnTestSuite` (which the component tests
use) for representative cases. Run with:

```bash
cd /path/to/InductorHtn/mcp-server
python -m pytest tests/ -v
```

The mapping from framework methods to MCP tools:

| `HtnTestSuite` method     | MCP tool                                     |
| ------------------------- | -------------------------------------------- |
| `load_file(path)`         | `indhtn_load_files([path])`                  |
| `compile_additional(src)` | `indhtn_append_source(src)`                  |
| `set_state(facts)`        | `indhtn_add_facts(facts)`                    |
| `get_state()`             | `indhtn_list_facts()`                        |
| `query_all(q)`            | `indhtn_query(q)`                            |
| `run_goal(g, idx)`        | `indhtn_find_plans(g)` + `indhtn_apply_plan(idx)` |
| `snapshot_state()`        | `indhtn_snapshot_state(name)`                |
| `restore_state()`         | `indhtn_restore_state(name)`                 |
| `reset()`                 | `indhtn_clear_ruleset()`                     |

## Demo

Walk through the Taxi domain end-to-end:

```bash
cd mcp-server
python play_taxi_game.py
```

Shows session creation, file load, multi-solution planning, per-solution
preview, apply, query, and snapshot/restore.

## Notes

- The earlier draft of this server shelled out to the `indhtn` executable
  over stdio. That design is gone. To use the raw REPL, run
  `./build/Release/indhtn` directly — the MCP no longer exposes it.
- Each session owns one `HtnPlanner` C++ instance. Multiple sessions in the
  same process are isolated except for **trace state** and the
  **debug-tracing flag**, which are process-global in the engine.
