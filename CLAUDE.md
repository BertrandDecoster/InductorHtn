# CLAUDE.md

InductorHTN: Lightweight HTN planner for C++/Python. SHOP model, memory-constrained, stackless execution.

Always enter the python venv
For Windows:
`source .venv/Scripts/activate`

## Build & Test

See `BUILD.md` for full commands.

```bash
# Quick build (Windows, from Developer Command Prompt)
cmake --build ./build --config Release

# Test
./build/Release/runtests.exe

# Interactive mode
./build/Release/indhtn.exe Examples/Taxi.htn
```

## Directory Structure

```
src/FXPlatform/Htn/      # HTN engine (HtnPlanner, HtnMethod, HtnOperator)
src/FXPlatform/Prolog/   # Prolog engine (HtnGoalResolver, HtnRuleSet, HtnTerm)
src/FXPlatform/Parser/   # Lexer and parser framework
src/Python/              # Python bindings (indhtnpy)
gui/                     # Web IDE (Flask backend, React frontend)
mcp-server/              # MCP server for AI assistants
Examples/                # .htn example files
components/              # Reusable HTN component library
levels/                  # Puzzle level definitions
```

## Component System

Reusable building blocks for puzzle game HTN rulesets. See `.claude/rules/component-system.md` for full details.

**Layers:** Primitives → Strategies → Goals → Levels

**CLI:**
```bash
PYTHONPATH=src/Python python -m htn_components <command>

status                           # List all components with certification
certify <path> [--dry-run]       # Full certification (linter + tests + design)
test <path>                      # Run component tests
test-all [--layer <layer>]       # Batch test all components
play <level> [--solution N | --class LABEL] [-i]   # Plan narrative (grounded effects)
trace <level> [--goal GOAL]      # Decomposition tree visualization
verify <level>                   # deps + tests + plan + fun scorecard (non-gating)

fun <level> [--ablate] [--loadouts] [--json] [--md FILE]   # Fun scorecard
fun-all                          # Comparison table across levels
fun-compare <a> <b>              # Side-by-side profile diff
```

## Fun Metrics

`fun` scores the *shape of a level's solution space* — how many genuinely different
ways exist, how deep they are, whether the player is required, and which of the
declared X-of-Y choices work. It never claims a level is fun.

Full definition, bands, and known blind spots: **`docs/FUN_METRICS.md`**.
Calibration fixtures: `tests/fun_fixtures/`; tests: `python -m pytest tests/test_fun_metrics.py`.

Bands and weights are data, in `src/Python/htn_metrics/metrics.json` — calibrate there, not in code.

A level opts into the choice-space family (F4) by declaring facts in `level.htn`:
```prolog
funChoiceSpace(kit, 2).                       % pick 2 ...
funChoice(kit, emp).                          % ... from these
funChoiceFact(emp, carrying(player, emp)).    % how a pick alters the world
funBlocker(door).                             % must be solved
funBlockerGoal(door, clear(door)).            % optional; else derived from goals()
```
`--ablate` and `--loadouts` re-plan many times; results are disk-cached in
`.htn_metrics_cache/`, so a second run over an unchanged level is fast.

## Level Design Loop & MCP Play

Iterate a level as: one hypothesis → one rule change → certify → play it through the
MCP level tools as the player → `explain`/`fun` afterwards → compare → a human tries it.
Rules: `.claude/rules/level-design-loop.md`. Tools: `.claude/rules/mcp-server.md`
(`indhtn_load_level`, `indhtn_observe`, `indhtn_actions`, `indhtn_act`, `indhtn_undo`,
`indhtn_explain`, `indhtn_fun`). `.mcp.json` starts the server via `mcp-server/launch.py`;
`python mcp-server/launch.py --check` verifies the setup. Playthroughs land in
`.playthroughs/` (gitignored).

**Current certified components:**
- Core (unified vocabulary, `components/core/`): primitives `core_world`, `core_chemistry`,
  `core_attunement`, `core_aggro`; strategies `the_burn`, `the_slipstream`; goal
  `defeat_group`; level `grease_trap`
- Original tree: primitives `locomotion`, `tags`, `aggro`; strategies `the_burn`,
  `the_slipstream`; goals `defeat_enemy`, `clear_room`; level `puzzle1`
- GameHack (`components/gamehack/`): primitives `gh_movement`, `gh_tags`, `gh_aggro`,
  `gh_skills`; action `gh_tag_application`; strategies `wet_and_electrocute`,
  `stun_and_slow_skill`, `stun_and_burn`; goal `plan_to_damage`; levels `gamehack_gh4`,
  `gamehack_gh7`, `gamehack_mvp`, `gamehack_multipath` (`gh_doors`, `complete_toy_level`
  are not certified)

Core vocabulary and operator rules: `.claude/rules/component-system.md`.

## Critical Rules

### Variable Syntax
Variables use `?` prefix: `?varname` (not Prolog capitalization)
```prolog
travel(?from, ?to) :- if(at(?from)), do(walk(?from, ?to)).
```

### HTN Syntax
- **Methods**: `task() :- if(conditions), do(subtasks).`
- **Operators**: `action() :- del(remove), add(insert).`
- **Modifiers**: `else`, `anyOf`, `allOf`, `hidden`
- **Parallel**: `parallel(taskA, taskB, ...)` - marks tasks for parallel execution

### Parallel Execution Feature

The `parallel()` keyword enables multi-agent parallel execution through post-processing:

```prolog
% Tasks within parallel() can execute concurrently
workflow() :- if(), do(setup, parallel(movePlayer, moveWarden), cleanup).
movePlayer :- del(playerAt(a)), add(playerAt(b)).
moveWarden :- del(wardenAt(x)), add(wardenAt(y)).
```

**How it works:**
- During planning: Tasks are planned sequentially (no search explosion)
- Plan output: Contains `beginParallel`/`endParallel` markers
- Post-processing: `PlanParallelizer` assigns timesteps for parallel execution

**Key files:**
- `src/FXPlatform/Htn/HtnPlanner.cpp` - `parallel()` handling in `CheckForSpecialTask()`
- `src/FXPlatform/Htn/PlanParallelizer.h/cpp` - Post-processor for timestep assignment
- `src/Tests/Htn/HtnParallelTests.cpp` - Test suite

**Python API:**
```python
error, parallelized = planner.GetParallelizedPlan(solutionIndex)
# Returns JSON: {"operators": [{"operator": "taskA", "timestep": 0, "scopeId": 1, "dependsOn": []}, ...]}
```

**Design notes:**
- Domain author is responsible for ensuring tasks within `parallel()` are truly independent
- Tasks in same parallel scope get same timestep (can run concurrently)
- Avoids exponential complexity of partial-order planning

### Factory Pattern
All terms must come from the same `HtnTermFactory` for unification to work.

### Test Initialization
Always clear state before tests:
```cpp
compiler->ClearWithNewRuleSet();
```

### Expected Test Formats
- Success with operators: `"[ { operator1(args) } ]"`
- Empty plan: `"[ { () } ]"`
- Failure: `"null"`
- Variable bindings: `"((?X = value))"`

## Code Style

- C++11 standard
- Platform-specific code in `Win/`, `iOS/`, `Posix/` directories
- Use existing patterns for new components

## All Executables & Tools

### C++ Executables (build/Release/)

| Executable | Description | Usage |
|------------|-------------|-------|
| `indhtn.exe` | Interactive HTN planner REPL | `./build/Release/indhtn.exe Examples/Taxi.htn` |
| `runtests.exe` | Unit test runner | `./build/Release/runtests.exe` |
| `indhtnpy.dll` | Python bindings library | Used by Python scripts via ctypes |

### GUI Tools (gui/)

| Tool | Description | Usage |
|------|-------------|-------|
| `start_gui.py` | Launch full GUI (backend + frontend) | `python gui/start_gui.py [--no-browser]` |
| `start.bat` | Windows batch launcher | `gui\start.bat` |
| `backend/app.py` | Flask REST API server (port 5000) | `python gui/backend/app.py` |
| `test_backend.py` | Backend API tests | `python gui/test_backend.py` |
| `test_htn_api.py` | HTN API tests | `python gui/test_htn_api.py` |

### Frontend (gui/frontend/)

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server (port 5173) |
| `npm run build` | Build production frontend |
| `npm run preview` | Preview production build |

### Python Scripts (src/Python/)

| Script | Description | Usage |
|--------|-------------|-------|
| `htn_test_suite.py` | Test suite CLI runner | `python htn_test_suite.py [--file FILE] [--verbose] [--json] [--list]` |
| `PythonUsage.py` | Basic usage examples | `python PythonUsage.py` |
| `PythonUsageTrace.py` | Tracing/debugging examples | `python PythonUsageTrace.py` |
| `PythonUsageTree.py` | Decomposition tree examples | `python PythonUsageTree.py` |
| `PythonUsageBD.py` | Block Dude game example | `python PythonUsageBD.py` |
| `HtnTreeReconstructor.py` | Tree reconstruction utilities | `python HtnTreeReconstructor.py` |

### MCP Server (mcp-server/)

| Tool | Description | Usage |
|------|-------------|-------|
| `indhtn_mcp/server.py` | MCP Protocol server | `python -m indhtn_mcp.server` or `indhtn-mcp` after install |
| `play_taxi_game.py` | Interactive Taxi game demo | `python play_taxi_game.py` |
| `test_server.py` | MCP server tests | `python test_server.py` |
| `test_session_only.py` | Session management tests | `python test_session_only.py` |

### Example Domains (Examples/)

| File | Description |
|------|-------------|
| `Taxi.htn` | Taxi planning domain |
| `Taxi2.htn` | Extended taxi domain |
| `Game.htn` | Game planning domain |
| `GameHack*.htn` | Game domain variants |
| `Jam.htn` | Simple example domain |
| `JordanAdventure.pl` | Prolog adventure example |
| `TestFailures.htn` | Failure testing domain |
