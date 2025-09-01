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

# Build (generic)
cmake --build ./ --config Release
# or
cmake --build ./ --config Debug

# VSCode/Homebrew CMake specific build command (use this one)
/opt/homebrew/bin/cmake --build /Users/bertranddecoster/Projects/InductorHtn/build --config Debug --target all

# Run tests (from project root)
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

## Prolog

### Prolog architecture
 - Default Prolog syntax has variables starting with an uppercase letter `constant`, `Variable`
 - When you ask a Prolog Compiler to compile strings, it will split the standard rules with those with the special keyword goals()
 - The Prolog compiler has SolveGoals to directly do Prolog resolution (it has an inner HtnGoalResolver)
 - It is advised to never use the goals() keyword and instead...
 - You can ask it to ResolveAll, and provide it a list of terms, and it will unify

### Custom rules

### first() - Return First Solution Only
Returns only the first solution from a Prolog query, useful for deterministic behavior.

```prolog
% Get the first available taxi (don't try all taxis)
getTaxi() :- if(first(available(?taxi))), do(hire(?taxi)).

% State: multiple taxis available
available(taxi1). available(taxi2). available(taxi3).

% Result: Only binds ?taxi to taxi1 (first match), doesn't try taxi2, taxi3
```
## HTN

### HTN Syntax Key Points
- HTN syntax (also referred to as CustomVariables) start with a question mark `?` : `?varname` (instead of Prolog capitalization)
- Methods decompose complex tasks: `travel-to(?dest) :- if(...), do(...).`
- Operators are primitive actions: `walk(?from, ?to) :- del(at(?from)), add(at(?to)).`
- Mix HTN constructs with standard Prolog rules
- Methods (if/do) can accept the keywords `else`, `allOf`, `anyOf`
- Operators (del/add) can accept the keyword `hidden`


### anyOf - Multiple Variable Bindings (OR Logic)
The `anyOf` modifier handles multiple variable bindings within a SINGLE method. It executes the `do()` clause for each variable binding that satisfies the `if()` condition, wrapping each execution in try() blocks. The method succeeds if **at least one** execution succeeds.

```prolog
% Attack all enemies in range - succeed if at least one attack succeeds
attackEnemies() :- anyOf, if(isInRange(?enemy)), do(attack(?enemy)).

% State: multiple enemies
isInRange(orc1). isInRange(goblin1). isInRange(dragon1).

% Operator
attack(?target) :- del(alive(?target)), add(dead(?target)).

% Result: Attempts attack(?enemy) for each enemy (orc1, goblin1, dragon1)
% Succeeds if at least one attack succeeds (wrapped in try() blocks)
```

**Key Point**: anyOf is NOT for selecting between different methods. It's for handling multiple solutions within one method.

### allOf - Multiple Variable Bindings (AND Logic) 
The `allOf` modifier handles multiple variable bindings within a SINGLE method. It executes the `do()` clause for each variable binding that satisfies the `if()` condition. The method succeeds only if **ALL** executions succeed.

```prolog
% Repair all damaged units - succeed only if all repairs succeed
repairAllDamaged() :- allOf, if(isDamaged(?unit)), do(repair(?unit)).

% State: multiple damaged units  
isDamaged(tank1). isDamaged(infantry2). isDamaged(artillery1).

% Operator
repair(?unit) :- del(isDamaged(?unit)), add(fullyRepaired(?unit)).

% Result: Executes repair(?unit) for each unit (tank1, infantry2, artillery1)
% Succeeds only if ALL repairs succeed
```

### else - Method Priority (Fallback)
Provides fallback method selection with explicit priority ordering.

```prolog
travel(?dest) :- if(hasCarKey), do(drive(?dest)).
travel(?dest) :- else, if(hasBusPass), do(takeBus(?dest)).
travel(?dest) :- else, if(), do(walk(?dest)).
```

### try() - Optional Execution (HtnPlanner::CheckForSpecialTask)
Wraps operations for optional execution that shouldn't cause the entire plan to fail.

```prolog
% Try to get bonus item, but continue even if it fails
collectRewards() :- if(), do(getMainReward, try(getBonusItem)).

% If getBonusItem fails, the method still succeeds with just getMainReward
```


## Creating HTN Plans - Best Practices

### 1. Basic Method Structure
```prolog
% Method: decomposes complex task into subtasks
methodName(?params) :- if(preconditions), do(subtask1(?params), subtask2(?params)).

% Operator: primitive action that modifies world state  
operatorName(?params) :- del(oldFacts), add(newFacts).
```

### 2. Complete Travel Example
```prolog
% High-level goal
travel(?destination) :- if(at(?start), canReach(?start, ?destination)), 
                        do(move(?start, ?destination)).

% Method alternatives (normal HTN - not anyOf/allOf)
move(?from, ?to) :- if(hasVehicle(?vehicle)), do(driveVehicle(?vehicle, ?from, ?to)).
move(?from, ?to) :- if(hasTicket(?from, ?to)), do(takeTransport(?from, ?to)).  
move(?from, ?to) :- if(), do(walk(?from, ?to)).

% Operators (primitive actions)
driveVehicle(?vehicle, ?from, ?to) :- 
    del(at(?from), hasVehicle(?vehicle)), 
    add(at(?to), usedVehicle(?vehicle)).

walk(?from, ?to) :- 
    del(at(?from)), 
    add(at(?to), tired).

% World state
at(home).
hasVehicle(car).
canReach(home, work).

% Goal
goals(travel(work)).
```

### 3. anyOf/allOf Usage Patterns
```prolog
% anyOf: Handle multiple targets, succeed if any works
clearArea() :- anyOf, if(enemy(?e)), do(eliminate(?e)).

% allOf: Handle multiple targets, succeed only if all work  
setupDefenses() :- allOf, if(defensivePosition(?pos)), do(fortify(?pos)).

% NOT for method selection - use regular HTN methods for that:
defend() :- if(hasWeapons), do(fightBack).
defend() :- if(hasShield), do(blockAttack).  
defend() :- if(), do(retreat).
```

### 4. Proper Variable Usage
```prolog
% Correct: ?variable notation
processItem(?item) :- if(needsProcessing(?item)), do(process(?item)).

% State facts use same notation
needsProcessing(document1).
needsProcessing(document2).

% Operators bind variables correctly  
process(?item) :- del(needsProcessing(?item)), add(processed(?item)).
```

### 5. Integration with Prolog
```prolog
% HTN methods can use full Prolog reasoning
planBattle(?enemy) :- 
    if(enemyStrength(?enemy, ?str), 
       myStrength(?str2), 
       >=(?str2, ?str)),
    do(directAttack(?enemy)).

planBattle(?enemy) :- 
    if(enemyStrength(?enemy, ?str),
       myStrength(?str2),
       <(?str2, ?str)), 
    do(callForReinforcements, waitForBackup, directAttack(?enemy)).

% Mix facts and rules freely
enemyStrength(orc, 5).
myStrength(?s) :- troopCount(?c), weaponBonus(?b), is(?s, +(?c, ?b)).
troopCount(3).
weaponBonus(2).
```

## Testing HTN Plans

### C++ Testing Pattern
```cpp
class HtnTestHelper {
public:
    string FindFirstPlan(const string& program) {
        compiler->ClearWithNewRuleSet();  // CRITICAL: Always clear state
        CHECK(compiler->Compile(program));
        auto solutions = planner->FindAllPlans(factory.get(), 
                                              compiler->compilerOwnedRuleSet(), 
                                              compiler->goals());
        if (solutions && !solutions->empty()) {
            return HtnPlanner::ToStringSolution((*solutions)[0]);
        }
        return "null";
    }
};
```

### Expected Result Formats
- Success: `"[ { operator1(args), operator2(args) } ]"`
- Empty plan: `"[ { () } ]"`
- Failure: `"null"`
- Variable bindings: `"((?X = value))"`

### Memory Management
- All terms must come from the same `HtnTermFactory`
- Configurable memory budgets for planning
- Returns out-of-memory status when limits exceeded

## Code Style Guidelines
- C++11 standard
- Platform-specific code isolated in Win/iOS/Posix directories
- Use existing patterns for new components