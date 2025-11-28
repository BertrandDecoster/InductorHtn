# Hierarchical Task Network (HTN) Planning - Technical Reference

This document provides a comprehensive reference for understanding HTN planning as implemented in the InductorHTN engine. It serves as documentation for navigating and understanding the codebase.

## Table of Contents

1. Introduction to HTN Planning
2. Theoretical Foundations
3. Prolog and Logic Programming
4. Core Data Structures
5. The Unification Algorithm
6. SLD Resolution
7. HTN Planning Algorithm
8. InductorHTN Architecture
9. Codebase Navigation Guide
10. Built-in Predicates Reference

---

## 1. Introduction to HTN Planning

### The Core Insight

When humans plan, they don't enumerate all possible world states. Instead, they think hierarchically: "To travel from A to B, I could drive, take a taxi, or walk. To drive, I need to get my keys, walk to the car, start it..." This recursive decomposition is the essence of HTN planning.

### HTN vs Classical Planning

Classical planners (like STRIPS) search through a space of world states, applying operators to reach a goal state. HTN planners instead search through a space of task decompositions, guided by domain knowledge encoded in methods.

Key differences:
- Classical planning: "What sequence of actions achieves this goal state?"
- HTN planning: "How do I accomplish this task?"

HTN planning is often more efficient because methods encode expert knowledge about how to solve problems, pruning the search space dramatically.

### The SHOP Model

InductorHTN implements the SHOP (Simple Hierarchical Ordered Planner) model. SHOP processes tasks in the order they will be executed, which means:
- The planner always knows the complete current world state
- No goal interactions to resolve (tasks are ordered)
- Easy to integrate procedural code

---

## 2. Theoretical Foundations

### First-Order Logic

HTN planning uses first-order logic (FOL) to represent knowledge. FOL provides:
- Constants: Specific objects (e.g., `downtown`, `taxi1`)
- Variables: Placeholders that can be bound to constants (e.g., `?location`)
- Predicates: Relations between objects (e.g., `at(taxi1, downtown)`)
- Functions: Mappings from objects to objects
- Quantifiers: "for all" and "there exists"
- Connectives: and, or, not, implies

### Terms

A term is the fundamental unit of representation:
- A constant is a term (e.g., `downtown`)
- A variable is a term (e.g., `?x`)
- If `f` is a function symbol and `t1...tn` are terms, then `f(t1,...,tn)` is a term

In Prolog/HTN terminology:
- An atom is a constant (no arguments)
- A compound term has a functor and arguments: `at(agent, downtown)`
- A ground term contains no variables

### Substitutions

A substitution is a mapping from variables to terms. Written as:
```
{?x/downtown, ?y/taxi1}
```

Applying a substitution replaces variables with their mapped terms:
```
at(?x, ?y) with {?x/agent, ?y/downtown} becomes at(agent, downtown)
```

---

## 3. Prolog and Logic Programming

InductorHTN uses Prolog as its knowledge representation and reasoning layer. Understanding Prolog is essential for understanding how HTN planning works.

### Facts

Facts are unconditional assertions about the world:
```prolog
at(agent, downtown).
distance(downtown, park, 2).
hasVehicle(taxi1).
```

A fact is stored as a rule with an empty body.

### Rules

Rules express conditional knowledge:
```prolog
canWalk(?from, ?to) :- distance(?from, ?to, ?d), =<(?d, 3).
```

This reads: "canWalk from ?from to ?to if the distance from ?from to ?to is ?d and ?d is less than or equal to 3."

The `:-` operator means "if" (read right to left). The head is true if all goals in the body are true.

### Queries

A query asks Prolog to find variable bindings that make a goal true:
```prolog
?- canWalk(downtown, ?where).
```

Prolog searches for all values of `?where` that satisfy the goal.

### Variable Naming Convention

InductorHTN uses `?` prefix for variables instead of Prolog's capitalization convention:
- Standard Prolog: `Variable` (capitalized), `constant` (lowercase)
- InductorHTN: `?variable` (? prefix), `constant` (no prefix)

This is controlled by the compiler template and stored internally with the `?` prefix in the term's name.

### The Closed World Assumption

Prolog operates under the Closed World Assumption (CWA): anything not known to be true is assumed false. If `at(agent, park)` is not in the knowledge base, then `not(at(agent, park))` succeeds.

---

## 4. Core Data Structures

### HtnTerm (src/FXPlatform/Prolog/HtnTerm.h)

The fundamental data structure representing all logical expressions.

Term types (ordered for Prolog comparison):
1. Variable - Unbound placeholder
2. FloatType - Floating point number
3. IntType - Integer
4. Atom - Named constant with no arguments
5. Compound - Functor with arguments

Key properties:
- Immutable after creation (required for use as map keys)
- Names are interned (pointer comparison for equality)
- Variables store `?` prefix internally: `?x` stored as `"?x"`

Important methods:
- `isVariable()`: Check if term is a variable
- `isGround()`: True if term contains no variables
- `isConstant()`: True if no arguments (atom)
- `TermCompare()`: Prolog-standard term ordering
- `SubstituteTermForVariable()`: Apply substitution
- `MakeVariablesUnique()`: Rename variables for clause instantiation

### HtnTermFactory (src/FXPlatform/Prolog/HtnTermFactory.h)

Central factory managing all term creation with memory efficiency.

Features:
- String interning: Each unique string stored once
- Term interning: Frequently used terms cached
- Memory tracking: `dynamicSize()` reports total usage
- Out-of-memory detection: `outOfMemory()` flag

All terms must come from the same factory for correct interning.

### UnifierType

Represents a set of variable bindings:
```cpp
typedef std::pair<std::shared_ptr<HtnTerm>, std::shared_ptr<HtnTerm>> UnifierItemType;
typedef std::vector<UnifierItemType> UnifierType;
```

Example: `[(?x, downtown), (?y, taxi1)]` means `?x` is bound to `downtown` and `?y` to `taxi1`.

### HtnRule (src/FXPlatform/Prolog/HtnRule.h)

Represents a Prolog rule or fact:
- `head`: The conclusion (left of `:-`)
- `tail`: The conditions (right of `:-`), empty for facts

Methods:
- `IsFact()`: True if tail is empty
- `MakeVariablesUnique()`: Instantiate with fresh variables

### HtnRuleSet (src/FXPlatform/Prolog/HtnRuleSet.h)

The knowledge base containing facts and rules.

Architecture for memory efficiency:
- `HtnSharedRules`: Base ruleset shared across copies
- `FactsDiff`: Delta tracking additions/deletions
- Copy-on-write semantics for backtracking

Key methods:
- `AllRulesThatCouldUnify()`: Find matching rules by signature
- `CreateNextState()`: Create new state with modifications
- `Update()`: Modify current state (for operators)

### HtnMethod (src/FXPlatform/Htn/HtnMethod.h)

Represents how to decompose a compound task:
- `head`: Task being decomposed (e.g., `travel(?dest)`)
- `condition`: Preconditions (if-clause)
- `tasks`: Subtasks (do-clause)
- `methodType`: Normal, AllSetOf, or AnySetOf
- `isDefault`: True if fallback method (else)

### HtnOperator (src/FXPlatform/Htn/HtnOperator.h)

Represents a primitive action that modifies world state:
- `head`: Action name and parameters
- `deletions`: Facts to remove (del-clause)
- `additions`: Facts to add (add-clause)
- `isHidden`: If true, excluded from final plan output

---

## 5. The Unification Algorithm

Unification is the process of finding a substitution that makes two terms identical.

### The Algorithm (Robinson's Unification)

Given two terms `t1` and `t2`, find substitution `θ` such that `t1θ = t2θ`.

```
Unify(t1, t2):
  If t1 and t2 are identical constants:
    Return empty substitution {}

  If t1 is a variable:
    If t1 occurs in t2 (occurs check):
      Fail
    Return {t1/t2}

  If t2 is a variable:
    If t2 occurs in t1 (occurs check):
      Fail
    Return {t2/t1}

  If t1 and t2 are compound terms with same functor/arity:
    θ = {}
    For each pair of corresponding arguments (a1, a2):
      σ = Unify(a1θ, a2θ)
      If σ fails: Fail
      θ = compose(θ, σ)
    Return θ

  Fail
```

### Examples

```
Unify(at(?x, downtown), at(agent, ?y))
  = {?x/agent, ?y/downtown}

Unify(f(a, ?x), f(?y, b))
  = {?y/a, ?x/b}

Unify(f(a), g(a))
  = Fail (different functors)

Unify(?x, f(?x))
  = Fail (occurs check - infinite term)
```

### Implementation

In InductorHTN, unification is implemented in `HtnGoalResolver::Unify()`:
```cpp
static std::shared_ptr<UnifierType> Unify(
    HtnTermFactory *factory,
    std::shared_ptr<HtnTerm> term1,
    std::shared_ptr<HtnTerm> term2
);
```

Returns `nullptr` if unification fails, otherwise returns the unifier.

---

## 6. SLD Resolution

SLD (Selective Linear Definite clause) Resolution is Prolog's inference procedure.

### The Resolution Process

Given:
- A goal (query) to prove
- A knowledge base of facts and rules

Resolution proceeds:
1. Select the leftmost goal in the resolvent
2. Find a rule whose head unifies with the goal
3. Replace the goal with the rule's body (instantiated with the unifier)
4. Repeat until resolvent is empty (success) or no rules match (failure with backtracking)

### Example Trace

Knowledge base:
```prolog
grandparent(?x, ?z) :- parent(?x, ?y), parent(?y, ?z).
parent(alice, bob).
parent(bob, charlie).
```

Query: `grandparent(alice, ?who)`

Resolution:
```
1. Goal: grandparent(alice, ?who)
   Unify with: grandparent(?x, ?z) :- parent(?x, ?y), parent(?y, ?z)
   Unifier: {?x/alice, ?z/?who}
   New goals: parent(alice, ?y), parent(?y, ?who)

2. Goal: parent(alice, ?y)
   Unify with: parent(alice, bob).
   Unifier: {?y/bob}
   New goals: parent(bob, ?who)

3. Goal: parent(bob, ?who)
   Unify with: parent(bob, charlie).
   Unifier: {?who/charlie}
   New goals: (empty)

4. Success! ?who = charlie
```

### Backtracking

When a goal cannot be satisfied, Prolog backtracks:
1. Undo the most recent unification
2. Try the next matching rule for that goal
3. If no more rules, backtrack further

This depth-first search with backtracking explores all solutions.

### Implementation in InductorHTN

SLD Resolution is implemented in `HtnGoalResolver` (src/FXPlatform/Prolog/HtnGoalResolver.cpp):

Key components:
- `ResolveState`: Complete computation state (resumable)
- `ResolveNode`: Single node in the search tree
- `resolvent`: Current goals to prove
- `rulesThatUnify`: Matching rules for current goal

Main methods:
- `ResolveAll()`: Find all solutions
- `ResolveNext()`: Find next solution (resumable)
- `FindAllRulesThatUnify()`: Get matching rules

The algorithm is iterative (not recursive) for:
- Memory efficiency (explicit stack instead of call stack)
- Resumability (can pause and continue)
- Memory budget enforcement

### Continue Points

The resolver uses an explicit state machine with continue points:
```cpp
enum class ResolveContinuePoint {
    CustomStart,      // Starting custom rule
    CustomContinue1-4,// Custom rule continuation
    Cut,              // Processing cut (!)
    NextGoal,         // Process next goal
    NextRuleThatUnifies, // Try next matching rule
    ProgramError,     // Error state
    Return            // Return to parent
};
```

---

## 7. HTN Planning Algorithm

The HTN planning algorithm decomposes tasks into primitive operators.

### Core Concepts

**Task**: An abstract action to accomplish. Can be:
- Primitive: Directly executable (operator)
- Compound: Requires decomposition (method)

**Method**: A recipe for accomplishing a compound task:
```prolog
travel(?dest) :- if(at(?here)), do(go(?here, ?dest)).
```

**Operator**: A primitive action that changes world state:
```prolog
go(?from, ?to) :- del(at(?from)), add(at(?to)).
```

### The Algorithm (SHOP-style)

```
Plan(tasks, state):
  If tasks is empty:
    Return empty plan (success)

  task = first(tasks)
  remaining = rest(tasks)

  If task is primitive (has operator):
    operator = FindOperator(task)
    If operator.head unifies with task with unifier θ:
      If operatorθ is ground:
        newState = Apply(operator, state)
        plan = Plan(remaining, newState)
        If plan succeeds:
          Return [operator | plan]
    Fail

  If task is compound (has methods):
    For each method where method.head unifies with task:
      For each solution to method.condition in state:
        subtasks = method.tasks (instantiated)
        plan = Plan(subtasks + remaining, state)
        If plan succeeds:
          Return plan
    Fail
```

### Task Processing Details

For primitive tasks (operators):
1. Find operator matching task name
2. Unify operator head with task
3. Verify result is ground (no unbound variables)
4. Apply operator: delete facts, add facts
5. Continue with remaining tasks
6. No backtrack point needed (operators are deterministic)

For compound tasks (methods):
1. Find all methods whose head unifies with task
2. For each method (in document order):
   a. Resolve precondition against current state
   b. For each solution:
      - Substitute unifiers into subtasks
      - Replace task with subtasks
      - Create backtrack point (copy state)
      - Continue planning

### Implementation in InductorHTN

The planner is implemented in `HtnPlanner` (src/FXPlatform/Htn/HtnPlanner.cpp).

Key structures:
- `PlanState`: Complete planning computation (resumable)
- `PlanNode`: Single node in planning search tree

PlanNode members:
- `task`: Current task being processed
- `tasks`: Remaining tasks
- `method`: Current method being tried
- `unifiedMethods`: All methods that match
- `conditionResolutions`: Solutions to precondition
- `state`: Current world state
- `operators`: Collected plan operators

Continue points:
```cpp
enum class PlanNodeContinuePoint {
    Fail,
    NextTask,
    ReturnFromCheckForOperator,
    NextMethodThatApplies,
    NextNormalMethodCondition,
    OutOfMemory,
    ReturnFromNextNormalMethodCondition,
    ReturnFromHandleTryTerm,
    ReturnFromSetOfConditions,
    Abort
};
```

### Memory Management

InductorHTN uses careful memory management for constrained environments:
- Configurable memory budget
- State copying only at backtrack points
- Shared base ruleset (copy-on-write)
- Periodic memory checks during planning
- Graceful out-of-memory handling

---

## 8. InductorHTN Architecture

### Component Layers

```
Application Code
      |
      v
HtnCompiler (HTN syntax -> methods/operators)
      |
      v
PrologCompiler (Prolog syntax -> rules/facts)
      |
      v
HtnPlanner (Main orchestrator)
      |
      +---> HtnGoalResolver (Precondition resolution)
      |         |
      |         v
      |     HtnRuleSet (Knowledge base)
      |
      v
Plan Generation
```

### HTN Syntax Extensions

InductorHTN extends Prolog syntax with HTN-specific constructs:

**Methods** (if/do):
```prolog
methodName(?args) :- if(conditions), do(subtasks).
```

**Operators** (del/add):
```prolog
operatorName(?args) :- del(factsToRemove), add(factsToAdd).
```

**Method Modifiers**:
- `else`: Fallback method (only try if previous methods fail)
- `allOf`: Execute for all condition solutions (all must succeed)
- `anyOf`: Execute for all condition solutions (at least one must succeed)

**Operator Modifiers**:
- `hidden`: Operator not included in plan output

**Special Terms**:
- `try(task)`: Optional task, failure doesn't fail parent
- `first(goal)`: Return only first solution (deterministic)

### Control Flow for Special Constructs

**try() Handling**:
When the planner encounters `try(task)`:
1. Attempt to plan task
2. If task fails, continue with remaining tasks (no failure)
3. If task succeeds, include its operators in plan

**anyOf Methods**:
1. Resolve condition to get all solutions
2. For each solution, wrap subtask execution in try()
3. Succeed if at least one execution succeeds

**allOf Methods**:
1. Resolve condition to get all solutions
2. Execute subtasks for each solution sequentially
3. Succeed only if all executions succeed

**else Methods**:
Methods with `else` are only tried if all non-else methods fail. This provides explicit priority ordering.

---

## 9. Codebase Navigation Guide

### Directory Structure

```
src/FXPlatform/
  Prolog/           - Prolog reasoning engine
  Htn/              - HTN planning engine
  Parser/           - PEG parser framework
  Win/iOS/Posix/    - Platform-specific code
```

### Prolog Engine Files

**HtnTerm.h/.cpp** - Term representation
- `HtnTermType` enum: Variable, Float, Int, Atom, Compound
- `HtnTerm` class: Immutable term with name, arguments
- Key: `isVariable()`, `isGround()`, `SubstituteTermForVariable()`

**HtnTermFactory.h/.cpp** - Term creation and interning
- String pool: `GetInternedString()`
- Term cache: `GetInternedTerm()`
- Memory tracking: `dynamicSize()`, `outOfMemory()`

**HtnRule.h/.cpp** - Rule/fact representation
- `head` + `tail` structure
- `IsFact()`: True if empty tail
- `MakeVariablesUnique()`: Clause instantiation

**HtnRuleSet.h/.cpp** - Knowledge base
- `HtnSharedRules`: Shared base rules
- `FactsDiff`: Delta for modifications
- `AllRulesThatCouldUnify()`: Rule lookup
- `CreateNextState()`: State forking

**HtnGoalResolver.h/.cpp** - SLD Resolution
- `ResolveAll()`: Find all solutions
- `ResolveNext()`: Resumable resolution
- `Unify()`: Unification algorithm
- `ResolveNode`, `ResolveState`: Search tree

**HtnArithmeticOperators.h/.cpp** - Built-in arithmetic
- Operators: +, -, *, /, comparison
- Functions: abs, min, max, float, integer

### HTN Engine Files

**HtnPlanner.h/.cpp** - Main planning engine
- `FindPlan()`, `FindAllPlans()`: Plan generation
- `PlanNode`, `PlanState`: Search tree
- `CheckForOperator()`: Operator handling
- Memory budget enforcement

**HtnMethod.h/.cpp** - Method representation
- `head`, `condition`, `tasks`
- `methodType`: Normal, AllSetOf, AnySetOf
- `isDefault`: Else method flag

**HtnOperator.h/.cpp** - Operator representation
- `head`, `deletions`, `additions`
- `isHidden`: Visibility flag

**HtnDomain.h** - Domain interface
- `AddMethod()`, `AddOperator()`
- `AllMethods()`, `AllOperators()`

**HtnCompiler.h/.cpp** - HTN syntax parsing
- Extends `PrologCompiler`
- `ParseRule()`: HTN keyword processing
- Handles: if, do, del, add, else, allOf, anyOf, hidden

### Parser Files

**Parser.h/.cpp** - PEG parser framework
- Template-based recursive descent
- Transactional parsing with backtrack
- Symbol tree construction

**Lexer.h/.cpp** - Tokenization
- Transaction support for backtracking
- Error position tracking
- Character-by-character processing

**PrologParser.h** - Prolog grammar
- Symbol IDs for AST nodes
- Two variable conventions (templates)
- Comment handling

**PrologCompiler.h/.cpp** - Prolog compilation
- `CreateTermFromItem()`: AST to terms
- `ParseRule()`, `ParseAtom()`, `ParseList()`
- Logic error detection

---

## 10. Built-in Predicates Reference

### Arithmetic

**is(?Result, Expression)**
Evaluates arithmetic expression:
```prolog
is(?x, +(3, 4))      % ?x = 7
is(?y, *(2, ?x))     % ?y = 14
```

**Comparison: <, >, =<, >=, ==**
```prolog
<(3, 5)              % succeeds
>=(4, 4)             % succeeds
```

### Unification

**=(?X, ?Y)**
Unifies two terms:
```prolog
=(?x, foo)           % ?x = foo
=(f(?a, ?b), f(1, 2)) % ?a = 1, ?b = 2
```

### Control

**! (Cut)**
Commits to current choices, preventing backtracking. When cut succeeds:
- Discards all alternative rules for the current goal
- Discards alternative solutions for goals left of cut in the rule

```prolog
max(?x, ?y, ?x) :- >=(?x, ?y), !.  % Commits if first clause matches
max(?x, ?y, ?y).                    % Only tried if cut not reached
```

Use cases: if-then-else, preventing redundant solutions, implementing negation.
Implementation: `isCut()` detects `!`, handled via `ResolveContinuePoint::Cut` with `!>` / `!<` scope markers.

**not(Goal)**
Negation as failure (succeeds if Goal is not provable):
```prolog
not(at(agent, park))
```

**first(Goal)**
Returns only first solution:
```prolog
first(member(?x, [a, b, c])) % ?x = a only
```

**forall(Generator, Test)**
Universal quantification:
```prolog
forall(member(?x, [1,2,3]), <(?x, 5)) % all elements < 5
```

### Meta-predicates

**findall(?Template, Goal, ?List)**
Collect all solutions:
```prolog
findall(?x, member(?x, [a,b,c]), ?list) % ?list = [a,b,c]
```

**count(?Count, Goal)**
Count solutions:
```prolog
count(?n, member(?x, [a,b,c])) % ?n = 3
```

**distinct(?Key, Goal)**
Unique solutions by key:
```prolog
distinct(?x, parent(?x, ?y)) % unique parents
```

**sortBy(?Key, Direction, Goal)**
Sort solutions:
```prolog
sortBy(?dist, <(distance(?from, ?to, ?dist))) % ascending by distance
```

### Database Modification

**assert(Fact)**
Add fact to knowledge base:
```prolog
assert(visited(room1))
```

**retract(Fact)**
Remove first matching fact:
```prolog
retract(at(agent, ?old))
```

**retractall(Pattern)**
Remove all matching facts:
```prolog
retractall(visited(?x))
```

### String Operations

**atom_chars(?Atom, ?List)**
Convert between atom and character list:
```prolog
atom_chars(hello, ?list)  % ?list = [h,e,l,l,o]
atom_chars(?atom, [a,b])  % ?atom = ab
```

**atom_concat(?A, ?B, ?Result)**
Concatenate atoms:
```prolog
atom_concat(foo, bar, ?r) % ?r = foobar
```

**downcase_atom(?In, ?Out)**
Convert to lowercase:
```prolog
downcase_atom('Hello', ?x) % ?x = hello
```

### Type Checking

**atomic(?X)**
True if X is an atom (not compound):
```prolog
atomic(foo)     % succeeds
atomic(f(x))    % fails
```

---

## Algorithm Quick Reference

### Unification

Input: Two terms t1, t2
Output: Unifier (substitution) or failure

1. Both constants? Equal names -> {} else fail
2. One variable? Occurs check, then bind variable to other term
3. Both compound? Same functor/arity -> recursively unify arguments
4. Otherwise fail

### SLD Resolution

Input: Goals, knowledge base
Output: Variable bindings or failure

1. Empty goals? Success, return unifier
2. Select leftmost goal
3. Find rules with matching head
4. Unify goal with rule head
5. Replace goal with rule body (substituted)
6. Recurse; backtrack on failure

### HTN Planning

Input: Tasks, initial state, methods, operators
Output: Sequence of operators

1. Empty tasks? Success, return plan
2. First task primitive? Find operator, apply to state, continue
3. First task compound? Find methods, resolve preconditions, decompose
4. Backtrack on failure, trying alternatives

---

## Key Insights for Development

1. **All terms must come from the same factory** for interning to work correctly.

2. **Variables are immutable** - unification creates new terms with substitutions applied.

3. **State copies are expensive** - only made at backtrack points (method application).

4. **Operators don't create backtrack points** - they must be deterministic.

5. **Resolution is resumable** - ResolveState/PlanState can be paused and continued.

6. **Memory budget is configurable** - checked at node creation, graceful degradation.

7. **Document order matters** - methods tried in order they appear in source.

8. **Cut (!) affects backtracking** - prevents trying alternative rules for cut goal.

9. **try() wraps in success** - failure of try() content doesn't fail parent.

10. **Hidden operators** - used for internal state tracking, not in output plan.

---

## Adding Custom Rules (External Tool Integration)

To integrate external tools (pathfinding, math solvers, etc.), add a custom rule in `HtnGoalResolver.cpp`. There are dozens of existing rules to use as templates:
- `RuleIs` - arithmetic evaluation with variable binding
- `RuleNot` - negation as failure
- `RuleFirst` - returns first solution only

Steps:
1. Register in constructor (line ~486-516) with `AddCustomRule()`
2. Declare static method in `HtnGoalResolver.h` (line ~79-103)
3. Implement using existing rules as template (success pushes child node, failure pops stack)
