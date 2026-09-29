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
│  STRATEGIES (oil_and_burn, wet_and_freeze, ...)│
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
    oil_and_burn/
    wet_and_freeze/
  goals/
    defeat/
    clear_location/
  challenges/
    door/
  gamehack/          # a second tree: primitives, actions, strategies, goals

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

# Assembly:
assemble <level> [-o <path>]     # Assemble level + deps into a single .htn
  [--no-verify]                  #   write output without running the verifier
  [--verify-only]                #   run the verifier but skip writing output
  [--skip-compile-check]         #   skip layer 3 (C++ HtnCompile round-trip)
```

### Assemble output layout

Without `-o`, `assemble` writes to `assembled/<level>/<UTC-timestamp>.htn`
and refreshes `assembled/<level>/latest.htn`. The `assembled/` directory is
gitignored — committed goldens live under `tests/fixtures/assembled/<level>.htn`.

### Assembly verifier

`assemble` runs a 3-layer verifier on the concatenated output before writing
(unless `--no-verify` is passed). Errors block the write and exit non-zero (2):

| Layer | Codes | What it catches |
|-------|-------|-----------------|
| 1. literal-duplicate clauses | `ASM001` | Same head AND body defined twice (ignores whitespace and trailing comments) |
| 2. semantic lint | `SEM*`, `VAR*`, `SYN*`, `TYP*` | Undefined tasks, unused vars, syntax shape, typed-parameter mismatches — via `gui/backend/htn_linter.py` |
| 3. C++ parser round-trip | `ASM002` | Anything the engine itself would reject; uses `HtnPlanner.HtnCompileCustomVariables` (`?varname` syntax) |

Codes `ASM003`/`ASM998`/`ASM999` are infrastructure warnings (binding missing,
linter import or runtime failure).

### Typed parameters (TYP001)

Components and levels may opt into argument type-checking by declaring two
conventional facts:

```prolog
type(typeName, instance).
signature(predName, [argType1, argType2, ...]).
```

The engine treats both as ordinary facts and never queries them at planning
time — they exist purely for the linter to read.

`TYP001` (warning) fires when a *constant* argument at a typed call site is
declared as a different type, or has no `type/2` declaration at all.
Variables and compound terms are not yet checked. Calls nested inside
wrappers (`try()`, `first()`, `and()`, `parallel()`, `forall()`) are also
not recursed into in the MVP — only calls directly in `if`/`do`/`del`/`add`
clauses are inspected. Rulesets with no `signature/2` declarations get no
TYP* diagnostics — the rule is fully opt-in.

`TYP002` (warning) fires when the same `predName/arity` appears in two
`signature/2` facts. The first declaration wins; the rest are reported as
redundant.

Numeric literals (integers and floats, including negatives) satisfy the
three built-in primitive types `int`, `float`, and `number`
interchangeably — no `type(int, 5)` fact required. User-declared types
layer on top: declaring `type(int, myConstant)` still works for non-numeric
constants.

The puzzle1 path (`components/primitives/`, `components/strategies/`,
`components/goals/`) and the gamehack path (`components/gamehack/`) are
**separate trees**. Both use the words of `docs/authoring/vocabulary.md` and
define some of the same verbs (`goToLocation`, `bringEnemyTo`, `opMoveTo`), so
they are not meant to co-assemble into a single level: a level depends on one
tree.

Example fixtures live under `Examples/ErrorTests/typed_arg_swapped.htn` and
`Examples/ErrorTests/typed_arg_untyped_constant.htn`. Example annotations
live in `components/primitives/*/src.htn` (signatures) and
`levels/puzzle1/level.htn` (type instances).

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
- Components loaded via `HtnCompile()` calls (incremental). The planner accumulates rules from each call.
- `load_component` reads `manifest.json` dependencies and recursively loads them first, then compiles the component's own `src.htn`. Order matters: higher layers reference methods/operators defined in lower layers.
- Higher-layer files are very thin (often 2-5 lines of HTN). A strategy might just be `if(enemy(?t), companion(?lurer), companion(?caster), \==(?lurer, ?caster)), do(applyTag(?lurer, oil, ?t), applyTag(?caster, burning, ?t)).` — all the actual logic lives in the primitives it composes. Goals are even thinner: just method alternatives selecting between strategies.
- No preprocessor - parameters are facts

### Parameter System
- Parameters defined as facts, not preprocessor macros
- Example: `dashDistance(3).` instead of `#define DASH_DISTANCE 3`
- Works with Unreal Engine (C++ only, no Python runtime)

### Words
The facts, verbs and operators are the ones in
[`../authoring/vocabulary.md`](../authoring/vocabulary.md): `hasTag(?agent, burning)`,
`locationCanApplyTag(?l, oil)`, `hasAggro(?enemy, ?target)` (enemies follow their target;
`bringEnemyTo` lures them), `locationCombo(oil, burning)`.

## How to write the rules

The rules themselves follow [`../authoring/rubric.md`](../authoring/rubric.md) and [`../authoring/patterns.md`](../authoring/patterns.md); the language is [`language.md`](language.md).

## Testing Philosophy

### Example-Based Tests
Replay scenarios from design.md:
```python
def test_example_1_slide_through_corridor(self):
    """From design.md Example 1"""
    self.set_state([...])
    self.assert_plan("wetAndFreeze(enemy1).", contains=["opMoveTo"])
    self.assert_state_after("wetAndFreeze(enemy1).", has=["hasTag(enemy1,stunned)"])
```

### Property Tests
Verify invariants hold:
```python
def test_property_p1_enemy_relocated(self):
    """P1: Enemy ends up in hazard room."""
    self.run_goal("wetAndFreeze(enemy1)")
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
    {"contains": ["oilAndBurn"], "not_contains": ["wetAndFreeze"]},  # Plan A
    {"contains": ["wetAndFreeze"]},                                # Plan B
])

# Plan complexity bounds
suite.assert_plan_complexity("goal.", min_operators=2, max_operators=10)
```

## Naming Conventions

| Layer | Prefix | Examples |
|-------|--------|----------|
| Goals | (none) | `defeat`, `clearLocation` |
| Strategies | (none) | `wetAndFreeze`, `oilAndBurn` |
| Verbs | (none) | `applyTag`, `bringEnemyTo` |
| Operators | `op` | `opMoveTo`, `opApplyTag`; "already true" no-ops `opStayInLocation`, `opTagAlreadyOnTarget` |

## Current Components

Both trees use the words and the tag system of `docs/authoring/vocabulary.md`: four location
tags, three location combos, `vulnerableToLocationCombo`. The earlier versions are in
`archive/pre-vocabulary/` and `archive/pre-tag-system/`.

### Primitives
- **locomotion**: `goToLocation`, `goToSameLocation` (one step; arriving lands the location's tag), `enemiesFollow`
- **tags**: `landSkillTag` (the location combos), `landTag`, `landLocationTag`, `tagEveryoneAt`, `defeatVulnerable`, `defeatVulnerableAt`; the `locationCombo` facts
- **aggro**: `getAggro`, `bringEnemyTo`
- **skills**: `applyTag` (a tag on a target, by an actor's skill or lure), `prepareToUseSkill`, `getSkillFrom` (skills granted by objects), `useSkillOnTarget`, `applySkillTags`

### Strategies
- **oil_and_burn**: a lurer brings the enemy onto oil, a second companion burns it there
- **wet_and_freeze**: a lurer brings the enemy into water or onto ice, a second companion chills it there

### Goals
- **defeat**: a menu of wetAndFreeze and oilAndBurn
- **clear_location**: every enemy at a location is defeated (`allOf`)

### Challenges
- **door**: `unlockDoor` with one companion on the single plate that opens it

### Levels
- **puzzle1**: "The Grease Trap" - two guards, one burnt on oil, one frozen in water

### GameHack Components (`gamehack/`)

#### Primitives
- **gh_movement**: `goToLocation`, `goToSameLocation`, `enemiesFollow` (one step; arriving lands the location's tag)
- **gh_tags**: `useSkillOnTarget`, `applySkillTags`, `landSkillTag` and the landing verbs (as in `tags`)
- **gh_aggro**: `getAggro`, `bringEnemyTo`
- **gh_skills**: `applyTag`, `prepareToUseSkill`, `getSkillFrom` (skills granted by objects)
- **gh_doors**: `unlockDoor` with two companions on two plates (`opSynchronizeOnPlates`)

#### Strategies
- **wet_and_freeze**, **oil_and_burn**: as above
- **stun_and_slow**: two companions, a stun and a slow skill together, with `opSynchronize`

#### Goals
- **defeat**: a menu of wetAndFreeze, oilAndBurn and stunAndSlow
- **complete_toy_level**: unlock a door, then defeat an enemy

#### Levels
- **gamehack_gh4**: GH4-style world, only wetAndFreeze viable
- **gamehack_gh7**: GH7-style world, all three strategies viable
- **gamehack_multipath**, **gamehack_mvp**: a larger world, and the smallest one
