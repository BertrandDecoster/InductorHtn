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
