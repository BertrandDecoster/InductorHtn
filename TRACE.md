# HTN Plan Tree Reconstruction

## Problem Statement

The HTN planner returns only a flat list of operators via `ToStringSolution()`. The hierarchical decomposition tree (which methods were chosen, in what order, with what conditions) is lost. For debugging, explanation, and visualization, we need the full tree structure.

## Current Solution: Dummy Operators + Trace Parsing

### How It Works

1. **Preprocessing**: Inject dummy operators into HTN methods that encode method identity:
   ```prolog
   % Original
   travel-to(?dest) :- if(at(?here)), do(walk(?here, ?dest)).

   % Transformed - m1 indicates first method alternative
   travel-to(?dest) :- if(at(?here)), do(m1_travel-to(?dest), walk(?here, ?dest)).
   m1_travel-to(?dest) :- del(), add().  % Empty dummy operator
   ```

2. **Execution**: Run planner with trace capture enabled

3. **Output**: Plan now contains method markers:
   ```
   (m1_travel-to(park), walk(downtown, park))
   ```

4. **Trace Parsing**: Parse trace lines to reconstruct tree:
   - `SOLVE nodeID:X task:'...'` - new node
   - `METHOD nodeID:X resolve next method '...'` - method selection
   - `OPERATOR nodeID:X` - primitive action
   - `PUSH nodeID:Y parentID:X` - parent-child relationship
   - `SUCCESS nodeID:X` - plan found

### Implementation Files

- `src/Python/PythonUsageTree.py` - preprocessing + trace parsing
- `src/Python/HtnTreeReconstructor.py` - tree reconstruction from traces

### Pros

- No C++ changes required
- Full tree with method conditions visible
- Works with existing API

### Cons

- String parsing overhead (~18KB traces for simple plan)
- Fragile - depends on exact trace format
- Dummy operators pollute plan output
- Preprocessing step adds complexity

## Alternative 1: Trace Parsing Only (No Dummy Operators)

### Approach

Parse traces without injecting dummy operators. The METHOD lines already contain full method information:
```
METHOD nodeID:0 resolve next method 'travel-to(?q) => if(at(?p)...), do(walk(?p,?q))'
```

### Pros

- No preprocessing needed
- Clean plan output (no dummy operators)
- Same information available

### Cons

- Same string parsing overhead
- Requires trace capture to be enabled
- Cannot reconstruct tree from plan output alone

## Alternative 2: C++ Modification - Tree in Solution

### Approach

Modify `SolutionType` to include the decomposition tree:

```cpp
// HtnPlanner.h
struct TreeNode {
    int nodeID;
    int parentID;
    enum Type { METHOD, OPERATOR } type;
    std::string task;           // e.g., "travel-to(park)"
    std::string methodUsed;     // e.g., "travel-to(?q) => if(...), do(...)"
    std::vector<int> children;
};

class SolutionType {
public:
    std::vector<std::shared_ptr<HtnTerm>> first;      // operators (existing)
    std::shared_ptr<HtnRuleSet> second;               // final state (existing)
    std::vector<TreeNode> decompositionTree;          // NEW
};
```

### Changes Required

1. **HtnPlanner.h** (~line 64-82):
   - Add `TreeNode` struct
   - Add `decompositionTree` to `SolutionType`

2. **HtnPlanner.cpp** - `SolutionFromCurrentNode()` (~line 139):
   - Walk the stack and build tree from `PlanNode` parent/child relationships
   - Store in solution before returning

3. **HtnPlanner.cpp** - Add `ToStringTree()`:
   ```cpp
   static std::string ToStringTree(std::shared_ptr<SolutionType> solution, bool json = false);
   ```

4. **Python bindings** (indhtnpy):
   - Expose tree as list of tuples: `[(nodeID, parentID, type, task, method), ...]`

### Data Already Available in PlanNode

```cpp
class PlanNode {
    int m_nodeID;                    // Node identifier
    // parentID available via stack position
    shared_ptr<HtnTerm> task;        // Current task
    HtnMethod *method;               // Method used (if compound task)
    vector<shared_ptr<HtnTerm>> operators;  // Accumulated operators
};
```

### Pros

- Zero string parsing overhead
- Native data structure
- Clean API

### Cons

- Requires C++ changes and recompilation
- More memory per solution (tree storage)
- Python binding changes needed

## Alternative 3: JSON Output Mode

### Approach

Add a JSON output mode that preserves hierarchy:

```cpp
// New method in HtnPlanner
static std::string ToJsonWithTree(std::shared_ptr<SolutionType> solution);
```

Output:
```json
{
  "operators": ["walk(downtown,park)"],
  "tree": {
    "task": "travel-to(park)",
    "type": "method",
    "method": "travel-to(?q) => if(at(?p)), do(walk(?p,?q))",
    "condition": "(?p = downtown)",
    "children": [
      {"task": "walk(downtown,park)", "type": "operator"}
    ]
  }
}
```

### Pros

- Single API call returns everything
- Easy to parse in any language
- Backward compatible (existing API unchanged)

### Cons

- Still requires C++ changes
- String-based (though structured)
- JSON parsing overhead (but minimal)

## Recommendation

| Use Case | Recommended Approach |
|----------|---------------------|
| Prototyping/debugging | Current (dummy ops + traces) |
| Production with Python | Alternative 2 (C++ tree in solution) |
| Multi-language support | Alternative 3 (JSON output) |
| Minimal changes | Alternative 1 (traces only) |

## Trace Format Reference

Key trace lines for tree reconstruction:

```
HtnPlanner::FindPlan SOLVE      nodeID:0 task:'travel-to(park)' remaining:'()'
HtnPlanner::FindPlan            nodeID:0 3 methods unify with 'travel-to(park)'
HtnPlanner::FindPlan METHOD     nodeID:0 resolve next method 'travel-to(?q) => if(...), do(...)'
HtnPlanner::FindPlan            nodeID:0 substituted condition:'(...)' with unifier '(?q = park)'
HtnPlanner::FindPlan            1 condition alternatives for method '...'
HtnPlanner::FindPlan            nodeID:0 condition:'(?p = downtown)'
HtnPlanner::FindPlan            PUSH       nodeID:1 parentID:0
HtnPlanner::FindPlan OPERATOR   nodeID:1 Operator 'walk(?here,?there)' unifies with 'walk(downtown,park)'
HtnPlanner::FindPlan            isHidden: 0, deletes:'(at(downtown))', adds:'(at(park))'
HtnPlanner::FindPlan SUCCESS    nodeID:2 no tasks remain.
HtnPlanner::FindPlan END        Solution:'(...)'
```

## Tree Node Types

From trace analysis:

- **METHOD**: Task with multiple decomposition alternatives
- **INFO_OP**: Dummy operator encoding method choice (m1_, m2_, etc.)
- **OPERATOR**: Real primitive action with del/add effects
- **FINAL**: Leaf node indicating successful plan

## Implementation Priority

1. Continue using current approach for development
2. When performance matters, implement Alternative 2
3. Document trace format stability requirements
