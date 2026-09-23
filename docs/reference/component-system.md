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
**separate type namespaces** by design. Both declare `signature(opMoveTo,
...)` with different argument types (`entity`/`room` vs `agent`/`location`)
to match their respective domain shapes. They are not meant to co-assemble
into a single level; if a future level depends on both, rename the
gamehack operator first to avoid the duplicate-signature collision.

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
- Higher-layer files are very thin (often 2-5 lines of HTN). A strategy might just be `if(enemy(?t)), do(applyTag(wet, ?t), applyTag(electrocute, ?t)).` — all the actual logic lives in the primitives it composes. Goals are even thinner: just method alternatives selecting between strategies.
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

## Core Vocabulary (`components/core/*`)

The unified vocabulary for new levels. The older `components/primitives|strategies|goals`
and `components/gamehack/*` trees stay as they are until migrated.

**World** (`core_world`)
```prolog
region(?r).  connected(?a, ?b).          % declared per direction
lineOfSight(?from, ?to).                 % ranged skills reach ?to from ?from
regionHas(?r, ?feature).                 % oil | sludge | scorched | water | ...
at(?entity, ?r).  status(?entity, ?s).   % anchored | snared | dazzled | shielded | dead
role(?entity, player | companion | enemy).
```

**Chemistry as facts** (`core_chemistry`) - elements change materials, elements change
entities, materials never change materials:
```prolog
skillElement(ignite, fire).       reacts(fire, oil, scorched).    blast(fire, oil, dead).
skillElement(freeze, freeze).     reacts(freeze, oil, sludge).    terrain(sludge, snared).
strike(lightning, dead).          mark(light, dazzled).           immune(?e, ?el).
```
Reactions rewrite `regionHas`, so what one fight consumes is gone for the next.

**Paying for casts.** `signature(?a, ?skill)` is unswappable and unlimited; `unlimited(?skill)`
is free for anyone; everything else is a **token**: `charge(?a, ?skill, ?tok)`, chosen with
`first(charge(...))` in `if()` and deleted by `opSpendCharge`. No counters.

**Companions are interchangeable.** `role(?e, player)` and `role(?e, companion)` are both
companions; they differ only by who controls them. Abilities live on the character (`hasSkill`,
`signature`, `charge`). **Never gate an ability on `role(?a, player)`.** Cooperation comes from
**task roles**: `core_attunement` declares primer and pay-off, and the pay-off may not be the
primer (`detonate(?el, ?r, ?not)`, `finish(?e, ?not)`, `detonateLethal(?r, ?not)`); anyone may
fill either role. The rule is that **no single companion can carry a plan alone**; two companions
finishing the fight while the human's companion stands idle is acceptable, and how busy the human's
seat is stays a per-level design knob (F6 in `docs/FUN_METRICS.md`).

**Chemistry as needs** (`core_chemistry`): `castElement(?el, ?r[, ?not])` (element on region:
who holds it is bound at the leaf), `castElementAs(?a, ?el, ?r)`, `obtainFeature(?r, ?feat)`
(already there, or made by a reaction), `strikeElement(?el, ?e[, ?not])`, `markElement(?el, ?e)`,
rule `holder(?el, ?a)`.

**Attunement** (`core_attunement`): the fight's needs - `blastDeadAt(?r[, ?not])` (some element
reacts lethally with the feature there), `strikeDead(?e[, ?not])`, `expose(?e)`; `prime(?el, ?r[, ?a])`
and rule `primer(?el, ?a)` for the primer role.

**Aggro** (`core_aggro`): `lure` (iron only, from range - Magnetize), `push` (flesh only - Gust),
`taunt` (dash; the player lands in the terrain too), `holdPosition` (`opAnchor`/`opRelease`:
an anchored Warden neither moves nor pulls until released), `bringTo`.

**Leaf operators - the actor is always the first argument:**
`opNavigate(?a, ?from, ?to)`, `opSpendCharge(?a, ?skill, ?tok)`,
`opCastRegion(?a, ?skill, ?r, ?old, ?new)`, `opCastEntity(?a, ?skill, ?e, ?status)`,
`opStatus(?a, ?e, ?status)`, `opLure/opPush/opTaunt(?a, ?e, ?from, ?to)`, `opAnchor(?a)`,
`opRelease(?a)`.

### Rulesets are top-down

A ruleset decomposes from the **need**, never from an actor and its inventory. The goal asks
for a neutralized enemy; a method for that asks for a lethal blast; that asks for an element
on a feature; only then does the planner ask *who holds the element* and *which region has
the feature*. Name methods after the need they satisfy (`neutralize`, `blastDead`,
`obtainFeature`, `castElement`, `haveElement`); put the "what would work" lookup
(`blast(?el, ?feat, dead)`, `reacts(?el2, ?old, ?feat)`) in the `if()`; acquire each
ingredient as a subtask. A method shaped "I am `?a`, I hold `?el`, there is `?r`, let us see
what happens" is a bottom-up simulation, not a plan - see `docs/reference/authoring-rulesets.md`.

### Operator rules (engine facts, learned the hard way)

1. **No `is()` in operators.** The compiler drops `is()` after `add()`. Counters use
   `increase`/`decrease` (see `htn-syntax.md`); core charges stay tokens, one fact per use.
2. **Every `del`/`add` variable must appear in the head.** Substitution uses the head MGU only.
3. **A fact added twice is a planner error.** Every `allOf` or status-adding method needs a
   `not(status(...))` guard, and rules used inside `allOf` conditions must be single-clause
   (see `exposed`, `vulnerable` in `core_chemistry`).
4. **No `hidden` operators.** They vanish from the plan and desync state replay from
   `GetSolutionFacts`.
5. **A failed search that decomposed locks the rule set.** After `FindAllPlans` returns no
   solution for a goal whose method *did* decompose into subtasks, `HtnCompile` of further
   facts fails with `Internal Error ... HtnRuleSet.cpp line 16` (`m_isLocked`). A goal that
   fails at its own `if()` does not lock. In tests, set all facts first, or query the leaf
   arity directly for the no-plan case; in tools, use a fresh planner per world.
6. **Actor first.** The metrics (`actor_position: 0`) and the MCP play tools read the actor
   from the first argument. A level can override per operator with `funActor(opName, index)`
   and mark bookkeeping with `funNoop(opName)`.

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
- **puzzle1**: "The Grease Trap" (old vocabulary) - two guards, theBurn + theSlipstream

### Core Components (`core/`) - the unified vocabulary

- **Primitives:** `core_world` (regions, `navigate`, `takeVantage`), `core_chemistry`
  (`castElement`, `obtainFeature`, `strikeElement`, `markElement`, `payFor`), `core_attunement`
  (`blastDeadAt`, `strikeDead`, `expose`, `prime`), `core_aggro` (`lure`, `push`, `taunt`,
  `holdPosition`, `bringTo`)
- **Strategies:** `the_burn` (ground that burns: bring the enemy there, someone lights it),
  `the_slipstream` (ground that snares, made if needed by the primer; cover; bring them in;
  someone other than the primer strikes or blasts)
- **Goals:** `defeat_group` (burn or slipstream, both enumerable)
- **Levels:** `grease_trap` - swarm in the gallery, iron bearer at the exit, pick 2 of 5
  skills; declares `funChoiceSpace` so F4 is measured

### GameHack Components (`gamehack/`)

Separate namespace for combat game domains (direct location movement, skill-based tags, multi-agent aggro).

#### Primitives
- **gh_movement**: `opMoveTo`, `goToLocation`, `goToSameLocation` (direct, no room connections)
- **gh_tags**: `opApplyTag`, `applyTag`, `useSkillOnTarget`, `applySkillTags_L_ApplyTag` (skill→tag mapping, anyOf for multi-tag)
- **gh_aggro**: `opAggro`, `aggroTarget`, `bringMobToLocation`, `bringMobsTogether` (lure via aggro chain)
- **gh_skills**: `opSwapSkill`, `prepareToUseSkill`, `getSkillFromLocation` (skill acquisition at locations)

#### Actions
- **gh_tag_application**: 3-path `applyTagNotPresent` dispatcher (ally skill, location, mob skill)

#### Strategies
- **wet_and_electrocute**: Sequential wet+electrocute combo
- **stun_and_slow_skill**: Simultaneous two-ally stun+slow with `opSynchronize`
- **stun_and_burn**: Sequential ice+fire (documented failure without skills)

#### Goals
- **plan_to_damage**: Select between stunAndSlowSkill and wetAndElectrocute

#### Levels
- **gamehack_gh4**: GH4-style world, only wetAndElectrocute viable
- **gamehack_gh7**: GH7-style world, both strategies viable
