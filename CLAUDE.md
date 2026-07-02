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

- **Writing rulesets** → `docs/reference/ruleset-writing.md` (heuristics, examples, validated optimizations; worked example: `Examples/TrunkThumper.htn`)
- **Exemplars to copy** → `docs/reference/exemplars/` (Blocks World, Logistics, Barman, Rover translated to InductorHTN syntax, one per design pattern). Improving a ruleset from an instruction? Use the `/htn-improve` command (`.claude/commands/htn-improve.md`).
- **Iterating on rulesets** (debug/analyze/improve) → `docs/reference/ruleset-iterating.md`
- **Syntax & Prolog reference** → `docs/reference/ruleset-htn-syntax.md`, `docs/reference/prolog-reference.md`
- **Planner internals** → `docs/reference/planner-internals.md`
- **Component system** → `docs/reference/component-system.md`
- **Tools** (REPL, tests, Python, GUI, MCP, components CLI) → `docs/TOOLS.md`
- **Design decisions** (legacy engine, language, HDDL, online rulesets) → `docs/DESIGN.md`
- **Fork upgrades** (new keywords, query tracing, failure tracking) → `docs/upgrades/`
- **Legacy upstream docs** → `docs/legacy/`

## Critical Rules

### Variable Syntax
Variables use `?` prefix: `?varname` (not Prolog capitalization).
```prolog
travel(?from, ?to) :- if(at(?from)), do(walk(?from, ?to)).
```

### HTN Syntax
- **Methods**: `task() :- if(conditions), do(subtasks).`
- **Operators**: `action() :- del(remove), add(insert).`
- **Numeric effects**: `increase(pred(args), delta)` / `decrease(pred(args), delta)` — see `docs/reference/ruleset-htn-syntax.md`
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
