# HTN Planner Internals - FindNextPlan

## Overview
The `FindNextPlan` function in `HtnPlanner.cpp` implements a stackless depth-first search HTN planner. It avoids recursion to prevent stack overflow on deep plans and explicitly manages memory.

## Core Data Structures

### PlanState
Maintains the overall planning state across multiple solution searches.

**Key members:**
- `stack`: Vector of `PlanNode` pointers representing the search tree
- `factory`: Term factory for creating/managing HTN terms  
- `initialState`: The starting world state (facts/rules)
- `memoryBudget`: Memory limit for planning
- `returnValue`: Communication mechanism between nodes (success/failure)
- `highestMemoryUsed`: Tracks peak memory usage
- `furthestCriteriaFailure`: For error reporting

### PlanNode
Represents a single node in the HTN search tree.

**Key members:**
- `state`: Current world state at this node
- `tasks`: Remaining tasks to solve
- `task`: Current task being solved  
- `operators`: Accumulated operators (the plan so far)
- `continuePoint`: Where to resume execution when returning to this node
- `unifiedMethods`: All the methods that unify with the current task
- `method`: Current method being applied
- `conditionResolutions`: Different ways the method's conditions can be satisfied
- `unifiedMethods`: Methods that unify with the current task
- `retry`: Used for `try()` clause handling
- `methodHadSolution`: Tracks if any method branch succeeded (for `else` handling)

### PlanNodeContinuePoint Enum
Controls the state machine flow:

1. **NextTask**: Start processing the next task from the task list
2. **NextMethodThatApplies**: Try the next method that unifies with the current task  
3. **NextNormalMethodCondition**: Try the next condition resolution for the current method
4. **ReturnFromCheckForOperator**: Returning from operator application
5. **ReturnFromNextNormalMethodCondition**: Returning from exploring a method's subtasks
6. **ReturnFromHandleTryTerm**: Returning from a `try()` clause
7. **ReturnFromSetOfConditions**: Returning from `anyOf`/`allOf` processing
8. **OutOfMemory**: Memory limit exceeded
9. **Abort**: User-requested abort
10. **Fail**: Should never occur (assertion failure)

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

### Detailed Flow Between Continue Points

#### 1. NextTask → NextMethodThatApplies
**Entry**: Node starts with `NextTask` when first created or returning from completed subtask
**Process**:
1. Calls `SetNodeTask()` to get next task from node's task list
2. If no tasks → SUCCESS (plan complete)
3. If task exists:
   - Checks if it's an operator → pushes child node with `ReturnFromCheckForOperator`
   - Checks if it's special task → handles accordingly
   - Otherwise: finds all methods that unify with task
4. **Transition**: Sets `continuePoint = NextMethodThatApplies` if methods found
5. **Exit**: Continues loop to process methods

#### 2. NextMethodThatApplies → NextNormalMethodCondition
**Entry**: Node has list of unified methods to try
**Process**:
1. Calls `SetNextMethodThatUnifies()` to get next method
2. Handles `else` clause logic (skips if previous method succeeded)
3. If no more methods → returns to parent with success/failure status
4. If method exists:
   - Resolves method's conditions (if) against current state
   - Gets list of condition resolutions (different variable bindings)
5. **Transition**: If conditions resolve and method is Normal type, sets `continuePoint = NextNormalMethodCondition`
6. **Alternative**: For `anyOf`/`allOf`, calls special handlers instead
7. **Failure**: If conditions don't resolve, stays in `NextMethodThatApplies` to try next method

#### 3. NextNormalMethodCondition → Child Node → ReturnFromNextNormalMethodCondition
**Entry**: Node has method with resolved conditions to explore
**Process**:
1. Calls `SetNextCondition()` to get next condition resolution
2. If no more conditions → goes back to `NextMethodThatApplies`
3. If condition exists:
   - Substitutes variables from method head and condition into subtasks
   - Creates **new child node** with these subtasks
   - Sets child's `continuePoint = NextTask`
   - Sets parent's `continuePoint = ReturnFromNextNormalMethodCondition`
4. **Child Execution**: Child node runs, potentially creating its own children
5. **Return**: When child completes, parent resumes at `ReturnFromNextNormalMethodCondition`

#### 4. ReturnFromNextNormalMethodCondition → NextNormalMethodCondition
**Entry**: Returning from exploring a condition's subtasks
**Process**:
1. Checks `returnValue` from child
2. If true → sets `methodHadSolution = true`
3. **Transition**: Sets `continuePoint = NextNormalMethodCondition` to try next condition
4. **Loop**: Goes back to step 3 to explore next condition resolution

#### 5. ReturnFromCheckForOperator → Parent
**Entry**: Returning from operator application
**Process**:
1. Operator already modified state and added to plan
2. Simply returns to parent with child's return value
3. **No alternatives**: Operators don't have alternative branches

### Complete Flow Example

For task `travel-to(park)`:

```
Node1: continuePoint=NextTask
  → Gets task "travel-to(park)"
  → Finds 3 methods that unify
  → Sets continuePoint=NextMethodThatApplies

Node1: continuePoint=NextMethodThatApplies  
  → Gets method "travel-to(?q) :- if(at(?p),...), do(walk(?p,?q))"
  → Resolves conditions, gets 1 resolution (?p=downtown)
  → Sets continuePoint=NextNormalMethodCondition

Node1: continuePoint=NextNormalMethodCondition
  → Gets condition resolution (?p=downtown)
  → Creates Node2 with tasks [walk(downtown,park)]
  → Sets own continuePoint=ReturnFromNextNormalMethodCondition
  → Pushes Node2

Node2: continuePoint=NextTask
  → Gets task "walk(downtown,park)"
  → Finds it's an operator
  → Creates Node3, sets return point=ReturnFromCheckForOperator
  → Pushes Node3

Node3: continuePoint=NextTask
  → No more tasks → SUCCESS
  → Returns true to Node2

Node2: continuePoint=ReturnFromCheckForOperator
  → Returns true to Node1

Node1: continuePoint=ReturnFromNextNormalMethodCondition
  → Records methodHadSolution=true
  → Sets continuePoint=NextNormalMethodCondition
  → No more conditions
  → Sets continuePoint=NextMethodThatApplies
  → Tries next method (taxi)...
```

### Key State Transitions

- **NextTask** → `NextMethodThatApplies` (when methods found) OR Success/Failure
- **NextMethodThatApplies** → `NextNormalMethodCondition` (when conditions resolve) OR back to `NextMethodThatApplies` (try next method)
- **NextNormalMethodCondition** → Push child with `NextTask`, set self to `ReturnFromNextNormalMethodCondition`
- **ReturnFromNextNormalMethodCondition** → `NextNormalMethodCondition` (try next condition) OR `NextMethodThatApplies` (no more conditions)
- **ReturnFromCheckForOperator** → Always returns to parent

## Special Constructs

### try() Handling
- Creates two alternative branches:
  1. Execute the try() subtasks
  2. Skip the try() clause if first branch fails
- Uses `retry` flag to track if should try second branch
- `tryEnd()` bookkeeping task marks successful completion

### anyOf Handling  
- Wraps each condition resolution in `try()`
- Adds `countAnyOf()` to track successes
- Adds `failIfNoneOf()` at end to fail if zero succeeded
- Succeeds if at least one condition succeeds

### allOf Handling
- Merges all condition resolutions into single task list
- Default behavior ensures all must succeed
- Fails if any subtask fails

### else Methods
- Methods marked with `isDefault()` flag
- Only executed if previous non-else method failed
- Skipped if previous method succeeded

## Memory Management

### State Copying Strategy
- `SearchNextNode()`: Shares state with parent (no backtracking needed)
- `SearchNextNodeBacktrackable()`: Copies state (for trying alternatives)

### Memory Tracking
- Each node tracks `totalMemoryAtNodePush`
- Warns on high memory usage (>1MB per node)
- Returns partial solution if budget exceeded
- Factory tracks term memory usage

## Example Trace Analysis

For query `travel-to(park)` with initial state `at(downtown)`:

### Solution 1: Walking
```
Method: travel-to(?q) :- if(at(?p), first(walking-distance(?p,?q))), do(walk(?p,?q))
Bindings: ?p = downtown, ?q = park
Operators: walk(downtown,park)
State changes: del(at(downtown)), add(at(park))
```

### Solution 2: Taxi
```
Method: travel-to(?y) :- if(first(at(?x),at-taxi-stand(?t,?x),...)), do(hail,ride,pay)
Bindings: ?x = downtown, ?t = taxi1, ?y = park, ?d = 2
Operators: hail(taxi1,downtown), ride(taxi1,downtown,park), pay-driver(3.50)
Submethod: pay-driver decomposes to set-cash operator
```

### Solution 3: Bus
```
Method: travel-to(?y) :- if(at(?x), bus-route(?bus,?x,?y)), do(wait-for,pay,ride)
Bindings: ?x = downtown, ?bus = bus1, ?y = park
Operators: wait-for(bus1,downtown), pay-driver(1.00), ride(bus1,downtown,park)
```

## Key Design Principles

1. **Stackless Implementation**: Explicit stack management avoids recursion limits
2. **State Machine Pattern**: Continue points enable resumption after subtree exploration
3. **Memory Budgeting**: Tracks and limits memory usage with graceful degradation
4. **Backtracking Support**: State copying enables exploring alternatives
5. **Special Task Integration**: Complex constructs handled via bookkeeping tasks
6. **Trace Integration**: Comprehensive logging at each decision point

## Performance Considerations

- Terms are interned via `HtnTermFactory` for memory efficiency
- State copies are made only when backtracking is needed
- Memory is tracked per-node to identify problematic expansions
- Early termination on memory limits returns best partial solution
- Method ordering preserved from source file for predictable behavior