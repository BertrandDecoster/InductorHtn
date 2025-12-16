---
description: Prolog syntax, built-in predicates, and custom rules reference
globs: src/FXPlatform/Prolog/**
---

# Prolog Reference

## Variable Syntax

InductorHTN uses `?` prefix for variables (not Prolog capitalization):
- Standard Prolog: `Variable` (capitalized), `constant` (lowercase)
- InductorHTN: `?variable` (? prefix), `constant` (no prefix)

```prolog
at(?agent, ?location).    % ?agent and ?location are variables
at(player, downtown).     % player and downtown are constants
```

## Facts and Rules

**Facts** are unconditional assertions:
```prolog
at(agent, downtown).
distance(downtown, park, 2).
```

**Rules** express conditional knowledge:
```prolog
canWalk(?from, ?to) :- distance(?from, ?to, ?d), =<(?d, 3).
```

## Built-in Predicates

All added in `HtnGoalResolver::HtnGoalResolver()` via `AddCustomRule()`.

### Unification
```prolog
=(?X, ?Y)                 % Unifies two terms
```

### Arithmetic (`HtnGoalResolver.cpp:~480`)
```prolog
is(?Result, Expression)   % Evaluate: is(?x, +(3, 4)) -> ?x = 7
<(?X, ?Y)                 % Less than
>(?X, ?Y)                 % Greater than
=<(?X, ?Y)                % Less or equal
>=(?X, ?Y)                % Greater or equal
==(?X, ?Y)                % Structural equality
```

### Control Flow
```prolog
!                         % Cut - commits to current choices
not(Goal)                 % Negation as failure
first(Goal)               % Returns first solution only (HtnGoalResolver.cpp:497)
forall(Generator, Test)   % Universal quantification
```

### Meta-predicates
```prolog
findall(?Template, Goal, ?List)  % Collect all solutions
count(?Count, Goal)              % Count solutions
distinct(?Key, Goal)             % Unique solutions by key
sortBy(?Key, Direction, Goal)    % Sort solutions
```

### Database Modification
```prolog
assert(Fact)              % Add fact to knowledge base
retract(Fact)             % Remove first matching fact
retractall(Pattern)       % Remove all matching facts
```

### String Operations
```prolog
atom_chars(?Atom, ?List)  % Convert: atom_chars(foo, ?L) -> ?L = [f,o,o]
atom_concat(?A, ?B, ?R)   % Concatenate: atom_concat(foo, bar, ?r) -> ?r = foobar
downcase_atom(?In, ?Out)  % Lowercase: downcase_atom('Hello', ?x) -> ?x = hello
```

### Type Checking
```prolog
atomic(?X)                % True if X is atom (not compound)
```

## Adding Custom Rules

To integrate external tools, add a custom rule in `HtnGoalResolver.cpp`:

1. Register in constructor (~line 486-516) with `AddCustomRule()`
2. Declare static method in `HtnGoalResolver.h` (~line 79-103)
3. Implement using existing rules as template

Example patterns to follow:
- `RuleIs` - arithmetic evaluation with variable binding
- `RuleNot` - negation as failure
- `RuleFirst` - returns first solution only

## SLD Resolution

Prolog uses SLD (Selective Linear Definite) resolution:

1. Select leftmost goal in resolvent
2. Find rule whose head unifies with goal
3. Replace goal with rule's body (instantiated)
4. Repeat until empty (success) or no match (backtrack)

Implementation in `HtnGoalResolver::ResolveAll()` and `ResolveNext()`.

### Unification Algorithm

In `HtnGoalResolver::Unify()`:
```
Unify(t1, t2):
  If both constants: equal names -> {} else fail
  If t1 variable: occurs check, then bind t1 to t2
  If t2 variable: occurs check, then bind t2 to t1
  If both compound: same functor/arity -> recursively unify args
  Otherwise: fail
```

## Key Data Structures

### HtnTerm (`HtnTerm.h`)
Term types (ordered for comparison):
1. Variable - unbound placeholder
2. FloatType - floating point
3. IntType - integer
4. Atom - named constant (no args)
5. Compound - functor with arguments

Key methods: `isVariable()`, `isGround()`, `isConstant()`, `TermCompare()`

### HtnTermFactory (`HtnTermFactory.h`)
Central factory for term creation with memory efficiency:
- String interning: each unique string stored once
- Term interning: frequently used terms cached
- Memory tracking: `dynamicSize()`, `outOfMemory()`

**Critical**: All terms must come from the same factory for unification.

### HtnRuleSet (`HtnRuleSet.h`)
Knowledge base with facts and rules:
- `AllRulesThatCouldUnify()` - find matching rules
- `CreateNextState()` - state forking for backtracking
- Copy-on-write semantics for memory efficiency
