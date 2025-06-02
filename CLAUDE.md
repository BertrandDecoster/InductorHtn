# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

InductorHTN is a lightweight Hierarchical Task Network (HTN) planning engine for C++ and Python. It implements the classic SHOP Planner model and is designed for memory-constrained environments. The engine combines HTN planning with Prolog reasoning capabilities.

## Key Architecture

### Core Components
- **HTN Engine** (`src/FXPlatform/Htn/`): Planning algorithm, methods, operators
- **Prolog Engine** (`src/FXPlatform/Prolog/`): Facts, rules, goal resolution
- **Parser** (`src/FXPlatform/Parser/`): Lexer and parser framework
- **Platform Support** (`src/FXPlatform/[Win|iOS|Posix]/`): OS-specific implementations

### Important Design Patterns
- **Factory Pattern**: `HtnTermFactory` manages term creation with interning for memory efficiency
- **Stackless Execution**: Memory-efficient planning suitable for constrained environments
- **Hybrid HTN/Prolog**: Variables use `?` prefix (not capitalization like standard Prolog)

## Build Commands

```bash
# Create build directory
mkdir build && cd build

# Configure with CMake (macOS example)
cmake -G "Unix Makefiles" ../src
# or for Xcode:
cmake -G "Xcode" ../src

# Build
cmake --build ./ --config Release
# or
cmake --build ./ --config Debug

# Run tests
./runtests

# Python tests (requires libindhtnpy.dylib in /usr/local/lib)
cd ../src/Python
python PythonUsage.py
```

## Development Workflow

### Running Interactive Mode
```bash
./indhtn Examples/Game.htn
```

### Testing
- Unit tests: `./runtests` 
- Python interface tests: `python src/Python/PythonUsage.py`
- Test files are in `src/Tests/`

### HTN Syntax Key Points
- Variables use `?varname` (not Prolog capitalization)
- Methods decompose complex tasks: `travel-to(?dest) :- if(...), do(...).`
- Operators are primitive actions: `walk(?from, ?to) :- del(at(?from)), add(at(?to)).`
- Mix HTN constructs with standard Prolog rules

### Memory Management
- All terms must come from the same `HtnTermFactory`
- Configurable memory budgets for planning
- Returns out-of-memory status when limits exceeded

## Code Style Guidelines
- C++11 standard
- Platform-specific code isolated in Win/iOS/Posix directories
- Use existing patterns for new components