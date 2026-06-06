# pushable

## Purpose

Mastery challenge: agent must push a movable object to its target location
(Sokoban-style). The agent must navigate to the correct push position
(behind the object relative to the push direction) and then execute the push.

Supports single-push and two-push sequences for puzzle variety.

## Layer

challenges

## Dependencies

- `challenges/nav_obstacle` -- provides `navigateTo` and `opMoveTo`

## Operators

| Operator | Description |
|----------|-------------|
| `opPush(?obj, ?objLoc, ?target)` | Push object from `?objLoc` to `?target`. Deletes `objectAt(?obj, ?objLoc)`, adds `objectAt(?obj, ?target)`. Agent must be at the push-from position before this executes. |

## Methods

| Method | Description |
|--------|-------------|
| `pushToTarget(?obj)` | Push `?obj` to the location declared by `targetFor(?obj, ?target)`. Handles single-push and two-push sequences. |

## Required Facts

| Fact | Description |
|------|-------------|
| `at(agent, ?location)` | Current agent location |
| `objectAt(?obj, ?location)` | Current object location |
| `targetFor(?obj, ?targetLoc)` | Where the object must be pushed to |
| `connected(?from, ?to)` | Traversable link between locations |
| `blocked(?location)` | Impassable location (from nav_obstacle) |

## Examples

### Example 1: Single push to target

**Given:**
- `at(agent, startLoc)`
- `objectAt(box1, midLoc)`
- `targetFor(box1, goalLoc)`
- `connected(startLoc, midLoc)`, `connected(midLoc, goalLoc)`

**When:**
- `pushToTarget(box1)`

**Then:**
- Plan: navigate to push position behind box, then push
- Plan contains: `opPush(box1, midLoc, goalLoc)`
- Final state has: `objectAt(box1, goalLoc)`
- Final state does not have: `objectAt(box1, midLoc)`

### Example 2: No valid push position -- no plan

**Given:**
- `at(agent, startLoc)`
- `objectAt(box1, midLoc)`
- `targetFor(box1, goalLoc)`
- No connection from any location to midLoc (cannot get behind box)

**When:**
- `pushToTarget(box1)`

**Then:**
- Planning fails (no way to position agent for push)

### Example 3: Two-push sequence

**Given:**
- `at(agent, a)`
- `objectAt(box1, b)`
- `targetFor(box1, d)`
- `connected(a, b)`, `connected(b, c)`, `connected(c, d)`, `connected(a, c)`

**When:**
- `pushToTarget(box1)`

**Then:**
- Plan contains two `opPush` calls (via c, then to d)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Object at target | After successful plan, `objectAt(box, target)` is true |
| P2 | Object not at origin | After plan, object is no longer at original location |
| P3 | No push without approach | Every `opPush` is preceded by a `navigateTo` to the push-from position |
