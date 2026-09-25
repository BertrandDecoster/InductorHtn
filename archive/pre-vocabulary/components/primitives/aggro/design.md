# Aggro

## Purpose

Manage enemy threat (aggro) targeting and following behavior. When an enemy has aggro on a target, they will follow that target. This enables tactics like luring enemies to specific locations.

## Layer

primitive

## Dependencies

- `primitives/locomotion` - For enemy movement when following targets

## Operators

| Operator | Description |
|----------|-------------|
| `opGetAggro(?enemy)` | Enemy gains aggro on player |
| `opLoseAggro(?enemy)` | Enemy loses aggro |

## Methods

| Method | Description |
|--------|-------------|
| `getAggro(?enemy)` | Gain aggro if not already have it |
| `loseAggro(?enemy)` | Lose aggro if currently have it |
| `enemyFollows(?enemy, ?target)` | Enemy moves to target's location |
| `lureToRoom(?enemy, ?targetRoom)` | Composite: player moves, gets aggro, enemy follows |

## Required Facts

| Fact | Description |
|------|-------------|
| `hasAggro(?enemy, ?target)` | Enemy is targeting this entity |
| `at(?entity, ?room)` | Entity location (from locomotion) |
| `connected(?from, ?to)` | Room connections (from locomotion) |

## Parameters

No configurable parameters.

## Examples

### Example 1: Gain aggro

**Given:**
- Enemy has no aggro

**When:**
- `getAggro(enemy1)`

**Then:**
- Plan contains: `opGetAggro(enemy1)`
- Final state has: `hasAggro(enemy1, player)`

### Example 2: Already has aggro (no-op)

**Given:**
- `hasAggro(enemy1, player)`

**When:**
- `getAggro(enemy1)`

**Then:**
- Plan contains: empty (no operators)
- Final state has: `hasAggro(enemy1, player)`

### Example 3: Enemy follows to different room

**Given:**
- `hasAggro(enemy1, player)`
- `at(player, roomB)`
- `at(enemy1, roomA)`
- `connected(roomA, roomB)`

**When:**
- `enemyFollows(enemy1, player)`

**Then:**
- Plan contains: `opMoveTo(enemy1, roomA, roomB)`
- Final state has: `at(enemy1, roomB)`

### Example 4: Lure enemy to room

**Given:**
- `at(player, roomA)`
- `at(enemy1, roomA)`
- `connected(roomA, roomB)`

**When:**
- `lureToRoom(enemy1, roomB)`

**Then:**
- Plan contains player and enemy movement plus aggro
- Final state has: `at(player, roomB)`, `at(enemy1, roomB)`, `hasAggro(enemy1, player)`

### Example 5: Lose aggro

**Given:**
- `hasAggro(enemy1, player)`

**When:**
- `loseAggro(enemy1)`

**Then:**
- Plan contains: `opLoseAggro(enemy1)`
- Final state does not have: `hasAggro(enemy1, player)`

### Example 6: Lose aggro when none (no-op)

**Given:**
- Enemy has no aggro

**When:**
- `loseAggro(enemy1)`

**Then:**
- Plan contains: empty (no operators)

### Example 7: Enemy already in same room as player

**Given:**
- `hasAggro(enemy1, player)`, `at(player, roomA)`, `at(enemy1, roomA)`

**When:**
- `enemyFollows(enemy1, player)`

**Then:**
- Plan contains: empty (no movement needed)

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Single target | An enemy can only have aggro on one target at a time |
| P2 | Following requires aggro | enemyFollows only moves if hasAggro exists |
| P3 | Lure is composite | lureToRoom combines player move + aggro + enemy follow |
