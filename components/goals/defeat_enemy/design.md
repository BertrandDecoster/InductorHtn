# Defeat Enemy

## Purpose

A high-level goal that defeats an enemy by selecting the appropriate strategy based on enemy vulnerabilities and available environmental hazards.

This goal orchestrates strategies like "the_burn" and "the_slipstream" to defeat enemies without direct combat.

## Layer

goal

## Dependencies

- `primitives/locomotion` - For entity movement
- `primitives/tags` - For applying effects
- `primitives/aggro` - For enemy management
- `strategies/the_burn` - Fire + oil strategy
- `strategies/the_slipstream` - Ice slide into hazard strategy

## Methods

| Method | Description |
|--------|-------------|
| `defeatEnemy(?enemy)` | Main goal: select and execute best strategy |

## Required Facts

| Fact | Description |
|------|-------------|
| `at(?entity, ?room)` | Entity location |
| `vulnerableTo(?enemy, ?element)` | Enemy weakness |
| `roomHasHazard(?room, ?hazard)` | Room contains a hazard |
| `canApplyTag(?entity, ?tag)` | Entity has ability to apply tag |

## Parameters

No configurable parameters.

## Examples

### Example 1: Enemy vulnerable to fire near oil

**Given:**
- `at(enemy1, roomA)`
- `vulnerableTo(enemy1, burning)`
- `roomHasHazard(roomB, oil)`
- `canApplyTag(player, burning)`
- `connected(roomA, roomB)`

**When:**
- `defeatEnemy(enemy1)`

**Then:**
- Uses theBurn strategy
- Final state has: `hasTag(enemy1, burning)`

### Example 2: Enemy vulnerable to cold near spikes

**Given:**
- `at(enemy1, roomA)`
- `vulnerableTo(enemy1, wounded)`
- `roomHasHazard(roomB, spikes)`
- `connected(roomA, roomB)`
- `canApplyTag(arcanist, frozen)`

**When:**
- `defeatEnemy(enemy1)`

**Then:**
- Uses theSlipstream strategy
- Final state has: `at(enemy1, roomB)`, `hasTag(enemy1, wounded)`

### Example 3: No matching strategy

**Given:**
- `at(enemy1, roomA)`
- `vulnerableTo(enemy1, poison)`
- No poison hazard available

**When:**
- `defeatEnemy(enemy1)`

**Then:**
- Planning fails

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | Enemy affected | Enemy receives a status tag |
| P2 | Strategy selection | Correct strategy chosen based on vulnerabilities |
| P3 | Requires vulnerability match | Must have matching enemy weakness and hazard |
