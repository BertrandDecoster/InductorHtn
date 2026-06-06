# Challenge Play Protocol

Canonical workflow for "playing" an HTN challenge level using MCP tools.

**Purpose:** Playing a level means stepping through HTN plans to understand what the player experiences — what operators fire, what state changes occur, which strategies the planner chooses. The goal is to *narrate the plan space*, not to find an optimal solution.

---

## Workflow

### Step 1 — Load

Create a session and compile the assembled level file.

```
indhtn_create_session → sessionId
indhtn_load_files sessionId ["/path/to/assembled/<level>/latest.htn"]
```

The assembled file is a single `.htn` that includes all component dependencies. It lives under `assembled/<level>/latest.htn` (gitignored) or `tests/fixtures/assembled/<level>.htn` (committed golden).

### Step 2 — Snapshot initial state

Save a named checkpoint before touching anything.

```
indhtn_snapshot_state sessionId "start"
```

This is the restore point used at the end and between plan explorations.

### Step 3 — Find plans

Run the planner without modifying state.

```
indhtn_find_plans sessionId "completePuzzle."
```

Record:
- Total number of solutions returned.
- The operator sequence of each solution (the flat list of primitive operators).

`indhtn_find_plans` populates the solution cache. State is **not** modified.

### Step 4 — Pick greedy plan

Select the shortest plan by operator count. On a tie, use index 0.

This is the plan that will be stepped through in Step 5.

### Step 5 — Step through operators

Apply each operator of the chosen plan one at a time.

```
indhtn_apply_operator sessionId "opMoveTo(player, roomA, roomB)"
```

After each call:
- Read `added` and `removed` from the response to see the exact state delta.
- State what the operator means in game terms (e.g., "player moves from roomA to roomB", "enemy acquires burning tag").

`indhtn_apply_operator` modifies state permanently. If you need to replay or try another plan, restore the snapshot first (Step 6).

### Step 6 — Report and restore

After completing the plan:

1. Call `indhtn_get_decomposition_tree sessionId 0` and walk it depth-first to identify which methods were invoked at each depth (field `taskName`, flag `isOperator`).
2. Summarise:
   - Method chain from goal to operators (one line per depth level).
   - Total operator count.
   - Whether alternative plans existed; compare the first operator of each solution to characterise how they diverge.
3. Restore initial state:

```
indhtn_restore_state sessionId "start"
```

---

## Tool reference

| Tool | Changes state? | When to use |
|------|---------------|-------------|
| `indhtn_find_plans` | No | Explore the full plan space |
| `indhtn_apply_operator` | Yes | Step through a plan by hand |
| `indhtn_apply_plan` | Yes | Apply a whole cached solution at once |
| `indhtn_snapshot_state` | No | Save a checkpoint |
| `indhtn_restore_state` | Yes | Undo back to a checkpoint |
| `indhtn_get_decomposition_tree` | No | Read how the planner decomposed the goal |
| `indhtn_preview_solution_facts` | No | Preview post-apply state without applying |

Always snapshot before applying operators if you intend to step through more than one plan.

---

## Goal format

Goals use `?varname` variable syntax and end with a period:

```
defeatAllGuards.
completePuzzle.
clearRoom(roomA).
```

Pass the goal string directly to `indhtn_find_plans`. The session's ruleset must already define a method for the goal predicate.

---

## Reading the decomposition tree

`indhtn_get_decomposition_tree` returns a tree JSON. Each node has:

| Field | Meaning |
|-------|---------|
| `taskName` | Method or operator name with bound arguments |
| `methodSignature` | Source method head (methods only) |
| `isOperator` | `true` for leaf operators, `false` for method nodes |
| `isSuccess` | Whether this branch succeeded |
| `children` | Child nodes (subtasks) |

Walk depth-first. Skip failed branches (`isSuccess: false`). At each method node, note the `methodSignature` — this is the strategy or action the planner chose. Operator nodes (`isOperator: true`) are the leaves that actually changed state.

---

## Example session skeleton

```
1.  indhtn_create_session
      → sessionId = "abc123"

2.  indhtn_load_files "abc123" ["assembled/puzzle1/latest.htn"]
      → ok: true

3.  indhtn_snapshot_state "abc123" "start"
      → ok: true

4.  indhtn_find_plans "abc123" "clearRoom(hallway)."
      → 2 solutions
        solution 0: opMoveTo(player,spawn,hallway), opGetAggro(guard1,player), opMoveTo(guard1,hallway,oilRoom), opApplyTag(guard1,burning)
        solution 1: opMoveTo(player,spawn,hallway), opGetAggro(guard2,player), ...

5.  greedy plan: solution 0 (4 operators)

6.  indhtn_apply_operator "abc123" "opMoveTo(player,spawn,hallway)"
      → added: [at(player,hallway)], removed: [at(player,spawn)]
      → "Player enters the hallway."

    indhtn_apply_operator "abc123" "opGetAggro(guard1,player)"
      → added: [hasAggro(guard1,player)], removed: []
      → "Guard1 locks onto player."

    indhtn_apply_operator "abc123" "opMoveTo(guard1,hallway,oilRoom)"
      → added: [at(guard1,oilRoom)], removed: [at(guard1,hallway)]
      → "Guard1 chases player into the oil room."

    indhtn_apply_operator "abc123" "opApplyTag(guard1,burning)"
      → added: [hasTag(guard1,burning)], removed: []
      → "Guard1 catches fire."

7.  indhtn_get_decomposition_tree "abc123" 0
      → clearRoom(hallway)
          defeatEnemy(guard1)         ← goal layer
            theBurn(guard1)           ← strategy layer
              lureToRoom(guard1, oilRoom)
                opGetAggro(guard1,player)   ← operator
                opMoveTo(guard1,...)        ← operator
              opApplyTag(guard1,burning)    ← operator

8.  indhtn_restore_state "abc123" "start"
      → ok: true
```
