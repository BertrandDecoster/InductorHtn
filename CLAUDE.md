# CLAUDE.md

InductorHTN: Lightweight HTN planner for C++/Python. SHOP model, memory-constrained, stackless execution.

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
```

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
