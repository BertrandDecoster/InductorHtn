# Documentation Validation Design

**Date:** 2025-12-16
**Goal:** Comprehensive validation of all documentation in `.claude/rules/*.md` and `CLAUDE.md`

## Approach

Hybrid approach: parallel subagents for code verification, sequential CLI execution.

## File Classification

| File | Code References | CLI Commands | Conceptual |
|------|----------------|--------------|------------|
| `CLAUDE.md` | Paths | Build, test | Light |
| `build-setup.md` | None | Heavy | Light |
| `htn-syntax.md` | Line numbers | None | Yes |
| `prolog-reference.md` | Line numbers | None | Yes |
| `planner-internals.md` | Line numbers | None | Yes |
| `gui-backend.md` | Paths, files | None | Yes |
| `gui-frontend.md` | Paths, files | None | Light |
| `mcp-server.md` | Paths, files | None | Yes |
| `python-bindings.md` | Paths, files | None | Yes |

## Phase 1: Parallel Code Verification (6 Subagents)

| Subagent | Doc File | What It Checks |
|----------|----------|----------------|
| Agent 1 | `htn-syntax.md` | Line numbers in HtnCompiler.h (115-125, 126-137, 99-111), HtnPlanner.cpp:514, HtnGoalResolver.cpp:497 |
| Agent 2 | `prolog-reference.md` | HtnGoalResolver constructor (~486-516), Unify(), HtnTerm.h types, HtnTermFactory.h, HtnRuleSet.h methods |
| Agent 3 | `planner-internals.md` | PlanNode struct, PlanNodeContinuePoint enum (~85), state machine flow in HtnPlanner.cpp |
| Agent 4 | `gui-backend.md` | Flask routes in app.py, HtnService in htn_service.py, directory structure |
| Agent 5 | `gui-frontend.md` | React components exist, package.json deps, vite.config.js |
| Agent 6 | `mcp-server.md` + `python-bindings.md` | MCP tools in server.py, session.py, PythonInterface.cpp exports, indhtnpy.py |

Each subagent returns: `{file, reference, status, issue?, suggested_fix?}`

## Phase 2: Sequential CLI Testing

From CLAUDE.md:
```bash
cmake --build ./build --config Release
./build/Release/runtests.exe
echo "/q" | ./build/Release/indhtn.exe Examples/Taxi.htn
```

From build-setup.md:
```bash
cmake -help
vswhere.exe -latest ...
```

## Phase 3: Report Generation

Single markdown report with:
- Summary (files checked, issues by severity)
- Per-file findings
- Suggested fixes

Severity levels:
- **Critical**: Reference broken (file/function doesn't exist)
- **Warning**: Reference shifted (exists but different location)
- **Info**: Minor discrepancy

## Phase 4: Fix Application

Options after review:
1. Batch all approved fixes
2. Per-file application
3. Cherry-pick specific fixes
4. Skip (manual fix later)

Auto-fix exclusions:
- Conceptual inaccuracies
- Uncertain line number mappings
- Items marked "needs verification"
