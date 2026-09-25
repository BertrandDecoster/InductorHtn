# GH Doors

## Purpose

Door and pressure-plate primitive for GameHack domains. A locked door is opened by two allies stepping simultaneously on two distinct pressure plates linked to that door. Decomposes into one lens-dispatched operator (synchronized plate activation) followed by a pure state-mutation operator (unlock).

The compound operator `opSynchronizeOnPlates` is intentionally a marker in HTN state: its real effect happens in the runtime (via SynchroLens materializing Synchro cells at the plate positions). The subsequent `opUnlock` records the new world state once the lens reports success.

## Layer

primitive

## Dependencies

(none)

## Operators

| Operator | Description |
|----------|-------------|
| `opSynchronizeOnPlates(?a1, ?a2, ?p1, ?p2)` | Marker operator dispatched to SynchroLens. Lens materializes Synchro cells at the two plate positions and succeeds when both allies stand on them the same tick. |
| `opUnlock(?d)` | Pure state mutation: removes `locked(?d)`. |

## Methods

| Method | Description |
|--------|-------------|
| `unlockDoor(?d)` | Given a locked door, two plates linked to it, and two distinct allies, synchronize on plates then unlock. No-op if already unlocked. |

## Required Facts

| Fact | Description |
|------|-------------|
| `locked(?door)` | Door is currently locked (absence means unlocked) |
| `plateOpens(?plate, ?door)` | Stepping on this plate contributes to opening this door |
| `ally(?entity)` | Entity is an ally (same convention as gh_aggro) |

## Examples

### Example 1: Basic unlock with two allies

**Given:**
- `locked(door1)`, `plateOpens(plate1, door1)`, `plateOpens(plate2, door1)`
- `ally(companion1)`, `ally(companion2)`

**When:**
- `unlockDoor(door1)`

**Then:**
- Plan contains: `opSynchronizeOnPlates(companion1, companion2, plate1, plate2)` (or symmetric binding), `opUnlock(door1)`
- Final state no longer has `locked(door1)`

### Example 2: Already unlocked is no-op

**Given:**
- `plateOpens(plate1, door1)`, `plateOpens(plate2, door1)`, `ally(companion1)`, `ally(companion2)`
- (No `locked(door1)` fact)

**When:**
- `unlockDoor(door1)`

**Then:**
- Plan is empty (no operators)

### Example 3: No allies - planning fails

**Given:**
- `locked(door1)`, `plateOpens(plate1, door1)`, `plateOpens(plate2, door1)`

**When:**
- `unlockDoor(door1)`

**Then:**
- Planning fails (no two allies available)

### Example 4: Only one plate linked - planning fails

**Given:**
- `locked(door1)`, `plateOpens(plate1, door1)`
- `ally(companion1)`, `ally(companion2)`

**When:**
- `unlockDoor(door1)`

**Then:**
- Planning fails (need two distinct plates)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Atomic unlock | `unlockDoor` either produces a complete plan or fails — no partial unlocks. |
| P2 | Distinct plates | Two distinct plates linked to the door are required (`\==(?p1, ?p2)`). |
| P3 | Distinct allies | Two distinct allies are required (`\==(?a1, ?a2)`). |
| P4 | Idempotent | Calling `unlockDoor` on an already-unlocked door is a no-op (empty plan). |
