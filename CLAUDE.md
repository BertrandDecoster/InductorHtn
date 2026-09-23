# CLAUDE.md

InductorHTN: Lightweight HTN planner for C++/Python. SHOP model, memory-constrained, stackless execution.

Always enter the python venv first. On Windows: `source .venv/Scripts/activate`.

## Build & Test

See `BUILD.md` for full commands.

```bash
cmake --build ./build --config Release   # build
./build/Release/runtests.exe             # test
./build/Release/indhtn.exe Examples/Taxi.htn   # interactive REPL
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
docs/                    # All documentation (see map below)
```

## Documentation Map

All docs live under `docs/`. Start at `docs/README.md`.

- **Authoring rulesets** → `docs/reference/authoring-rulesets.md` (worked example: `Examples/TrunkThumper.htn`)
- **Syntax & Prolog reference** → `docs/reference/htn-syntax.md`, `docs/reference/prolog-reference.md`
- **Planner internals** → `docs/reference/planner-internals.md`
- **Component system** → `docs/reference/component-system.md` (core vocabulary, operator rules)
- **Level design loop** → `docs/reference/level-design-loop.md`
- **Fun metrics** → `docs/FUN_METRICS.md`
- **Tools** (REPL, tests, Python, GUI, MCP, components CLI) → `docs/TOOLS.md`
- **Design decisions** (legacy engine, language, HDDL, online rulesets) → `docs/DESIGN.md`
- **Fork upgrades** (new keywords, query tracing, failure tracking) → `docs/upgrades/`
- **Legacy upstream docs** → `docs/legacy/`

## Component System

Reusable building blocks for puzzle game HTN rulesets. See `docs/reference/component-system.md`.

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
ways exist, how deep they are, whether any one companion can carry a plan alone (the
human's seat being idle is only a warning), and which of the declared X-of-Y choices
work. It never claims a level is fun.

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
Rules: `docs/reference/level-design-loop.md`. Tools: `docs/tools/mcp-server.md`
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

Core vocabulary and operator rules: `docs/reference/component-system.md`.

## Critical Rules

### Variable Syntax
Variables use `?` prefix: `?varname` (not Prolog capitalization).
```prolog
travel(?from, ?to) :- if(at(?from)), do(walk(?from, ?to)).
```

### HTN Syntax
- **Methods**: `task() :- if(conditions), do(subtasks).`
- **Operators**: `action() :- del(remove), add(insert).`
- **Numeric effects**: `increase(pred(args), delta)` / `decrease(pred(args), delta)` — see `docs/reference/htn-syntax.md`
- **Modifiers**: `else`, `anyOf`, `allOf`, `hidden`
- **Parallel**: `parallel(taskA, taskB, ...)` marks tasks for parallel execution — see `docs/upgrades/ruleset-keywords.md`

### Factory Pattern
All terms must come from the same `HtnTermFactory` for unification to work.

### Test Initialization
Always clear state before tests: `compiler->ClearWithNewRuleSet();`

### Expected Test Formats
- Success with operators: `"[ { operator1(args) } ]"`
- Empty plan: `"[ { () } ]"`
- Failure: `"null"`
- Variable bindings: `"((?X = value))"`

## Code Style

- C++11 standard
- Platform-specific code in `Win/`, `iOS/`, `Posix/` directories
- Use existing patterns for new components
