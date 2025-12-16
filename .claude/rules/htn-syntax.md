---
description: HTN syntax reference for methods, operators, and modifiers
globs: src/FXPlatform/Htn/**, Examples/**/*.htn
---

# HTN Syntax Reference

## Methods (Task Decomposition)

Methods decompose complex tasks into subtasks. Parsed in `HtnCompiler.h:115-125`.

```prolog
methodName(?params) :- if(preconditions), do(subtask1, subtask2).
```

### Basic Example
```prolog
travel(?dest) :- if(at(?start), canReach(?start, ?dest)), do(move(?start, ?dest)).

move(?from, ?to) :- if(hasVehicle(?v)), do(drive(?v, ?from, ?to)).
move(?from, ?to) :- if(), do(walk(?from, ?to)).
```

## Operators (Primitive Actions)

Operators modify world state directly. Parsed in `HtnCompiler.h:126-137`.

```prolog
operatorName(?params) :- del(factsToRemove), add(factsToAdd).
```

### Basic Example
```prolog
walk(?from, ?to) :- del(at(?from)), add(at(?to)).

drive(?vehicle, ?from, ?to) :-
    del(at(?from), fuel(?vehicle, ?f)),
    add(at(?to), fuel(?vehicle, ?newF)),
    is(?newF, -(?f, 1)).
```

## Method Modifiers

Parsed in `HtnCompiler.h:99-114`.

### else - Fallback Methods
Methods marked `else` only execute if all previous non-else methods fail.

```prolog
travel(?dest) :- if(hasCarKey), do(drive(?dest)).
travel(?dest) :- else, if(hasBusPass), do(takeBus(?dest)).
travel(?dest) :- else, if(), do(walk(?dest)).
```

### anyOf - Multiple Bindings (OR Logic)
Executes `do()` for each variable binding from `if()`. Succeeds if **at least one** succeeds. Each execution wrapped in `try()`.

```prolog
attackEnemies() :- anyOf, if(isInRange(?enemy)), do(attack(?enemy)).
```
With `isInRange(orc1). isInRange(goblin1).` - attempts attack on each, succeeds if any attack succeeds.

### allOf - Multiple Bindings (AND Logic)
Executes `do()` for each variable binding. Succeeds only if **ALL** succeed.

```prolog
repairAllDamaged() :- allOf, if(isDamaged(?unit)), do(repair(?unit)).
```
With `isDamaged(tank1). isDamaged(infantry2).` - repairs both, fails if any repair fails.

**Important**: `anyOf`/`allOf` handle multiple bindings within ONE method. They are NOT for selecting between different methods.

## Operator Modifiers

### hidden - Internal Operators
Operators marked `hidden` are excluded from final plan output. Used for internal state tracking.

```prolog
hidden, updateInternalState() :- del(old), add(new).
```

## Special Constructs

### try() - Optional Execution
Handled in `HtnPlanner.cpp:514` (`CheckForSpecialTask`). Wraps tasks for optional execution. If the wrapped task fails, the parent method continues.

```prolog
collectRewards() :- if(), do(getMainReward, try(getBonusItem)).
```
If `getBonusItem` fails, method still succeeds with just `getMainReward`.

### first() - First Solution Only
Implemented in `HtnGoalResolver.cpp:1843` (`RuleFirst`). Returns only the first solution from a Prolog query. Prevents backtracking.

```prolog
getTaxi() :- if(first(available(?taxi))), do(hire(?taxi)).
```
With `available(taxi1). available(taxi2).` - only binds `?taxi` to `taxi1`.

## Complete Example

```prolog
% High-level goal
travel(?destination) :-
    if(at(?start), canReach(?start, ?destination)),
    do(move(?start, ?destination)).

% Method alternatives
move(?from, ?to) :- if(hasVehicle(?v)), do(driveVehicle(?v, ?from, ?to)).
move(?from, ?to) :- if(hasTicket(?from, ?to)), do(takeTransport(?from, ?to)).
move(?from, ?to) :- else, if(), do(walk(?from, ?to)).

% Operators
driveVehicle(?v, ?from, ?to) :-
    del(at(?from), hasVehicle(?v)),
    add(at(?to), usedVehicle(?v)).

walk(?from, ?to) :- del(at(?from)), add(at(?to), tired).

% World state
at(home).
hasVehicle(car).
canReach(home, work).

% Goal
goals(travel(work)).
```

## Testing Patterns

### C++ Test Helper
```cpp
compiler->ClearWithNewRuleSet();  // CRITICAL: Always clear state
CHECK(compiler->Compile(program));
auto solutions = planner->FindAllPlans(factory.get(),
    compiler->compilerOwnedRuleSet(), compiler->goals());
```

### Expected Formats
- Success: `"[ { operator1(args), operator2(args) } ]"`
- Empty plan: `"[ { () } ]"`
- Failure: `"null"`
- Variable bindings: `"((?X = value))"`
