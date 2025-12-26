# Puzzle 1: The Grease Trap

## Overview

A introductory puzzle that demonstrates the core mechanics: luring enemies into hazards using theBurn and theSlipstream strategies.

Based on Level 1 concepts from PUZZLE_IDEAS.md, adapted to room-level HTN planning.

## Layout

```
    [storage]     [generator]
         \           /
          \         /
           [main]
             |
        [corridor]
             |
          [exit]
```

## Rooms

| Room | Contents | Hazards |
|------|----------|---------|
| main | Player, Warden | - |
| storage | Enemy (guard1) | Oil pool |
| generator | - | Electricity |
| corridor | Enemy (guard2) | - |
| exit | (goal destination) | - |

## Initial State

- `at(player, main)` - Player starts in main room
- `at(warden, main)` - Warden companion in main room
- `at(guard1, storage)` - Guard enemy in storage
- `at(guard2, corridor)` - Guard enemy in corridor
- `isEnemy(guard1)` - guard1 is hostile
- `isEnemy(guard2)` - guard2 is hostile
- `roomHasHazard(storage, oil)` - Oil pool in storage
- `roomHasHazard(generator, electricity)` - Electrical hazard
- `connected(main, storage)` - Rooms are connected
- `connected(main, generator)`
- `connected(main, corridor)`
- `connected(corridor, exit)`
- `canApplyTag(player, burning)` - Player can ignite
- `canApplyTag(arcanist, frozen)` - (Arcanist ability if present)
- `vulnerableTo(guard1, burning)` - Guard1 weak to fire
- `vulnerableTo(guard2, electrified)` - Guard2 weak to electricity

## Goals

1. **Primary Goal**: Reach the exit with all guards defeated
   - `clearRoom(storage)` - Defeat guard1
   - `clearRoom(corridor)` - Defeat guard2
   - `moveTo(player, exit)` - Reach exit

## HTN Solutions

### Solution A: The Grease Trap
1. Player lures guard1 to storage (already there)
2. Player ignites oil in storage → guard1 gets burning tag
3. Player uses theSlipstream on guard2 (freeze corridor, push into generator)
4. Player moves to exit

### Solution B: Double Slipstream
(Requires arcanist companion with freeze ability)
1. Freeze path from storage to generator, push guard1 into electricity
2. Freeze path from corridor to generator, push guard2 into electricity
3. Player moves to exit

## Examples

### Example 1: Puzzle can be completed

**Given:** Initial level state
**When:** `completePuzzle`
**Then:** Plan exists with operators

### Example 2: Guard1 uses theBurn strategy

**Given:** guard1 vulnerable to burning, storage has oil
**When:** `defeatEnemy(guard1)`
**Then:** guard1 has burning tag

### Example 3: Guard2 uses theSlipstream strategy

**Given:** guard2 vulnerable to electrified, generator has electricity
**When:** `defeatEnemy(guard2)`
**Then:** guard2 has electrified tag

## Properties

| ID | Property | Description |
|----|----------|-------------|
| P1 | All enemies tagged | After completion, all enemies have status tags |
| P2 | Player at exit | After completion, player is at exit room |
| P3 | Valid strategy selection | Strategy matches enemy vulnerability |

## Success Criteria

- All enemies have status tags (burning, electrified, etc.)
- Player is at exit room
