# HTN Component System

Reusable component library for building puzzle game HTN rulesets.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  LEVELS (puzzle1, puzzle2, ...)                 │
│  - Compose goals + initial state                │
│  - Contains level.htn with world facts          │
├─────────────────────────────────────────────────┤
│  GOALS (defeat_enemy, clear_room, reach_room)   │
│  - Multiple strategies per goal                 │
│  - HTN methods with if() selecting strategy     │
├─────────────────────────────────────────────────┤
│  STRATEGIES (the_burn, the_slipstream, ...)    │
│  - Named tactical patterns                      │
│  - Compose primitive operations                 │
├─────────────────────────────────────────────────┤
│  PRIMITIVES (locomotion, tags, aggro)           │
│  - Core operators + helper methods              │
│  - Foundation for all higher layers             │
└─────────────────────────────────────────────────┘
```

## Directory Structure

```
components/
  primitives/
    locomotion/
      src.htn        # HTN rules
      design.md      # Specification
      test.py        # Tests
      manifest.json  # Metadata + certification
    tags/
    aggro/
  strategies/
    the_burn/
    the_slipstream/
  goals/
    defeat_enemy/
    clear_room/

levels/
  puzzle1/
    level.htn        # World state + goals (not src.htn)
    design.md
    test.py
    manifest.json
```

## Component Bundle Files

| File | Purpose |
|------|---------|
| `src.htn` / `level.htn` | HTN rules (methods, operators, facts) |
| `design.md` | Specification with Examples and Properties |
| `test.py` | Example tests + property tests |
| `manifest.json` | Metadata, dependencies, certification status |

## Certification System

Components are certified when they pass all checks:

```json
{
  "certified": true,
  "certification": {
    "linter": true,      // Syntax valid
    "tests_pass": true,  // All tests pass
    "design_match": true, // Examples have tests
    "last_checked": "2025-12-25T..."
  }
}
```

**Certification workflow:**
1. Linter validates HTN syntax
2. Tests execute via test.py
3. Design coverage checks examples have corresponding tests

## CLI Toolchain

```bash
PYTHONPATH=src/Python python -m htn_components <command>

# Core Commands:
status                           # List all components with certification status
test <path>                      # Run tests for component
certify <path> [--dry-run]       # Full certification (linter + tests + design)
new <path>                       # Create component from template
coverage <path>                  # Check design-to-test coverage

# Playback & Debugging:
play <level>                     # Step-by-step plan narrative execution
trace <level> [--goal GOAL]      # Decomposition tree visualization

# Batch Operations:
test-all [--layer <layer>]       # Run all component tests
verify <level>                   # Full level verification (assemble + certify deps + test)
```

### Test Naming Convention

For semantic design-to-test coverage matching:
- `test_example_N_*` - Tests for Example N in design.md
- `test_property_pN_*` - Tests for Property PN in design.md

Example:
```python
def test_example_1_simple_tag_application(self):  # Matches Example 1
def test_property_p2_no_double_tags(self):        # Matches Property P2
```

## Key Design Decisions

### HTN Level of Abstraction
- **Room-level, not tile-level** - HTN operates on rooms, connections, hazards
- Grid pathfinding, LoS, physics handled by game engine
- HTN focuses on "what to do", engine handles "how to move"

### Composition Pattern
- Components loaded via `HtnCompile()` calls (incremental)
- Dependencies resolved by loading in order
- No preprocessor - parameters are facts

### Parameter System
- Parameters defined as facts, not preprocessor macros
- Example: `dashDistance(3).` instead of `#define DASH_DISTANCE 3`
- Works with Unreal Engine (C++ only, no Python runtime)

### Tag System
- Tags represent status effects: `hasTag(?entity, burning)`
- Explicit combination rules: `tagCombines(burning, wet, steam)`
- Room tags: `roomHasTag(?room, frozen)`

### Aggro System
- Binary: `hasAggro(?enemy, player)` or not
- Enemies follow their aggro target
- Used for luring enemies into hazards

## HTN Patterns

### Strategy Pattern
```prolog
% Named strategy with clear preconditions
theStrategyName(?target) :-
    if(precondition1, precondition2, ...),
    do(step1, step2, step3).
```

### Goal with Strategy Selection
```prolog
% Try strategies in priority order
achieveGoal(?target) :-
    if(conditionsForStrategy1),
    do(strategy1(?target)).

achieveGoal(?target) :-
    else, if(conditionsForStrategy2),
    do(strategy2(?target)).
```

### AllOf for Multiple Targets
```prolog
% Apply to all matching entities
clearRoom(?room) :-
    allOf, if(at(?enemy, ?room), isEnemy(?enemy)),
    do(defeatEnemy(?enemy)).
```

### Idempotent Operations
```prolog
% Check before applying to avoid "already exists" errors
applyTagToRoom(?room, ?tag) :-
    if(roomHasTag(?room, ?tag)),
    do().  % Skip if already tagged

applyTagToRoom(?room, ?tag) :-
    else, if(),
    do(opApplyRoomTag(?room, ?tag)).
```

### Multi-hop Navigation
```prolog
% 1-hop (direct)
moveTo(?e, ?dest) :-
    if(at(?e, ?cur), connected(?cur, ?dest)),
    do(opMoveTo(?e, ?cur, ?dest)).

% 2-hop (through intermediate)
moveTo(?e, ?dest) :-
    else, if(at(?e, ?cur),
             connected(?cur, ?via),
             connected(?via, ?dest)),
    do(opMoveTo(?e, ?cur, ?via),
       opMoveTo(?e, ?via, ?dest)).
```

## Testing Philosophy

### Example-Based Tests
Replay scenarios from design.md:
```python
def test_example_1_slide_through_corridor(self):
    """From design.md Example 1"""
    self.set_state([...])
    self.assert_plan("theSlipstream(enemy1).", contains=["opMoveTo"])
    self.assert_state_after("theSlipstream(enemy1).", has=["hasTag(enemy1,burning)"])
```

### Property Tests
Verify invariants hold:
```python
def test_property_p1_enemy_relocated(self):
    """P1: Enemy ends up in hazard room."""
    self.run_goal("theSlipstream(enemy1)")
    state = self.get_state()
    assert any("at(enemy1,roomB)" in f for f in state)
```

### Test Framework Methods
```python
# Setup
suite.load_component("primitives/locomotion", reset_first=True)
suite.set_state(["at(player, roomA)", "connected(roomA, roomB)"])

# Basic assertions
suite.assert_plan("goal.", contains=["opName"])
suite.assert_state_after("goal.", has=["fact1"], hasnt=["fact2"])
suite.assert_no_plan("impossible_goal.")
suite.run_goal("goal")  # Apply solution
suite.get_state()  # Current facts

# State checkpointing
suite.snapshot_state()   # Save current state
suite.restore_state()    # Restore from snapshot

# Design alternative testing
suite.assert_plan_matches_any("goal.", [
    {"contains": ["theBurn"], "not_contains": ["theSlipstream"]},  # Plan A
    {"contains": ["theSlipstream"]},                                # Plan B
])

# Plan complexity bounds
suite.assert_plan_complexity("goal.", min_operators=2, max_operators=10)
```

## Naming Conventions

| Layer | Prefix | Examples |
|-------|--------|----------|
| Goals | (none) | `defeatEnemy`, `clearRoom` |
| Strategies | (none) | `theBurn`, `theSlipstream` |
| Actions | (none) | `applyTag`, `lureToRoom` |
| Triggers | `trigger` | `triggerBurnOil` |
| Operators | `op` | `opMoveTo`, `opApplyTag` |

## Current Components

### Primitives
- **locomotion**: `opMoveTo`, `moveTo` (1-3 hop), `canReach`
- **tags**: `opApplyTag`, `opRemoveTag`, `applyTag` (with combinations)
- **aggro**: `opGetAggro`, `opLoseAggro`, `lureToRoom`, `enemyFollows`

### Strategies
- **the_burn**: Lure to oil room, ignite → burning tag
- **the_slipstream**: Freeze path, push into hazard → hazard's tag

### Goals
- **defeat_enemy**: Select strategy based on vulnerability + available hazards
- **clear_room**: Defeat all enemies in room (allOf)

### Levels
- **puzzle1**: "The Grease Trap" - two guards, theBurn + theSlipstream
