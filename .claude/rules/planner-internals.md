---
description: HTN planner internals - FindNextPlan algorithm and state machine
globs: src/FXPlatform/Htn/HtnPlanner.*
---

# HTN Planner Internals

The `FindNextPlan` function in `HtnPlanner.cpp` implements a stackless depth-first search HTN planner.

## Core Data Structures

### PlanState
Maintains overall planning state across solution searches.

Key members:
- `stack` - Vector of `PlanNode` pointers (search tree)
- `factory` - Term factory for creating HTN terms
- `initialState` - Starting world state (facts/rules)
- `memoryBudget` - Memory limit for planning
- `returnValue` - Communication between nodes (success/failure)

### PlanNode
Single node in the HTN search tree.

Key members:
- `state` - Current world state at this node
- `tasks` - Remaining tasks to solve
- `task` - Current task being solved
- `operators` - Accumulated operators (plan so far)
- `continuePoint` - Where to resume when returning to this node
- `unifiedMethods` - Methods that unify with current task
- `method` - Current method being applied
- `conditionResolutions` - Ways method's conditions can be satisfied
- `methodHadSolution` - Tracks if any method branch succeeded

### PlanNodeContinuePoint Enum

Controls state machine flow (`HtnPlanner.cpp:~85`):

| Continue Point | Description |
|---------------|-------------|
| `NextTask` | Start processing next task from task list |
| `NextMethodThatApplies` | Try next method that unifies with current task |
| `NextNormalMethodCondition` | Try next condition resolution for current method |
| `ReturnFromCheckForOperator` | Returning from operator application |
| `ReturnFromNextNormalMethodCondition` | Returning from exploring method's subtasks |
| `ReturnFromHandleTryTerm` | Returning from `try()` clause |
| `ReturnFromSetOfConditions` | Returning from `anyOf`/`allOf` processing |
| `OutOfMemory` | Memory limit exceeded |
| `Abort` | User-requested abort |

## Algorithm Flow

### Main Loop Structure
```cpp
while(stack->size() > 0) {
    PlanNode node = stack->back();
    switch(node->continuePoint) {
        case NextTask: ...
        case NextMethodThatApplies: ...
        // etc.
    }
}
```

### State Transitions

```
NextTask
  ├── No tasks → SUCCESS (plan complete)
  ├── Is operator → push child, set ReturnFromCheckForOperator
  └── Has methods → set NextMethodThatApplies

NextMethodThatApplies
  ├── No more methods → return to parent
  ├── else method + previous succeeded → skip
  └── Conditions resolve → set NextNormalMethodCondition

NextNormalMethodCondition
  ├── No more conditions → set NextMethodThatApplies
  └── Has condition → push child with NextTask,
                      set ReturnFromNextNormalMethodCondition

ReturnFromNextNormalMethodCondition
  └── Record methodHadSolution, set NextNormalMethodCondition

ReturnFromCheckForOperator
  └── Always return to parent
```

## Special Constructs Handling

### try() Handling (`HtnPlanner.cpp:514`)
Creates two alternative branches:
1. Execute the `try()` subtasks
2. Skip the `try()` clause if first fails

Uses `retry` flag to track if should try second branch.

### anyOf Handling (`HtnPlanner.cpp:~1160`)
- Wraps each condition resolution in `try()`
- Adds `countAnyOf()` to track successes
- Adds `failIfNoneOf()` at end
- Succeeds if at least one condition succeeds

### allOf Handling
- Merges all condition resolutions into single task list
- All must succeed for method to succeed

### else Methods
- Methods with `isDefault()` flag
- Only executed if previous non-else method failed
- Skipped if previous method succeeded (`methodHadSolution`)

## Memory Management

### State Copying Strategy
- `SearchNextNode()` - Shares state with parent (no backtracking needed)
- `SearchNextNodeBacktrackable()` - Copies state (for trying alternatives)

### Memory Tracking
- Each node tracks `totalMemoryAtNodePush`
- Warns on high memory usage (>1MB per node)
- Returns partial solution if budget exceeded
- Factory tracks term memory via `dynamicSize()`

## Example Flow

For task `travel-to(park)`:

```
Node1: NextTask
  → Gets "travel-to(park)"
  → Finds 3 methods
  → Sets NextMethodThatApplies

Node1: NextMethodThatApplies
  → Gets method with condition at(?p)
  → Resolves: ?p=downtown
  → Sets NextNormalMethodCondition

Node1: NextNormalMethodCondition
  → Creates Node2 with [walk(downtown,park)]
  → Sets ReturnFromNextNormalMethodCondition
  → Pushes Node2

Node2: NextTask
  → "walk(downtown,park)" is operator
  → Applies operator (del/add)
  → Creates Node3

Node3: NextTask
  → No more tasks → SUCCESS
  → Returns true

Node2: ReturnFromCheckForOperator
  → Returns true

Node1: ReturnFromNextNormalMethodCondition
  → Records methodHadSolution=true
  → Tries next condition/method...
```

## Key Design Principles

1. **Stackless** - Explicit stack avoids recursion limits
2. **State Machine** - Continue points enable resumption
3. **Memory Budgets** - Tracked with graceful degradation
4. **Backtracking** - State copying only when needed
5. **Method Order** - Preserved from source file
