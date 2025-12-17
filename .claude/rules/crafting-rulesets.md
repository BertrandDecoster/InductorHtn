# Crafting & Understanding Rulesets

Tools for understanding ruleset dynamics - seeing what plans work, how state changes, and exploring facts.

## 1. Interactive REPL (`indhtn.exe`) - Quick Exploration

```bash
./build/Release/indhtn.exe Examples/Taxi.htn
```

**Key commands:**
| Command | Purpose |
|---------|---------|
| `at(?x).` | Query current facts (list all `at` facts) |
| `goals(travel-to(park)).` | Find plans without applying |
| `apply(travel-to(park)).` | Find plans AND apply state changes |
| `/t` | Toggle tracing (see method decomposition) |
| `/r` | Reset and reload |

**List all facts:** Query each predicate, e.g., `at(?x).`, `have-cash.`

## 2. Python API - Best for Programmatic Analysis

```python
from indhtnpy import HtnPlanner

planner = HtnPlanner(False)
planner.Compile(open("Examples/Taxi.htn").read())

# Get ALL current facts
error, facts = planner.GetStateFacts()  # Returns JSON list

# Find plans
error, solutions = planner.FindAllPlansCustomVariables("travel-to(uptown).")

# See what state WOULD be after a plan (without applying)
error, new_facts = planner.GetSolutionFacts(0)  # Solution index 0

# Apply a plan and update state permanently
planner.ApplySolution(0)

# Get decomposition tree (see HOW plan was derived)
error, tree = planner.GetDecompositionTree(0)
```

**Run the demo:**
```bash
python src/Python/PythonUsageTrace.py
```

## 3. GUI (`start_gui.py`) - Visual State Diff

```bash
python gui/start_gui.py
```

The GUI provides:
- **State panel** showing current facts
- **State diff** after each solution (shows added/removed/unchanged facts)
- **Decomposition tree visualization**

API endpoint: `POST /api/state/diff` returns:
```json
{
  "added": ["at(park)"],
  "removed": ["at(downtown)"],
  "unchanged": ["have-cash"]
}
```

## Best Tool by Use Case

| Goal | Best Tool |
|------|-----------|
| Quick interactive testing | `indhtn.exe` REPL |
| List all facts | Python `GetStateFacts()` |
| See state changes | Python `GetSolutionFacts()` or GUI diff |
| Understand plan decomposition | Python `GetDecompositionTree()` or `/t` tracing |
| Batch testing | `htn_test_suite.py` |

## Deep Understanding Workflow

For thorough ruleset analysis, use the Python API with these three methods together:

1. `GetStateFacts()` - Initial state (all facts before planning)
2. `GetSolutionFacts(i)` - Final state after solution i
3. `GetDecompositionTree(i)` - How the plan was derived (method choices, bindings)

This shows before/after state plus the decomposition logic explaining WHY those operators were chosen.

## MCP Tools for LLM Workflow

These MCP tools support the ruleset creation workflow:

### indhtn_lint
Validate HTN syntax and get structured errors.
```json
{
  "source": "travel(?x) :- if(at(?y)), do(walk(?y, ?x))."
}
```
Returns: diagnostics with line numbers, error codes, severity.

### indhtn_introspect
List all methods, operators, and facts in a ruleset.
```json
{
  "source": "<htn source>"
}
```
Returns: methods[], operators[], facts[] with signatures and line numbers.

### indhtn_state_diff
Preview what a plan would change (without applying).
```json
{
  "sessionId": "<id>",
  "goal": "travel-to(park)"
}
```
Returns: plan preview.

### indhtn_step
Execute one operator at a time for debugging.
```json
{
  "sessionId": "<id>",
  "operator": "walk(downtown, park)"
}
```
Returns: operator result, query facts to see new state.
