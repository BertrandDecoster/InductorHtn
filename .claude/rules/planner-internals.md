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

## Decomposition Tree Tracking

The planner builds a decomposition tree showing how tasks decompose into subtasks. Enabled with `INDHTN_TREE_SIBLING_TRACKING` cmake flag.

### Tree Node IDs: treeNodeID vs nodeID

The decomposition tree uses two distinct ID systems:

| Field | Description |
|-------|-------------|
| `treeNodeID` | Unique ID for each tree entry. Used for parent-child relationships. |
| `nodeID` | Reference to the PlanNode. May be shared when try() fails and next task runs on same node. |
| `parentNodeID` | Parent's `treeNodeID` (-1 for root) |
| `childNodeIDs` | Vector of children's `treeNodeID`s |

**Why two IDs?** When `try()` fails, the planner continues with remaining tasks on the **same PlanNode** (same `nodeID`). Each task still needs its own tree entry with a unique `treeNodeID` to maintain correct parent-child relationships.

Example: `do(opApply, try(triggerFreeze), try(triggerSnare), nextTask)`
- If `try(triggerSnare)` fails, `nextTask` runs on the same PlanNode
- Both `try(triggerSnare)` and `nextTask` get separate tree entries with different `treeNodeID`s but same `nodeID`

### PlanState Tree Tracking Maps

```cpp
std::vector<DecompTreeNode> decompositionTree;           // The tree itself
std::map<int, size_t> treeNodeIDToTreeIndex;             // treeNodeID -> index in decompositionTree
std::map<int, int> nodeIDToLastTreeNodeID;               // PlanNode nodeID -> last treeNodeID created for it
```

- `treeNodeIDToTreeIndex`: Fast lookup from treeNodeID to tree vector index
- `nodeIDToLastTreeNodeID`: Converts PlanNode nodeID to treeNodeID for parent lookups

### Sibling Stack

Each `PlanNode` maintains a `siblingStack: vector<pair<int, int>>` where each entry is `{parentNodeID, remainingSiblingCount}`.

- **Push**: When a method decomposes, push `{nodeID, subtaskCount - 1}` onto child's stack
- **Pop**: When scope is exhausted (count reaches 0) or explicit markers reached

### Scope Markers (Bookkeeping Tasks)

| Marker | Purpose |
|--------|---------|
| `methodScopeEnd(nodeID)` | Inserted between method's subtasks and remaining parent tasks; pops method's scope |
| `tryEnd(nodeID)` | Marks end of try() subtasks; pops try's scope |
| `countAnyOf(nodeID)` | Increments success count for anyOf processing |
| `failIfNoneOf(nodeID)` | Fails if no anyOf alternatives succeeded |
| `beginParallel` | Marks start of parallel execution block |
| `endParallel` | Marks end of parallel execution block |

### Task Merging with Scope Markers

When `SearchNextNodeBacktrackable` merges tasks:
```
Method decomposes to [A, B, C], remaining parent tasks [D, E]
Merged tasks: [A, B, C, methodScopeEnd(methodNodeID), D, E]
```

### Tree Parent Determination (`DetermineTreeParent`)

1. If sibling stack non-empty: parent = `sibStack.back().first`
2. Otherwise: parent = previous node on stack

### Special Construct Scope Handling

**try()**: On failure (`ReturnFromHandleTryTerm` with `retry=true`):
- Pop try's scope via `popSiblingScopeIfMatches(nodeID)`
- Continue with remaining tasks on same node
- `methodScopeEnd` markers ensure proper scope cleanup

**anyOf**: Each alternative wrapped in try(); `countAnyOf` tracks successes; `failIfNoneOf` at end

**allOf**: All alternatives merged into single task list

**parallel()**: Wrapped with `beginParallel`/`endParallel` markers for post-processing by `PlanParallelizer`

### Tree Node Creation (`CreateTreeNodeForTask`)

Called in `NextTask` before processing each task:

1. **Skip if task is nullptr**
2. **Skip bookkeeping tasks** (markers listed above - they consume nodeIDs but don't create tree entries)
3. **Duplicate check**: Skip if same nodeID AND same taskName already has a tree entry
4. **Determine parent**: Use `DetermineTreeParent()` to get parent's PlanNode nodeID, then convert to treeNodeID via `NodeIDToTreeNodeID()`
5. **Create tree entry**:
   - Allocate new `treeNodeID = nextTreeNodeID++`
   - Set `nodeID` to PlanNode's ID (reference only)
   - Set `parentNodeID` to parent's `treeNodeID`
   - Update `nodeIDToLastTreeNodeID[nodeID] = treeNodeID`
   - Add to parent's `childNodeIDs` vector

```cpp
// Simplified logic
int parentPlanNodeID = DetermineTreeParent(planState, node);
int parentTreeNodeID = NodeIDToTreeNodeID(planState, parentPlanNodeID);

DecompTreeNode treeNode;
treeNode.treeNodeID = planState->nextTreeNodeID++;
treeNode.nodeID = node->nodeID();
treeNode.parentNodeID = parentTreeNodeID;
treeNode.taskName = node->task->ToString();

planState->nodeIDToLastTreeNodeID[node->nodeID()] = treeNode.treeNodeID;
planState->decompositionTree.push_back(treeNode);
```

**Key insight**: When try() fails, the next task runs on the same PlanNode but gets a NEW treeNodeID. The duplicate check (same nodeID + same taskName) prevents redundant entries while allowing different tasks on the same node.

## Key Design Principles

1. **Stackless** - Explicit stack avoids recursion limits
2. **State Machine** - Continue points enable resumption
3. **Memory Budgets** - Tracked with graceful degradation
4. **Backtracking** - State copying only when needed
5. **Method Order** - Preserved from source file
6. **Sibling Tracking** - Scope markers ensure correct tree parent relationships
