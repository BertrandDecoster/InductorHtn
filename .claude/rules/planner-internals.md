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

## Choice-Count Tracking (`INDHTN_CHOICE_TRACKING`)

Compiled out by default (`option ... OFF` in `src/CMakeLists.txt`). When enabled,
`FindAllPlans` accumulates two kinds of data across the **entire** backtracking
search (not just successful plans):

- **`ChoiceRecord`** (original): per task tree-node, the *sets* `unifyingMethods`
  and `viableMethods`. Exposed via `HtnGetChoiceData` → `GetChoiceData()`.
- **`MethodClauseStats` / `AtomStats`** (cross-search counts): exposed via
  `HtnGetChoiceStats` → `GetChoiceStats()` as `{byAtom, byMethod}` and rendered
  by `htn_components evaluate`.

### Counting model — unit is **groundings**, completion is **local**

For a normal method `M` with `N` body subtasks, the precondition produces some
number of groundings; each grounding is classified by the **furthest subtask of
`M`'s own body that fully completed** (its whole subtree reached leaves),
*independent of anything downstream of `M`*:

```
furthestCompleted[k]  (0 <= k < N)  = groundings that completed subtasks 0..k-1
                                      but failed to complete subtask k
furthestCompleted[N]                = groundings whose entire body completed
sum(furthestCompleted) == groundingsN
```

For backward-compatible reporting, `positions[k].failCount == furthestCompleted[k]`
and `successS == furthestCompleted[N]`. A precondition gate failure (`N == 0`
groundings) is counted separately in `gateFailCount`.

This answers, e.g. for `do(find_enemy, cast_spell, loot_body)`: did the method
fail to *find*, to *cast*, or to *loot*? — using only the method's own body.

**Why local (not continuation-based).** Body subtasks are pushed *ahead of* the
method's continuation, with a `methodScopeEnd(M)` marker between them. Reaching
subtask `k+1` proves subtask `k` fully completed to leaves; reaching
`methodScopeEnd(M)` proves the whole body completed — all **before** `M`'s
continuation runs. So a *downstream* sibling failing does **not** count against
`M`. Concretely, for `head :- do(func1, func2)` where `func2(c)` fails: `head`
is recorded as failing at position 1 (`func2`), and `func1`'s own grounding for
that case is recorded as a **full local success** (its body completed), not a
failure. (`completion` is detected via the `methodScopeEnd` marker, which
requires `INDHTN_TREE_SIBLING_TRACKING`; without it the histogram degrades to
the continuation-based `returnValue`.)

### Per-hook implementation

| Hook | Location (`HtnPlanner.cpp`) | What it records |
|------|----------------------------|-----------------|
| Emission tag | `NextNormalMethodCondition` (before the `SearchNextNodeBacktrackable` push); `HandleAllOf`/`HandleAnyOf`; goals tagged in `PlanState` ctor | `csTagBody` stamps each bound subtask term with `{clauseDocOrder, slot, parentNodeID}` in `csTermOrigin`, and resets `csGroundingDeepestPos[M]` for the new grounding |
| A — tested | `NextTask`, right after `CreateTreeNodeForTask` | `csRecordTested`: bumps by-atom + by-method position `testedCount` (operators included, bookkeeping skipped); updates deepest-position-reached. Also detects `methodScopeEnd(parentNodeID)` and marks that parent's body as locally completed this grounding (`csGroundingBodyDone`) |
| B — clears | the existing viable block (`NextMethodThatApplies` success path) | `csRecordClear`: bumps per-resolving-method `clearCount` (deduped once per invocation via `csClearedCounted`) |
| C/D — grounding outcome | `ReturnFromNextNormalMethodCondition` | `csRecordGrounding`: `groundingsN++`; increments `furthestCompleted[N]` if the body completed locally (`methodScopeEnd` reached, or `N==0`, or `returnValue`), else `furthestCompleted[deepestReached]` |
| Gate fail | `conditionResolutions == nullptr` branch | `csRecordGateFail`: `gateFailCount++` |

Attribution avoids the sibling stack entirely: parent clause + position travel
on the **term tag** (`csTermOrigin`, keyed by `HtnTerm*`). Because terms are
interned, the tag is stable across find-all re-resolution (same pointer).

Two pointer-identity subtleties are handled, one is a documented residual:
- **Arithmetic args** (e.g. `opGain(+(2,3))`): `NextTask` runs
  `ResolveArithmeticTerms` (re-interning to `opGain(5)`, a *different* pointer)
  before the tag is read. `csTagBody` therefore keys on the *resolved* term and
  pins it alive in `csTermOriginKeepAlive` so the factory's weak-ptr interning
  can't free it before re-resolution. Without this the by-method position for an
  arithmetic-bearing subtask would silently drop.
- **Address reuse across groundings**: each grounding re-runs `csTagBody`, which
  overwrites the stale `csTermOrigin[ptr]` entry before that grounding's subtasks
  are tested, so a freed-then-reused address self-corrects.
- **Residual (known limitation)**: the *same fully-ground subtask appearing at
  two positions in one `do()`* — e.g. `do(foo(x), foo(x))` — interns to a single
  pointer, so both occurrences resolve to the last slot tagged. This mis-slots
  between two positions of one method only; by-atom counts are unaffected. A
  structural (decomposition-tree) fix was scoped and declined as too invasive for
  the payoff — see the by-method caveats in `docs/method-failure-analysis.md`.

### Excluded / approximate cases

- **`anyOf`/`allOf`** clauses are excluded from the S+A+B partition (their
  groundings are merged/flattened, returning via `ReturnFromSetOfConditions`, not
  `ReturnFromNextNormalMethodCondition`). They still record `tested`/`clears`,
  and are labelled `methodType` `anyOf`/`allOf` (report shows `partition=N/A`).
- Tasks inside `try()` and `parallel()` are not separately tagged, so their
  by-method position attribution falls back; by-atom counts are still exact (they
  only need the functor).
