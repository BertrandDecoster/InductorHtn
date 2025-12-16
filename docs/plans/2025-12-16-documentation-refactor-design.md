# Documentation Refactor Design

**Date**: 2025-12-16
**Status**: Approved

## Goal

Refactor documentation to have:
- Lean `CLAUDE.md` for AI assistant (absolute core only)
- Fine-grained `.claude/rules/` files with path-based loading
- Legacy human docs in `inductorHtnDocs/` (not referenced)
- Actionable command-only docs at root and subdirectories

## New File Structure

### Root Level (actionable commands only)
```
CLAUDE.md          # AI core rules (lean, ~80 lines)
BUILD.md           # Build/test commands for all platforms
license.md         # Keep as-is
```

### inductorHtnDocs/ (legacy, not referenced)
```
gettingstarted.md  # Moved from root
readme.md          # Moved from root
```

### .claude/rules/ (AI context, explanations)
```
htn-syntax.md         # HTN methods, operators, modifiers
prolog-reference.md   # Built-in predicates, custom rules
planner-internals.md  # FindNextPlan algorithm, state machine
build-setup.md        # One-time setup, troubleshooting context
gui-backend.md        # Flask, htn_service, API endpoints
gui-frontend.md       # React, Monaco, components
mcp-server.md         # MCP protocol, session management
python-bindings.md    # How to add functions, indhtnpy
```

### Subdirectory Docs (commands only)
```
gui/README.md          # How to run GUI
mcp-server/README.md   # How to run MCP server
```

### Keep As-Is
```
src/Tests/BugReports.md
src/docs/*.md
```

### Delete After Extraction
```
HTN.md
HTN_PLANNER_INTERNALS.md
WINDOWS.md
src/FXPlatform/CLAUDE.md
src/Python/CLAUDE.md
gui/IMPLEMENTATION_SUMMARY.md
mcp-server/FEATURE_MCP.md
```

## CLAUDE.md Content (~80 lines)

- Project Identity (2 lines)
- Build & Test Commands (reference BUILD.md)
- Directory Structure (brief)
- Critical Rules (variable syntax, factory pattern, test init)
- Code Style (brief)

## Rule Files Content

### htn-syntax.md (~150 lines)
- Path: `src/FXPlatform/Htn/**`, `Examples/**/*.htn`
- Method/operator structure, modifiers, try(), first(), examples

### prolog-reference.md (~120 lines)
- Path: `src/FXPlatform/Prolog/**`
- Variable syntax, built-in predicates, custom rules

### planner-internals.md (~200 lines)
- Path: `src/FXPlatform/Htn/HtnPlanner.*`
- PlanState, PlanNode, continue points, memory management

### build-setup.md (~80 lines)
- Path: `CMakeLists.txt`, `src/**`
- Visual Studio setup, CMake config, troubleshooting

### gui-backend.md (~60 lines)
- Path: `gui/backend/**`
- Flask endpoints, htn_service wrapper

### gui-frontend.md (~60 lines)
- Path: `gui/frontend/**`
- React components, Monaco, Vite

### mcp-server.md (~80 lines)
- Path: `mcp-server/**`
- MCP protocol, session management

### python-bindings.md (~50 lines)
- Path: `src/Python/**`
- Adding Python functions, library paths

## Verification Steps

1. Run build commands to verify BUILD.md accuracy
2. Run test commands
3. Check GUI startup (backend + frontend)
4. Check MCP server startup
