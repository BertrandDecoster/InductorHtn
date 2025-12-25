# Clear Room

## Purpose

A high-level goal that clears a room of all enemies by defeating each one. Uses the defeat_enemy goal for each enemy present in the target room.

## Layer

goal

## Dependencies

- `primitives/locomotion` - For entity movement
- `primitives/tags` - For applying effects
- `primitives/aggro` - For enemy management
- `strategies/the_burn` - Fire + oil strategy
- `strategies/the_slipstream` - Ice slide into hazard strategy
- `goals/defeat_enemy` - Individual enemy defeat

## Methods

| Method | Description |
|--------|-------------|
| `clearRoom(?room)` | Main goal: defeat all enemies in room |

## Required Facts

| Fact | Description |
|------|-------------|
| `at(?entity, ?room)` | Entity location |
| `isEnemy(?entity)` | Entity is an enemy |

## Parameters

No configurable parameters.

## Examples

### Example 1: Room with single enemy

**Given:**
- `at(enemy1, roomA)`
- `isEnemy(enemy1)`
- `at(player, roomA)`
- `roomHasHazard(roomB, oil)`
- `canApplyTag(player, burning)`
- `connected(roomA, roomB)`
- `vulnerableTo(enemy1, burning)`

**When:**
- `clearRoom(roomA)`

**Then:**
- Plan defeats enemy1
- Final state has: `hasTag(enemy1, burning)`

### Example 2: Room with multiple enemies

**Given:**
- `at(enemy1, roomA)`
- `at(enemy2, roomA)`
- `isEnemy(enemy1)`
- `isEnemy(enemy2)`
- `at(player, roomA)`
- `roomHasHazard(roomB, oil)`
- `canApplyTag(player, burning)`
- `connected(roomA, roomB)`
- `vulnerableTo(enemy1, burning)`
- `vulnerableTo(enemy2, burning)`

**When:**
- `clearRoom(roomA)`

**Then:**
- Plan defeats both enemies
- Final state has tags on both enemies

### Example 3: Empty room

**Given:**
- No enemies in roomA

**When:**
- `clearRoom(roomA)`

**Then:**
- Empty plan (nothing to do)

### Example 4: Undefeatable enemy

**Given:**
- `at(enemy1, roomA)`
- `isEnemy(enemy1)`
- No available hazards or abilities

**When:**
- `clearRoom(roomA)`

**Then:**
- Planning fails (cannot defeat enemy)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | All enemies affected | Every enemy in room receives a status tag |
| P2 | Uses defeat_enemy | Delegates to defeat_enemy for each enemy |
| P3 | Empty room succeeds | Room with no enemies returns empty plan |
